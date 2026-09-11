"""
Range & Domain Validation Rule
Validates bounded domains: percentages, geographic coordinates, and non-negative quantities.
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


class RangeValidationRule(BaseQualityRule):
    rule_id = "RULE_RANGE_VALIDATION"
    name = "Domain & Boundary Validation"
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
            if not col_meta.numeric_metrics:
                continue

            num_metrics = col_meta.numeric_metrics
            col_name_lower = col_name.lower()
            sem_type = col_meta.semantic_type

            # 1. Percentage Bounds [0, 100]
            is_percentage = (
                sem_type == "percentage"
                or "percent" in col_name_lower
                or col_name_lower.endswith(("_pct", "_percentage"))
            )
            if is_percentage and (num_metrics.min < 0 or num_metrics.max > 100):
                try:
                    q = f'SELECT COUNT(*) FROM "{table_name}" WHERE "{col_name}" < 0 OR "{col_name}" > 100'
                    out_of_bounds = conn.execute(q).fetchone()[0]
                    if out_of_bounds > 0:
                        pct = round((out_of_bounds / total_rows) * 100.0, 2)
                        issues.append(
                            QualityIssue(
                                issue_id=self.generate_issue_id(dataset_id, "PERCENT_RANGE", col_name),
                                dataset_id=dataset_id,
                                issue_type=IssueType.INVALID_RANGE,
                                dimension=self.dimension,
                                severity=Severity.HIGH,
                                column_name=col_name,
                                affected_rows=out_of_bounds,
                                affected_percentage=pct,
                                description=f"Percentage column '{col_name}' contains {out_of_bounds} value(s) outside [0, 100] (min: {num_metrics.min}, max: {num_metrics.max}).",
                                evidence={"min": num_metrics.min, "max": num_metrics.max, "invalid_count": out_of_bounds},
                                rule_id=self.rule_id,
                                confidence=0.98,
                                recommended_action=f"Clip or scale values in '{col_name}' to standard [0, 100] scale in Phase 6.",
                            )
                        )
                except Exception:
                    pass

            # 2. Geographic Latitude Bounds [-90, 90]
            is_lat = sem_type == "geographic_latitude" or col_name_lower in ("lat", "latitude")
            if is_lat and (num_metrics.min < -90 or num_metrics.max > 90):
                try:
                    q = f'SELECT COUNT(*) FROM "{table_name}" WHERE "{col_name}" < -90 OR "{col_name}" > 90'
                    out_of_bounds = conn.execute(q).fetchone()[0]
                    if out_of_bounds > 0:
                        pct = round((out_of_bounds / total_rows) * 100.0, 2)
                        issues.append(
                            QualityIssue(
                                issue_id=self.generate_issue_id(dataset_id, "LAT_RANGE", col_name),
                                dataset_id=dataset_id,
                                issue_type=IssueType.INVALID_RANGE,
                                dimension=self.dimension,
                                severity=Severity.HIGH,
                                column_name=col_name,
                                affected_rows=out_of_bounds,
                                affected_percentage=pct,
                                description=f"Latitude column '{col_name}' contains {out_of_bounds} value(s) outside valid Earth coordinates [-90, 90].",
                                evidence={"min": num_metrics.min, "max": num_metrics.max, "invalid_count": out_of_bounds},
                                rule_id=self.rule_id,
                                confidence=1.0,
                                recommended_action=f"Filter or correct corrupt GPS latitude values in Phase 6.",
                            )
                        )
                except Exception:
                    pass

            # 3. Geographic Longitude Bounds [-180, 180]
            is_lon = sem_type == "geographic_longitude" or col_name_lower in ("lon", "lng", "longitude")
            if is_lon and (num_metrics.min < -180 or num_metrics.max > 180):
                try:
                    q = f'SELECT COUNT(*) FROM "{table_name}" WHERE "{col_name}" < -180 OR "{col_name}" > 180'
                    out_of_bounds = conn.execute(q).fetchone()[0]
                    if out_of_bounds > 0:
                        pct = round((out_of_bounds / total_rows) * 100.0, 2)
                        issues.append(
                            QualityIssue(
                                issue_id=self.generate_issue_id(dataset_id, "LON_RANGE", col_name),
                                dataset_id=dataset_id,
                                issue_type=IssueType.INVALID_RANGE,
                                dimension=self.dimension,
                                severity=Severity.HIGH,
                                column_name=col_name,
                                affected_rows=out_of_bounds,
                                affected_percentage=pct,
                                description=f"Longitude column '{col_name}' contains {out_of_bounds} value(s) outside valid Earth coordinates [-180, 180].",
                                evidence={"min": num_metrics.min, "max": num_metrics.max, "invalid_count": out_of_bounds},
                                rule_id=self.rule_id,
                                confidence=1.0,
                                recommended_action=f"Filter or correct corrupt GPS longitude values in Phase 6.",
                            )
                        )
                except Exception:
                    pass

            # 4. Strictly Non-Negative Quantities (Age, Count, Quantity, Monetary price/fare)
            is_strictly_positive = (
                col_name_lower in ("age", "user_age", "customer_age")
                or col_name_lower.startswith(("quantity", "qty", "count_"))
                or col_name_lower.endswith(("_count", "_quantity", "_qty"))
                or (sem_type == "monetary" and col_name_lower in ("price", "salary", "fare", "cost"))
            )
            if is_strictly_positive and num_metrics.min < 0:
                try:
                    q = f'SELECT COUNT(*) FROM "{table_name}" WHERE "{col_name}" < 0'
                    neg_count = conn.execute(q).fetchone()[0]
                    if neg_count > 0:
                        pct = round((neg_count / total_rows) * 100.0, 2)
                        issues.append(
                            QualityIssue(
                                issue_id=self.generate_issue_id(dataset_id, "NEG_VALUE", col_name),
                                dataset_id=dataset_id,
                                issue_type=IssueType.NEGATIVE_VALUE,
                                dimension=self.dimension,
                                severity=Severity.HIGH,
                                column_name=col_name,
                                affected_rows=neg_count,
                                affected_percentage=pct,
                                description=f"Column '{col_name}' contains {neg_count} negative value(s) (min: {num_metrics.min}), which violates domain validity.",
                                evidence={"min": num_metrics.min, "negative_count": neg_count},
                                rule_id=self.rule_id,
                                confidence=0.95,
                                recommended_action=f"Investigate sign errors; apply ABS() or replace negatives with NULL/median in Phase 6.",
                            )
                        )
                except Exception:
                    pass

            # 5. Impossible Age (> 130)
            if col_name_lower in ("age", "user_age", "customer_age") and num_metrics.max > 130:
                try:
                    q = f'SELECT COUNT(*) FROM "{table_name}" WHERE "{col_name}" > 130'
                    elder_count = conn.execute(q).fetchone()[0]
                    if elder_count > 0:
                        pct = round((elder_count / total_rows) * 100.0, 2)
                        issues.append(
                            QualityIssue(
                                issue_id=self.generate_issue_id(dataset_id, "IMPOSSIBLE_AGE", col_name),
                                dataset_id=dataset_id,
                                issue_type=IssueType.INVALID_RANGE,
                                dimension=self.dimension,
                                severity=Severity.HIGH,
                                column_name=col_name,
                                affected_rows=elder_count,
                                affected_percentage=pct,
                                description=f"Age column '{col_name}' contains {elder_count} biologically implausible value(s) > 130 (max: {num_metrics.max}).",
                                evidence={"max": num_metrics.max, "implausible_count": elder_count},
                                rule_id=self.rule_id,
                                confidence=0.98,
                                recommended_action=f"Replace corrupted ages > 130 with median age in Phase 6.",
                            )
                        )
                except Exception:
                    pass

        return issues
