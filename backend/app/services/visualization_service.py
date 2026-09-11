"""
Visualization Application Service.
Orchestrates recommendations, server-side data preparation, spec validation,
version compatibility, and saved visualization management.
"""

from datetime import datetime, timezone
import os
from typing import Any, Dict, List, Optional
import uuid

from backend.app.core.logging import logger
from backend.app.engines.visualization.data_preparer import VisualizationDataPreparer
from backend.app.engines.visualization.models import (
    ChartSpec,
    SavedVisualization,
    VisualizationHistoryEntry,
    VisualizationIntent,
    VisualizationProvenance,
    VisualizationRecommendation,
    VisualizationValidationResult,
)
from backend.app.engines.visualization.rules import ColumnContext
from backend.app.engines.visualization.recommender import VisualizationRecommender
from backend.app.engines.visualization.repository import (
    SavedVisualizationRepository,
    VisualizationHistoryRepository,
)
from backend.app.engines.visualization.validation import ChartSpecValidator
from backend.app.services.cleaning.version_service import VersionService
from backend.app.services.dataset_service import dataset_service
from backend.app.services.profiling_service import profiling_service
from backend.app.services.quality_service import QualityService


class VisualizationService:
    """
    Coordinates end-to-end visualization workflows:
    - Recommends charts from profiling and quality data
    - Validates specifications against dataset version schemas
    - Hydrates chart data using server-side DuckDB execution
    - Enforces version isolation and provenance
    - Manages saved visualizations
    """

    def __init__(self):
        self._recommender = VisualizationRecommender()
        self._validator = ChartSpecValidator()
        self._data_preparer = VisualizationDataPreparer()
        self._saved_repo = SavedVisualizationRepository()
        self._history_repo = VisualizationHistoryRepository()
        self._version_service = VersionService()
        self._quality_service = QualityService()

    def _resolve_version_and_path(
        self,
        dataset_id: str,
        version_id: Optional[str] = None,
    ) -> tuple[str, str]:
        """Resolves (version_id, parquet_file_path)."""
        if not version_id:
            version = self._version_service.get_or_create_v1(dataset_id)
            version_id = version.version_id
        else:
            version = self._version_service.get_version(dataset_id, version_id)
            if not version:
                version = self._version_service.get_or_create_v1(dataset_id)
                version_id = version.version_id

        parquet_path = version.storage_path
        if not os.path.exists(parquet_path):
            ds = dataset_service.get_dataset(dataset_id)
            if ds and hasattr(ds, "file_path") and os.path.exists(ds.file_path):
                parquet_path = ds.file_path
            else:
                raise ValueError(f"Parquet file not found for dataset {dataset_id} version {version_id}")

        return version_id, parquet_path

    def recommend_visualizations(
        self,
        dataset_id: str,
        version_id: Optional[str] = None,
        selected_fields: Optional[List[str]] = None,
        intent: Optional[VisualizationIntent] = None,
    ) -> List[VisualizationRecommendation]:
        """
        Generates deterministic chart recommendations for a dataset version.
        """
        resolved_version_id, _ = self._resolve_version_and_path(dataset_id, version_id)

        # 1. Fetch profiling metadata
        try:
            profile = profiling_service.get_profile(dataset_id)
        except Exception:
            profile = None

        col_contexts: Dict[str, ColumnContext] = {}
        row_count = 100

        if profile and profile.columns:
            row_count = profile.row_count or 100
            for col_name, c_prof in profile.columns.items():
                card = getattr(c_prof, "cardinality", None) or getattr(c_prof, "unique_count", 0)
                null_pct = getattr(c_prof, "null_percentage", 0.0)
                sem_type = getattr(c_prof, "semantic_type", "unknown")
                phys_type = getattr(c_prof, "physical_type", "string")

                col_contexts[col_name] = ColumnContext(
                    name=col_name,
                    physical_type=phys_type,
                    semantic_type=sem_type,
                    cardinality=card,
                    null_percentage=null_pct,
                    is_constant=(card == 1),
                    is_identifier=(card == row_count and card > 20 and sem_type != "numeric"),
                )

        # 2. Quality report for missingness & warnings
        quality_issues = []
        try:
            q_report = self._quality_service.get_cached_report(dataset_id)
            if q_report and hasattr(q_report, "issues"):
                quality_issues = [i.model_dump() if hasattr(i, "model_dump") else dict(i) for i in q_report.issues]
        except Exception:
            pass

        return self._recommender.recommend(
            columns=col_contexts,
            row_count=row_count,
            selected_fields=selected_fields,
            intent=intent,
            quality_issues=quality_issues,
        )

    def validate_chart_spec(
        self,
        spec: ChartSpec,
    ) -> VisualizationValidationResult:
        """
        Validates ChartSpec fields against the active or bound dataset version schema.
        """
        try:
            resolved_version_id, _ = self._resolve_version_and_path(
                spec.dataset_id, spec.dataset_version_id
            )
            profile = profiling_service.get_profile(spec.dataset_id)
            schema_cols = {k: getattr(v, "physical_type", "string") for k, v in profile.columns.items()} if profile else {}
        except Exception:
            schema_cols = {}

        return self._validator.validate(spec, schema_columns=schema_cols if schema_cols else None)

    def preview_chart(
        self,
        spec: ChartSpec,
    ) -> ChartSpec:
        """
        Validates and executes server-side data preparation for a ChartSpec,
        returning the fully hydrated ChartSpec ready for rendering.
        """
        resolved_version_id, parquet_path = self._resolve_version_and_path(
            spec.dataset_id, spec.dataset_version_id
        )

        # Ensure spec has provenance
        if not spec.provenance:
            spec.provenance = VisualizationProvenance(
                dataset_id=spec.dataset_id,
                dataset_version_id=resolved_version_id,
                source_type=spec.source_type or "dataset",
                source_reference=spec.source_reference,
                created_at=datetime.now(timezone.utc).isoformat(),
            )

        # Validate spec
        validation = self.validate_chart_spec(spec)
        if not validation.is_valid:
            error_msgs = "; ".join([e.message for e in validation.errors])
            raise ValueError(f"Invalid ChartSpec: {error_msgs}")

        # Hydrate data using server-side DuckDB aggregation & sampling
        return self._data_preparer.prepare_data(parquet_path, spec)

    def save_visualization(
        self,
        name: str,
        spec: ChartSpec,
        description: Optional[str] = None,
        source_reference: Optional[str] = None,
    ) -> SavedVisualization:
        """
        Saves a visualization strictly bound to its dataset version.
        """
        viz_id = f"viz_{uuid.uuid4().hex[:12]}"
        now_str = datetime.now(timezone.utc).isoformat()

        # Re-hydrate or ensure data exists
        if not spec.data:
            spec = self.preview_chart(spec)

        saved = SavedVisualization(
            visualization_id=viz_id,
            name=name,
            description=description,
            dataset_id=spec.dataset_id,
            dataset_version_id=spec.dataset_version_id,
            chart_spec=spec,
            source_reference=source_reference or spec.source_reference,
            created_at=now_str,
            updated_at=now_str,
        )

        res = self._saved_repo.save(saved)

        # Log audit history
        ct_str = spec.chart_type.value if hasattr(spec.chart_type, "value") else str(spec.chart_type)
        self._history_repo.log_action(
            VisualizationHistoryEntry(
                id=str(uuid.uuid4()),
                visualization_id=viz_id,
                action="created",
                dataset_id=spec.dataset_id,
                dataset_version_id=spec.dataset_version_id,
                chart_type=ct_str,
                timestamp=now_str,
            )
        )

        return res

    def list_saved_visualizations(
        self,
        dataset_id: Optional[str] = None,
        version_id: Optional[str] = None,
    ) -> List[SavedVisualization]:
        return self._saved_repo.get_all(dataset_id=dataset_id, version_id=version_id)

    def get_saved_visualization(
        self,
        visualization_id: str,
    ) -> Optional[SavedVisualization]:
        return self._saved_repo.get_by_id(visualization_id)

    def delete_saved_visualization(
        self,
        visualization_id: str,
    ) -> bool:
        viz = self._saved_repo.get_by_id(visualization_id)
        deleted = self._saved_repo.delete(visualization_id)
        if deleted and viz:
            del_ct = (
                viz.chart_spec.chart_type.value
                if hasattr(viz.chart_spec.chart_type, "value")
                else str(viz.chart_spec.chart_type)
            )
            self._history_repo.log_action(
                VisualizationHistoryEntry(
                    id=str(uuid.uuid4()),
                    visualization_id=visualization_id,
                    action="deleted",
                    dataset_id=viz.dataset_id,
                    dataset_version_id=viz.dataset_version_id,
                    chart_type=del_ct,
                    timestamp=datetime.now(timezone.utc).isoformat(),
                )
            )
        return deleted

    def check_version_compatibility(
        self,
        visualization_id: str,
        target_version_id: str,
    ) -> VisualizationValidationResult:
        """
        Explicitly checks if a saved visualization is compatible with target_version_id.
        Fails if fields are removed, renamed, or type-incompatible (VIZ-41, VIZ-61).
        """
        viz = self._saved_repo.get_by_id(visualization_id)
        if not viz:
            raise ValueError(f"Visualization '{visualization_id}' not found.")

        # Resolve target version schema
        try:
            _, target_path = self._resolve_version_and_path(viz.dataset_id, target_version_id)
            import duckdb
            c = duckdb.connect(":memory:")
            safe_p = target_path.replace("'", "''").replace("\\", "/")
            schema_info = c.execute(f"DESCRIBE SELECT * FROM read_parquet('{safe_p}')").fetchall()
            schema_cols = {row[0]: row[1] for row in schema_info}
            c.close()
        except Exception as e:
            return VisualizationValidationResult(
                is_valid=False,
                is_compatible=False,
                incompatibility_reason=f"Failed to inspect target version {target_version_id}: {str(e)}",
            )

        spec = viz.chart_spec
        # Check against target schema
        return self._validator.validate(spec, schema_columns=schema_cols)

    def recommend_from_sql(
        self,
        columns: List[Dict[str, Any]],
        rows: List[Dict[str, Any]],
        query_text: Optional[str] = None,
    ) -> List[VisualizationRecommendation]:
        """
        Generates chart recommendations directly from SQL QueryResult rows/columns.
        """
        return self._recommender.recommend_from_sql_result(
            columns=columns,
            rows=rows,
            query_text=query_text,
        )


visualization_service = VisualizationService()
