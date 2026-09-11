"""
AnalyzaX — Phase 11: Central Machine Learning Domain Engine Facade.
Coordinates data validation, leakage-free preprocessing, splitting, model training,
evaluation, interpretation, artifact persistence, and visualization generation.
"""

import hashlib
import time
import uuid
from typing import Any, Dict, List, Optional, Tuple
import numpy as np
import pandas as pd
import polars as pl

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.ml.artifacts import save_model_artifact
from backend.app.engines.ml.exceptions import MLErrorCode, MLException
from backend.app.engines.ml.inference import execute_model_predictions
from backend.app.engines.ml.interpretation import generate_ml_findings
from backend.app.engines.ml.models import (
    MLExperimentRequest,
    MLJobStatus,
    MLModelRun,
    MLResult,
    MLTaskType,
    PredictionResult,
    SuitabilityReport,
)
from backend.app.engines.ml.preprocessing import (
    build_preprocessing_pipeline,
    get_feature_names_and_mapping,
)
from backend.app.engines.ml.registry import model_registry
from backend.app.engines.ml.splitting import perform_train_val_test_split
from backend.app.engines.ml.suitability import analyze_suitability
from backend.app.engines.ml.training import train_single_model
from backend.app.engines.ml.visualization.chart_specs import (
    build_actual_vs_predicted_chart_spec,
    build_confusion_matrix_chart_spec,
    build_feature_importance_chart_spec,
    build_pr_curve_chart_spec,
    build_residual_distribution_chart_spec,
    build_roc_curve_chart_spec,
)


class MLEngine:
    """Pure domain engine executing deterministic ML workflows without HTTP/API dependencies."""

    def analyze_suitability(
        self,
        df: pl.DataFrame,
        target_column: Optional[str] = None,
        task_type: Optional[MLTaskType] = None,
        candidate_features: Optional[List[str]] = None,
    ) -> SuitabilityReport:
        return analyze_suitability(df, target_column, task_type, candidate_features)

    def execute_experiment(
        self,
        df: pl.DataFrame,
        request: MLExperimentRequest,
        experiment_id: Optional[str] = None,
    ) -> MLResult:
        """
        Executes an end-to-end ML experiment:
        Validation -> Leakage-Free Preprocessing -> Splitting -> Training -> Evaluation -> Persistence -> ChartSpecs.
        """
        exp_id = experiment_id or f"exp_{uuid.uuid4().hex[:12]}"
        start_time = time.perf_counter()

        # 1. Resource Limit Guard
        max_rows = getattr(settings, "ML_MAX_ROWS", 100_000)
        max_feats = getattr(settings, "ML_MAX_FEATURES", 100)
        if df.height > max_rows:
            raise MLException(
                f"Dataset row count ({df.height}) exceeds maximum permitted for ML ({max_rows}).",
                MLErrorCode.ML_RESOURCE_LIMIT_EXCEEDED,
            )
        if len(request.feature_columns) > max_feats:
            raise MLException(
                f"Feature count ({len(request.feature_columns)}) exceeds maximum permitted ({max_feats}).",
                MLErrorCode.ML_RESOURCE_LIMIT_EXCEEDED,
            )

        # 2. Target and Feature Validation
        if request.task_type != MLTaskType.CLUSTERING and not request.target_column:
            raise MLException(
                "Supervised ML task requires an explicit target column.",
                MLErrorCode.ML_INVALID_TARGET,
            )

        if request.target_column and request.target_column in request.feature_columns:
            raise MLException(
                f"Target column '{request.target_column}' cannot be included in predictor features (leakage prevention).",
                MLErrorCode.ML_LEAKAGE_WARNING,
            )

        # Convert to pandas for scikit-learn compatibility
        df_pd = df.to_pandas()

        # Drop rows where target is null for supervised tasks
        if request.target_column:
            orig_len = len(df_pd)
            df_pd = df_pd.dropna(subset=[request.target_column]).reset_index(drop=True)
            if len(df_pd) < 6:
                raise MLException(
                    f"Too few valid observations ({len(df_pd)} remain after dropping target nulls from {orig_len}).",
                    MLErrorCode.ML_INSUFFICIENT_DATA,
                )

        X = df_pd[request.feature_columns]
        y: Optional[pd.Series] = df_pd[request.target_column] if request.target_column else None

        # Class labels for classification
        class_labels: Optional[List[str]] = None
        if y is not None and request.task_type in (MLTaskType.BINARY_CLASSIFICATION, MLTaskType.MULTICLASS_CLASSIFICATION):
            class_labels = [str(c) for c in sorted(y.unique())]

        # 3. Deterministic Splitting
        (
            X_train,
            X_val,
            X_test,
            y_train_s,
            y_val_s,
            y_test_s,
            split_summary,
            split_warnings,
        ) = perform_train_val_test_split(X, y, request.task_type, request.split)

        # 4. Leakage-Free Preprocessing Pipeline: FIT STRICTLY ON X_TRAIN ONLY
        preprocessor, steps_meta, num_cols, cat_cols = build_preprocessing_pipeline(
            X_train, request.feature_columns, request.preprocessing
        )

        try:
            X_train_trans = preprocessor.fit_transform(X_train)
            X_val_trans = preprocessor.transform(X_val)
            X_test_trans = preprocessor.transform(X_test)
        except Exception as e:
            raise MLException(
                f"Preprocessing transformation failed: {e}",
                MLErrorCode.ML_PREPROCESSING_ERROR,
            )

        feature_names, source_mapping = get_feature_names_and_mapping(
            preprocessor, num_cols, cat_cols
        )

        y_train = y_train_s.to_numpy() if y_train_s is not None else None
        y_val = y_val_s.to_numpy() if y_val_s is not None else None
        y_test = y_test_s.to_numpy() if y_test_s is not None else None

        # 5. Default Primary Metric Determination
        primary_metric = request.primary_metric
        if not primary_metric:
            if request.task_type == MLTaskType.REGRESSION:
                primary_metric = "rmse"
            elif request.task_type in (MLTaskType.BINARY_CLASSIFICATION, MLTaskType.MULTICLASS_CLASSIFICATION):
                primary_metric = "f1_macro"
            elif request.task_type == MLTaskType.CLUSTERING:
                primary_metric = "inertia"
            else:
                primary_metric = "accuracy"

        # 6. Model Selection Setup (add baseline automatically)
        candidate_models = list(request.models)
        if request.task_type == MLTaskType.REGRESSION:
            if "dummy_regressor" not in candidate_models:
                candidate_models.insert(0, "dummy_regressor")
            if not any(m for m in candidate_models if m != "dummy_regressor"):
                candidate_models.append("ridge")
        elif request.task_type in (MLTaskType.BINARY_CLASSIFICATION, MLTaskType.MULTICLASS_CLASSIFICATION):
            if "dummy_classifier" not in candidate_models:
                candidate_models.insert(0, "dummy_classifier")
            if not any(m for m in candidate_models if m != "dummy_classifier"):
                candidate_models.append("logistic_regression")
        elif request.task_type == MLTaskType.CLUSTERING:
            if not candidate_models:
                candidate_models = ["kmeans"]

        # Enforce max models per experiment
        max_models = getattr(settings, "ML_MAX_MODELS_PER_EXPERIMENT", 8)
        candidate_models = candidate_models[:max_models]

        model_runs: List[MLModelRun] = []
        fitted_estimators: Dict[str, Any] = {}
        train_scores: Dict[str, float] = {}
        val_scores: Dict[str, float] = {}
        experiment_warnings: List[str] = list(split_warnings)

        schema_hash = hashlib.sha256(
            "".join(f"{c}:{t}" for c, t in zip(df.columns, [str(d) for d in df.dtypes])).encode()
        ).hexdigest()[:16]

        feature_schema = {c: str(X[c].dtype) for c in request.feature_columns}
        target_schema = {request.target_column: str(y.dtype)} if request.target_column and y is not None else None

        # 7. Model Training Loop
        for m_id in candidate_models:
            raw_params = request.model_parameters.get(m_id, {})
            try:
                run, estimator, t_score, v_score = train_single_model(
                    model_id=m_id,
                    task_type=request.task_type,
                    X_train_trans=X_train_trans,
                    y_train=y_train,
                    X_val_trans=X_val_trans,
                    y_val=y_val,
                    X_test_trans=X_test_trans,
                    y_test=y_test,
                    feature_names=feature_names,
                    source_mapping=source_mapping,
                    class_labels=class_labels,
                    raw_parameters=raw_params,
                    search_config=request.hyperparameter_search,
                    cv_config=request.cross_validation,
                    random_seed=request.random_seed,
                    primary_metric=primary_metric,
                )

                # Persist model artifact safely
                manifest = save_model_artifact(
                    experiment_id=exp_id,
                    model_run_id=run.model_run_id,
                    model_id=m_id,
                    task_type=request.task_type,
                    dataset_id=request.dataset_id,
                    dataset_version_id=request.dataset_version_id,
                    schema_hash=schema_hash,
                    estimator=estimator,
                    preprocessor=preprocessor,
                    feature_schema=feature_schema,
                    target_name=request.target_column,
                    target_schema=target_schema,
                    class_labels=class_labels,
                    random_seed=request.random_seed,
                )
                run.artifact_reference = manifest.artifact_id

                model_runs.append(run)
                fitted_estimators[run.model_run_id] = estimator
                train_scores[run.model_run_id] = t_score
                val_scores[run.model_run_id] = v_score

            except Exception as e:
                logger.error(f"Model training failed for {m_id}: {e}")
                model_runs.append(
                    MLModelRun(
                        model_run_id=f"run_{m_id}_failed",
                        model_id=m_id,
                        model_name=m_id,
                        task_type=request.task_type,
                        status=MLJobStatus.FAILED,
                        warnings=[f"Model execution error: {str(e)}"],
                    )
                )

        # 8. Identify Best Model Run
        valid_runs = [r for r in model_runs if r.status == MLJobStatus.COMPLETED and "dummy" not in r.model_id]
        best_run_id = None
        is_higher_better = primary_metric in ("r2", "accuracy", "balanced_accuracy", "f1_macro", "f1_weighted", "roc_auc", "pr_auc", "silhouette_score")

        if valid_runs:
            sorted_runs = sorted(
                valid_runs,
                key=lambda r: (
                    r.metrics.get(primary_metric, -float("inf") if is_higher_better else float("inf"))
                    if is_higher_better
                    else -r.metrics.get(primary_metric, float("inf"))
                ),
                reverse=True,
            )
            best_run_id = sorted_runs[0].model_run_id

        # 9. Baseline comparison annotation
        baseline_run = next((r for r in model_runs if "dummy" in r.model_id), None)
        if baseline_run and baseline_run.metrics:
            for r in model_runs:
                if r != baseline_run and r.metrics:
                    base_val = baseline_run.metrics.get(primary_metric)
                    m_val = r.metrics.get(primary_metric)
                    if base_val is not None and m_val is not None:
                        delta = round(m_val - base_val, 4)
                        r.baseline_comparison = {
                            "baseline_model": baseline_run.model_name,
                            "metric": primary_metric,
                            "baseline_value": base_val,
                            "model_value": m_val,
                            "delta": delta,
                            "outperforms_baseline": (delta > 0) if is_higher_better else (delta < 0),
                        }

        # 10. Generate Findings
        imbalance_ratio = None
        if class_labels and y is not None:
            vc = y.value_counts()
            if len(vc) >= 2:
                imbalance_ratio = float(vc.min() / vc.max())

        findings = generate_ml_findings(
            experiment_id=exp_id,
            task_type=request.task_type,
            model_runs=model_runs,
            primary_metric=primary_metric,
            train_scores=train_scores,
            val_scores=val_scores,
            imbalance_ratio=imbalance_ratio,
        )

        # 11. Generate Phase 9 ChartSpecs
        visualizations: List[Dict[str, Any]] = []
        best_run = next((r for r in model_runs if r.model_run_id == best_run_id), None)

        if best_run:
            # Feature importance
            if best_run.feature_importance:
                fi_spec = build_feature_importance_chart_spec(
                    best_run.feature_importance,
                    request.dataset_id,
                    request.dataset_version_id,
                    best_run.model_name,
                )
                if fi_spec:
                    visualizations.append(fi_spec)

            # Regression diagnostics
            if best_run.residual_diagnostics:
                act_pred_spec = build_actual_vs_predicted_chart_spec(
                    best_run.residual_diagnostics,
                    request.dataset_id,
                    request.dataset_version_id,
                    best_run.model_name,
                )
                if act_pred_spec:
                    visualizations.append(act_pred_spec)

                resid_spec = build_residual_distribution_chart_spec(
                    best_run.residual_diagnostics,
                    request.dataset_id,
                    request.dataset_version_id,
                    best_run.model_name,
                )
                if resid_spec:
                    visualizations.append(resid_spec)

            # Classification diagnostics
            if best_run.confusion_matrix:
                cm_spec = build_confusion_matrix_chart_spec(
                    best_run.confusion_matrix,
                    request.dataset_id,
                    request.dataset_version_id,
                    best_run.model_name,
                )
                if cm_spec:
                    visualizations.append(cm_spec)

            if best_run.roc_curves:
                roc_spec = build_roc_curve_chart_spec(
                    best_run.roc_curves,
                    request.dataset_id,
                    request.dataset_version_id,
                    best_run.model_name,
                )
                if roc_spec:
                    visualizations.append(roc_spec)

            if best_run.pr_curves:
                pr_spec = build_pr_curve_chart_spec(
                    best_run.pr_curves,
                    request.dataset_id,
                    request.dataset_version_id,
                    best_run.model_name,
                )
                if pr_spec:
                    visualizations.append(pr_spec)

        limitations = [
            "Trained models represent statistical approximations based strictly on the training sample.",
            "Feature importance does NOT prove causal directionality or mechanistic causation.",
            "Unseen category levels outside the training set are ignored or assigned default encodings.",
        ]

        provenance = {
            "dataset_id": request.dataset_id,
            "dataset_version_id": request.dataset_version_id,
            "schema_hash": schema_hash,
            "row_count": df.height,
            "feature_count": len(request.feature_columns),
            "target": request.target_column,
            "random_seed": request.random_seed,
            "engine_version": "v1.0.0",
        }

        return MLResult(
            result_id=f"res_{exp_id}",
            experiment_id=exp_id,
            dataset_id=request.dataset_id,
            dataset_version_id=request.dataset_version_id,
            task_type=request.task_type,
            status=MLJobStatus.COMPLETED,
            target=request.target_column,
            features=request.feature_columns,
            sample_summary=split_summary,
            preprocessing_steps=steps_meta,
            model_runs=model_runs,
            best_model_run_id=best_run_id,
            primary_metric=primary_metric,
            findings=findings,
            visualizations=visualizations,
            warnings=experiment_warnings,
            limitations=limitations,
            provenance=provenance,
            created_at=str(pd.Timestamp.now(tz="UTC")),
        )

    def predict(
        self,
        experiment_id: str,
        model_run_id: str,
        df_input: pd.DataFrame,
        dataset_id: Optional[str] = None,
        dataset_version_id: Optional[str] = None,
    ) -> PredictionResult:
        return execute_model_predictions(
            experiment_id=experiment_id,
            model_run_id=model_run_id,
            df_input=df_input,
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
        )


ml_engine = MLEngine()
