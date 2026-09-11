"""
AnalyzaX — Phase 11: Deterministic Splitting & Cross-Validation.
Provides leakage-free train/validation/test splitting and K-Fold cross-validation
with stratification support and sample count validation.
"""

from typing import Any, Dict, Generator, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.model_selection import KFold, StratifiedKFold, train_test_split

from backend.app.core.config import settings
from backend.app.engines.ml.exceptions import MLErrorCode, MLException
from backend.app.engines.ml.models import (
    CrossValidationConfig,
    MLTaskType,
    SplitConfig,
    SplitSummary,
)


def perform_train_val_test_split(
    X: pd.DataFrame,
    y: Optional[pd.Series],
    task_type: MLTaskType,
    config: SplitConfig,
) -> Tuple[
    pd.DataFrame,
    pd.DataFrame,
    pd.DataFrame,
    Optional[pd.Series],
    Optional[pd.Series],
    Optional[pd.Series],
    SplitSummary,
    List[str],
]:
    """
    Deterministically splits data into train, validation, and test subsets.
    Supports stratified splitting for classification tasks where feasible.
    """
    n_samples = len(X)
    warnings: List[str] = []

    if n_samples < 6:
        raise MLException(
            f"Dataset has only {n_samples} samples; cannot perform train/val/test split.",
            MLErrorCode.ML_INSUFFICIENT_DATA,
        )

    # Normalize proportions if needed
    total_prop = config.train_size + config.val_size + config.test_size
    train_pct = config.train_size / total_prop
    val_pct = config.val_size / total_prop
    test_pct = config.test_size / total_prop

    # Determine whether stratification is feasible
    stratify_col: Optional[pd.Series] = None
    is_stratified = False

    if (
        config.stratify
        and y is not None
        and task_type in (MLTaskType.BINARY_CLASSIFICATION, MLTaskType.MULTICLASS_CLASSIFICATION)
    ):
        class_counts = y.value_counts()
        min_class_count = class_counts.min()
        if min_class_count >= 3:
            stratify_col = y
            is_stratified = True
        else:
            warnings.append(
                f"Stratification disabled: minority class has only {min_class_count} sample(s), which is fewer than the 3 subsets."
            )

    # Step 1: Split into Train and Temp (Val + Test)
    temp_size = val_pct + test_pct
    if y is not None:
        try:
            X_train, X_temp, y_train, y_temp = train_test_split(
                X,
                y,
                test_size=temp_size,
                random_state=config.random_seed,
                stratify=stratify_col,
            )
        except Exception as e:
            warnings.append(f"Stratification error during initial split ({e}); fell back to random split.")
            X_train, X_temp, y_train, y_temp = train_test_split(
                X,
                y,
                test_size=temp_size,
                random_state=config.random_seed,
                stratify=None,
            )
            is_stratified = False
    else:
        X_train, X_temp = train_test_split(
            X,
            test_size=temp_size,
            random_state=config.random_seed,
        )
        y_train, y_temp = None, None

    # Step 2: Split Temp into Validation and Test
    val_ratio = val_pct / temp_size
    stratify_temp = y_temp if is_stratified else None

    # Check if temp has enough minority samples
    if stratify_temp is not None and stratify_temp.value_counts().min() < 2:
        stratify_temp = None
        is_stratified = False
        warnings.append("Stratification disabled for validation/test split due to small class counts in holdout.")

    if y_temp is not None:
        try:
            X_val, X_test, y_val, y_test = train_test_split(
                X_temp,
                y_temp,
                train_size=val_ratio,
                random_state=config.random_seed,
                stratify=stratify_temp,
            )
        except Exception:
            X_val, X_test, y_val, y_test = train_test_split(
                X_temp,
                y_temp,
                train_size=val_ratio,
                random_state=config.random_seed,
                stratify=None,
            )
            is_stratified = False
    else:
        X_val, X_test = train_test_split(
            X_temp,
            train_size=val_ratio,
            random_state=config.random_seed,
        )
        y_val, y_test = None, None

    summary = SplitSummary(
        train_rows=len(X_train),
        val_rows=len(X_val),
        test_rows=len(X_test),
        total_rows=n_samples,
        stratified=is_stratified,
    )

    return X_train, X_val, X_test, y_train, y_val, y_test, summary, warnings


def get_cross_validation_generator(
    X_train: pd.DataFrame,
    y_train: Optional[pd.Series],
    task_type: MLTaskType,
    config: CrossValidationConfig,
) -> Tuple[Any, int, List[str]]:
    """
    Constructs a cross-validation fold generator respecting dataset size and class counts.
    Returns (cv_generator, effective_n_splits, warnings).
    """
    warnings: List[str] = []
    n_samples = len(X_train)
    max_splits = getattr(settings, "ML_MAX_CV_FOLDS", 10)
    n_splits = min(config.n_splits, max_splits)

    # Adjust folds if n_samples is small
    if n_splits > n_samples:
        n_splits = max(2, n_samples // 2)
        warnings.append(f"Reduced cross-validation folds to {n_splits} due to small training sample size ({n_samples}).")

    if (
        config.stratified
        and y_train is not None
        and task_type in (MLTaskType.BINARY_CLASSIFICATION, MLTaskType.MULTICLASS_CLASSIFICATION)
    ):
        min_class_count = y_train.value_counts().min()
        if min_class_count < n_splits:
            if min_class_count >= 2:
                n_splits = min_class_count
                warnings.append(
                    f"Reduced Stratified CV folds to {n_splits} to match minority class frequency."
                )
                cv = StratifiedKFold(n_splits=n_splits, shuffle=config.shuffle, random_state=config.random_seed)
            else:
                warnings.append(
                    "Minority class has < 2 samples in training set; falling back to regular K-Fold CV."
                )
                cv = KFold(n_splits=min(n_splits, 5), shuffle=config.shuffle, random_state=config.random_seed)
        else:
            cv = StratifiedKFold(n_splits=n_splits, shuffle=config.shuffle, random_state=config.random_seed)
    else:
        cv = KFold(n_splits=n_splits, shuffle=config.shuffle, random_state=config.random_seed)

    return cv, n_splits, warnings
