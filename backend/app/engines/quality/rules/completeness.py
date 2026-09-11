"""
Completeness Quality Rule
Evaluates missing values, empty columns, completely empty rows, and blank string values.
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
from backend.app.engines.quality.thresholds import (
    QUALITY_MISSING_CRITICAL,
    QUALITY_MISSING_HIGH,
    QUALITY_MISSING_LOW,
    QUALITY_MISSING_MEDIUM,
)
from backend.app.schemas.profile import DatasetProfileResponse


class CompletenessRule(BaseQualityRule):
    rule_id = "RULE_COMPLETENESS"
    name = "Completeness & Sparsity Audit"
    dimension = Dimension.COMPLETENESS

    def evaluate(
        self,
        conn: duckdb.DuckDBPyConnection,
        table_name: str,
        profile: DatasetProfileResponse,
    ) -> List[QualityIssue]:
        issues: List[QualityIssue] = []
        total_rows = profile.row_count
        dataset_id = profile.dataset_id

        # Edge case: Empty dataset
        if total_rows == 0:
            issues.append(
                QualityIssue(
                    issue_id=self.generate_issue_id(dataset_id, "EMPTY_DATASET"),
                    dataset_id=dataset_id,
                    issue_type=IssueType.EMPTY_COLUMN,
                    dimension=self.dimension,
                    severity=Severity.CRITICAL,
                    affected_rows=0,
                    affected_percentage=100.0,
                    description="Dataset contains zero rows.",
                    evidence={"total_rows": 0},
                    rule_id=self.rule_id,
                    confidence=1.0,
                    recommended_action="Verify upstream data pipeline or file export; ingest a populated dataset.",
                )
            )
            return issues

        # 1. Check for completely empty rows (all columns are NULL)
        if profile.column_count > 0 and len(profile.columns) > 0:
            null_conditions = " AND ".join(
                [f'"{c.name}" IS NULL' for c in profile.columns]
            )
            empty_row_query = f'SELECT COUNT(*) FROM "{table_name}" WHERE {null_conditions}'
            try:
                empty_row_count = conn.execute(empty_row_query).fetchone()[0]
                if empty_row_count > 0:
                    pct = round((empty_row_count / total_rows) * 100.0, 2)
                    issues.append(
                        QualityIssue(
                            issue_id=self.generate_issue_id(dataset_id, "EMPTY_ROWS"),
                            dataset_id=dataset_id,
                            issue_type=IssueType.EMPTY_ROW,
                            dimension=self.dimension,
                            severity=Severity.HIGH if pct < 10 else Severity.CRITICAL,
                            affected_rows=empty_row_count,
                            affected_percentage=pct,
                            description=f"Dataset contains {empty_row_count} completely empty row(s) (all fields are NULL).",
                            evidence={"empty_rows": empty_row_count, "total_rows": total_rows},
                            rule_id=self.rule_id,
                            confidence=1.0,
                            recommended_action="Filter out completely empty rows during dataset cleaning in Phase 6.",
                        )
                    )
            except Exception:
                pass

        # 2. Check each column for missingness and blank strings
        for col_meta in profile.columns:
            col_name = col_meta.name
            null_count = col_meta.null_count
            null_pct = col_meta.null_percentage

            # 2a. Completely empty column (100% null)
            if null_count == total_rows:
                issues.append(
                    QualityIssue(
                        issue_id=self.generate_issue_id(dataset_id, "EMPTY_COL", col_name),
                        dataset_id=dataset_id,
                        issue_type=IssueType.EMPTY_COLUMN,
                        dimension=self.dimension,
                        severity=Severity.CRITICAL,
                        column_name=col_name,
                        affected_rows=null_count,
                        affected_percentage=100.0,
                        description=f"Column '{col_name}' is 100% null (all values missing).",
                        evidence={"null_count": null_count, "total_rows": total_rows},
                        rule_id=self.rule_id,
                        confidence=1.0,
                        recommended_action=f"Drop empty column '{col_name}' in Phase 6 or populate from external source.",
                    )
                )
                continue

            # 2b. High or critical missingness
            if null_pct >= QUALITY_MISSING_CRITICAL:
                issues.append(
                    QualityIssue(
                        issue_id=self.generate_issue_id(dataset_id, "CRIT_MISSING", col_name),
                        dataset_id=dataset_id,
                        issue_type=IssueType.CRITICAL_MISSINGNESS,
                        dimension=self.dimension,
                        severity=Severity.CRITICAL,
                        column_name=col_name,
                        affected_rows=null_count,
                        affected_percentage=null_pct,
                        description=f"Column '{col_name}' has critical sparsity ({null_pct}% missing).",
                        evidence={"null_count": null_count, "null_percentage": null_pct},
                        rule_id=self.rule_id,
                        confidence=1.0,
                        recommended_action=f"Consider dropping '{col_name}' or assessing if missingness is systematic.",
                    )
                )
            elif null_pct >= QUALITY_MISSING_HIGH:
                issues.append(
                    QualityIssue(
                        issue_id=self.generate_issue_id(dataset_id, "HIGH_MISSING", col_name),
                        dataset_id=dataset_id,
                        issue_type=IssueType.HIGH_MISSINGNESS,
                        dimension=self.dimension,
                        severity=Severity.HIGH,
                        column_name=col_name,
                        affected_rows=null_count,
                        affected_percentage=null_pct,
                        description=f"Column '{col_name}' has high missingness ({null_pct}% missing).",
                        evidence={"null_count": null_count, "null_percentage": null_pct},
                        rule_id=self.rule_id,
                        confidence=1.0,
                        recommended_action=f"Apply targeted imputation (e.g. median/mode) or filter rows in Phase 6.",
                    )
                )
            elif null_pct >= QUALITY_MISSING_MEDIUM:
                issues.append(
                    QualityIssue(
                        issue_id=self.generate_issue_id(dataset_id, "MED_MISSING", col_name),
                        dataset_id=dataset_id,
                        issue_type=IssueType.MISSING_VALUES,
                        dimension=self.dimension,
                        severity=Severity.MEDIUM,
                        column_name=col_name,
                        affected_rows=null_count,
                        affected_percentage=null_pct,
                        description=f"Column '{col_name}' has moderate missingness ({null_pct}% missing).",
                        evidence={"null_count": null_count, "null_percentage": null_pct},
                        rule_id=self.rule_id,
                        confidence=1.0,
                        recommended_action=f"Impute missing values using domain-appropriate defaults in Phase 6.",
                    )
                )
            elif null_pct >= QUALITY_MISSING_LOW:
                issues.append(
                    QualityIssue(
                        issue_id=self.generate_issue_id(dataset_id, "LOW_MISSING", col_name),
                        dataset_id=dataset_id,
                        issue_type=IssueType.MISSING_VALUES,
                        dimension=self.dimension,
                        severity=Severity.LOW,
                        column_name=col_name,
                        affected_rows=null_count,
                        affected_percentage=null_pct,
                        description=f"Column '{col_name}' has minor missingness ({null_pct}% missing).",
                        evidence={"null_count": null_count, "null_percentage": null_pct},
                        rule_id=self.rule_id,
                        confidence=1.0,
                        recommended_action=f"Impute or drop {null_count} missing value(s) in Phase 6.",
                    )
                )

            # 2c. Blank string detection in textual/string columns ('' or '   ')
            if col_meta.physical_type in ("string", "text", "varchar"):
                try:
                    blank_query = (
                        f'SELECT COUNT(*) FROM "{table_name}" '
                        f'WHERE "{col_name}" IS NOT NULL AND TRIM(CAST("{col_name}" AS VARCHAR)) = \'\''
                    )
                    blank_count = conn.execute(blank_query).fetchone()[0]
                    if blank_count > 0:
                        blank_pct = round((blank_count / total_rows) * 100.0, 2)
                        issues.append(
                            QualityIssue(
                                issue_id=self.generate_issue_id(dataset_id, "BLANK_STR", col_name),
                                dataset_id=dataset_id,
                                issue_type=IssueType.BLANK_STRINGS,
                                dimension=self.dimension,
                                severity=Severity.MEDIUM if blank_pct > 5.0 else Severity.LOW,
                                column_name=col_name,
                                affected_rows=blank_count,
                                affected_percentage=blank_pct,
                                description=f"Column '{col_name}' contains {blank_count} blank/whitespace-only string(s) that act as implicit nulls.",
                                evidence={"blank_count": blank_count, "percentage": blank_pct},
                                rule_id=self.rule_id,
                                confidence=1.0,
                                recommended_action=f"Standardize blank strings to explicit NULLs in Phase 6.",
                            )
                        )
                except Exception:
                    pass

        return issues
