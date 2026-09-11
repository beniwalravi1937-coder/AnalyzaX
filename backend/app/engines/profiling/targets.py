"""
Target Variable Candidate Detection Module
Identifies probable machine learning target variables for classification and regression tasks.
"""

from typing import List, Optional
from backend.app.schemas.profile import ColumnProfile, TargetCandidate

TARGET_NAME_KEYWORDS = ("target", "label", "churn", "default", "fraud", "outcome", "status", "converted", "revenue", "price", "sales", "rating", "score")


def evaluate_target_candidate(col: ColumnProfile) -> Optional[TargetCandidate]:
    """
    Evaluates whether a single column is a suitable ML target candidate.
    Strictly filters out constant columns and identifier candidates.
    """
    if col.is_identifier_candidate or col.unique_count <= 1:
        return None

    clean_name = col.name.strip().lower()
    has_target_keyword = any(kw in clean_name for kw in TARGET_NAME_KEYWORDS)

    # 1. Binary Classification Candidate
    if col.unique_count == 2:
        conf = 0.90 if has_target_keyword else 0.80
        if col.semantic_type == "boolean":
            conf = min(1.0, conf + 0.05)
        return TargetCandidate(
            column_name=col.name,
            task_type="binary_classification",
            confidence=round(conf, 2),
            reason=f"Binary variable with 2 discrete classes ('{col.name}') suitable for binary classification.",
        )

    # 2. Multiclass Classification Candidate
    if 3 <= col.unique_count <= 15 and col.physical_type in ("string", "integer"):
        if col.cardinality_ratio < 0.2:
            conf = 0.85 if has_target_keyword else 0.70
            return TargetCandidate(
                column_name=col.name,
                task_type="multiclass_classification",
                confidence=round(conf, 2),
                reason=f"Categorical variable with {col.unique_count} balanced discrete classes suitable for multiclass prediction.",
            )

    # 3. Continuous Regression Candidate
    if col.physical_type in ("float", "decimal", "integer") and col.numeric_metrics is not None:
        metrics = col.numeric_metrics
        if metrics.variance is not None and metrics.variance > 0 and col.unique_count > 15:
            conf = 0.85 if has_target_keyword else 0.65
            if col.semantic_type in ("monetary", "percentage", "ratio"):
                conf = min(0.95, conf + 0.10)
            return TargetCandidate(
                column_name=col.name,
                task_type="regression",
                confidence=round(conf, 2),
                reason=f"Continuous numerical variable with non-zero variance ({metrics.variance:.2f}) suitable for regression modeling.",
            )

    return None


def detect_target_candidates(columns: List[ColumnProfile]) -> List[TargetCandidate]:
    """Scans all column profiles in a dataset and returns ranked target candidate recommendations."""
    candidates = []
    for col in columns:
        cand = evaluate_target_candidate(col)
        if cand:
            candidates.append(cand)

    # Rank by confidence descending
    candidates.sort(key=lambda c: c.confidence, reverse=True)
    return candidates
