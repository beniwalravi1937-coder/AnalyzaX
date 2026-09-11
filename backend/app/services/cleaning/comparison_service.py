"""
Quality Comparison Service
Calculates deterministic before-and-after scorecards, metric differentials,
and quality improvement summaries between dataset versions.
"""

from typing import Any, Dict, List, Optional
from backend.app.engines.transformations.models import QualityComparison
from backend.app.engines.quality.models import DataQualityReport
from backend.app.engines.profiling.engine import DatasetProfiler
from backend.app.engines.quality.engine import DataQualityEngine
from backend.app.services.cleaning.version_service import VersionService
from backend.app.services.duckdb_service import duckdb_service
from backend.app.schemas.profile import DatasetProfileResponse


class ComparisonService:
    """
    Evaluates and compares the quality score and dimension metrics
    between two dataset versions.
    """

    def __init__(self) -> None:
        self._version_service = VersionService()
        self._profiler = DatasetProfiler()
        self._quality_engine = DataQualityEngine()

    def evaluate_version_quality(self, dataset_id: str, version_id: str) -> DataQualityReport:
        """
        Profiles and evaluates the quality of a specific dataset version.
        """
        version = self._version_service.get_version(dataset_id, version_id)
        if not version:
            raise ValueError(f"Version '{version_id}' not found for dataset '{dataset_id}'")

        table_name = version.duckdb_table_name
        with duckdb_service.get_connection() as conn:
            profile_response = self._profiler.profile_table(conn, table_name, dataset_id)
            report = self._quality_engine.evaluate(conn, table_name, profile_response)

        return report

    def compare_versions(
        self,
        dataset_id: str,
        before_version_id: str,
        after_version_id: str,
        before_report: Optional[DataQualityReport] = None,
        after_report: Optional[DataQualityReport] = None,
    ) -> QualityComparison:
        """
        Calculates the quality scorecard and impact metrics between two versions.
        """
        if not before_report:
            before_report = self.evaluate_version_quality(dataset_id, before_version_id)
        if not after_report:
            after_report = self.evaluate_version_quality(dataset_id, after_version_id)

        before_score = round(before_report.overall_score, 1)
        after_score = round(after_report.overall_score, 1)
        score_delta = round(after_score - before_score, 1)

        before_total_issues = len(before_report.issues)
        after_total_issues = len(after_report.issues)
        issues_delta = before_total_issues - after_total_issues

        improvements: List[str] = []
        regressions: List[str] = []

        if score_delta > 0:
            improvements.append(f"Overall data quality improved by {score_delta}% (Grade: {before_report.overall_grade} -> {after_report.overall_grade})")
        elif score_delta < 0:
            regressions.append(f"Overall data quality decreased by {abs(score_delta)}%")

        if issues_delta > 0:
            improvements.append(f"Resolved {issues_delta} detected quality issue{'s' if issues_delta > 1 else ''}")
        elif issues_delta < 0:
            regressions.append(f"Introduced {abs(issues_delta)} new quality issue{'s' if abs(issues_delta) > 1 else ''}")

        # Dimension level comparisons
        dim_comparisons: Dict[str, Any] = {}
        before_dims = {
            (k.value if hasattr(k, "value") else str(k)): v.score
            for k, v in before_report.dimension_scores.items()
        }
        after_dims = {
            (k.value if hasattr(k, "value") else str(k)): v.score
            for k, v in after_report.dimension_scores.items()
        }

        for dim_name, before_val in before_dims.items():
            after_val = after_dims.get(dim_name, before_val)
            delta = round(after_val - before_val, 1)
            dim_comparisons[dim_name] = {
                "before": before_val,
                "after": after_val,
                "delta": delta,
            }
            if delta >= 5.0:
                improvements.append(f"{dim_name.capitalize()} dimension score increased by {delta}%")
            elif delta <= -5.0:
                regressions.append(f"{dim_name.capitalize()} dimension score dropped by {abs(delta)}%")

        v_before = self._version_service.get_version(dataset_id, before_version_id)
        v_after = self._version_service.get_version(dataset_id, after_version_id)

        return QualityComparison(
            before_version_id=before_version_id,
            after_version_id=after_version_id,
            before_score=before_score,
            after_score=after_score,
            score_delta=score_delta,
            before_grade=before_report.overall_grade,
            after_grade=after_report.overall_grade,
            before_total_issues=before_total_issues,
            after_total_issues=after_total_issues,
            issues_delta=issues_delta,
            metrics_comparison={
                "dimensions": dim_comparisons,
                "rows_before": v_before.row_count if v_before else 0,
                "rows_after": v_after.row_count if v_after else 0,
            },
            improvements=improvements,
            regressions=regressions,
        )

    def compare_versions_metadata(
        self, dataset_id: str, version_a_id: str, version_b_id: str
    ) -> Dict[str, Any]:
        """
        Calculates metadata-level version comparison (schema, column differences,
        row count deltas) without expensive analytical re-computation.
        """
        v_a = self._version_service.get_version(dataset_id, version_a_id)
        v_b = self._version_service.get_version(dataset_id, version_b_id)
        if not v_a or not v_b:
            raise ValueError(f"One or both versions not found: '{version_a_id}', '{version_b_id}'")

        schema_diff = []
        cols_a = {
            (c["name"] if isinstance(c, dict) else getattr(c, "name", str(c))): (
                c.get("dtype") if isinstance(c, dict) else getattr(c, "dtype", None)
            )
            for c in (v_a.schema_columns or [])
        }
        cols_b = {
            (c["name"] if isinstance(c, dict) else getattr(c, "name", str(c))): (
                c.get("dtype") if isinstance(c, dict) else getattr(c, "dtype", None)
            )
            for c in (v_b.schema_columns or [])
        }

        all_col_names = sorted(list(set(cols_a.keys()) | set(cols_b.keys())))
        for col in all_col_names:
            if col not in cols_a:
                schema_diff.append({"name": col, "change": "ADDED", "old_dtype": None, "new_dtype": cols_b.get(col)})
            elif col not in cols_b:
                schema_diff.append({"name": col, "change": "REMOVED", "old_dtype": cols_a.get(col), "new_dtype": None})
            elif cols_a[col] != cols_b[col]:
                schema_diff.append({"name": col, "change": "TYPE_CHANGED", "old_dtype": cols_a[col], "new_dtype": cols_b[col]})
            else:
                schema_diff.append({"name": col, "change": "UNCHANGED", "old_dtype": cols_a[col], "new_dtype": cols_b[col]})

        row_delta = (v_b.row_count - v_a.row_count) if (v_a.row_count is not None and v_b.row_count is not None) else None
        col_delta = (v_b.column_count - v_a.column_count) if (v_a.column_count is not None and v_b.column_count is not None) else None

        return {
            "dataset_id": dataset_id,
            "version_a_id": version_a_id,
            "version_b_id": version_b_id,
            "row_count_a": v_a.row_count,
            "row_count_b": v_b.row_count,
            "row_count_delta": row_delta,
            "column_count_a": v_a.column_count,
            "column_count_b": v_b.column_count,
            "column_count_delta": col_delta,
            "schema_diff": schema_diff,
            "transformation_summary_a": v_a.transformation_summary,
            "transformation_summary_b": v_b.transformation_summary,
            "comparison_available": True,
        }
