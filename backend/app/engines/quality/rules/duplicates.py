"""
Duplicates Quality Rule
Evaluates exact full-row duplicates across all dimensions.
"""

from typing import List
import duckdb
from backend.app.engines.quality.models import (
    Dimension,
    IssueType,
    QualityIssue,
    Severity,
)
from backend.app.engines.quality.rules.base import BaseQualityRule
from backend.app.schemas.profile import DatasetProfileResponse


class DuplicatesRule(BaseQualityRule):
    rule_id = "RULE_DUPLICATES"
    name = "Full-Row Duplicate Audit"
    dimension = Dimension.UNIQUENESS

    def evaluate(
        self,
        conn: duckdb.DuckDBPyConnection,
        table_name: str,
        profile: DatasetProfileResponse,
    ) -> List[QualityIssue]:
        issues: List[QualityIssue] = []
        total_rows = profile.row_count
        dataset_id = profile.dataset_id

        if total_rows <= 1 or profile.column_count == 0:
            return issues

        # Query DuckDB for exact identical full-row duplicates
        try:
            dup_query = f"""
                SELECT
                    COALESCE(SUM(dup_count - 1), 0) AS total_extra_duplicates,
                    COUNT(*) AS duplicate_groups
                FROM (
                    SELECT *, COUNT(*) AS dup_count
                    FROM "{table_name}"
                    GROUP BY ALL
                    HAVING COUNT(*) > 1
                )
            """
            result = conn.execute(dup_query).fetchone()
            total_duplicate_rows = int(result[0]) if result and result[0] is not None else 0
            duplicate_groups = int(result[1]) if result and result[1] is not None else 0

            if total_duplicate_rows > 0:
                dup_pct = round((total_duplicate_rows / total_rows) * 100.0, 2)
                if dup_pct >= 20.0:
                    sev = Severity.CRITICAL
                elif dup_pct >= 5.0:
                    sev = Severity.HIGH
                else:
                    sev = Severity.MEDIUM

                issues.append(
                    QualityIssue(
                        issue_id=self.generate_issue_id(dataset_id, "FULL_ROW_DUPLICATES"),
                        dataset_id=dataset_id,
                        issue_type=IssueType.DUPLICATES,
                        dimension=self.dimension,
                        severity=sev,
                        affected_rows=total_duplicate_rows,
                        affected_percentage=dup_pct,
                        description=f"Dataset contains {total_duplicate_rows} exact duplicate row(s) across {duplicate_groups} distinct record group(s).",
                        evidence={
                            "duplicate_rows": total_duplicate_rows,
                            "duplicate_groups": duplicate_groups,
                            "duplicate_percentage": dup_pct,
                            "total_rows": total_rows,
                        },
                        rule_id=self.rule_id,
                        confidence=1.0,
                        recommended_action="Review and deduplicate exact matching records in Phase 6.",
                    )
                )
        except Exception:
            pass

        return issues
