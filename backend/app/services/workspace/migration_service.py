"""
Migration Application Service for Phase 16.
Non-destructively scans existing Phase 1–15 analytical assets and bootstraps
the Default Workspace, Default Project, Asset Registry, and initial relationships.
"""

from typing import Dict, Any, List
import os

from backend.app.core.logging import logger
from backend.app.engines.workspace.models import (
    ActivityRecord,
    ActivityType,
    AssetCreateRequest,
    AssetType,
    RelationshipType,
)
from backend.app.engines.workspace.repository import WorkspaceRepository, workspace_repo
from backend.app.services.workspace.workspace_service import workspace_service
from backend.app.services.workspace.project_service import project_service
from backend.app.services.workspace.asset_service import asset_service
from backend.app.services.dataset_service import dataset_service
from backend.app.services.cleaning.version_service import VersionService
from backend.app.services.dashboard_service import dashboard_service
from backend.app.services.sql.saved_query_service import sql_saved_query_service
from backend.app.services.export_service import export_service


class MigrationService:
    """
    Coordinates non-destructive data migration and registry bootstrapping.
    """

    def __init__(self, repo: WorkspaceRepository = workspace_repo):
        self._repo = repo
        self._ws_service = workspace_service
        self._proj_service = project_service
        self._asset_service = asset_service
        self._version_service = VersionService()

    def run_initial_migration(self) -> Dict[str, Any]:
        """
        Executes automatic bootstrapping of Default Workspace, Default Project,
        and registers all existing datasets, dashboards, queries, and exports.
        """
        logger.info("Starting Phase 16 initial migration...")

        # 1. Ensure Default Workspace and Project exist
        default_ws = self._ws_service.get_or_create_default_workspace()
        default_proj = self._proj_service.get_or_create_default_project(default_ws.workspace_id)

        stats = {
            "workspace_id": default_ws.workspace_id,
            "project_id": default_proj.project_id,
            "migrated_datasets": 0,
            "migrated_versions": 0,
            "migrated_dashboards": 0,
            "migrated_queries": 0,
            "migrated_exports": 0,
            "created_relationships": 0,
        }

        # 2. Migrate existing Datasets and their Versions
        try:
            datasets = dataset_service.list_datasets()
            for ds in datasets:
                existing_ds_asset = self._repo.get_asset_by_source(default_proj.project_id, ds.id)
                if existing_ds_asset:
                    stats["migrated_datasets"] += 1
                    continue

                # Register dataset asset
                ds_asset = self._asset_service.register_asset(
                    AssetCreateRequest(
                        asset_type=AssetType.DATASET,
                        project_id=default_proj.project_id,
                        workspace_id=default_ws.workspace_id,
                        source_entity_id=ds.id,
                        name=ds.name or ds.original_filename,
                        description=f"Format: {ds.format}, size: {ds.file_size_bytes} bytes",
                        metadata={
                            "format": ds.format,
                            "file_size_bytes": ds.file_size_bytes,
                            "duckdb_table_name": ds.duckdb_table_name,
                            "status": ds.status,
                        },
                    )
                )
                stats["migrated_datasets"] += 1

                # Register versions if lineage records exist
                try:
                    record = self._version_service._load_lineage_record(ds.id)
                    for v_dict in record.get("versions", []):
                        v_id = v_dict.get("version_id", "v1")
                        ver_asset = self._asset_service.register_asset(
                            AssetCreateRequest(
                                asset_type=AssetType.DATASET_VERSION,
                                project_id=default_proj.project_id,
                                workspace_id=default_ws.workspace_id,
                                source_entity_id=f"{ds.id}:{v_id}",
                                name=f"{ds.name or ds.original_filename} ({v_id})",
                                description=v_dict.get("transformation_summary") or f"Version {v_id}",
                                source_version_reference=v_id,
                                metadata={
                                    "version_id": v_id,
                                    "dataset_id": ds.id,
                                    "row_count": v_dict.get("row_count"),
                                    "column_count": v_dict.get("column_count"),
                                    "parent_version_id": v_dict.get("parent_version_id"),
                                },
                            )
                        )
                        stats["migrated_versions"] += 1

                        # Relationship: Dataset CONTAINS Dataset Version
                        self._asset_service.create_relationship(
                            source_asset_id=ds_asset.asset_id,
                            target_asset_id=ver_asset.asset_id,
                            relationship_type=RelationshipType.CONTAINS,
                            metadata={"dataset_id": ds.id, "version_id": v_id},
                        )
                        stats["created_relationships"] += 1
                except Exception as e:
                    logger.debug(f"Version migration error for {ds.id}: {e}")

        except Exception as e:
            logger.warning(f"Dataset migration error: {e}")

        # 3. Migrate Dashboards
        try:
            dashboards = dashboard_service.list_dashboards()
            for dash in dashboards:
                dash_asset = self._asset_service.register_asset(
                    AssetCreateRequest(
                        asset_type=AssetType.DASHBOARD,
                        project_id=default_proj.project_id,
                        workspace_id=default_ws.workspace_id,
                        source_entity_id=dash.dashboard_id,
                        name=dash.name,
                        description=dash.description,
                        source_version_reference=dash.dataset_version_id,
                        metadata={
                            "dashboard_id": dash.dashboard_id,
                            "dataset_id": dash.dataset_id,
                            "dataset_version_id": dash.dataset_version_id,
                            "components_count": len(dash.components),
                        },
                    )
                )
                stats["migrated_dashboards"] += 1

                # Find source dataset asset and link
                ds_asset = self._repo.get_asset_by_source(default_proj.project_id, dash.dataset_id)
                if ds_asset:
                    try:
                        self._asset_service.add_relationship(
                            source_asset_id=ds_asset.asset_id,
                            target_asset_id=dash_asset.asset_id,
                            rel_type=RelationshipType.VISUALIZES,
                        )
                        stats["created_relationships"] += 1
                    except Exception:
                        pass
        except Exception as e:
            logger.warning(f"Dashboard migration error: {e}")

        # 4. Migrate Saved Queries
        try:
            queries = sql_saved_query_service.list()
            for q in queries:
                qid = getattr(q, "id", getattr(q, "query_id", "query"))
                sql_str = getattr(q, "sql", getattr(q, "sql_query", ""))
                q_asset = self._asset_service.register_asset(
                    AssetCreateRequest(
                        asset_type=AssetType.QUERY,
                        project_id=default_proj.project_id,
                        workspace_id=default_ws.workspace_id,
                        source_entity_id=qid,
                        name=q.name,
                        description=q.description or sql_str[:100],
                        tags=q.tags,
                        metadata={
                            "query_id": qid,
                            "dataset_id": q.dataset_id,
                            "sql_query": sql_str,
                        },
                    )
                )
                stats["migrated_queries"] += 1

                if q.dataset_id:
                    ds_asset = self._repo.get_asset_by_source(default_proj.project_id, q.dataset_id)
                    if ds_asset:
                        try:
                            self._asset_service.add_relationship(
                                source_asset_id=ds_asset.asset_id,
                                target_asset_id=q_asset.asset_id,
                                rel_type=RelationshipType.USES,
                            )
                            stats["created_relationships"] += 1
                        except Exception:
                            pass
        except Exception as e:
            logger.warning(f"Query migration error: {e}")

        # 5. Migrate Exports
        try:
            exports = export_service.list_exports()
            for exp in exports:
                exp_asset = self._asset_service.register_asset(
                    AssetCreateRequest(
                        asset_type=AssetType.EXPORT,
                        project_id=default_proj.project_id,
                        workspace_id=default_ws.workspace_id,
                        source_entity_id=exp.job_id,
                        name=exp.file_name or f"Export ({exp.format.value})",
                        description=f"Format: {exp.format.value}, size: {exp.file_size_bytes or 0} bytes",
                        source_version_reference=exp.version_id,
                        metadata={
                            "job_id": exp.job_id,
                            "dataset_id": exp.dataset_id,
                            "format": exp.format.value,
                            "status": exp.status.value,
                        },
                    )
                )
                stats["migrated_exports"] += 1
        except Exception as e:
            logger.warning(f"Export migration error: {e}")

        logger.info(f"Phase 16 migration complete: {stats}")
        return stats


migration_service = MigrationService()
