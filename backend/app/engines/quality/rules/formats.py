"""
Format & Pattern Quality Rule
Validates specialized string formats: emails, URLs, and date strings.
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


class FormatValidationRule(BaseQualityRule):
    rule_id = "RULE_FORMAT_VALIDATION"
    name = "Semantic Format & Pattern Validation"
    dimension = Dimension.VALIDITY

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
            sem_type = col_meta.semantic_type

            # 1. Email Format Validation
            if sem_type == "email":
                try:
                    q = f"""
                        SELECT COUNT(*)
                        FROM "{table_name}"
                        WHERE "{col_name}" IS NOT NULL
                          AND TRIM(CAST("{col_name}" AS VARCHAR)) != ''
                          AND NOT regexp_matches(CAST("{col_name}" AS VARCHAR), '^[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\\.[A-Za-z]{{2,}}$')
                    """
                    invalid_emails = conn.execute(q).fetchone()[0]
                    if invalid_emails > 0:
                        pct = round((invalid_emails / total_rows) * 100.0, 2)
                        issues.append(
                            QualityIssue(
                                issue_id=self.generate_issue_id(dataset_id, "MALFORMED_EMAIL", col_name),
                                dataset_id=dataset_id,
                                issue_type=IssueType.INVALID_FORMAT,
                                dimension=self.dimension,
                                severity=Severity.MEDIUM,
                                column_name=col_name,
                                affected_rows=invalid_emails,
                                affected_percentage=pct,
                                description=f"Email column '{col_name}' contains {invalid_emails} malformed email address pattern(s).",
                                evidence={"invalid_count": invalid_emails, "affected_percentage": pct},
                                rule_id=self.rule_id,
                                confidence=0.98,
                                recommended_action=f"Clean or NULL malformed email addresses in '{col_name}' during Phase 6.",
                            )
                        )
                except Exception:
                    pass

            # 2. URL Format Validation
            elif sem_type == "url":
                try:
                    q = f"""
                        SELECT COUNT(*)
                        FROM "{table_name}"
                        WHERE "{col_name}" IS NOT NULL
                          AND TRIM(CAST("{col_name}" AS VARCHAR)) != ''
                          AND NOT regexp_matches(CAST("{col_name}" AS VARCHAR), '^(https?|ftp)://[^\\s/$.?#].[^\\s]*$')
                    """
                    invalid_urls = conn.execute(q).fetchone()[0]
                    if invalid_urls > 0:
                        pct = round((invalid_urls / total_rows) * 100.0, 2)
                        issues.append(
                            QualityIssue(
                                issue_id=self.generate_issue_id(dataset_id, "MALFORMED_URL", col_name),
                                dataset_id=dataset_id,
                                issue_type=IssueType.INVALID_FORMAT,
                                dimension=self.dimension,
                                severity=Severity.LOW,
                                column_name=col_name,
                                affected_rows=invalid_urls,
                                affected_percentage=pct,
                                description=f"URL column '{col_name}' contains {invalid_urls} malformed web link(s).",
                                evidence={"invalid_count": invalid_urls, "affected_percentage": pct},
                                rule_id=self.rule_id,
                                confidence=0.95,
                                recommended_action=f"Sanitize or validate URL protocols in '{col_name}' during Phase 6.",
                            )
                        )
                except Exception:
                    pass

            # 3. Unparseable Date Strings
            elif (
                sem_type in ("date", "datetime")
                and col_meta.physical_type in ("string", "varchar", "text")
            ):
                try:
                    q = f"""
                        SELECT COUNT(*)
                        FROM "{table_name}"
                        WHERE "{col_name}" IS NOT NULL
                          AND TRIM(CAST("{col_name}" AS VARCHAR)) != ''
                          AND TRY_CAST("{col_name}" AS TIMESTAMP) IS NULL
                    """
                    invalid_dates = conn.execute(q).fetchone()[0]
                    if invalid_dates > 0:
                        pct = round((invalid_dates / total_rows) * 100.0, 2)
                        issues.append(
                            QualityIssue(
                                issue_id=self.generate_issue_id(dataset_id, "INVALID_DATE_PARSE", col_name),
                                dataset_id=dataset_id,
                                issue_type=IssueType.INVALID_DATE,
                                dimension=self.dimension,
                                severity=Severity.HIGH,
                                column_name=col_name,
                                affected_rows=invalid_dates,
                                affected_percentage=pct,
                                description=f"Date column '{col_name}' contains {invalid_dates} unparseable or corrupted timestamp string(s).",
                                evidence={"invalid_count": invalid_dates, "affected_percentage": pct},
                                rule_id=self.rule_id,
                                confidence=0.98,
                                recommended_action=f"Parse mixed date formats and convert '{col_name}' to strict date type in Phase 6.",
                            )
                        )
                except Exception:
                    pass

        return issues
