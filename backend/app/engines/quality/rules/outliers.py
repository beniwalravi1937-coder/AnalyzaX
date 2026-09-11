"""
Outlier Risk Quality Rule
Quality-oriented anomaly detection flagging unusual numerical values via Tukey's IQR boundaries.
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
from backend.app.engines.quality.thresholds import QUALITY_OUTLIER_IQR_MULTIPLIER
from backend.app.schemas.profile import DatasetProfileResponse


class OutlierRiskRule(BaseQualityRule):
    rule_id = "RULE_OUTLIER_RISK"
    name = "Statistical Anomaly & Outlier Risk Audit"
    dimension = Dimension.ANOMALY_RISK

    def evaluate(
        self,
        conn: duckdb.DuckDBPyConnection,
        table_name: str,
        profile: DatasetProfileResponse,
    ) -> List[QualityIssue]:
        issues: List[QualityIssue] = []
        total_rows = profile.row_count
        dataset_id = profile.dataset_id

        # Skip small datasets or zero-variance tables where IQR is uninformative
        if total_rows < 10:
            return issues

        for col_meta in profile.columns:
            col_name = col_meta.name
            # Skip identifier columns
            if col_meta.semantic_type == "identifier" or getattr(col_meta, "is_identifier_candidate", False):
                continue

            num_metrics = col_meta.numeric_metrics
            if not num_metrics or not num_metrics.quantiles:
                continue

            q = num_metrics.quantiles
            iqr = q.iqr
            if iqr is None or iqr <= 0:
                continue

            q25 = q.p25
            q75 = q.p75
            lower_fence = q25 - (QUALITY_OUTLIER_IQR_MULTIPLIER * iqr)
            upper_fence = q75 + (QUALITY_OUTLIER_IQR_MULTIPLIER * iqr)

            # Check if dataset min or max actually breaches the fences
            if num_metrics.min >= lower_fence and num_metrics.max <= upper_fence:
                continue

            try:
                outlier_query = f"""
                    SELECT COUNT(*)
                    FROM "{table_name}"
                    WHERE "{col_name}" IS NOT NULL
                      AND (""{col_name}"" < {lower_fence} OR "{col_name}" > {upper_fence})
                """
                # Handle possible DuckDB query escaping safely
                outlier_query = f"""
                    SELECT COUNT(*)
                    FROM "{table_name}"
                    WHERE "{col_name}" IS NOT NULL
                      AND ("{col_name}" < {lower_fence} OR "{col_name}" > {upper_fence})
                """
                outlier_count = conn.execute(outlier_query).fetchone()[0]
                if outlier_count > 0:
                    pct = round((outlier_count / total_rows) * 100.0, 2)
                    if pct >= 10.0:
                        sev = Severity.HIGH
                    elif pct >= 2.0:
                        sev = Severity.MEDIUM
                    else:
                        sev = Severity.LOW

                    issues.append(
                        QualityIssue(
                            issue_id=self.generate_issue_id(dataset_id, "OUTLIER_IQR", col_name),
                            dataset_id=dataset_id,
                            issue_type=IssueType.OUTLIER_RISK,
                            dimension=self.dimension,
                            severity=sev,
                            column_name=col_name,
                            affected_rows=outlier_count,
                            affected_percentage=pct,
                            description=(
                                f"Column '{col_name}' has {outlier_count} potential statistical outlier(s) ({pct}%) "
                                f"outside Tukey's fences [{lower_fence:.2f}, {upper_fence:.2f}]."
                            ),
                            evidence={
                                "lower_fence": round(lower_fence, 4),
                                "upper_fence": round(upper_fence, 4),
                                "q25": round(q25, 4),
                                "q75": round(q75, 4),
                                "iqr": round(iqr, 4),
                                "outlier_count": outlier_count,
                                "min": num_metrics.min,
                                "max": num_metrics.max,
                            },
                            rule_id=self.rule_id,
                            confidence=0.90,
                            recommended_action=f"Inspect extreme values in '{col_name}'; evaluate clipping, winsorization, or log transformation in Phase 6.",
                        )
                    )
            except Exception:
                pass

        return issues
