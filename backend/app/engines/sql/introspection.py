"""
AnalyzaX — Phase 8: Schema Introspector
Extracts tables, columns, physical types, semantic types, nullability,
cardinality, and sample values for the SQL Studio schema explorer.
"""

import math
import re
from typing import Any, List, Optional
import polars as pl

from backend.app.engines.sql.models import SchemaColumnInfo, SchemaTableInfo


class SchemaIntrospector:
    """
    Introspects schema details from a dataset version Parquet file.
    """

    @staticmethod
    def _clean_sample(val: Any) -> Any:
        if val is None:
            return None
        if isinstance(val, float) and (math.isnan(val) or math.isinf(val)):
            return None
        return str(val) if not isinstance(val, (int, float, bool)) else val

    @classmethod
    def introspect(
        cls,
        storage_path: str,
        dataset_id: str,
        version_id: str,
        friendly_name: Optional[str] = None,
    ) -> SchemaTableInfo:
        """
        Reads Parquet file metadata and inspects column types, distinct counts, and sample values.
        """
        # Read a scan/sample using Polars for fast, lazy metadata extraction
        df = pl.read_parquet(storage_path)
        row_count = len(df)
        col_count = len(df.columns)

        safe_alias = "dataset"
        if friendly_name:
            clean_alias = re.sub(r"[^a-zA-Z0-9_]", "_", friendly_name).strip("_").lower()
            if clean_alias and clean_alias not in ("select", "from", "where"):
                safe_alias = clean_alias

        columns_info: List[SchemaColumnInfo] = []

        for col_name in df.columns:
            series = df[col_name]
            pl_dtype = series.dtype

            # Physical type representation
            physical_type = str(pl_dtype).upper()

            # Infer semantic type
            if pl_dtype.is_numeric():
                sem_type = "numeric"
            elif pl_dtype.is_temporal():
                sem_type = "datetime"
            elif pl_dtype == pl.Boolean:
                sem_type = "boolean"
            else:
                sem_type = "categorical"

            # Compute cardinality & sample values
            cardinality = series.n_unique()
            null_count = series.null_count()
            nullable = null_count > 0

            # Get up to 5 non-null sample values
            samples_raw = series.drop_nulls().head(5).to_list()
            sample_values = [cls._clean_sample(v) for v in samples_raw]

            columns_info.append(
                SchemaColumnInfo(
                    name=col_name,
                    physical_type=physical_type,
                    semantic_type=sem_type,
                    nullable=nullable,
                    cardinality=cardinality,
                    sample_values=sample_values,
                )
            )

        return SchemaTableInfo(
            table_name=f"dataset_{dataset_id}_{version_id}",
            table_alias=safe_alias,
            dataset_id=dataset_id,
            version_id=version_id,
            row_count=row_count,
            column_count=col_count,
            columns=columns_info,
        )
