"""
AnalyzaX — Phase 11: Feature Importance & Interpretation Engine.
Extracts linear coefficients and tree feature importances, maps transformed columns
back to source features, and generates structured ML findings with explicit non-causality notices.
"""

from typing import Any, Dict, List, Optional
import numpy as np
import uuid

from backend.app.engines.ml.models import (
    FeatureImportanceItem,
    MLFinding,
    MLModelRun,
    MLTaskType,
)


def extract_feature_importance(
    estimator: Any,
    feature_names: List[str],
    source_mapping: Dict[str, str],
) -> List[FeatureImportanceItem]:
    """
    Extracts feature importances (for tree ensembles) or absolute coefficients (for linear models).
    Maps transformed names back to original dataset columns.
    """
    items: List[FeatureImportanceItem] = []

    # 1. Tree-based models (feature_importances_)
    if hasattr(estimator, "feature_importances_"):
        raw_importances = estimator.feature_importances_
        for feat_name, imp in zip(feature_names, raw_importances):
            src_col = source_mapping.get(feat_name, feat_name)
            items.append(
                FeatureImportanceItem(
                    feature=feat_name,
                    source_column=src_col,
                    importance=round(float(imp), 4),
                    coefficient=None,
                )
            )

    # 2. Linear models (coef_)
    elif hasattr(estimator, "coef_"):
        raw_coefs = estimator.coef_
        # If 2D (e.g. multiclass or multiple outputs), average the absolute values
        if raw_coefs.ndim == 2:
            avg_abs_coef = np.mean(np.abs(raw_coefs), axis=0)
            rep_coef = raw_coefs[0]
        else:
            avg_abs_coef = np.abs(raw_coefs)
            rep_coef = raw_coefs

        # Normalize to sum to 1.0 for comparability if sum > 0
        coef_sum = np.sum(avg_abs_coef)
        norm_imp = (avg_abs_coef / coef_sum) if coef_sum > 0 else avg_abs_coef

        for feat_name, imp, coef in zip(feature_names, norm_imp, rep_coef):
            src_col = source_mapping.get(feat_name, feat_name)
            items.append(
                FeatureImportanceItem(
                    feature=feat_name,
                    source_column=src_col,
                    importance=round(float(imp), 4),
                    coefficient=round(float(coef), 4),
                )
            )

    # Sort descending by importance
    return sorted(items, key=lambda x: x.importance, reverse=True)


def generate_ml_findings(
    experiment_id: str,
    task_type: MLTaskType,
    model_runs: List[MLModelRun],
    primary_metric: str,
    train_scores: Dict[str, float],
    val_scores: Dict[str, float],
    imbalance_ratio: Optional[float] = None,
) -> List[MLFinding]:
    """
    Generates structured analytical findings regarding model performance,
    overfitting/underfitting gaps, class imbalance, and top predictors.
    """
    findings: List[MLFinding] = []

    # 1. Best Model & Performance finding
    successful_runs = [r for r in model_runs if r.status == "COMPLETED" and "dummy" not in r.model_id]
    baseline_runs = [r for r in model_runs if "dummy" in r.model_id]

    if successful_runs:
        # Pick best run
        is_higher_better = primary_metric in ("r2", "accuracy", "balanced_accuracy", "f1_macro", "f1_weighted", "roc_auc", "pr_auc", "silhouette_score")
        sorted_runs = sorted(
            successful_runs,
            key=lambda r: (
                r.metrics.get(primary_metric, -float("inf") if is_higher_better else float("inf"))
                if is_higher_better
                else -r.metrics.get(primary_metric, float("inf"))
            ),
            reverse=True,
        )
        best_run = sorted_runs[0]
        best_val = best_run.metrics.get(primary_metric)

        evidence_str = f"Best model is {best_run.model_name} with validation {primary_metric} = {best_val}."
        if baseline_runs:
            base_run = baseline_runs[0]
            base_val = base_run.metrics.get(primary_metric)
            if base_val is not None and best_val is not None:
                diff = round(best_val - base_val, 4)
                evidence_str += f" Baseline ({base_run.model_name}) achieved {base_val} (delta: {diff:+0.4f})."

        findings.append(
            MLFinding(
                finding_id=f"find_{uuid.uuid4().hex[:8]}",
                experiment_id=experiment_id,
                category="PERFORMANCE",
                severity="INFO",
                title=f"Top Performing Model: {best_run.model_name}",
                description=f"Model evaluation ranked {len(successful_runs)} candidate model(s) using primary metric '{primary_metric}'.",
                evidence=evidence_str,
                metrics={primary_metric: best_val},
                related_model=best_run.model_name,
                methodology="Validation holdout set scoring",
                limitations=["Metrics reflect holdout data sample distribution."],
            )
        )

        # 2. Overfitting / Generalization Gap Check
        for run in successful_runs:
            t_score = train_scores.get(run.model_run_id)
            v_score = val_scores.get(run.model_run_id)
            if t_score is not None and v_score is not None and is_higher_better:
                gap = t_score - v_score
                if gap > 0.20:
                    findings.append(
                        MLFinding(
                            finding_id=f"find_{uuid.uuid4().hex[:8]}",
                            experiment_id=experiment_id,
                            category="OVERFITTING",
                            severity="HIGH",
                            title=f"Potential Overfitting Detected in {run.model_name}",
                            description=(
                                f"Training score ({t_score:.3f}) differs substantially from validation score ({v_score:.3f}). "
                                f"A gap of {gap:.3f} indicates the model may be fitting idiosyncrasies in the training sample."
                            ),
                            evidence=f"Train {primary_metric}: {t_score:.3f}, Val {primary_metric}: {v_score:.3f}, Gap: {gap:.3f}",
                            metrics={"train_score": t_score, "val_score": v_score, "gap": gap},
                            related_model=run.model_name,
                            methodology="Comparison of in-sample training performance against validation holdout",
                            limitations=["Overfitting threshold is a heuristic (gap > 0.20) rather than a strict statistical proof."],
                        )
                    )
                elif gap < -0.15:
                    findings.append(
                        MLFinding(
                            finding_id=f"find_{uuid.uuid4().hex[:8]}",
                            experiment_id=experiment_id,
                            category="UNDERFITTING",
                            severity="MEDIUM",
                            title=f"Potential Underfitting in {run.model_name}",
                            description="Validation performance matches or exceeds training performance while both scores remain low.",
                            evidence=f"Train {primary_metric}: {t_score:.3f}, Val {primary_metric}: {v_score:.3f}",
                            related_model=run.model_name,
                            methodology="Holdout vs training performance evaluation",
                            limitations=["Can occur when model regularization is too high or feature signal is weak."],
                        )
                    )

        # 3. Top Predictors Finding
        if best_run.feature_importance:
            top_feats = best_run.feature_importance[:3]
            feat_names = [f.source_column for f in top_feats]
            findings.append(
                MLFinding(
                    finding_id=f"find_{uuid.uuid4().hex[:8]}",
                    experiment_id=experiment_id,
                    category="FEATURE_IMPORTANCE",
                    severity="INFO",
                    title="Key Predictive Features Identified",
                    description=(
                        f"The most influential predictor columns for {best_run.model_name} are: {', '.join(feat_names)}. "
                        "Note: Feature importance indicates predictive association within the model architecture, NOT causal relationships."
                    ),
                    evidence=", ".join([f"{f.source_column} ({f.importance * 100:.1f}%)" for f in top_feats]),
                    related_columns=feat_names,
                    related_model=best_run.model_name,
                    methodology="Tree impurity reduction or absolute linear coefficient magnitude",
                    limitations=[
                        "Feature importance does NOT prove causal impact.",
                        "Correlated features can split or mask individual importance scores.",
                    ],
                )
            )

    # 4. Class Imbalance Finding
    if imbalance_ratio is not None and imbalance_ratio < 0.20:
        findings.append(
            MLFinding(
                finding_id=f"find_{uuid.uuid4().hex[:8]}",
                experiment_id=experiment_id,
                category="IMBALANCE",
                severity="MEDIUM",
                title="Class Imbalance Influence",
                description=(
                    f"Minority class ratio is {imbalance_ratio * 100:.1f}%. "
                    "Models evaluated primarily on standard accuracy may appear artificially competent by predicting the majority class."
                ),
                evidence=f"Imbalance ratio: {imbalance_ratio:.3f}",
                methodology="Relative class frequency analysis",
                limitations=["Rely on Balanced Accuracy and F1-macro for reliable decision-making."],
            )
        )

    return findings
