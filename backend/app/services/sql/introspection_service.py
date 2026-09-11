"""
AnalyzaX — Phase 8: SQL Introspection Service
Provides schema tree introspection and context-aware query templates for datasets and versions.
"""

from typing import List, Optional

from backend.app.engines.sql.introspection import SchemaIntrospector
from backend.app.engines.sql.models import SchemaTableInfo, SQLTemplate
from backend.app.engines.sql.templates import SQLTemplateGenerator
from backend.app.services.cleaning.version_service import VersionService
from backend.app.services.dataset_service import dataset_service


class SQLIntrospectionService:
    """
    Coordinates schema extraction and dynamic templates for the SQL Studio.
    """

    def __init__(self) -> None:
        self._dataset_service = dataset_service
        self._version_service = VersionService()

    def _resolve_context(self, dataset_id: str, version_id: Optional[str] = None):
        dataset = self._dataset_service.get_dataset(dataset_id)
        if not dataset:
            raise ValueError(f"Dataset '{dataset_id}' not found.")

        if version_id:
            version = self._version_service.get_version(dataset_id, version_id)
            if not version:
                raise ValueError(f"Version '{version_id}' not found for dataset '{dataset_id}'.")
        else:
            version = self._version_service.get_active_version(dataset_id)

        return dataset, version

    def get_schema(self, dataset_id: str, version_id: Optional[str] = None) -> SchemaTableInfo:
        """Introspects schema for the requested dataset version."""
        dataset, version = self._resolve_context(dataset_id, version_id)
        return SchemaIntrospector.introspect(
            storage_path=version.storage_path,
            dataset_id=dataset_id,
            version_id=version.version_id,
            friendly_name=dataset.name,
        )

    def get_templates(self, dataset_id: str, version_id: Optional[str] = None) -> List[SQLTemplate]:
        """Generates dynamic SQL templates adapted to dataset columns."""
        schema = self.get_schema(dataset_id, version_id)
        return SQLTemplateGenerator.generate_templates(schema)


sql_introspection_service = SQLIntrospectionService()
