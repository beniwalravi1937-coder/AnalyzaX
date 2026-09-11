"""
Dataset Versioning & Lineage Service
Manages immutable dataset versions, Parquet persistence, DuckDB view registration,
and reproducible lineage DAG tracking.
"""

import json
import os
import shutil
import uuid
from typing import Any, Dict, List, Optional
import polars as pl

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.transformations.engine import TransformationEngine
from backend.app.engines.transformations.models import DatasetVersion, VersionStatus
from backend.app.services.duckdb_service import duckdb_service
from backend.app.services.dataset_service import dataset_service


class VersionService:
    """
    Coordinates immutable dataset versions (v1, v2, ...), Parquet files,
    lineage histories, and active DuckDB views.
    """

    def __init__(self) -> None:
        self._processed_root = os.path.abspath(settings.DATA_PROCESSED_DIR)
        self._lineage_root = os.path.abspath(settings.DATA_LINEAGE_DIR)
        self._temp_dir = os.path.abspath(settings.DATA_TEMP_DIR)
        self._dataset_service = dataset_service
        self._ensure_dirs()

    def _ensure_dirs(self) -> None:
        os.makedirs(self._processed_root, exist_ok=True)
        os.makedirs(self._lineage_root, exist_ok=True)
        os.makedirs(self._temp_dir, exist_ok=True)

    def _get_lineage_file(self, dataset_id: str) -> str:
        return os.path.join(self._lineage_root, f"{dataset_id}.json")

    def _load_lineage_record(self, dataset_id: str) -> Dict[str, Any]:
        lineage_file = self._get_lineage_file(dataset_id)
        if os.path.exists(lineage_file):
            try:
                with open(lineage_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to read lineage file for {dataset_id}: {e}")
        return {"dataset_id": dataset_id, "active_version_id": None, "versions": []}

    def _save_lineage_record(self, dataset_id: str, record: Dict[str, Any]) -> None:
        lineage_file = self._get_lineage_file(dataset_id)
        try:
            with open(lineage_file, "w", encoding="utf-8") as f:
                json.dump(record, f, indent=2, default=str)
        except Exception as e:
            logger.error(f"Failed to save lineage record for {dataset_id}: {e}")

    def get_or_create_v1(self, dataset_id: str) -> DatasetVersion:
        """
        Ensures baseline version v1 exists for a dataset.
        If not, initializes v1 from the ingested dataset parquet file.
        """
        lineage = self._load_lineage_record(dataset_id)
        if lineage.get("versions"):
            # Return active or v1
            active_id = lineage.get("active_version_id")
            for v_data in lineage["versions"]:
                if v_data["version_id"] == active_id:
                    return DatasetVersion(**v_data)
            return DatasetVersion(**lineage["versions"][0])

        # Initialize v1 from DatasetService
        ds = self._dataset_service.get_dataset(dataset_id)
        if not ds:
            raise ValueError(f"Dataset '{dataset_id}' not found.")

        dataset_processed_dir = os.path.join(self._processed_root, dataset_id)
        os.makedirs(dataset_processed_dir, exist_ok=True)
        v1_path = os.path.join(dataset_processed_dir, "v1.parquet")
        posix_v1_path = v1_path.replace("\\", "/")

        with duckdb_service.get_connection() as conn:
            conn.execute(
                f"COPY {ds.duckdb_table_name} TO '{posix_v1_path}' (FORMAT PARQUET);"
            )

        # Read using Polars to compute hashes & metrics
        df = pl.read_parquet(v1_path)
        file_size = os.path.getsize(v1_path)
        schema_hash = TransformationEngine.compute_schema_hash(dict(df.schema))
        data_hash = TransformationEngine.compute_data_hash(df)
        v1_table_name = f"dataset_{dataset_id}_v1"

        v1 = DatasetVersion(
            version_id="v1",
            dataset_id=dataset_id,
            version_number=1,
            version_label="Initial Ingested Dataset",
            parent_version_id=None,
            storage_path=v1_path,
            duckdb_table_name=v1_table_name,
            row_count=len(df),
            column_count=len(df.columns),
            file_size_bytes=file_size,
            schema_hash=schema_hash,
            data_hash=data_hash,
            pipeline_hash=None,
            status=VersionStatus.READY,
            operation_count=0,
        )

        # Register v1 and main view in DuckDB
        posix_v1_path = v1_path.replace("\\", "/")
        with duckdb_service.get_connection() as conn:
            conn.execute(f"CREATE OR REPLACE VIEW {v1_table_name} AS SELECT * FROM read_parquet('{posix_v1_path}');")
            conn.execute(f"CREATE OR REPLACE VIEW dataset_{dataset_id} AS SELECT * FROM read_parquet('{posix_v1_path}');")

        lineage["active_version_id"] = "v1"
        lineage["versions"] = [v1.model_dump()]
        self._save_lineage_record(dataset_id, lineage)

        logger.info(f"Initialized baseline version v1 for dataset {dataset_id}")
        return v1

    def list_versions(self, dataset_id: str) -> List[DatasetVersion]:
        """Lists all versions of a dataset sorted by version number descending."""
        self.get_or_create_v1(dataset_id)
        lineage = self._load_lineage_record(dataset_id)
        versions = [DatasetVersion(**v) for v in lineage.get("versions", [])]
        return sorted(versions, key=lambda x: x.version_number, reverse=True)

    def get_version(self, dataset_id: str, version_id: str) -> Optional[DatasetVersion]:
        """Retrieves a specific dataset version."""
        self.get_or_create_v1(dataset_id)
        lineage = self._load_lineage_record(dataset_id)
        for v in lineage.get("versions", []):
            if v["version_id"] == version_id:
                return DatasetVersion(**v)
        return None

    def get_active_version(self, dataset_id: str) -> DatasetVersion:
        """Retrieves the currently active version for a dataset."""
        self.get_or_create_v1(dataset_id)
        lineage = self._load_lineage_record(dataset_id)
        active_id = lineage.get("active_version_id")
        for v in lineage.get("versions", []):
            if v["version_id"] == active_id:
                return DatasetVersion(**v)
        return DatasetVersion(**lineage["versions"][0])

    def get_version_dataframe(self, dataset_id: str, version_id: Optional[str] = None) -> pl.DataFrame:
        """Loads a Polars DataFrame for the requested (or active) version."""
        if version_id:
            version = self.get_version(dataset_id, version_id)
        else:
            version = self.get_active_version(dataset_id)

        if not version or not os.path.exists(version.storage_path):
            raise ValueError(f"Version file not found for dataset {dataset_id}, version {version_id}")

        return pl.read_parquet(version.storage_path)

    def create_version(
        self,
        dataset_id: str,
        df: pl.DataFrame,
        parent_version_id: str,
        label: str,
        pipeline_hash: Optional[str] = None,
        operation_count: int = 0,
    ) -> DatasetVersion:
        """
        Atomically saves a new dataset version (v2, v3, ...) and registers it.
        """
        lineage = self._load_lineage_record(dataset_id)
        existing_versions = lineage.get("versions", [])
        next_version_number = len(existing_versions) + 1
        new_version_id = f"v{next_version_number}"

        dataset_processed_dir = os.path.join(self._processed_root, dataset_id)
        os.makedirs(dataset_processed_dir, exist_ok=True)
        final_parquet_path = os.path.join(dataset_processed_dir, f"{new_version_id}.parquet")

        temp_file = os.path.join(self._temp_dir, f"{uuid.uuid4().hex}.parquet")
        try:
            # Atomic write to temp then rename
            df.write_parquet(temp_file)
            if not os.path.exists(temp_file) or os.path.getsize(temp_file) == 0:
                raise RuntimeError("Failed to generate Parquet file for new version")

            shutil.move(temp_file, final_parquet_path)
        finally:
            if os.path.exists(temp_file):
                try:
                    os.remove(temp_file)
                except Exception:
                    pass

        file_size = os.path.getsize(final_parquet_path)
        schema_hash = TransformationEngine.compute_schema_hash(dict(df.schema))
        data_hash = TransformationEngine.compute_data_hash(df)
        table_name = f"dataset_{dataset_id}_{new_version_id}"

        new_version = DatasetVersion(
            version_id=new_version_id,
            dataset_id=dataset_id,
            version_number=next_version_number,
            version_label=label,
            parent_version_id=parent_version_id,
            storage_path=final_parquet_path,
            duckdb_table_name=table_name,
            row_count=len(df),
            column_count=len(df.columns),
            file_size_bytes=file_size,
            schema_hash=schema_hash,
            data_hash=data_hash,
            pipeline_hash=pipeline_hash,
            status=VersionStatus.READY,
            operation_count=operation_count,
        )

        # Register in DuckDB and point active alias to this new version
        posix_path = final_parquet_path.replace("\\", "/")
        with duckdb_service.get_connection() as conn:
            conn.execute(f"CREATE OR REPLACE VIEW {table_name} AS SELECT * FROM read_parquet('{posix_path}');")
            conn.execute(f"CREATE OR REPLACE VIEW dataset_{dataset_id} AS SELECT * FROM read_parquet('{posix_path}');")

        lineage["active_version_id"] = new_version_id
        lineage["versions"].append(new_version.model_dump())
        self._save_lineage_record(dataset_id, lineage)

        logger.info(f"Created version {new_version_id} for dataset {dataset_id}")
        return new_version

    def set_active_version(self, dataset_id: str, version_id: str) -> DatasetVersion:
        """
        Activates a previous version (rollback/switch), updating DuckDB active views.
        """
        version = self.get_version(dataset_id, version_id)
        if not version:
            raise ValueError(f"Version '{version_id}' not found for dataset '{dataset_id}'")

        posix_path = version.storage_path.replace("\\", "/")
        with duckdb_service.get_connection() as conn:
            conn.execute(f"CREATE OR REPLACE VIEW dataset_{dataset_id} AS SELECT * FROM read_parquet('{posix_path}');")

        lineage = self._load_lineage_record(dataset_id)
        lineage["active_version_id"] = version_id
        self._save_lineage_record(dataset_id, lineage)

        logger.info(f"Activated version {version_id} for dataset {dataset_id}")
        return version

    def get_lineage(self, dataset_id: str) -> Dict[str, Any]:
        """Returns lineage DAG nodes and links for visualization."""
        self.get_or_create_v1(dataset_id)
        lineage = self._load_lineage_record(dataset_id)
        versions = lineage.get("versions", [])
        active_id = lineage.get("active_version_id")

        nodes = []
        links = []

        for v in versions:
            nodes.append({
                "id": v["version_id"],
                "label": v["version_label"],
                "version_number": v["version_number"],
                "row_count": v["row_count"],
                "column_count": v["column_count"],
                "created_at": v["created_at"],
                "is_active": v["version_id"] == active_id,
            })
            if v.get("parent_version_id"):
                links.append({
                    "source": v["parent_version_id"],
                    "target": v["version_id"],
                })

        return {
            "dataset_id": dataset_id,
            "active_version_id": active_id,
            "nodes": nodes,
            "links": links,
        }
