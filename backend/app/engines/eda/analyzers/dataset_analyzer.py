"""
AnalyzaX — Phase 7: Dataset Overview Analyzer
Computes dataset-level structural and health metrics.
"""

from datetime import datetime, timezone
from typing import Optional
import polars as pl

from backend.app.engines.eda.models import EDAOverview
from backend.app.schemas.profile import DatasetProfileResponse
from backend.app.schemas.quality import DataQualityReportResponse


class DatasetAnalyzer:
    @staticmethod
    def analyze(
        df: pl.DataFrame,
        dataset_id: str,
        version_id: str,
        profile: Optional[DatasetProfileResponse] = None,
        quality: Optional[DataQualityReportResponse] = None,
        quality_score: Optional[float] = None,
        anomalies_count: int = 0,
        storage_size_bytes: Optional[int] = None,
        profile_timestamp: Optional[str] = None,
        quality_timestamp: Optional[str] = None,
    ) -> EDAOverview:
        row_count = len(df)
        column_count = len(df.columns)
        total_cells = row_count * column_count

        # Count nulls across all columns
        null_counts = [df[col].null_count() for col in df.columns]
        missing_cells = sum(null_counts)
        missing_percentage = round((missing_cells / total_cells * 100.0), 2) if total_cells > 0 else 0.0

        # Exact duplicate rows count
        duplicate_rows = 0
        if row_count > 0:
            duplicate_rows = row_count - len(df.unique())
        duplicate_percentage = round((duplicate_rows / row_count * 100.0), 2) if row_count > 0 else 0.0

        # Column type classification
        numeric_count = 0
        categorical_count = 0
        datetime_count = 0
        boolean_count = 0
        text_count = 0
        identifier_count = 0

        for col, dtype in df.schema.items():
            if dtype.is_numeric():
                numeric_count += 1
            elif dtype.is_temporal():
                datetime_count += 1
            elif dtype == pl.Boolean:
                boolean_count += 1
            elif dtype == pl.Utf8 or dtype == pl.Categorical:
                # Check profile semantic type if available
                if profile:
                    col_p = next((c for c in profile.columns if c.name == col), None)
                    if col_p and col_p.semantic_type == "text":
                        text_count += 1
                    elif col_p and col_p.semantic_type in ["datetime", "date"]:
                        datetime_count += 1
                    else:
                        categorical_count += 1
                else:
                    categorical_count += 1

        if quality:
            quality_score = quality.overall_score
            anomalies_count = len(quality.issues)
            quality_ts = quality.generated_at
        else:
            quality_ts = quality_timestamp

        if profile:
            identifier_count = profile.identifier_columns_count
            profile_ts = profile.generated_at
        else:
            profile_ts = profile_timestamp

        eda_ts = datetime.now(timezone.utc).isoformat()

        return EDAOverview(
            dataset_id=dataset_id,
            version_id=version_id,
            row_count=row_count,
            column_count=column_count,
            numeric_columns_count=numeric_count,
            categorical_columns_count=categorical_count,
            datetime_columns_count=datetime_count,
            boolean_columns_count=boolean_count,
            text_columns_count=text_count,
            identifier_columns_count=identifier_count,
            total_cells=total_cells,
            missing_cells=missing_cells,
            missing_percentage=missing_percentage,
            duplicate_rows=duplicate_rows,
            duplicate_percentage=duplicate_percentage,
            quality_score=quality_score,
            anomalies_count=anomalies_count,
            storage_size_bytes=storage_size_bytes,
            profile_timestamp=profile_ts,
            quality_timestamp=quality_ts,
            eda_timestamp=eda_ts,
        )
