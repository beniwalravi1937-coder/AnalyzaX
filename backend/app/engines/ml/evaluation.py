"""
AnalyzaX — Phase 11: Task-Aware ML Evaluation Engine.
Computes deterministic regression, classification, and clustering metrics,
confusion matrices, ROC/PR curves, and regression residual diagnostics.
"""

from typing import Any, Dict, List, Optional, Tuple, Union
import numpy as np
import pandas as pd
from scipy import stats
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    log_loss,
    mean_absolute_error,
    mean_squared_error,
    median_absolute_error,
    precision_recall_curve,
    precision_score,
    r2_score,
    recall_score,
    roc_auc_score,
    roc_curve,
    silhouette_score,
    calinski_harabasz_score,
    davies_bouldin_score,
)

from backend.app.engines.ml.models import (
    ClassificationMetrics,
    ClusteringMetrics,
    ClusterSummaryItem,
    ConfusionMatrixData,
    CurveData,
    MLTaskType,
    RegressionMetrics,
    ResidualDiagnostics,
)


def _safe_float(val: Any, default: float = 0.0) -> float:
    try:
        f = float(val)
        return f if np.isfinite(f) else default
    except Exception:
        return default


def evaluate_regression(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    n_features: int = 1,
) -> Tuple[RegressionMetrics, ResidualDiagnostics]:
    """Computes full regression metrics and diagnostic residuals."""
    n_samples = len(y_true)
    mae = _safe_float(mean_absolute_error(y_true, y_pred))
    mse = _safe_float(mean_squared_error(y_true, y_pred))
    rmse = _safe_float(np.sqrt(mse))
    r2 = _safe_float(r2_score(y_true, y_pred))
    med_ae = _safe_float(median_absolute_error(y_true, y_pred))

    # Adjusted R2
    adj_r2 = None
    if n_samples > n_features + 1:
        calc_adj = 1.0 - (1.0 - r2) * (n_samples - 1) / (n_samples - n_features - 1)
        if np.isfinite(calc_adj):
            adj_r2 = float(calc_adj)

    # MAPE with zero protection
    mape = None
    non_zero_mask = np.abs(y_true) > 1e-6
    if np.sum(non_zero_mask) > 0:
        mape_val = np.mean(np.abs((y_true[non_zero_mask] - y_pred[non_zero_mask]) / y_true[non_zero_mask])) * 100.0
        if np.isfinite(mape_val):
            mape = float(mape_val)

    reg_metrics = RegressionMetrics(
        mae=round(mae, 4),
        mse=round(mse, 4),
        rmse=round(rmse, 4),
        r2=round(r2, 4),
        adjusted_r2=round(adj_r2, 4) if adj_r2 is not None else None,
        mape=round(mape, 2) if mape is not None else None,
        median_absolute_error=round(med_ae, 4),
    )

    # Residuals
    residuals_arr = y_true - y_pred
    mean_res = _safe_float(np.mean(residuals_arr))
    std_res = _safe_float(np.std(residuals_arr))
    skew_res = _safe_float(stats.skew(residuals_arr)) if len(residuals_arr) > 2 else 0.0

    # Sample actual vs predicted for preview (capped at 100 points)
    sample_size = min(100, n_samples)
    indices = np.linspace(0, n_samples - 1, sample_size, dtype=int)
    act_vs_pred = [
        {"actual": round(_safe_float(y_true[i]), 4), "predicted": round(_safe_float(y_pred[i]), 4), "residual": round(_safe_float(residuals_arr[i]), 4)}
        for i in indices
    ]

    # Top 5 largest absolute errors
    abs_errs = np.abs(residuals_arr)
    top_indices = np.argsort(abs_errs)[::-1][: min(5, n_samples)]
    largest_errors = [
        {
            "row_index": int(i),
            "actual": round(float(y_true[i]), 4),
            "predicted": round(float(y_pred[i]), 4),
            "error": round(float(abs_errs[i]), 4),
        }
        for i in top_indices
    ]

    diagnostics = ResidualDiagnostics(
        actual_vs_predicted=act_vs_pred,
        residuals=[round(float(r), 4) for r in residuals_arr[:100]],
        mean_residual=round(mean_res, 4),
        std_residual=round(std_res, 4),
        residual_skew=round(skew_res, 4),
        largest_errors=largest_errors,
    )

    return reg_metrics, diagnostics


def evaluate_classification(
    y_true: np.ndarray,
    y_pred: np.ndarray,
    y_proba: Optional[np.ndarray],
    class_labels: List[str],
    task_type: MLTaskType,
) -> Tuple[
    ClassificationMetrics,
    ConfusionMatrixData,
    Optional[List[CurveData]],
    Optional[List[CurveData]],
]:
    """Computes comprehensive classification metrics, confusion matrix, and ROC/PR curves."""
    acc = float(accuracy_score(y_true, y_pred))
    bal_acc = float(balanced_accuracy_score(y_true, y_pred))

    prec_macro = float(precision_score(y_true, y_pred, average="macro", zero_division=0))
    rec_macro = float(recall_score(y_true, y_pred, average="macro", zero_division=0))
    f1_macro = float(f1_score(y_true, y_pred, average="macro", zero_division=0))

    prec_wt = float(precision_score(y_true, y_pred, average="weighted", zero_division=0))
    rec_wt = float(recall_score(y_true, y_pred, average="weighted", zero_division=0))
    f1_wt = float(f1_score(y_true, y_pred, average="weighted", zero_division=0))

    # ROC AUC and PR AUC
    roc_auc = None
    pr_auc = None
    logloss_val = None

    if y_proba is not None:
        try:
            if task_type == MLTaskType.BINARY_CLASSIFICATION:
                # Expecting 1D probability of positive class or 2D array
                p = y_proba[:, 1] if y_proba.ndim == 2 and y_proba.shape[1] == 2 else y_proba
                roc_auc = float(roc_auc_score(y_true, p))
                pr_auc = float(average_precision_score(y_true, p))
                logloss_val = float(log_loss(y_true, y_proba))
            elif task_type == MLTaskType.MULTICLASS_CLASSIFICATION and len(class_labels) > 2:
                roc_auc = float(roc_auc_score(y_true, y_proba, multi_class="ovr", average="macro"))
                logloss_val = float(log_loss(y_true, y_proba))
        except Exception:
            pass

    clf_metrics = ClassificationMetrics(
        accuracy=round(acc, 4),
        balanced_accuracy=round(bal_acc, 4),
        precision_macro=round(prec_macro, 4),
        recall_macro=round(rec_macro, 4),
        f1_macro=round(f1_macro, 4),
        precision_weighted=round(prec_wt, 4),
        recall_weighted=round(rec_wt, 4),
        f1_weighted=round(f1_wt, 4),
        roc_auc=round(roc_auc, 4) if roc_auc is not None else None,
        pr_auc=round(pr_auc, 4) if pr_auc is not None else None,
        log_loss=round(logloss_val, 4) if logloss_val is not None else None,
    )

    # Confusion matrix
    cm = confusion_matrix(y_true, y_pred, labels=class_labels)
    cm_norm = confusion_matrix(y_true, y_pred, labels=class_labels, normalize="true")

    per_class_report = classification_report(
        y_true,
        y_pred,
        labels=class_labels,
        target_names=class_labels,
        output_dict=True,
        zero_division=0,
    )
    per_class_metrics = {}
    for lbl in class_labels:
        if lbl in per_class_report:
            per_class_metrics[lbl] = {
                "precision": round(per_class_report[lbl]["precision"], 4),
                "recall": round(per_class_report[lbl]["recall"], 4),
                "f1": round(per_class_report[lbl]["f1-score"], 4),
                "support": int(per_class_report[lbl]["support"]),
            }

    cm_data = ConfusionMatrixData(
        labels=class_labels,
        matrix=cm.tolist(),
        normalized_matrix=[[round(float(val), 4) for val in row] for row in cm_norm.tolist()],
        per_class_metrics=per_class_metrics,
    )

    # ROC & PR Curves
    roc_curves: Optional[List[CurveData]] = None
    pr_curves: Optional[List[CurveData]] = None

    if y_proba is not None:
        try:
            if task_type == MLTaskType.BINARY_CLASSIFICATION:
                p = y_proba[:, 1] if y_proba.ndim == 2 and y_proba.shape[1] == 2 else y_proba
                fpr, tpr, thresh = roc_curve(y_true, p, pos_label=class_labels[-1])
                # Sample 50 points
                sample_pts = min(50, len(fpr))
                step = max(1, len(fpr) // sample_pts)
                roc_points = [
                    {
                        "fpr": round(_safe_float(fpr[i]), 4),
                        "tpr": round(_safe_float(tpr[i]), 4),
                        "threshold": round(_safe_float(thresh[i], 1.0), 4),
                    }
                    for i in range(0, len(fpr), step)
                ]
                roc_curves = [CurveData(class_label=class_labels[-1], auc=_safe_float(roc_auc) if roc_auc is not None else None, points=roc_points)]

                prec_vals, rec_vals, pr_thresh = precision_recall_curve(y_true, p, pos_label=class_labels[-1])
                sample_pr = min(50, len(prec_vals))
                step_pr = max(1, len(prec_vals) // sample_pr)
                pr_points = [
                    {"precision": round(_safe_float(prec_vals[i]), 4), "recall": round(_safe_float(rec_vals[i]), 4)}
                    for i in range(0, len(prec_vals), step_pr)
                ]
                pr_curves = [CurveData(class_label=class_labels[-1], auc=_safe_float(pr_auc) if pr_auc is not None else None, points=pr_points)]
        except Exception:
            pass

    return clf_metrics, cm_data, roc_curves, pr_curves


def evaluate_clustering(
    X_transformed: np.ndarray,
    labels: np.ndarray,
    cluster_centers: Optional[np.ndarray] = None,
    feature_names: Optional[List[str]] = None,
    inertia: Optional[float] = None,
) -> Tuple[ClusteringMetrics, List[ClusterSummaryItem]]:
    """Computes clustering metrics (inertia, silhouette, etc.) and cluster summaries."""
    n_samples = len(X_transformed)
    n_clusters = len(np.unique(labels))

    sil_score = None
    ch_score = None
    db_score = None

    if 1 < n_clusters < n_samples:
        try:
            # Silhouette score capped at 5000 samples for performance
            sil_sample = min(2000, n_samples)
            sil_score = float(silhouette_score(X_transformed, labels, sample_size=sil_sample))
            ch_score = float(calinski_harabasz_score(X_transformed, labels))
            db_score = float(davies_bouldin_score(X_transformed, labels))
        except Exception:
            pass

    metrics = ClusteringMetrics(
        inertia=round(float(inertia), 4) if inertia is not None else 0.0,
        silhouette_score=round(sil_score, 4) if sil_score is not None else None,
        calinski_harabasz_score=round(ch_score, 4) if ch_score is not None else None,
        davies_bouldin_score=round(db_score, 4) if db_score is not None else None,
    )

    summaries: List[ClusterSummaryItem] = []
    unique_labels, counts = np.unique(labels, return_counts=True)
    for c_id, cnt in zip(unique_labels, counts):
        pct = round((cnt / n_samples) * 100.0, 2)
        center_dict: Dict[str, float] = {}
        if cluster_centers is not None and c_id < len(cluster_centers):
            centers = cluster_centers[c_id]
            feats = feature_names or [f"dim_{i}" for i in range(len(centers))]
            for i in range(min(10, len(centers))):
                center_dict[feats[i]] = round(float(centers[i]), 4)

        summaries.append(
            ClusterSummaryItem(
                cluster_id=int(c_id),
                size=int(cnt),
                percentage=pct,
                center=center_dict,
            )
        )

    return metrics, summaries
