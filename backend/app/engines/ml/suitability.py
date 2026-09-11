"""
AnalyzaX — Phase 11: ML Suitability Analysis & Target/Feature Validation.
Performs deterministic, rule-based checks for data suitability, leakage risks,
class imbalance, constant columns, and identifier probabilities.
"""

from typing import Any, Dict, List, Optional, Set, Tuple
import polars as pl
import numpy as np

from backend.app.engines.ml.models import (
    MLTaskType,
    SuitabilityIssue,
    SuitabilityReport,
    SuitabilitySeverity,
)


def analyze_suitability(
    df: pl.DataFrame,
    target_column: Optional[str] = None,
    requested_task: Optional[MLTaskType] = None,
    candidate_features: Optional[List[str]] = None,
) -> SuitabilityReport:
    """
    Evaluates whether a dataset version is suitable for ML.
    Checks row count, feature count, target properties, constant features,
    high cardinality, class imbalance, and data leakage candidates.
    """
    issues: List[SuitabilityIssue] = []
    total_rows = df.height
    total_cols = df.width
    col_names = df.columns

    # 1. Dataset Dimensions
    if total_rows < 10:
        issues.append(
            SuitabilityIssue(
                code="INSUFFICIENT_OBSERVATIONS",
                severity=SuitabilitySeverity.CRITICAL,
                title="Dataset Too Small",
                message=f"Dataset has only {total_rows} rows. Minimum 10 rows required for ML training.",
                action_recommendation="Collect more data or upload a larger dataset version.",
            )
        )
    elif total_rows < 50:
        issues.append(
            SuitabilityIssue(
                code="SMALL_SAMPLE_SIZE",
                severity=SuitabilitySeverity.MEDIUM,
                title="Small Sample Size",
                message=f"Dataset has {total_rows} rows. Overfitting risk is high; cross-validation folds will be small.",
                action_recommendation="Use simple linear models or baselines with 3-fold cross-validation.",
            )
        )

    # 2. Target Inference & Validation
    inferred_task = requested_task
    target_col = target_column

    # Recommend target if not provided and supervised task or general check
    if not target_col and (requested_task != MLTaskType.CLUSTERING):
        # Pick the best candidate target: usually last numeric or low-cardinality column, avoiding IDs
        for col in reversed(col_names):
            c_lower = col.lower()
            if any(id_word in c_lower for id_word in ["id", "uuid", "key", "index"]):
                continue
            dtype = df.schema[col]
            n_unique = df[col].n_unique()
            if dtype.is_numeric() and 1 < n_unique < total_rows:
                target_col = col
                break
            elif (dtype == pl.Utf8 or dtype == pl.Categorical or dtype == pl.Boolean) and 1 < n_unique <= 20:
                target_col = col
                break

    class_distribution: Optional[Dict[str, int]] = None
    imbalance_ratio: Optional[float] = None

    if target_col:
        if target_col not in col_names:
            issues.append(
                SuitabilityIssue(
                    code="TARGET_NOT_FOUND",
                    severity=SuitabilitySeverity.CRITICAL,
                    column=target_col,
                    title="Target Column Missing",
                    message=f"Specified target '{target_col}' does not exist in the dataset.",
                    action_recommendation="Select a valid column present in the dataset schema.",
                )
            )
        else:
            target_series = df[target_col]
            null_count = target_series.null_count()
            if null_count > 0:
                pct_null = (null_count / total_rows) * 100
                if pct_null > 50:
                    issues.append(
                        SuitabilityIssue(
                            code="HIGH_TARGET_MISSINGNESS",
                            severity=SuitabilitySeverity.CRITICAL,
                            column=target_col,
                            title="Target Has Excessive Missing Values",
                            message=f"Target column '{target_col}' has {pct_null:.1f}% missing values.",
                            action_recommendation="Clean or impute the target in Phase 6, or choose another target.",
                        )
                    )
                else:
                    issues.append(
                        SuitabilityIssue(
                            code="TARGET_NULLS",
                            severity=SuitabilitySeverity.MEDIUM,
                            column=target_col,
                            title="Target Contains Missing Values",
                            message=f"Target column '{target_col}' has {null_count} ({pct_null:.1f}%) missing values. Rows with missing targets will be dropped during training.",
                            action_recommendation="Review missingness in Data Quality or clean beforehand.",
                        )
                    )

            target_dtype = target_series.dtype
            n_unique = target_series.drop_nulls().n_unique()

            if n_unique <= 1:
                issues.append(
                    SuitabilityIssue(
                        code="CONSTANT_TARGET",
                        severity=SuitabilitySeverity.CRITICAL,
                        column=target_col,
                        title="Constant Target",
                        message=f"Target column '{target_col}' has {n_unique} unique values. Cannot train a predictive model with no target variance.",
                        action_recommendation="Select a column with variance across observations.",
                    )
                )

            # Auto-infer task if not explicitly given
            if not inferred_task:
                if target_dtype.is_numeric() and n_unique > 15:
                    inferred_task = MLTaskType.REGRESSION
                elif n_unique == 2:
                    inferred_task = MLTaskType.BINARY_CLASSIFICATION
                elif 2 < n_unique <= 20:
                    inferred_task = MLTaskType.MULTICLASS_CLASSIFICATION
                elif target_dtype.is_numeric():
                    inferred_task = MLTaskType.REGRESSION
                else:
                    inferred_task = MLTaskType.MULTICLASS_CLASSIFICATION

            # Task-specific target validation
            if inferred_task == MLTaskType.REGRESSION:
                if not target_dtype.is_numeric():
                    issues.append(
                        SuitabilityIssue(
                            code="INVALID_REGRESSION_TARGET_TYPE",
                            severity=SuitabilitySeverity.CRITICAL,
                            column=target_col,
                            title="Non-Numeric Target for Regression",
                            message=f"Target '{target_col}' has non-numeric type ({target_dtype}). Regression requires a continuous numeric target.",
                            action_recommendation="Select a numeric target or switch task to Classification.",
                        )
                    )
            elif inferred_task in (MLTaskType.BINARY_CLASSIFICATION, MLTaskType.MULTICLASS_CLASSIFICATION):
                # Count classes
                value_counts = target_series.drop_nulls().value_counts()
                dist_map = {str(row[0]): int(row[1]) for row in value_counts.iter_rows()}
                class_distribution = dist_map

                if inferred_task == MLTaskType.BINARY_CLASSIFICATION and n_unique != 2:
                    issues.append(
                        SuitabilityIssue(
                            code="INVALID_BINARY_CLASS_COUNT",
                            severity=SuitabilitySeverity.HIGH,
                            column=target_col,
                            title="Binary Classification Mismatch",
                            message=f"Target has {n_unique} distinct classes, but Binary Classification expects exactly 2.",
                            action_recommendation="Switch task to Multiclass Classification or filter classes.",
                        )
                    )
                elif inferred_task == MLTaskType.MULTICLASS_CLASSIFICATION and n_unique > 50:
                    issues.append(
                        SuitabilityIssue(
                            code="EXCESSIVE_CLASSES",
                            severity=SuitabilitySeverity.HIGH,
                            column=target_col,
                            title="Extremely High Class Cardinality",
                            message=f"Target has {n_unique} unique classes. Training will be computationally slow and require substantial data per class.",
                            action_recommendation="Group rare classes in Cleaning or choose a different target.",
                        )
                    )

                # Check class imbalance
                if dist_map and len(dist_map) >= 2:
                    counts = sorted(dist_map.values())
                    min_count = counts[0]
                    max_count = counts[-1]
                    imbalance_ratio = round(min_count / max_count, 4) if max_count > 0 else 1.0

                    if min_count < 2:
                        issues.append(
                            SuitabilityIssue(
                                code="SINGLETON_CLASS",
                                severity=SuitabilitySeverity.CRITICAL,
                                column=target_col,
                                title="Singleton Class Detected",
                                message=f"Minority class has only {min_count} sample(s). Cannot perform train/test split or stratified cross-validation.",
                                action_recommendation="Remove or merge singleton classes in Cleaning.",
                            )
                        )
                    elif imbalance_ratio < 0.10:
                        issues.append(
                            SuitabilityIssue(
                                code="SEVERE_CLASS_IMBALANCE",
                                severity=SuitabilitySeverity.HIGH,
                                column=target_col,
                                title="Severe Class Imbalance",
                                message=f"Minority class represents only {imbalance_ratio * 100:.1f}% of the majority class ({min_count} vs {max_count}). Standard accuracy will be misleading.",
                                action_recommendation="Evaluate models using Balanced Accuracy, F1-macro, and PR-AUC.",
                            )
                        )
                    elif imbalance_ratio < 0.30:
                        issues.append(
                            SuitabilityIssue(
                                code="MODERATE_CLASS_IMBALANCE",
                                severity=SuitabilitySeverity.LOW,
                                column=target_col,
                                title="Moderate Class Imbalance",
                                message=f"Class balance ratio is {imbalance_ratio * 100:.1f}%. Stratified splitting is strongly recommended.",
                                action_recommendation="Use Stratified K-Fold validation.",
                            )
                        )
    elif requested_task == MLTaskType.CLUSTERING:
        inferred_task = MLTaskType.CLUSTERING

    # 3. Feature Selection & Leakage Detection
    excluded_features: Dict[str, str] = {}
    recommended_features: List[str] = []
    features_to_check = candidate_features or [c for c in col_names if c != target_col]

    for col in features_to_check:
        if col == target_col:
            continue
        if col not in col_names:
            continue

        c_lower = col.lower()
        series = df[col]
        dtype = series.dtype
        n_unique = series.n_unique()

        # Check for constant feature (0 variance)
        if n_unique <= 1:
            excluded_features[col] = "Constant column (0 variance)"
            issues.append(
                SuitabilityIssue(
                    code="CONSTANT_FEATURE",
                    severity=SuitabilitySeverity.LOW,
                    column=col,
                    title=f"Constant Feature: {col}",
                    message=f"Column '{col}' has only 1 distinct value. It provides zero predictive signal and should be excluded.",
                    action_recommendation="Exclude this column from feature set.",
                )
            )
            continue

        # Check for near-constant feature (> 98% dominant value)
        if total_rows > 50:
            top_count = series.drop_nulls().value_counts().sort("count", descending=True)["count"][0]
            if top_count / total_rows > 0.98:
                issues.append(
                    SuitabilityIssue(
                        code="NEAR_CONSTANT_FEATURE",
                        severity=SuitabilitySeverity.LOW,
                        column=col,
                        title=f"Near-Constant Feature: {col}",
                        message=f"Column '{col}' has a single value in {(top_count / total_rows) * 100:.1f}% of observations.",
                        action_recommendation="Consider excluding or verify whether rare values are informative.",
                    )
                )

        # Check for identifier probability
        is_id_candidate = any(id_word in c_lower for id_word in ["id", "uuid", "key", "index", "hash", "ssn"])
        uniqueness_ratio = n_unique / total_rows
        if is_id_candidate and uniqueness_ratio > 0.90:
            excluded_features[col] = f"Identifier candidate ({uniqueness_ratio * 100:.1f}% unique values)"
            issues.append(
                SuitabilityIssue(
                    code="IDENTIFIER_FEATURE",
                    severity=SuitabilitySeverity.MEDIUM,
                    column=col,
                    title=f"Identifier Column: {col}",
                    message=f"Column '{col}' appears to be a unique entity identifier. Including it can cause spurious memorization and overfitting.",
                    action_recommendation="Exclude identifier columns from model training.",
                )
            )
            continue

        # Check for high-cardinality categorical
        if (dtype == pl.Utf8 or dtype == pl.Categorical) and n_unique > 50:
            excluded_features[col] = f"High cardinality categorical ({n_unique} unique values)"
            issues.append(
                SuitabilityIssue(
                    code="HIGH_CARDINALITY_CATEGORICAL",
                    severity=SuitabilitySeverity.MEDIUM,
                    column=col,
                    title=f"High Cardinality: {col}",
                    message=f"Categorical feature '{col}' has {n_unique} unique values. One-hot encoding would dramatically explode the feature dimension.",
                    action_recommendation="Exclude or aggregate categories into higher-level groupings in Phase 6.",
                )
            )
            continue

        # Check for extreme missingness
        null_count = series.null_count()
        if null_count / total_rows > 0.80:
            excluded_features[col] = f"Extreme missingness ({(null_count / total_rows) * 100:.1f}% nulls)"
            issues.append(
                SuitabilityIssue(
                    code="HIGH_FEATURE_MISSINGNESS",
                    severity=SuitabilitySeverity.LOW,
                    column=col,
                    title=f"Excessive Missingness: {col}",
                    message=f"Feature '{col}' has {(null_count / total_rows) * 100:.1f}% missing values.",
                    action_recommendation="Consider excluding this column from features.",
                )
            )
            continue

        # Check for obvious target leakage (e.g. feature name equals or strongly resembles target, or identical column)
        if target_col:
            if c_lower == target_col.lower():
                excluded_features[col] = "Direct target column duplication"
                issues.append(
                    SuitabilityIssue(
                        code="TARGET_LEAKAGE",
                        severity=SuitabilitySeverity.CRITICAL,
                        column=col,
                        title=f"Target Leakage: {col}",
                        message=f"Feature '{col}' is identical to target '{target_col}'.",
                        action_recommendation="Never include the target variable in the predictor set.",
                    )
                )
                continue
            elif target_col.lower() in c_lower and any(w in c_lower for w in ["pred", "result", "post", "score", "derived"]):
                issues.append(
                    SuitabilityIssue(
                        code="SUSPECTED_TARGET_LEAKAGE",
                        severity=SuitabilitySeverity.HIGH,
                        column=col,
                        title=f"Suspected Target Leakage: {col}",
                        message=f"Column '{col}' name indicates it may be derived post-outcome from target '{target_col}'.",
                        action_recommendation="Verify whether this variable is genuinely available prior to inference time.",
                    )
                )

        recommended_features.append(col)

    # 4. Final Suitability Determination
    has_critical = any(issue.severity == SuitabilitySeverity.CRITICAL for issue in issues)
    is_suitable = not has_critical and len(recommended_features) > 0

    if not is_suitable and len(recommended_features) == 0:
        issues.append(
            SuitabilityIssue(
                code="NO_USABLE_FEATURES",
                severity=SuitabilitySeverity.CRITICAL,
                title="No Usable Features",
                message="Zero usable predictor columns remained after filtering constant/identifier columns.",
                action_recommendation="Select or engineer meaningful feature columns.",
            )
        )

    summary_text = (
        f"Dataset is suitable for {inferred_task.value if inferred_task else 'ML'}. "
        f"{len(recommended_features)} features recommended, {len(excluded_features)} excluded."
        if is_suitable
        else f"Dataset is not currently ready for training due to {len([i for i in issues if i.severity == SuitabilitySeverity.CRITICAL])} critical issues."
    )

    return SuitabilityReport(
        is_suitable=is_suitable,
        summary=summary_text,
        issues=issues,
        dataset_row_count=total_rows,
        dataset_col_count=total_cols,
        recommended_task=inferred_task,
        recommended_target=target_col,
        recommended_features=recommended_features,
        excluded_features=excluded_features,
        class_distribution=class_distribution,
        imbalance_ratio=imbalance_ratio,
    )
