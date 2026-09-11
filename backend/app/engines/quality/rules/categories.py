"""
Category & Whitespace Consistency Rule
Identifies casing variations, leading/trailing whitespace, and unnormalized categorical values.
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


class CategoryConsistencyRule(BaseQualityRule):
    rule_id = "RULE_CATEGORY_CONSISTENCY"
    name = "Categorical & Whitespace Consistency Audit"
    dimension = Dimension.CONSISTENCY

    def evaluate(
        self,
        conn: duckdb.DuckDBPyConnection,
        table_name: str,
        profile: DatasetProfileResponse,
    ) -> List[QualityIssue]:
        issues: List[QualityIssue] = []
        total_rows = profile.row_count
        dataset_id = profile.dataset_id

        if total_rows == 0:
            return issues

        for col_meta in profile.columns:
            col_name = col_meta.name
            # Only evaluate categorical, string, or boolean-like columns
            if col_meta.physical_type not in ("string", "varchar", "text"):
                continue

            # Don't run casing checks on high-cardinality IDs or long free text
            if col_meta.semantic_type in ("identifier", "text") and col_meta.unique_count > 1000:
                continue

            # 1. Whitespace Inconsistency (Leading/Trailing spaces)
            try:
                ws_query = f"""
                    SELECT COUNT(*)
                    FROM "{table_name}"
                    WHERE "{col_name}" IS NOT NULL
                      AND CAST("{col_name}" AS VARCHAR) != TRIM(CAST("{col_name}" AS VARCHAR))
                """
                ws_count = conn.execute(ws_query).fetchone()[0]
                if ws_count > 0:
                    pct = round((ws_count / total_rows) * 100.0, 2)
                    issues.append(
                        QualityIssue(
                            issue_id=self.generate_issue_id(dataset_id, "WHITESPACE", col_name),
                            dataset_id=dataset_id,
                            issue_type=IssueType.WHITESPACE_INCONSISTENCY,
                            dimension=self.dimension,
                            severity=Severity.LOW if pct < 5.0 else Severity.MEDIUM,
                            column_name=col_name,
                            affected_rows=ws_count,
                            affected_percentage=pct,
                            description=f"Column '{col_name}' contains {ws_count} record(s) with unstripped leading or trailing whitespace.",
                            evidence={"untrimmed_records": ws_count, "affected_percentage": pct},
                            rule_id=self.rule_id,
                            confidence=1.0,
                            recommended_action=f"Apply TRIM() to remove whitespace noise in '{col_name}' during Phase 6.",
                        )
                    )
            except Exception:
                pass

            # 2. Case Inconsistency (e.g. 'Male' vs 'male' vs 'MALE')
            try:
                case_query = f"""
                    WITH grouped AS (
                        SELECT
                            LOWER(TRIM(CAST("{col_name}" AS VARCHAR))) AS norm_val,
                            COUNT(DISTINCT "{col_name}") AS variants,
                            COUNT(*) AS affected_count
                        FROM "{table_name}"
                        WHERE "{col_name}" IS NOT NULL
                          AND TRIM(CAST("{col_name}" AS VARCHAR)) != ''
                        GROUP BY 1
                        HAVING COUNT(DISTINCT "{col_name}") > 1
                    )
                    SELECT
                        COUNT(*) AS conflicting_groups,
                        COALESCE(SUM(affected_count), 0) AS total_affected,
                        string_agg(norm_val, ', ') AS sample_groups
                    FROM grouped
                """
                res = conn.execute(case_query).fetchone()
                if res and res[0] and res[0] > 0:
                    conflicting_groups = int(res[0])
                    total_affected = int(res[1])
                    sample_groups = str(res[2]) if res[2] else ""
                    # Limit sample list to first 3
                    samples = sample_groups.split(", ")[:3]
                    pct = round((total_affected / total_rows) * 100.0, 2)

                    issues.append(
                        QualityIssue(
                            issue_id=self.generate_issue_id(dataset_id, "CASE_INCONSISTENCY", col_name),
                            dataset_id=dataset_id,
                            issue_type=IssueType.CATEGORY_INCONSISTENCY,
                            dimension=self.dimension,
                            severity=Severity.MEDIUM,
                            column_name=col_name,
                            affected_rows=total_affected,
                            affected_percentage=pct,
                            description=f"Column '{col_name}' contains inconsistent letter casing across {conflicting_groups} category group(s) (e.g. {', '.join(samples)}).",
                            evidence={
                                "conflicting_groups": conflicting_groups,
                                "total_affected_rows": total_affected,
                                "samples": samples,
                            },
                            rule_id=self.rule_id,
                            confidence=0.95,
                            recommended_action=f"Standardize categorical casing (e.g. lowercase or Title Case) in Phase 6.",
                        )
                    )
            except Exception:
                pass

        return issues
