"""
Data Quality Scoring Engine
Implements deterministic, explainable, and versioned scoring models.
"""

from typing import Dict, List, Tuple
from backend.app.engines.quality.models import (
    ColumnQualitySummary,
    Dimension,
    DimensionScore,
    QualityIssue,
    Severity,
)
from backend.app.schemas.profile import DatasetProfileResponse

# Dimension weights for overall score calculation (Sum = 1.0)
DIMENSION_WEIGHTS: Dict[Dimension, float] = {
    Dimension.COMPLETENESS: 0.25,
    Dimension.VALIDITY: 0.25,
    Dimension.UNIQUENESS: 0.20,
    Dimension.CONSISTENCY: 0.15,
    Dimension.INTEGRITY: 0.10,
    Dimension.ANOMALY_RISK: 0.05,
}

# Penalty deductions per severity rating
SEVERITY_PENALTIES: Dict[Severity, float] = {
    Severity.CRITICAL: 20.0,
    Severity.HIGH: 10.0,
    Severity.MEDIUM: 4.0,
    Severity.LOW: 1.0,
    Severity.INFO: 0.0,
}


def get_grade_from_score(score: float) -> str:
    """Returns qualitative rating for a score 0-100."""
    if score >= 90.0:
        return "EXCELLENT"
    if score >= 75.0:
        return "GOOD"
    if score >= 60.0:
        return "FAIR"
    if score >= 40.0:
        return "POOR"
    return "CRITICAL"


class QualityScorer:
    """
    Computes deterministic dimension scores, overall dataset health score,
    and column-specific quality ratings.
    """

    @classmethod
    def calculate_scores(
        cls,
        issues: List[QualityIssue],
        profile: DatasetProfileResponse,
    ) -> Tuple[float, str, Dict[Dimension, DimensionScore], List[ColumnQualitySummary], str]:
        """
        Calculates all dimension scores, column summaries, and overall score.
        """
        # Group issues by dimension
        issues_by_dim: Dict[Dimension, List[QualityIssue]] = {dim: [] for dim in Dimension}
        for issue in issues:
            issues_by_dim[issue.dimension].append(issue)

        dimension_scores: Dict[Dimension, DimensionScore] = {}
        for dim, dim_issues in issues_by_dim.items():
            base_score = 100.0
            crit_count = 0
            high_count = 0
            med_count = 0
            low_count = 0
            info_count = 0

            for issue in dim_issues:
                penalty = SEVERITY_PENALTIES.get(issue.severity, 0.0)
                # Scale penalty by affected percentage (min 0.25x so even small anomalies register)
                pct_scale = max(0.25, min(1.0, issue.affected_percentage / 50.0))
                effective_penalty = penalty * pct_scale
                base_score -= effective_penalty

                if issue.severity == Severity.CRITICAL:
                    crit_count += 1
                elif issue.severity == Severity.HIGH:
                    high_count += 1
                elif issue.severity == Severity.MEDIUM:
                    med_count += 1
                elif issue.severity == Severity.LOW:
                    low_count += 1
                elif issue.severity == Severity.INFO:
                    info_count += 1

            clamped_score = round(max(0.0, min(100.0, base_score)), 1)
            desc = cls._dimension_description(dim, clamped_score, len(dim_issues))
            dimension_scores[dim] = DimensionScore(
                dimension=dim,
                score=clamped_score,
                issue_count=len(dim_issues),
                critical_count=crit_count,
                high_count=high_count,
                medium_count=med_count,
                low_count=low_count,
                info_count=info_count,
                description=desc,
            )

        # Compute weighted overall score
        overall_score = 0.0
        for dim, weight in DIMENSION_WEIGHTS.items():
            overall_score += dimension_scores[dim].score * weight
        overall_score = round(max(0.0, min(100.0, overall_score)), 1)
        grade = get_grade_from_score(overall_score)

        # Compute column-level quality scores
        column_summaries = cls._calculate_column_summaries(issues, profile)

        explanation = (
            f"Overall quality score ({overall_score}/100, {grade}) calculated across 6 weighted dimensions: "
            f"Completeness (25%), Validity (25%), Uniqueness (20%), Consistency (15%), Integrity (10%), Anomaly Risk (5%). "
            f"Each dimension starts at 100.0 and deducts weighted penalties for detected issues: "
            f"CRITICAL (-20), HIGH (-10), MEDIUM (-4), LOW (-1)."
        )

        return overall_score, grade, dimension_scores, column_summaries, explanation

    @classmethod
    def _dimension_description(cls, dim: Dimension, score: float, count: int) -> str:
        if count == 0:
            return f"Optimal {dim.value.lower()} with 0 detected anomalies."
        return f"{count} issue(s) detected affecting {dim.value.lower()} health."

    @classmethod
    def _calculate_column_summaries(
        cls,
        issues: List[QualityIssue],
        profile: DatasetProfileResponse,
    ) -> List[ColumnQualitySummary]:
        """Calculates per-column health summary."""
        # Index issues by column
        col_issues: Dict[str, List[QualityIssue]] = {}
        for issue in issues:
            if issue.column_name:
                col_issues.setdefault(issue.column_name, []).append(issue)

        summaries: List[ColumnQualitySummary] = []
        for col_meta in profile.columns:
            col_name = col_meta.name
            issues_for_col = col_issues.get(col_name, [])
            col_score = 100.0
            highest_sev: Optional[Severity] = None
            issue_types: List[str] = []

            for issue in issues_for_col:
                penalty = SEVERITY_PENALTIES.get(issue.severity, 0.0)
                col_score -= penalty
                issue_types.append(issue.issue_type.value)

                # Track highest severity
                if highest_sev is None:
                    highest_sev = issue.severity
                elif cls._severity_rank(issue.severity) > cls._severity_rank(highest_sev):
                    highest_sev = issue.severity

            clamped_col_score = round(max(0.0, min(100.0, col_score)), 1)
            summaries.append(
                ColumnQualitySummary(
                    column_name=col_name,
                    physical_type=col_meta.physical_type,
                    semantic_type=col_meta.semantic_type,
                    quality_score=clamped_col_score,
                    null_percentage=col_meta.null_percentage,
                    unique_percentage=min(100.0, max(0.0, col_meta.unique_percentage)),
                    issues_count=len(issues_for_col),
                    highest_severity=highest_sev,
                    issue_types=list(set(issue_types)),
                )
            )

        return summaries

    @staticmethod
    def _severity_rank(severity: Severity) -> int:
        ranks = {
            Severity.INFO: 0,
            Severity.LOW: 1,
            Severity.MEDIUM: 2,
            Severity.HIGH: 3,
            Severity.CRITICAL: 4,
        }
        return ranks.get(severity, 0)
