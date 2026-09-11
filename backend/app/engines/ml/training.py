"""
AnalyzaX — Phase 11: Deterministic Model Training & Bounded Hyperparameter Search.
Orchestrates model fitting, cross-validation, baseline comparison, and evaluation.
"""

import time
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
from sklearn.model_selection import GridSearchCV, RandomizedSearchCV, cross_validate

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.ml.evaluation import (
    evaluate_classification,
    evaluate_clustering,
    evaluate_regression,
)
from backend.app.engines.ml.exceptions import MLErrorCode, MLException
from backend.app.engines.ml.interpretation import extract_feature_importance
from backend.app.engines.ml.models import (
    CrossValidationConfig,
    HyperparameterSearchConfig,
    MLModelRun,
    MLTaskType,
)
from backend.app.engines.ml.registry import model_registry
from backend.app.engines.ml.splitting import get_cross_validation_generator


def train_single_model(
    model_id: str,
    task_type: MLTaskType,
    X_train_trans: np.ndarray,
    y_train: Optional[np.ndarray],
    X_val_trans: np.ndarray,
    y_val: Optional[np.ndarray],
    X_test_trans: np.ndarray,
    y_test: Optional[np.ndarray],
    feature_names: List[str],
    source_mapping: Dict[str, str],
    class_labels: Optional[List[str]],
    raw_parameters: Dict[str, Any],
    search_config: HyperparameterSearchConfig,
    cv_config: CrossValidationConfig,
    random_seed: int,
    primary_metric: str,
) -> Tuple[MLModelRun, Any, float, float]:
    """
    Trains an individual model (or baseline), runs CV, evaluates on validation and test sets,
    and extracts diagnostics and feature importances.
    Returns: (model_run, fitted_estimator, train_score, val_score)
    """
    defn = model_registry.get_model(model_id)
    run_id = f"run_{model_id}_{int(time.time() * 1000) % 1000000}"
    warnings: List[str] = []

    # 1. Instantiate base estimator
    estimator = model_registry.create_estimator(model_id, raw_parameters, random_seed)

    # 2. Hyperparameter Search (if enabled and not a baseline)
    start_time = time.perf_counter()
    best_params = dict(raw_parameters)

    if search_config.enabled and search_config.param_grid and "dummy" not in model_id:
        max_iters = min(search_config.n_iter, getattr(settings, "ML_MAX_SEARCH_ITERATIONS", 20))
        cv_gen, _, _ = get_cross_validation_generator(
            pd.DataFrame(X_train_trans),
            pd.Series(y_train) if y_train is not None else None,
            task_type,
            cv_config,
        )

        try:
            if search_config.search_method == "random":
                search = RandomizedSearchCV(
                    estimator=estimator,
                    param_distributions=search_config.param_grid,
                    n_iter=max_iters,
                    cv=cv_gen,
                    random_state=random_seed,
                    n_jobs=-1,
                )
            else:
                search = GridSearchCV(
                    estimator=estimator,
                    param_grid=search_config.param_grid,
                    cv=cv_gen,
                    n_jobs=-1,
                )
            search.fit(X_train_trans, y_train)
            estimator = search.best_estimator_
            best_params.update(search.best_params_)
        except Exception as e:
            warnings.append(f"Hyperparameter search failed ({e}); used default parameters.")
            estimator.fit(X_train_trans, y_train)
    else:
        # Standard fit
        if task_type == MLTaskType.CLUSTERING:
            estimator.fit(X_train_trans)
        else:
            estimator.fit(X_train_trans, y_train)

    train_duration_ms = int((time.perf_counter() - start_time) * 1000)

    # 3. Cross-Validation scoring on training set
    cv_metrics: Optional[Dict[str, Any]] = None
    if cv_config.enabled and task_type != MLTaskType.CLUSTERING and "dummy" not in model_id:
        try:
            cv_gen, n_splits, cv_warn = get_cross_validation_generator(
                pd.DataFrame(X_train_trans),
                pd.Series(y_train) if y_train is not None else None,
                task_type,
                cv_config,
            )
            warnings.extend(cv_warn)

            # Map primary metric to sklearn scoring string
            scoring_str = None
            if primary_metric == "r2":
                scoring_str = "r2"
            elif primary_metric == "rmse":
                scoring_str = "neg_root_mean_squared_error"
            elif primary_metric == "mae":
                scoring_str = "neg_mean_absolute_error"
            elif primary_metric == "accuracy":
                scoring_str = "accuracy"
            elif primary_metric == "balanced_accuracy":
                scoring_str = "balanced_accuracy"
            elif primary_metric in ("f1_macro", "f1"):
                scoring_str = "f1_macro"
            elif primary_metric == "roc_auc":
                scoring_str = "roc_auc"

            if scoring_str:
                cv_res = cross_validate(
                    estimator,
                    X_train_trans,
                    y_train,
                    cv=cv_gen,
                    scoring=scoring_str,
                    n_jobs=1,
                )
                test_scores = cv_res["test_score"]
                if scoring_str.startswith("neg_"):
                    test_scores = -test_scores
                cv_metrics = {
                    "metric": primary_metric,
                    "folds": int(n_splits),
                    "mean": round(float(np.mean(test_scores)), 4),
                    "std": round(float(np.std(test_scores)), 4),
                    "scores": [round(float(s), 4) for s in test_scores],
                }
        except Exception as e:
            warnings.append(f"Cross-validation skipped or failed: {e}")

    # 4. In-Sample Train Prediction & Validation Prediction
    train_score = 0.0
    val_score = 0.0

    metrics_val: Dict[str, Any] = {}
    metrics_test: Dict[str, Any] = {}
    cm_data = None
    roc_curves = None
    pr_curves = None
    residual_diag = None
    cluster_summaries = None

    if task_type == MLTaskType.REGRESSION:
        # In-sample
        y_train_pred = estimator.predict(X_train_trans)
        train_reg_metrics, _ = evaluate_regression(y_train, y_train_pred, n_features=X_train_trans.shape[1])
        train_score = getattr(train_reg_metrics, primary_metric, train_reg_metrics.r2)

        # Validation set evaluation
        y_val_pred = estimator.predict(X_val_trans)
        val_reg_metrics, residual_diag = evaluate_regression(y_val, y_val_pred, n_features=X_val_trans.shape[1])
        metrics_val = val_reg_metrics.model_dump()
        val_score = getattr(val_reg_metrics, primary_metric, val_reg_metrics.r2)

        # Test set evaluation
        y_test_pred = estimator.predict(X_test_trans)
        test_reg_metrics, _ = evaluate_regression(y_test, y_test_pred, n_features=X_test_trans.shape[1])
        metrics_test = test_reg_metrics.model_dump()

    elif task_type in (MLTaskType.BINARY_CLASSIFICATION, MLTaskType.MULTICLASS_CLASSIFICATION):
        # In-sample
        y_train_pred = estimator.predict(X_train_trans)
        train_clf_metrics, _, _, _ = evaluate_classification(
            y_train, y_train_pred, None, class_labels or [], task_type
        )
        train_score = getattr(train_clf_metrics, primary_metric, train_clf_metrics.accuracy)

        # Validation set evaluation
        y_val_pred = estimator.predict(X_val_trans)
        y_val_proba = None
        if hasattr(estimator, "predict_proba"):
            try:
                y_val_proba = estimator.predict_proba(X_val_trans)
            except Exception:
                pass

        val_clf_metrics, cm_data, roc_curves, pr_curves = evaluate_classification(
            y_val, y_val_pred, y_val_proba, class_labels or [], task_type
        )
        metrics_val = val_clf_metrics.model_dump()
        val_score = getattr(val_clf_metrics, primary_metric, val_clf_metrics.accuracy)

        # Test set evaluation
        y_test_pred = estimator.predict(X_test_trans)
        y_test_proba = None
        if hasattr(estimator, "predict_proba"):
            try:
                y_test_proba = estimator.predict_proba(X_test_trans)
            except Exception:
                pass
        test_clf_metrics, _, _, _ = evaluate_classification(
            y_test, y_test_pred, y_test_proba, class_labels or [], task_type
        )
        metrics_test = test_clf_metrics.model_dump()

    elif task_type == MLTaskType.CLUSTERING:
        labels_train = getattr(estimator, "labels_", estimator.predict(X_train_trans))
        centers = getattr(estimator, "cluster_centers_", None)
        inertia_val = getattr(estimator, "inertia_", None)
        clust_metrics, cluster_summaries = evaluate_clustering(
            X_train_trans, labels_train, centers, feature_names, inertia_val
        )
        metrics_val = clust_metrics.model_dump()
        train_score = clust_metrics.inertia
        val_score = clust_metrics.inertia

    # 5. Extract Feature Importance
    feat_importances = extract_feature_importance(estimator, feature_names, source_mapping)

    model_run = MLModelRun(
        model_run_id=run_id,
        model_id=model_id,
        model_name=defn.display_name,
        task_type=task_type,
        parameters=best_params,
        status="COMPLETED",
        duration_ms=train_duration_ms,
        sample_counts={
            "train": len(X_train_trans),
            "val": len(X_val_trans),
            "test": len(X_test_trans),
        },
        metrics=metrics_val,
        cv_metrics=cv_metrics,
        test_metrics=metrics_test,
        feature_importance=feat_importances,
        confusion_matrix=cm_data,
        residual_diagnostics=residual_diag,
        roc_curves=roc_curves,
        pr_curves=pr_curves,
        cluster_summaries=cluster_summaries,
        warnings=warnings,
    )

    return model_run, estimator, float(train_score), float(val_score)
