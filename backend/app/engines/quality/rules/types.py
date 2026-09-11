"""
Type Consistency & Uniformity Rule
Detects mixed formats, unparseable numeric strings, and constant/near-constant columns.
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
from backend.app.engines.quality.thresholds import QUALITY_NEAR_CONSTANT_THRESHOLD
from backend.app.schemas.profile import DatasetProfileResponse


class TypeConsistencyRule(BaseQualityRule):
    rule_id = "RULE_TYPE_CONSISTENCY"
    name = "Type Uniformity & Variance Audit"
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
            non_null_count = total_rows - col_meta.null_count
            if non_null_count == 0:
                continue

            top_cats = (
                col_meta.categorical_metrics.top_categories
                if col_meta.categorical_metrics
                else []
            )

            # 1. Constant Column Check (1 distinct non-null value)
            if col_meta.unique_count == 1 and non_null_count > 1:
                dominant_val = (
                    top_cats[0].value
                    if top_cats
                    else "constant"
                )
                issues.append(
                    QualityIssue(
                        issue_id=self.generate_issue_id(dataset_id, "CONST_COL", col_name),
                        dataset_id=dataset_id,
                        issue_type=IssueType.CONSTANT_COLUMN,
                        dimension=self.dimension,
                        severity=Severity.LOW,
                        column_name=col_name,
                        affected_rows=non_null_count,
                        affected_percentage=round((non_null_count / total_rows) * 100.0, 2),
                        description=f"Column '{col_name}' is constant; all non-null values are identical ('{dominant_val}').",
                        evidence={"distinct_values": 1, "value": dominant_val},
                        rule_id=self.rule_id,
                        confidence=1.0,
                        recommended_action=f"Consider dropping zero-variance column '{col_name}' before modeling in Phase 6.",
                    )
                )
                continue

            # 2. Near-Constant Column Check (Dominant value >= 95% of non-nulls)
            if top_cats and len(top_cats) > 0 and col_meta.unique_count > 1:
                top_cat = top_cats[0]
                dominant_freq_pct = (top_cat.count / non_null_count) * 100.0
                if dominant_freq_pct >= QUALITY_NEAR_CONSTANT_THRESHOLD and col_meta.unique_count <= 10:
                    issues.append(
                        QualityIssue(
                            issue_id=self.generate_issue_id(dataset_id, "NEAR_CONST_COL", col_name),
                            dataset_id=dataset_id,
                            issue_type=IssueType.NEAR_CONSTANT_COLUMN,
                            dimension=self.dimension,
                            severity=Severity.INFO,
                            column_name=col_name,
                            affected_rows=top_cat.count,
                            affected_percentage=round((top_cat.count / total_rows) * 100.0, 2),
                            description=f"Column '{col_name}' is near-constant: value '{top_cat.value}' accounts for {dominant_freq_pct:.1f}% of non-null records.",
                            evidence={
                                "dominant_value": top_cat.value,
                                "dominant_frequency_pct": round(dominant_freq_pct, 2),
                                "distinct_values": col_meta.unique_count,
                            },
                            rule_id=self.rule_id,
                            confidence=0.95,
                            recommended_action=f"Verify if extreme class imbalance in '{col_name}' reflects true variance or default placeholder filling.",
                        )
                    )

            # 3. Numeric Inconsistency in String/Text Columns
            # If column name suggests a number (age, price, salary, amount, score, quantity, count)
            # or semantic type is numeric, but physical type is string/varchar
            col_name_lower = col_name.lower()
            num_indicators = ("age", "price", "amount", "salary", "score", "rate", "cost", "quantity", "count", "num")
            is_likely_numeric = (
                col_meta.physical_type in ("string", "varchar", "text")
                and (
                    col_meta.semantic_type in ("numeric", "integer", "decimal", "monetary", "percentage")
                    or any(ind in col_name_lower for ind in num_indicators)
                )
            )

            if is_likely_numeric:
                try:
                    # Count non-null, non-blank strings that fail numeric cast
                    invalid_cast_query = f"""
                        SELECT COUNT(*)
                        FROM "{table_name}"
                        WHERE "{col_name}" IS NOT NULL
                          AND TRIM(CAST("{col_name}" AS VARCHAR)) != ''
                          AND TRY_CAST("{col_name}" AS DOUBLE) IS NULL
                    """
                    invalid_count = conn.execute(invalid_cast_query).fetchone()[0]
                    if invalid_count > 0:
                        pct = round((invalid_count / total_rows) * 100.0, 2)
                        issues.append(
                            QualityIssue(
                                issue_id=self.generate_issue_id(dataset_id, "INVALID_NUM_CAST", col_name),
                                dataset_id=dataset_id,
                                issue_type=IssueType.TYPE_INCONSISTENCY,
                                dimension=self.dimension,
                                severity=Severity.HIGH,
                                column_name=col_name,
                                affected_rows=invalid_count,
                                affected_percentage=pct,
                                description=f"Numeric column '{col_name}' contains {invalid_count} unparseable non-numeric text value(s) (e.g. corrupted strings or sentinel codes).",
                                evidence={"unparseable_rows": invalid_count, "affected_percentage": pct},
                                rule_id=self.rule_id,
                                confidence=0.98,
                                recommended_action=f"Clean unparseable text in '{col_name}' and coerce column to numeric in Phase 6.",
                            )
                        )
                except Exception:
                    pass

        return issues
