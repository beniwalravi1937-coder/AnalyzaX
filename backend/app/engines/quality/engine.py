"""
Data Quality Engine Orchestrator
Coordinates all modular quality rules, aggregates issues, and computes overall report.
"""

import time
from typing import List, Set
import duckdb
from backend.app.core.logging import logger
from backend.app.engines.quality.models import (
    DataQualityReport,
    QualityIssue,
    Severity,
)
from backend.app.engines.quality.rules.base import BaseQualityRule
from backend.app.engines.quality.rules.categories import CategoryConsistencyRule
from backend.app.engines.quality.rules.completeness import CompletenessRule
from backend.app.engines.quality.rules.duplicates import DuplicatesRule
from backend.app.engines.quality.rules.formats import FormatValidationRule
from backend.app.engines.quality.rules.identifiers import IdentifiersRule
from backend.app.engines.quality.rules.outliers import OutlierRiskRule
from backend.app.engines.quality.rules.ranges import RangeValidationRule
from backend.app.engines.quality.rules.types import TypeConsistencyRule
from backend.app.engines.quality.scoring import QualityScorer
from backend.app.engines.quality.thresholds import QUALITY_REPORT_VERSION
from backend.app.schemas.profile import DatasetProfileResponse


class DataQualityEngine:
    """
    Main Data Quality evaluation engine for AnalyzaX.
    Purely deterministic, read-only analytical engine that executes configured rule audits.
    """

    def __init__(self) -> None:
        self.rules: List[BaseQualityRule] = [
            CompletenessRule(),
            DuplicatesRule(),
            IdentifiersRule(),
            TypeConsistencyRule(),
            RangeValidationRule(),
            CategoryConsistencyRule(),
            FormatValidationRule(),
            OutlierRiskRule(),
        ]

    def evaluate(
        self,
        conn: duckdb.DuckDBPyConnection,
        table_name: str,
        profile: DatasetProfileResponse,
    ) -> DataQualityReport:
        """
        Executes all quality rules against the specified table and profile.
        Returns a complete, validated DataQualityReport.
        """
        start_time = time.perf_counter()
        logger.info(f"Starting Data Quality assessment for table '{table_name}' ({len(self.rules)} rules)")

        all_issues: List[QualityIssue] = []
        affected_cols_set: Set[str] = set()

        for rule in self.rules:
            try:
                rule_issues = rule.evaluate(conn=conn, table_name=table_name, profile=profile)
                for issue in rule_issues:
                    all_issues.append(issue)
                    if issue.column_name:
                        affected_cols_set.add(issue.column_name)
            except Exception as e:
                logger.error(f"Quality rule {rule.rule_id} failed during execution: {e}", exc_info=True)

        # Count severities
        crit_count = sum(1 for i in all_issues if i.severity == Severity.CRITICAL)
        high_count = sum(1 for i in all_issues if i.severity == Severity.HIGH)
        med_count = sum(1 for i in all_issues if i.severity == Severity.MEDIUM)
        low_count = sum(1 for i in all_issues if i.severity == Severity.LOW)
        info_count = sum(1 for i in all_issues if i.severity == Severity.INFO)

        # Estimate affected rows (max of row-level issues or capped at total_rows)
        row_level_issues = [i.affected_rows for i in all_issues if i.affected_rows > 0]
        total_affected_rows = min(profile.row_count, max(row_level_issues)) if row_level_issues else 0

        # Calculate scores and summaries
        overall_score, grade, dim_scores, col_summaries, explanation = QualityScorer.calculate_scores(
            issues=all_issues,
            profile=profile,
        )

        execution_time_ms = round((time.perf_counter() - start_time) * 1000.0, 2)
        logger.info(
            f"Quality assessment complete in {execution_time_ms}ms: "
            f"Score={overall_score} ({grade}), Total Issues={len(all_issues)}"
        )

        return DataQualityReport(
            dataset_id=profile.dataset_id,
            dataset_version="v1",
            quality_report_version=QUALITY_REPORT_VERSION,
            status="READY",
            overall_score=overall_score,
            overall_grade=grade,
            dimension_scores=dim_scores,
            total_issues=len(all_issues),
            critical_issues=crit_count,
            high_issues=high_count,
            medium_issues=med_count,
            low_issues=low_count,
            info_issues=info_count,
            affected_rows=total_affected_rows,
            affected_columns=len(affected_cols_set),
            issues=all_issues,
            column_summaries=col_summaries,
            execution_time_ms=execution_time_ms,
            scoring_explanation=explanation,
        )
