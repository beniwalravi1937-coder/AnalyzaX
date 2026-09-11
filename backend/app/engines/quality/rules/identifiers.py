"""
Identifier & Primary Key Integrity Rule
Audits primary keys and identifier candidates for nulls and key collisions.
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


class IdentifiersRule(BaseQualityRule):
    rule_id = "RULE_IDENTIFIERS"
    name = "Primary Key & Identifier Integrity Audit"
    dimension = Dimension.INTEGRITY

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
            # Check if this column is an identifier
            is_id_candidate = (
                col_meta.semantic_type == "identifier"
                or getattr(col_meta, "is_identifier_candidate", False)
                or col_name.lower() in ("id", "uuid", "guid", "pk")
                or col_name.lower().endswith(("_id", "_uuid", "_key", "id"))
            )
            # Only evaluate columns that are plausible IDs (not long text or constant)
            if not is_id_candidate:
                continue

            # 1. Check for NULL values in identifier
            if col_meta.null_count > 0:
                pct = col_meta.null_percentage
                issues.append(
                    QualityIssue(
                        issue_id=self.generate_issue_id(dataset_id, "NULL_ID", col_name),
                        dataset_id=dataset_id,
                        issue_type=IssueType.NULL_IDENTIFIER,
                        dimension=self.dimension,
                        severity=Severity.CRITICAL if pct > 5.0 else Severity.HIGH,
                        column_name=col_name,
                        affected_rows=col_meta.null_count,
                        affected_percentage=pct,
                        description=f"Primary key / identifier column '{col_name}' contains {col_meta.null_count} null value(s).",
                        evidence={"null_count": col_meta.null_count, "null_percentage": pct},
                        rule_id=self.rule_id,
                        confidence=1.0,
                        recommended_action=f"Assign unique identifiers to null records or remove invalid key rows in Phase 6.",
                    )
                )

            # 2. Check for duplicate keys in identifier
            try:
                dup_key_query = f"""
                    SELECT COALESCE(SUM(cnt - 1), 0)
                    FROM (
                        SELECT COUNT(*) AS cnt
                        FROM "{table_name}"
                        WHERE "{col_name}" IS NOT NULL
                        GROUP BY "{col_name}"
                        HAVING COUNT(*) > 1
                    )
                """
                dup_count = conn.execute(dup_key_query).fetchone()[0]
                if dup_count > 0:
                    pct = round((dup_count / total_rows) * 100.0, 2)
                    issues.append(
                        QualityIssue(
                            issue_id=self.generate_issue_id(dataset_id, "DUP_ID", col_name),
                            dataset_id=dataset_id,
                            issue_type=IssueType.DUPLICATE_IDENTIFIER,
                            dimension=self.dimension,
                            severity=Severity.CRITICAL,
                            column_name=col_name,
                            affected_rows=dup_count,
                            affected_percentage=pct,
                            description=f"Identifier column '{col_name}' contains {dup_count} duplicate key collision(s), violating record uniqueness.",
                            evidence={"duplicate_keys": dup_count, "affected_percentage": pct},
                            rule_id=self.rule_id,
                            confidence=1.0,
                            recommended_action=f"Investigate entity replication; deduplicate or re-index '{col_name}' in Phase 6.",
                        )
                    )
            except Exception:
                pass

        return issues
