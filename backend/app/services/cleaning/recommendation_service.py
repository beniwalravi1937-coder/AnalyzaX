"""
Cleaning Recommendation Service
Translates Phase 5 Data Quality issues into actionable, deterministic transformation recommendations.
"""

import uuid
from typing import List, Optional

from backend.app.engines.quality.models import IssueType, Severity
from backend.app.engines.transformations.models import (
    CleaningRecommendation,
    RiskLevel,
    TransformationStep,
    TransformationType,
)
from backend.app.services.quality_service import QualityService


class RecommendationService:
    """
    Analyzes quality audit reports and generates prioritized cleaning recommendations
    with fully pre-configured TransformationStep definitions.
    """

    def __init__(self) -> None:
        self._quality_service = QualityService()

    def generate_recommendations(
        self,
        dataset_id: str,
        force_refresh: bool = False,
    ) -> List[CleaningRecommendation]:
        """
        Derives prioritized cleaning steps based on detected dataset quality issues.
        """
        report = self._quality_service.assess_dataset_quality(dataset_id, force_refresh=force_refresh)
        if not report or not report.issues:
            return []

        recommendations: List[CleaningRecommendation] = []

        for issue in report.issues:
            rec = self._map_issue_to_recommendation(issue)
            if rec:
                recommendations.append(rec)

        # Sort recommendations by risk / priority (high severity issues first)
        severity_rank = {
            Severity.CRITICAL: 0,
            Severity.HIGH: 1,
            Severity.MEDIUM: 2,
            Severity.LOW: 3,
            Severity.INFO: 4,
        }
        recommendations.sort(
            key=lambda r: severity_rank.get(
                getattr(Severity, r.risk.value, Severity.LOW), 3
            )
        )

        return recommendations

    def _map_issue_to_recommendation(self, issue) -> Optional[CleaningRecommendation]:
        issue_id = issue.issue_id
        issue_type = issue.issue_type
        col = issue.column_name
        affected_pct = issue.affected_percentage
        affected_rows = issue.affected_rows

        step_id = f"step_{uuid.uuid4().hex[:8]}"

        # 1. High Missingness / Empty Column
        if issue_type == IssueType.EMPTY_COLUMN or (
            issue_type == IssueType.CRITICAL_MISSINGNESS and affected_pct > 75.0
        ):
            if not col:
                return None
            return CleaningRecommendation(
                recommendation_id=f"rec_{uuid.uuid4().hex[:8]}",
                issue_id=issue_id,
                title=f"Drop empty column '{col}'",
                description=f"Column '{col}' is {affected_pct:.1f}% empty and contains no useful analytical variance.",
                reason="Removing uninformative columns reduces noise and memory overhead.",
                risk=RiskLevel.MEDIUM,
                confidence=0.95,
                suggested_step=TransformationStep(
                    step_id=step_id,
                    type=TransformationType.DROP_COLUMNS,
                    parameters={"columns": [col]},
                    input_columns=[col],
                    output_columns=[],
                    description=f"Drop column {col}",
                ),
            )

        # 2. Missing Values in columns
        if issue_type in (IssueType.MISSING_VALUES, IssueType.HIGH_MISSINGNESS):
            if not col:
                return None

            # Suggest fill with median/mode if reasonable, or drop rows if very few
            if affected_pct <= 5.0 and affected_rows < 100:
                return CleaningRecommendation(
                    recommendation_id=f"rec_{uuid.uuid4().hex[:8]}",
                    issue_id=issue_id,
                    title=f"Drop rows with missing '{col}'",
                    description=f"Drop {affected_rows} rows missing '{col}' ({affected_pct:.1f}% of dataset).",
                    reason="Low missingness percentage makes row deletion safe without distorting distributions.",
                    risk=RiskLevel.LOW,
                    confidence=0.9,
                    suggested_step=TransformationStep(
                        step_id=step_id,
                        type=TransformationType.DROP_MISSING,
                        parameters={"strategy": "drop_rows", "columns": [col]},
                        input_columns=[col],
                        output_columns=[col],
                        description=f"Drop rows where {col} is null",
                    ),
                )
            else:
                return CleaningRecommendation(
                    recommendation_id=f"rec_{uuid.uuid4().hex[:8]}",
                    issue_id=issue_id,
                    title=f"Impute missing values in '{col}'",
                    description=f"Fill missing values in '{col}' ({affected_rows} rows) using statistical median/mode.",
                    reason="Imputation preserves existing row observations for downstream modeling and analysis.",
                    risk=RiskLevel.LOW,
                    confidence=0.88,
                    suggested_step=TransformationStep(
                        step_id=step_id,
                        type=TransformationType.FILL_MISSING,
                        parameters={"column": col, "strategy": "median"},
                        input_columns=[col],
                        output_columns=[col],
                        description=f"Impute missing values in {col} using median",
                    ),
                )

        # 3. Duplicate Rows
        if issue_type in (IssueType.DUPLICATES, IssueType.DUPLICATE_IDENTIFIER):
            return CleaningRecommendation(
                recommendation_id=f"rec_{uuid.uuid4().hex[:8]}",
                issue_id=issue_id,
                title="Deduplicate identical rows",
                description=f"Remove {affected_rows} redundant duplicate records from the dataset.",
                reason="Deduplication prevents artificial sample weighting and statistical bias.",
                risk=RiskLevel.LOW,
                confidence=0.99,
                suggested_step=TransformationStep(
                    step_id=step_id,
                    type=TransformationType.DROP_DUPLICATES,
                    parameters={"keep": "first"},
                    input_columns=[],
                    output_columns=[],
                    description="Remove duplicate rows, keeping first occurrence",
                ),
            )

        # 4. Whitespace Inconsistency
        if issue_type in (IssueType.WHITESPACE_INCONSISTENCY, IssueType.BLANK_STRINGS):
            if not col:
                return None
            return CleaningRecommendation(
                recommendation_id=f"rec_{uuid.uuid4().hex[:8]}",
                issue_id=issue_id,
                title=f"Trim whitespace in '{col}'",
                description=f"Strip leading, trailing, and redundant spaces in '{col}'.",
                reason="Inconsistent spacing produces duplicate categories and false mismatches.",
                risk=RiskLevel.LOW,
                confidence=0.98,
                suggested_step=TransformationStep(
                    step_id=step_id,
                    type=TransformationType.TRIM_WHITESPACE,
                    parameters={"column": col},
                    input_columns=[col],
                    output_columns=[col],
                    description=f"Trim whitespace in column {col}",
                ),
            )

        # 5. Category Inconsistency
        if issue_type == IssueType.CATEGORY_INCONSISTENCY:
            if not col:
                return None
            return CleaningRecommendation(
                recommendation_id=f"rec_{uuid.uuid4().hex[:8]}",
                issue_id=issue_id,
                title=f"Standardize text case in '{col}'",
                description=f"Normalize casing to lowercase across distinct categories in '{col}'.",
                reason="Aligns case variations like 'Apple' and 'apple' into canonical values.",
                risk=RiskLevel.LOW,
                confidence=0.92,
                suggested_step=TransformationStep(
                    step_id=step_id,
                    type=TransformationType.TEXT_CASE,
                    parameters={"column": col, "case": "lower"},
                    input_columns=[col],
                    output_columns=[col],
                    description=f"Convert {col} to lowercase",
                ),
            )

        # 6. Constant / Zero-Variance Column
        if issue_type == IssueType.CONSTANT_COLUMN:
            if not col:
                return None
            return CleaningRecommendation(
                recommendation_id=f"rec_{uuid.uuid4().hex[:8]}",
                issue_id=issue_id,
                title=f"Drop zero-variance column '{col}'",
                description=f"Column '{col}' has identical values across all rows.",
                reason="Constant features provide zero predictive or analytical information.",
                risk=RiskLevel.LOW,
                confidence=0.95,
                suggested_step=TransformationStep(
                    step_id=step_id,
                    type=TransformationType.DROP_COLUMNS,
                    parameters={"columns": [col]},
                    input_columns=[col],
                    output_columns=[],
                    description=f"Drop constant column {col}",
                ),
            )

        # 7. Outliers
        if issue_type == IssueType.OUTLIER_RISK:
            if not col:
                return None
            return CleaningRecommendation(
                recommendation_id=f"rec_{uuid.uuid4().hex[:8]}",
                issue_id=issue_id,
                title=f"Clip extreme outliers in '{col}'",
                description=f"Winsorize outliers in '{col}' exceeding 1.5x IQR boundaries.",
                reason="Prevents skewed calculations and unstable machine learning training.",
                risk=RiskLevel.MEDIUM,
                confidence=0.85,
                suggested_step=TransformationStep(
                    step_id=step_id,
                    type=TransformationType.HANDLE_OUTLIERS,
                    parameters={"column": col, "method": "clip_iqr", "iqr_multiplier": 1.5},
                    input_columns=[col],
                    output_columns=[col],
                    description=f"Clip outliers in {col} using 1.5x IQR",
                ),
            )

        # 8. Date Parsing
        if issue_type == IssueType.INVALID_DATE:
            if not col:
                return None
            return CleaningRecommendation(
                recommendation_id=f"rec_{uuid.uuid4().hex[:8]}",
                issue_id=issue_id,
                title=f"Parse dates in '{col}'",
                description=f"Parse string dates in '{col}' to native Date/Datetime objects.",
                reason="Enables temporal filtering, time series decomposition, and trend analysis.",
                risk=RiskLevel.LOW,
                confidence=0.88,
                suggested_step=TransformationStep(
                    step_id=step_id,
                    type=TransformationType.PARSE_DATE,
                    parameters={"column": col},
                    input_columns=[col],
                    output_columns=[col],
                    description=f"Parse {col} into Date/Datetime",
                ),
            )

        return None
