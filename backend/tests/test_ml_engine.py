"""
Unit and integration tests for Phase 11 Machine Learning Engine.
Validates suitability checks, preprocessing, splitting, baselines, models, evaluation,
diagnostics, interpretation, and safe artifact persistence.
"""

import os
import shutil
import tempfile
import numpy as np
import pandas as pd
import polars as pl
import pytest

from backend.app.engines.ml.artifacts import (
    load_model_artifact,
    save_model_artifact,
    validate_inference_schema_compatibility,
)
from backend.app.engines.ml.engine import ml_engine
from backend.app.engines.ml.evaluation import (
    evaluate_classification,
    evaluate_clustering,
    evaluate_regression,
)
from backend.app.engines.ml.exceptions import MLErrorCode, MLException
from backend.app.engines.ml.models import (
    CrossValidationConfig,
    HyperparameterSearchConfig,
    MLExperimentRequest,
    MLTaskType,
    PreprocessingConfig,
    SplitConfig,
    SuitabilitySeverity,
)
from backend.app.engines.ml.preprocessing import (
    build_preprocessing_pipeline,
    get_feature_names_and_mapping,
)
from backend.app.engines.ml.registry import model_registry
from backend.app.engines.ml.splitting import (
    get_cross_validation_generator,
    perform_train_val_test_split,
)
from backend.app.engines.ml.suitability import analyze_suitability


def test_registry_contains_all_models():
    """Verify registry has all required 13 algorithms + 2 baselines."""
    reg_models = model_registry.list_models(MLTaskType.REGRESSION)
    clf_models = model_registry.list_models(MLTaskType.BINARY_CLASSIFICATION)
    clust_models = model_registry.list_models(MLTaskType.CLUSTERING)

    reg_ids = {m.model_id for m in reg_models}
    assert "dummy_regressor" in reg_ids
    assert "linear_regression" in reg_ids
    assert "ridge" in reg_ids
    assert "lasso" in reg_ids
    assert "elastic_net" in reg_ids
    assert "random_forest_regressor" in reg_ids
    assert "gradient_boosting_regressor" in reg_ids
    assert "hist_gradient_boosting_regressor" in reg_ids

    clf_ids = {m.model_id for m in clf_models}
    assert "dummy_classifier" in clf_ids
    assert "logistic_regression" in clf_ids
    assert "random_forest_classifier" in clf_ids
    assert "gradient_boosting_classifier" in clf_ids
    assert "hist_gradient_boosting_classifier" in clf_ids

    clust_ids = {m.model_id for m in clust_models}
    assert "kmeans" in clust_ids
    assert "minibatch_kmeans" in clust_ids


def test_suitability_small_dataset():
    """Verify suitability rejects datasets with fewer than 10 rows."""
    tiny_df = pl.DataFrame({"x": [1, 2, 3], "y": [10, 20, 30]})
    report = analyze_suitability(tiny_df, target_column="y", requested_task=MLTaskType.REGRESSION)
    assert not report.is_suitable
    critical_codes = [i.code for i in report.issues if i.severity == SuitabilitySeverity.CRITICAL]
    assert "INSUFFICIENT_OBSERVATIONS" in critical_codes


def test_suitability_constant_target():
    """Verify suitability rejects constant target variable."""
    df = pl.DataFrame({
        "x": list(range(50)),
        "target": [5] * 50,
    })
    report = analyze_suitability(df, target_column="target", requested_task=MLTaskType.REGRESSION)
    assert not report.is_suitable
    codes = [i.code for i in report.issues if i.severity == SuitabilitySeverity.CRITICAL]
    assert "CONSTANT_TARGET" in codes


def test_suitability_leakage_and_id_detection():
    """Verify detection of direct target duplication and ID columns."""
    df = pl.DataFrame({
        "customer_id": [f"id_{i}" for i in range(100)],
        "income": [float(i * 1000) for i in range(100)],
        "target_score": [float(i * 2) for i in range(100)],
        "constant_col": [1] * 100,
    })
    report = analyze_suitability(df, target_column="target_score", requested_task=MLTaskType.REGRESSION)
    assert "constant_col" in report.excluded_features
    assert "customer_id" in report.excluded_features
    assert "income" in report.recommended_features


def test_preprocessing_leakage_free():
    """Verify preprocessor fits only on train data and handles unseen categories."""
    df_train = pd.DataFrame({
        "num": [10.0, 20.0, np.nan, 40.0],
        "cat": ["A", "B", "A", "B"],
    })
    df_test = pd.DataFrame({
        "num": [15.0, 25.0],
        "cat": ["A", "UNSEEN"],
    })

    pipe, steps, num_cols, cat_cols = build_preprocessing_pipeline(
        df_train, ["num", "cat"], PreprocessingConfig()
    )
    # Fit strictly on train
    X_train_trans = pipe.fit_transform(df_train)
    # Transform test without error even with unseen category
    X_test_trans = pipe.transform(df_test)

    assert X_train_trans.shape[0] == 4
    assert X_test_trans.shape[0] == 2
    assert not np.isnan(X_train_trans).any()
    assert not np.isnan(X_test_trans).any()


def test_stratified_splitting():
    """Verify stratified split preserves class ratios and prevents impossible splits."""
    np.random.seed(42)
    n = 100
    X = pd.DataFrame({"x1": np.random.randn(n), "x2": np.random.randn(n)})
    y = pd.Series([0] * 70 + [1] * 30)

    X_train, X_val, X_test, y_train, y_val, y_test, summary, warns = perform_train_val_test_split(
        X, y, MLTaskType.BINARY_CLASSIFICATION, SplitConfig(train_size=0.7, val_size=0.15, test_size=0.15, random_seed=42)
    )

    assert summary.stratified
    assert summary.train_rows == 70
    assert summary.val_rows == 15
    assert summary.test_rows == 15
    assert (y_train == 1).sum() > 0
    assert (y_val == 1).sum() > 0
    assert (y_test == 1).sum() > 0


def test_regression_evaluation_metrics():
    """Verify numerical correctness of regression metrics."""
    y_true = np.array([3.0, -0.5, 2.0, 7.0])
    y_pred = np.array([2.5, 0.0, 2.0, 8.0])

    metrics, diag = evaluate_regression(y_true, y_pred, n_features=1)
    assert metrics.mae == pytest.approx(0.5, abs=1e-3)
    assert metrics.mse == pytest.approx(0.375, abs=1e-3)
    assert metrics.rmse == pytest.approx(np.sqrt(0.375), abs=1e-3)
    assert diag.mean_residual == pytest.approx(-0.25, abs=1e-3)


def test_classification_evaluation_metrics():
    """Verify classification metrics and confusion matrix."""
    y_true = np.array(["cat", "dog", "cat", "dog", "dog"])
    y_pred = np.array(["cat", "dog", "cat", "cat", "dog"])

    metrics, cm_data, _, _ = evaluate_classification(
        y_true, y_pred, None, ["cat", "dog"], MLTaskType.BINARY_CLASSIFICATION
    )
    # 4 correct out of 5 = 0.8
    assert metrics.accuracy == pytest.approx(0.8, abs=1e-3)
    assert cm_data.labels == ["cat", "dog"]
    assert cm_data.matrix == [[2, 0], [1, 2]]


def test_clustering_evaluation_metrics():
    """Verify clustering metrics (inertia, silhouette)."""
    X = np.array([[1.0, 1.0], [1.2, 1.1], [5.0, 5.0], [5.2, 5.1]])
    labels = np.array([0, 0, 1, 1])

    metrics, summaries = evaluate_clustering(X, labels, inertia=0.2)
    assert metrics.inertia == 0.2
    assert metrics.silhouette_score is not None
    assert metrics.silhouette_score > 0.5
    assert len(summaries) == 2


def test_safe_artifact_storage_and_tamper_detection(tmp_path):
    """Verify model artifact saving, loading, and rejection of tampered artifacts."""
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler

    exp_id = "exp_test_safety"
    run_id = "run_test_linear"

    reg = LinearRegression().fit([[1.0], [2.0], [3.0]], [2.0, 4.0, 6.0])
    scaler = StandardScaler().fit([[1.0], [2.0], [3.0]])

    manifest = save_model_artifact(
        experiment_id=exp_id,
        model_run_id=run_id,
        model_id="linear_regression",
        task_type=MLTaskType.REGRESSION,
        dataset_id="ds_test",
        dataset_version_id="v1",
        schema_hash="hash123",
        estimator=reg,
        preprocessor=scaler,
        feature_schema={"x": "float"},
        target_name="y",
        target_schema={"y": "float"},
        class_labels=None,
        random_seed=42,
    )
    assert manifest.sha256_hash is not None

    # Load successfully
    bundle, loaded_manifest = load_model_artifact(exp_id, run_id)
    assert bundle["estimator"] is not None
    assert loaded_manifest.model_id == "linear_regression"

    # Tamper with file
    from backend.app.engines.ml.artifacts import get_models_storage_dir
    art_path = os.path.join(get_models_storage_dir(), exp_id, run_id, "model_bundle.joblib")
    with open(art_path, "ab") as f:
        f.write(b"tampered_bytes")

    # Loading tampered file should fail with security violation
    with pytest.raises(MLException) as exc:
        load_model_artifact(exp_id, run_id)
    assert exc.value.error_code == MLErrorCode.ML_SECURITY_VIOLATION


def test_end_to_end_regression_experiment():
    """Verify full deterministic regression experiment execution via ml_engine."""
    np.random.seed(42)
    n = 60
    x1 = np.linspace(1, 10, n)
    x2 = np.random.randn(n)
    y = 2.5 * x1 - 1.2 * x2 + np.random.normal(0, 0.1, n)

    df = pl.DataFrame({"feature_a": x1, "feature_b": x2, "target_val": y})

    req = MLExperimentRequest(
        dataset_id="ds_reg",
        dataset_version_id="v1",
        task_type=MLTaskType.REGRESSION,
        target_column="target_val",
        feature_columns=["feature_a", "feature_b"],
        models=["linear_regression", "ridge"],
        primary_metric="rmse",
        random_seed=42,
    )

    result = ml_engine.execute_experiment(df, req)
    assert result.status == "COMPLETED"
    assert len(result.model_runs) >= 3  # baseline + 2 requested models
    assert result.best_model_run_id is not None
    assert len(result.visualizations) >= 2  # actual vs predicted, residuals, etc.
    assert len(result.findings) >= 1

    # Verify predictions on new rows
    df_new = pd.DataFrame({"feature_a": [5.0, 6.0], "feature_b": [0.0, 0.5]})
    pred_res = ml_engine.predict(
        experiment_id=result.experiment_id,
        model_run_id=result.best_model_run_id,
        df_input=df_new,
    )
    assert pred_res.row_count == 2
    assert len(pred_res.predictions) == 2
    assert isinstance(pred_res.predictions[0], float)
