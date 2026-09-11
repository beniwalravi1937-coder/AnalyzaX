"""
AnalyzaX — Phase 11: Machine Learning Visualization Integration.
Translates deterministic ML evaluation results and diagnostics into standard Phase 9 ChartSpecs.
Reuses the central ChartRenderer without introducing duplicate visualization frameworks.
"""

from typing import Any, Dict, List, Optional
import uuid
import pandas as pd

from backend.app.engines.visualization.models import (
    ChartAxesConfig,
    ChartEncoding,
    ChartLegendConfig,
    ChartSamplingMetadata,
    ChartSpec,
    ChartType,
    VisualizationProvenance,
)
from backend.app.engines.ml.models import (
    ConfusionMatrixData,
    CurveData,
    FeatureImportanceItem,
    MLTaskType,
    ResidualDiagnostics,
)


def build_feature_importance_chart_spec(
    items: List[FeatureImportanceItem],
    dataset_id: str,
    dataset_version_id: str,
    model_name: str,
) -> Optional[Dict[str, Any]]:
    """Builds a horizontal bar chart of top predictive features."""
    if not items:
        return None

    # Top 15 features
    top_items = items[:15]
    data = [
        {
            "feature": item.source_column if item.source_column == item.feature else f"{item.source_column} ({item.feature})",
            "importance": round(item.importance * 100.0, 2),
            "coefficient": item.coefficient,
        }
        for item in reversed(top_items)  # reversed for clean ascending bar display
    ]

    spec = ChartSpec(
        chart_id=f"ml_feat_imp_{uuid.uuid4().hex[:8]}",
        chart_type=ChartType.BAR,
        title=f"Feature Importance: {model_name}",
        subtitle="Relative predictive influence (normalized to 100%). Note: Does not imply causal effect.",
        dataset_id=dataset_id,
        dataset_version_id=dataset_version_id,
        source_type="ml",
        x="feature",
        y="importance",
        data=data,
        axes=ChartAxesConfig(x_label="Feature", y_label="Importance (%)", x_rotate=30),
        legend=ChartLegendConfig(show=False),
        sampling=ChartSamplingMetadata(original_row_count=len(items), displayed_points=len(data)),
        provenance=VisualizationProvenance(
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            source_type="ml",
            source_reference=model_name,
            created_at=str(pd.Timestamp.now(tz="UTC")),
        ),
    )
    return spec.model_dump()


def build_actual_vs_predicted_chart_spec(
    diagnostics: ResidualDiagnostics,
    dataset_id: str,
    dataset_version_id: str,
    model_name: str,
) -> Optional[Dict[str, Any]]:
    """Builds a scatter plot of actual vs predicted target values."""
    if not diagnostics.actual_vs_predicted:
        return None

    data = diagnostics.actual_vs_predicted

    spec = ChartSpec(
        chart_id=f"ml_act_pred_{uuid.uuid4().hex[:8]}",
        chart_type=ChartType.SCATTER,
        title=f"Actual vs. Predicted: {model_name}",
        subtitle="Validation holdout observations plotted against model predictions",
        dataset_id=dataset_id,
        dataset_version_id=dataset_version_id,
        source_type="ml",
        x="actual",
        y="predicted",
        data=data,
        axes=ChartAxesConfig(x_label="Actual Target", y_label="Predicted Target"),
        legend=ChartLegendConfig(show=False),
        sampling=ChartSamplingMetadata(original_row_count=len(data), displayed_points=len(data)),
        provenance=VisualizationProvenance(
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            source_type="ml",
            source_reference=model_name,
            created_at=str(pd.Timestamp.now(tz="UTC")),
        ),
    )
    return spec.model_dump()


def build_residual_distribution_chart_spec(
    diagnostics: ResidualDiagnostics,
    dataset_id: str,
    dataset_version_id: str,
    model_name: str,
) -> Optional[Dict[str, Any]]:
    """Builds a bar chart showing the distribution of residuals."""
    if not diagnostics.residuals:
        return None

    residuals = diagnostics.residuals
    # Bin into 10 buckets
    import numpy as np
    counts, bin_edges = np.histogram(residuals, bins=10)
    data = [
        {
            "bin": f"[{round(bin_edges[i], 2)}, {round(bin_edges[i+1], 2)})",
            "count": int(counts[i]),
        }
        for i in range(len(counts))
    ]

    spec = ChartSpec(
        chart_id=f"ml_resid_{uuid.uuid4().hex[:8]}",
        chart_type=ChartType.BAR,
        title=f"Residual Distribution: {model_name}",
        subtitle=f"Prediction error spread (mean: {diagnostics.mean_residual:.3f}, std: {diagnostics.std_residual:.3f})",
        dataset_id=dataset_id,
        dataset_version_id=dataset_version_id,
        source_type="ml",
        x="bin",
        y="count",
        data=data,
        axes=ChartAxesConfig(x_label="Error Range (Actual - Pred)", y_label="Observation Count", x_rotate=30),
        legend=ChartLegendConfig(show=False),
        sampling=ChartSamplingMetadata(original_row_count=len(residuals), displayed_points=len(data)),
        provenance=VisualizationProvenance(
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            source_type="ml",
            source_reference=model_name,
            created_at=str(pd.Timestamp.now(tz="UTC")),
        ),
    )
    return spec.model_dump()


def build_confusion_matrix_chart_spec(
    cm_data: ConfusionMatrixData,
    dataset_id: str,
    dataset_version_id: str,
    model_name: str,
) -> Optional[Dict[str, Any]]:
    """Builds a heatmap representation of the classification confusion matrix."""
    if not cm_data or not cm_data.matrix:
        return None

    data = []
    labels = cm_data.labels
    for i, actual_lbl in enumerate(labels):
        for j, pred_lbl in enumerate(labels):
            data.append(
                {
                    "actual": actual_lbl,
                    "predicted": pred_lbl,
                    "count": cm_data.matrix[i][j],
                    "rate": cm_data.normalized_matrix[i][j],
                }
            )

    spec = ChartSpec(
        chart_id=f"ml_cm_{uuid.uuid4().hex[:8]}",
        chart_type=ChartType.HEATMAP,
        title=f"Confusion Matrix: {model_name}",
        subtitle="True vs. predicted classifications across holdout observations",
        dataset_id=dataset_id,
        dataset_version_id=dataset_version_id,
        source_type="ml",
        x="predicted",
        y="actual",
        color="rate",
        data=data,
        axes=ChartAxesConfig(x_label="Predicted Class", y_label="Actual Class"),
        legend=ChartLegendConfig(show=True),
        sampling=ChartSamplingMetadata(original_row_count=len(data), displayed_points=len(data)),
        provenance=VisualizationProvenance(
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            source_type="ml",
            source_reference=model_name,
            created_at=str(pd.Timestamp.now(tz="UTC")),
        ),
    )
    return spec.model_dump()


def build_roc_curve_chart_spec(
    curves: List[CurveData],
    dataset_id: str,
    dataset_version_id: str,
    model_name: str,
) -> Optional[Dict[str, Any]]:
    """Builds a ROC curve plot."""
    if not curves or not curves[0].points:
        return None

    curve = curves[0]
    data = [
        {
            "fpr": pt.get("fpr", 0.0),
            "tpr": pt.get("tpr", 0.0),
            "threshold": pt.get("threshold", 0.0),
        }
        for pt in curve.points
    ]

    auc_str = f" (AUC = {curve.auc:.3f})" if curve.auc is not None else ""
    spec = ChartSpec(
        chart_id=f"ml_roc_{uuid.uuid4().hex[:8]}",
        chart_type=ChartType.LINE,
        title=f"ROC Curve: {model_name}{auc_str}",
        subtitle=f"False Positive Rate vs True Positive Rate for class '{curve.class_label}'",
        dataset_id=dataset_id,
        dataset_version_id=dataset_version_id,
        source_type="ml",
        x="fpr",
        y="tpr",
        data=data,
        axes=ChartAxesConfig(x_label="False Positive Rate (1 - Specificity)", y_label="True Positive Rate (Sensitivity)"),
        legend=ChartLegendConfig(show=False),
        sampling=ChartSamplingMetadata(original_row_count=len(data), displayed_points=len(data)),
        provenance=VisualizationProvenance(
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            source_type="ml",
            source_reference=model_name,
            created_at=str(pd.Timestamp.now(tz="UTC")),
        ),
    )
    return spec.model_dump()


def build_pr_curve_chart_spec(
    curves: List[CurveData],
    dataset_id: str,
    dataset_version_id: str,
    model_name: str,
) -> Optional[Dict[str, Any]]:
    """Builds a Precision-Recall curve plot."""
    if not curves or not curves[0].points:
        return None

    curve = curves[0]
    data = [
        {
            "recall": pt.get("recall", 0.0),
            "precision": pt.get("precision", 0.0),
        }
        for pt in curve.points
    ]

    auc_str = f" (PR-AUC = {curve.auc:.3f})" if curve.auc is not None else ""
    spec = ChartSpec(
        chart_id=f"ml_pr_{uuid.uuid4().hex[:8]}",
        chart_type=ChartType.LINE,
        title=f"Precision-Recall Curve: {model_name}{auc_str}",
        subtitle=f"Precision vs Recall trade-off for class '{curve.class_label}'",
        dataset_id=dataset_id,
        dataset_version_id=dataset_version_id,
        source_type="ml",
        x="recall",
        y="precision",
        data=data,
        axes=ChartAxesConfig(x_label="Recall", y_label="Precision"),
        legend=ChartLegendConfig(show=False),
        sampling=ChartSamplingMetadata(original_row_count=len(data), displayed_points=len(data)),
        provenance=VisualizationProvenance(
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            source_type="ml",
            source_reference=model_name,
            created_at=str(pd.Timestamp.now(tz="UTC")),
        ),
    )
    return spec.model_dump()
