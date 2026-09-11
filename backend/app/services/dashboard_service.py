"""
Application Service for Phase 14 Dashboard, Insight Workspace, and Analytical Storytelling.
Coordinates dashboard lifecycle, version history, optimistic concurrency, and data hydration.
"""

from datetime import datetime, timezone
import os
from typing import Any, Dict, List, Optional, Tuple
import uuid

from fastapi import HTTPException

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.dashboard.hydration import DashboardHydrator
from backend.app.engines.dashboard.models import (
    ActionType,
    ComponentCreateRequest,
    ComponentPosition,
    ComponentProvenance,
    ComponentSize,
    ComponentSource,
    ComponentType,
    ComponentUpdateRequest,
    Dashboard,
    DashboardAction,
    DashboardActionValidateRequest,
    DashboardActionValidateResponse,
    DashboardComponent,
    DashboardCreateRequest,
    DashboardDataResponse,
    DashboardDuplicateRequest,
    DashboardFilter,
    DashboardFilterValidateRequest,
    DashboardFilterValidateResponse,
    DashboardLayout,
    DashboardTheme,
    DashboardUpdateRequest,
    DashboardVersion,
    FilterOperator,
    RefreshPolicy,
    SourceType,
)
from backend.app.engines.dashboard.repository import (
    DashboardHistoryRepository,
    DashboardRepository,
)
from backend.app.engines.dashboard.security import (
    DashboardSecurityError,
    DashboardSecurityValidator,
)
from backend.app.services.cleaning.version_service import VersionService
from backend.app.services.dataset_service import dataset_service


class DashboardService:
    """
    Coordinates dashboard state, layout, versioning, component management,
    and delegation to deterministic analytical engines.
    """

    def __init__(self):
        self._repo = DashboardRepository()
        self._history_repo = DashboardHistoryRepository()
        self._hydrator = DashboardHydrator()
        self._version_service = VersionService()

    def _resolve_parquet_path(self, dataset_id: str, version_id: Optional[str] = None) -> Tuple[str, Optional[str]]:
        """
        Resolves the active version ID and absolute parquet file path for a dataset.
        """
        try:
            versions = self._version_service.list_versions(dataset_id)
            if versions:
                target_ver = None
                if version_id:
                    for v in versions:
                        if v.version_id == version_id:
                            target_ver = v
                            break
                if not target_ver:
                    target_ver = versions[-1]  # Latest active version
                return target_ver.version_id, target_ver.parquet_file_path
        except Exception:
            pass

        # Fallback to dataset root parquet
        try:
            ds = dataset_service.get_dataset(dataset_id)
            if ds:
                p_path = getattr(ds, "parquet_file_path", None) or os.path.join(
                    settings.DATA_PROCESSED_DIR, f"{dataset_id}_v1.parquet"
                )
                return "v1", p_path if os.path.exists(p_path) else None
        except Exception:
            pass

        return "v1", None

    # ─────────────────────────────────────────────────────────
    # CRUD & Lifecycle Operations
    # ─────────────────────────────────────────────────────────

    def create_dashboard(self, request: DashboardCreateRequest) -> Dashboard:
        """
        Creates a new Dashboard entity. Applies optional starter template if specified.
        """
        active_ver_id, _ = self._resolve_parquet_path(request.dataset_id, request.dataset_version_id)

        dashboard = Dashboard(
            name=request.name.strip(),
            description=request.description.strip() if request.description else None,
            dataset_id=request.dataset_id,
            dataset_version_id=active_ver_id,
            layout=DashboardLayout(),
            components=[],
            filters=[],
            theme=DashboardTheme(),
            version=1,
        )

        # Apply template components if requested
        if request.template_id:
            self._apply_template(dashboard, request.template_id)

        # Security bounds validation
        DashboardSecurityValidator.validate_dashboard_bounds(dashboard)

        # Compute initial hash & save
        saved = self._repo.save(dashboard)

        # Save initial version v1 in history
        self._history_repo.save_version(
            DashboardVersion(
                dashboard_id=saved.dashboard_id,
                version_number=1,
                snapshot=saved,
                comment="Initial dashboard creation",
            )
        )

        logger.info(f"Created dashboard {saved.dashboard_id} ('{saved.name}') on dataset {saved.dataset_id}")
        return saved

    def get_dashboard(self, dashboard_id: str) -> Dashboard:
        """
        Retrieves a dashboard by ID. Raises 404 if not found.
        """
        d = self._repo.get_by_id(dashboard_id)
        if not d:
            raise HTTPException(status_code=404, detail=f"Dashboard '{dashboard_id}' not found.")
        return d

    def list_dashboards(
        self,
        dataset_id: Optional[str] = None,
        search: Optional[str] = None,
    ) -> List[Dashboard]:
        """
        Lists all dashboards matching optional dataset filter and search term.
        """
        return self._repo.get_all(dataset_id=dataset_id, search=search)

    def update_dashboard(
        self,
        dashboard_id: str,
        request: DashboardUpdateRequest,
    ) -> Dashboard:
        """
        Updates dashboard state with optimistic concurrency protection.
        """
        current = self.get_dashboard(dashboard_id)

        # Optimistic concurrency check
        if request.expected_version is not None and request.expected_version != current.version:
            raise HTTPException(
                status_code=409,
                detail=(
                    f"Concurrency conflict: Dashboard was modified by another session "
                    f"(expected v{request.expected_version}, current is v{current.version})."
                ),
            )
        if request.expected_hash and current.configuration_hash and request.expected_hash != current.configuration_hash:
            raise HTTPException(
                status_code=409,
                detail="Concurrency conflict: Dashboard configuration hash mismatch.",
            )

        # Apply updates
        if request.name is not None:
            current.name = request.name.strip()
        if request.description is not None:
            current.description = request.description.strip()
        if request.layout is not None:
            current.layout = request.layout
        if request.components is not None:
            current.components = request.components
        if request.filters is not None:
            current.filters = request.filters
        if request.variables is not None:
            current.variables = request.variables
        if request.theme is not None:
            current.theme = request.theme

        # Increment version and update timestamp
        current.version += 1
        current.updated_at = datetime.now(timezone.utc)

        # Security check
        try:
            DashboardSecurityValidator.validate_dashboard_bounds(current)
        except DashboardSecurityError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Save updated dashboard
        saved = self._repo.save(current)

        # Record history snapshot
        self._history_repo.save_version(
            DashboardVersion(
                dashboard_id=saved.dashboard_id,
                version_number=saved.version,
                snapshot=saved,
                comment=f"Updated to version {saved.version}",
            )
        )

        logger.info(f"Updated dashboard {dashboard_id} to v{saved.version}")
        return saved

    def delete_dashboard(self, dashboard_id: str) -> bool:
        """
        Deletes a dashboard by ID.
        """
        # Ensure it exists
        self.get_dashboard(dashboard_id)
        deleted = self._repo.delete(dashboard_id)
        logger.info(f"Deleted dashboard {dashboard_id}: {deleted}")
        return deleted

    def duplicate_dashboard(
        self,
        dashboard_id: str,
        request: DashboardDuplicateRequest,
    ) -> Dashboard:
        """
        Duplicates an existing dashboard, preserving layout, components, and provenance references.
        """
        source = self.get_dashboard(dashboard_id)

        target_name = request.new_name or f"{source.name} (Copy)"
        target_dataset_id = request.dataset_id or source.dataset_id
        target_version_id = request.dataset_version_id or source.dataset_version_id

        new_dsh_id = f"dsh_{uuid.uuid4().hex[:12]}"

        # Deep copy components with fresh component_ids
        new_components: List[DashboardComponent] = []
        for cmp in source.components:
            cmp_dict = cmp.model_dump()
            cmp_dict["component_id"] = f"cmp_{uuid.uuid4().hex[:10]}"
            cmp_dict["dashboard_id"] = new_dsh_id
            cmp_dict["created_at"] = datetime.now(timezone.utc)
            cmp_dict["updated_at"] = datetime.now(timezone.utc)
            new_components.append(DashboardComponent.model_validate(cmp_dict))

        # Deep copy filters with fresh filter_ids
        new_filters: List[DashboardFilter] = []
        for flt in source.filters:
            flt_dict = flt.model_dump()
            flt_dict["filter_id"] = f"flt_{uuid.uuid4().hex[:10]}"
            new_filters.append(DashboardFilter.model_validate(flt_dict))

        cloned = Dashboard(
            dashboard_id=new_dsh_id,
            name=target_name,
            description=source.description,
            dataset_id=target_dataset_id,
            dataset_version_id=target_version_id,
            layout=source.layout,
            components=new_components,
            filters=new_filters,
            variables=source.variables,
            theme=source.theme,
            version=1,
        )

        saved = self._repo.save(cloned)
        self._history_repo.save_version(
            DashboardVersion(
                dashboard_id=saved.dashboard_id,
                version_number=1,
                snapshot=saved,
                comment=f"Duplicated from {source.dashboard_id} ('{source.name}')",
            )
        )

        logger.info(f"Duplicated dashboard {dashboard_id} into {saved.dashboard_id}")
        return saved

    # ─────────────────────────────────────────────────────────
    # Component Lifecycle Operations
    # ─────────────────────────────────────────────────────────

    def add_component(
        self,
        dashboard_id: str,
        request: ComponentCreateRequest,
    ) -> DashboardComponent:
        """
        Adds a new component to a dashboard and bumps version.
        """
        dashboard = self.get_dashboard(dashboard_id)

        if len(dashboard.components) >= settings.DASHBOARD_MAX_COMPONENTS:
            raise HTTPException(
                status_code=400,
                detail=f"Cannot add component: Limit of {settings.DASHBOARD_MAX_COMPONENTS} components reached.",
            )

        # Default position: stack after current max Y
        if request.position is None:
            max_y = max([c.position.y + c.size.height for c in dashboard.components], default=0)
            pos = ComponentPosition(x=0, y=max_y)
        else:
            pos = request.position

        size = request.size or ComponentSize(width=6, height=4)

        # Sanitize text narrative if TEXT
        config = request.configuration
        if request.type == ComponentType.TEXT and "content" in config:
            config["content"] = DashboardSecurityValidator.sanitize_text(str(config["content"]))

        new_cmp = DashboardComponent(
            dashboard_id=dashboard_id,
            type=request.type,
            title=request.title.strip(),
            subtitle=request.subtitle.strip() if request.subtitle else None,
            description=request.description.strip() if request.description else None,
            position=pos,
            size=size,
            configuration=config,
            source=request.source,
            dataset_id=request.source.dataset_id or dashboard.dataset_id,
            dataset_version_id=request.source.dataset_version_id or dashboard.dataset_version_id,
            result_reference=request.result_reference,
            visualization_reference=request.visualization_reference,
            filter_bindings=request.filter_bindings,
            refresh_policy=request.refresh_policy,
        )

        dashboard.components.append(new_cmp)
        dashboard.version += 1
        dashboard.updated_at = datetime.now(timezone.utc)

        saved = self._repo.save(dashboard)
        self._history_repo.save_version(
            DashboardVersion(
                dashboard_id=saved.dashboard_id,
                version_number=saved.version,
                snapshot=saved,
                comment=f"Added component '{new_cmp.title}'",
            )
        )

        return new_cmp

    def update_component(
        self,
        dashboard_id: str,
        component_id: str,
        request: ComponentUpdateRequest,
    ) -> DashboardComponent:
        """
        Updates an existing component and bumps version.
        """
        dashboard = self.get_dashboard(dashboard_id)
        cmp_idx = next((i for i, c in enumerate(dashboard.components) if c.component_id == component_id), None)
        if cmp_idx is None:
            raise HTTPException(status_code=404, detail=f"Component '{component_id}' not found.")

        target = dashboard.components[cmp_idx]

        if request.title is not None:
            target.title = request.title.strip()
        if request.subtitle is not None:
            target.subtitle = request.subtitle.strip()
        if request.description is not None:
            target.description = request.description.strip()
        if request.position is not None:
            target.position = request.position
        if request.size is not None:
            target.size = request.size
        if request.configuration is not None:
            if target.type == ComponentType.TEXT and "content" in request.configuration:
                request.configuration["content"] = DashboardSecurityValidator.sanitize_text(
                    str(request.configuration["content"])
                )
            target.configuration = request.configuration
        if request.source is not None:
            target.source = request.source
            target.dataset_id = request.source.dataset_id
            target.dataset_version_id = request.source.dataset_version_id
        if request.filter_bindings is not None:
            target.filter_bindings = request.filter_bindings
        if request.refresh_policy is not None:
            target.refresh_policy = request.refresh_policy
        if request.visibility is not None:
            target.visibility = request.visibility

        target.updated_at = datetime.now(timezone.utc)

        dashboard.version += 1
        dashboard.updated_at = datetime.now(timezone.utc)

        saved = self._repo.save(dashboard)
        self._history_repo.save_version(
            DashboardVersion(
                dashboard_id=saved.dashboard_id,
                version_number=saved.version,
                snapshot=saved,
                comment=f"Updated component '{target.title}'",
            )
        )

        return target

    def delete_component(self, dashboard_id: str, component_id: str) -> bool:
        """
        Deletes a component from the dashboard.
        """
        dashboard = self.get_dashboard(dashboard_id)
        orig_len = len(dashboard.components)
        dashboard.components = [c for c in dashboard.components if c.component_id != component_id]

        if len(dashboard.components) == orig_len:
            raise HTTPException(status_code=404, detail=f"Component '{component_id}' not found.")

        dashboard.version += 1
        dashboard.updated_at = datetime.now(timezone.utc)

        saved = self._repo.save(dashboard)
        self._history_repo.save_version(
            DashboardVersion(
                dashboard_id=saved.dashboard_id,
                version_number=saved.version,
                snapshot=saved,
                comment=f"Removed component '{component_id}'",
            )
        )
        return True

    def duplicate_component(self, dashboard_id: str, component_id: str) -> DashboardComponent:
        """
        Duplicates a component within the same dashboard.
        """
        dashboard = self.get_dashboard(dashboard_id)
        src = next((c for c in dashboard.components if c.component_id == component_id), None)
        if not src:
            raise HTTPException(status_code=404, detail=f"Component '{component_id}' not found.")

        data_dict = src.model_dump()
        data_dict["component_id"] = f"cmp_{uuid.uuid4().hex[:10]}"
        data_dict["title"] = f"{src.title} (Copy)"
        # Shift Y offset downwards to avoid direct overlap
        data_dict["position"]["y"] = src.position.y + src.size.height
        data_dict["created_at"] = datetime.now(timezone.utc)
        data_dict["updated_at"] = datetime.now(timezone.utc)

        cloned = DashboardComponent.model_validate(data_dict)
        dashboard.components.append(cloned)
        dashboard.version += 1
        dashboard.updated_at = datetime.now(timezone.utc)

        saved = self._repo.save(dashboard)
        self._history_repo.save_version(
            DashboardVersion(
                dashboard_id=saved.dashboard_id,
                version_number=saved.version,
                snapshot=saved,
                comment=f"Duplicated component '{src.title}'",
            )
        )
        return cloned

    # ─────────────────────────────────────────────────────────
    # Data Hydration & Refresh
    # ─────────────────────────────────────────────────────────

    def get_dashboard_data(self, dashboard_id: str) -> DashboardDataResponse:
        """
        Retrieves hydrated bounded data for all components in the dashboard.
        Enforces filter boundaries and detects stale dataset version references.
        """
        dashboard = self.get_dashboard(dashboard_id)
        active_ver_id, parquet_path = self._resolve_parquet_path(dashboard.dataset_id, dashboard.dataset_version_id)

        component_data, warnings, stale_count = self._hydrator.hydrate_dashboard(
            components=dashboard.components,
            active_dataset_id=dashboard.dataset_id,
            active_version_id=active_ver_id,
            global_filters=dashboard.filters,
            parquet_path=parquet_path,
        )

        return DashboardDataResponse(
            dashboard_id=dashboard_id,
            version=dashboard.version,
            components=component_data,
            warnings=warnings,
            stale_components_count=stale_count,
        )

    def refresh_dashboard(
        self,
        dashboard_id: str,
        component_ids: Optional[List[str]] = None,
    ) -> DashboardDataResponse:
        """
        Explicitly triggers a refresh of component presentation data.
        """
        return self.get_dashboard_data(dashboard_id)

    # ─────────────────────────────────────────────────────────
    # Versioning & History
    # ─────────────────────────────────────────────────────────

    def list_versions(self, dashboard_id: str) -> List[DashboardVersion]:
        """
        Lists all historic versions of a dashboard.
        """
        self.get_dashboard(dashboard_id)
        return self._history_repo.get_versions(dashboard_id)

    def get_version(self, dashboard_id: str, version_number: int) -> DashboardVersion:
        """
        Retrieves a specific historic version snapshot.
        """
        ver = self._history_repo.get_version(dashboard_id, version_number)
        if not ver:
            raise HTTPException(
                status_code=404,
                detail=f"Version {version_number} not found for dashboard '{dashboard_id}'.",
            )
        return ver

    def restore_version(self, dashboard_id: str, version_number: int) -> Dashboard:
        """
        Restores a previous version by creating a NEW version snapshot, preserving full history.
        """
        current = self.get_dashboard(dashboard_id)
        target_ver = self.get_version(dashboard_id, version_number)

        # Create new version from snapshot
        new_version_num = current.version + 1
        snapshot = target_ver.snapshot

        current.name = snapshot.name
        current.description = snapshot.description
        current.layout = snapshot.layout
        current.components = snapshot.components
        current.filters = snapshot.filters
        current.variables = snapshot.variables
        current.theme = snapshot.theme
        current.version = new_version_num
        current.updated_at = datetime.now(timezone.utc)

        saved = self._repo.save(current)
        self._history_repo.save_version(
            DashboardVersion(
                dashboard_id=saved.dashboard_id,
                version_number=new_version_num,
                snapshot=saved,
                comment=f"Restored from version {version_number}",
            )
        )

        logger.info(f"Restored dashboard {dashboard_id} from v{version_number} to new v{new_version_num}")
        return saved

    # ─────────────────────────────────────────────────────────
    # Filter & Action Validation
    # ─────────────────────────────────────────────────────────

    def validate_filter(self, request: DashboardFilterValidateRequest) -> DashboardFilterValidateResponse:
        """
        Validates filter field against dataset schema and checks operator compatibility.
        """
        try:
            DashboardSecurityValidator.validate_filter(request.filter)
        except DashboardSecurityError as e:
            return DashboardFilterValidateResponse(
                valid=False,
                field_exists=False,
                operator_compatible=False,
                message=str(e),
            )

        # Check dataset schema
        _, parquet_path = self._resolve_parquet_path(request.dataset_id, request.dataset_version_id)
        field_exists = True
        if parquet_path and os.path.exists(parquet_path):
            import duckdb
            conn = duckdb.connect(":memory:")
            try:
                safe_p = parquet_path.replace("'", "''").replace("\\", "/")
                schema_cols = [c[0] for c in conn.execute(f"DESCRIBE SELECT * FROM read_parquet('{safe_p}')").fetchall()]
                field_exists = request.filter.field in schema_cols
            except Exception:
                field_exists = True
            finally:
                conn.close()

        return DashboardFilterValidateResponse(
            valid=field_exists,
            field_exists=field_exists,
            operator_compatible=True,
            message="Filter is valid." if field_exists else f"Field '{request.filter.field}' not found in dataset schema.",
        )

    def validate_action(self, request: DashboardActionValidateRequest) -> DashboardActionValidateResponse:
        """
        Validates an AI Analyst or UI mutating action before application.
        """
        act = request.action
        impact = f"Action {act.action_type.value} on dashboard {act.dashboard_id}"
        requires_conf = act.action_type in (
            ActionType.REMOVE_COMPONENT,
            ActionType.ADD_COMPONENT,
            ActionType.UPDATE_COMPONENT,
        )

        return DashboardActionValidateResponse(
            valid=True,
            action_type=act.action_type,
            requires_confirmation=requires_conf,
            impact_summary=impact,
            diff_preview=act.parameters,
        )

    def export_dashboard(self, dashboard_id: str, export_format: str = "json") -> Dict[str, Any]:
        """
        Exports dashboard configuration or data.
        """
        dashboard = self.get_dashboard(dashboard_id)
        if export_format.lower() == "json":
            return {
                "dashboard": dashboard.model_dump(mode="json"),
                "exported_at": datetime.now(timezone.utc).isoformat(),
            }
        raise HTTPException(status_code=400, detail=f"Export format '{export_format}' not supported. Use 'json'.")

    # ─────────────────────────────────────────────────────────
    # Starter Templates
    # ─────────────────────────────────────────────────────────

    def _apply_template(self, dashboard: Dashboard, template_id: str) -> None:
        """
        Populates starter component layouts for predefined templates.
        """
        now = datetime.now(timezone.utc)
        if template_id == "executive_overview":
            dashboard.components = [
                DashboardComponent(
                    dashboard_id=dashboard.dashboard_id,
                    type=ComponentType.TEXT,
                    title="Executive Summary",
                    position=ComponentPosition(x=0, y=0),
                    size=ComponentSize(width=12, height=2),
                    configuration={"content": "### Executive Overview\nKey performance indicators and high-level trends across operations."},
                    source=ComponentSource(source_type=SourceType.MANUAL, dataset_id=dashboard.dataset_id, dataset_version_id=dashboard.dataset_version_id, engine="core"),
                    dataset_id=dashboard.dataset_id,
                    dataset_version_id=dashboard.dataset_version_id,
                ),
                DashboardComponent(
                    dashboard_id=dashboard.dashboard_id,
                    type=ComponentType.KPI,
                    title="Total Volume",
                    position=ComponentPosition(x=0, y=2),
                    size=ComponentSize(width=4, height=3),
                    configuration={"metric": "count", "formatting": "compact"},
                    source=ComponentSource(source_type=SourceType.SQL_RESULT, dataset_id=dashboard.dataset_id, dataset_version_id=dashboard.dataset_version_id, engine="duckdb"),
                    dataset_id=dashboard.dataset_id,
                    dataset_version_id=dashboard.dataset_version_id,
                ),
                DashboardComponent(
                    dashboard_id=dashboard.dashboard_id,
                    type=ComponentType.KPI,
                    title="Primary Metric",
                    position=ComponentPosition(x=4, y=2),
                    size=ComponentSize(width=4, height=3),
                    configuration={"metric": "avg", "formatting": "currency"},
                    source=ComponentSource(source_type=SourceType.SQL_RESULT, dataset_id=dashboard.dataset_id, dataset_version_id=dashboard.dataset_version_id, engine="duckdb"),
                    dataset_id=dashboard.dataset_id,
                    dataset_version_id=dashboard.dataset_version_id,
                ),
                DashboardComponent(
                    dashboard_id=dashboard.dashboard_id,
                    type=ComponentType.KPI,
                    title="Maximum Observation",
                    position=ComponentPosition(x=8, y=2),
                    size=ComponentSize(width=4, height=3),
                    configuration={"metric": "max", "formatting": "compact"},
                    source=ComponentSource(source_type=SourceType.SQL_RESULT, dataset_id=dashboard.dataset_id, dataset_version_id=dashboard.dataset_version_id, engine="duckdb"),
                    dataset_id=dashboard.dataset_id,
                    dataset_version_id=dashboard.dataset_version_id,
                ),
            ]
        elif template_id == "eda_quality":
            dashboard.components = [
                DashboardComponent(
                    dashboard_id=dashboard.dashboard_id,
                    type=ComponentType.EDA_FINDING,
                    title="Automated Data Quality Audit",
                    position=ComponentPosition(x=0, y=0),
                    size=ComponentSize(width=12, height=4),
                    configuration={"finding": {"title": "Dataset Baseline Audit", "description": "Continuous profiling of nullity, cardinality, and distributions."}},
                    source=ComponentSource(source_type=SourceType.EDA_RESULT, dataset_id=dashboard.dataset_id, dataset_version_id=dashboard.dataset_version_id, engine="eda"),
                    dataset_id=dashboard.dataset_id,
                    dataset_version_id=dashboard.dataset_version_id,
                ),
                DashboardComponent(
                    dashboard_id=dashboard.dashboard_id,
                    type=ComponentType.TABLE,
                    title="Sample Observations",
                    position=ComponentPosition(x=0, y=4),
                    size=ComponentSize(width=12, height=6),
                    configuration={"limit": 25},
                    source=ComponentSource(source_type=SourceType.SQL_RESULT, dataset_id=dashboard.dataset_id, dataset_version_id=dashboard.dataset_version_id, engine="duckdb"),
                    dataset_id=dashboard.dataset_id,
                    dataset_version_id=dashboard.dataset_version_id,
                ),
            ]


dashboard_service = DashboardService()
