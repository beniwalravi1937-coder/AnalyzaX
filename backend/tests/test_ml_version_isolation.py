"""
AnalyzaX — Phase 11: Dataset Version Isolation Test.
Mandatory test verifying that a model trained on Version 1 remains strictly bound to Version 1,
that subsequent dataset versions cannot silently alter Model A, and that provenance and schema
compatibility are enforced.
"""

import numpy as np
import pandas as pd
import polars as pl
import pytest

from backend.app.engines.ml.engine import ml_engine
from backend.app.engines.ml.exceptions import MLErrorCode, MLException
from backend.app.engines.ml.models import (
    MLExperimentRequest,
    MLTaskType,
)


def test_dataset_version_isolation_and_immutability():
    # 1. Prepare Dataset Version 1
    np.random.seed(42)
    n = 60
    v1_x = np.linspace(1, 10, n)
    v1_y = 3.0 * v1_x + np.random.normal(0, 0.05, n)
    df_v1 = pl.DataFrame({"x_feature": v1_x, "y_target": v1_y})

    # Train Model A on Version 1
    req_v1 = MLExperimentRequest(
        dataset_id="ds_iso_test",
        dataset_version_id="v1",
        task_type=MLTaskType.REGRESSION,
        target_column="y_target",
        feature_columns=["x_feature"],
        models=["linear_regression"],
        primary_metric="r2",
        random_seed=42,
    )
    result_v1 = ml_engine.execute_experiment(df_v1, req_v1)
    best_run_v1 = result_v1.best_model_run_id

    # Verify provenance points to v1
    assert result_v1.provenance["dataset_id"] == "ds_iso_test"
    assert result_v1.provenance["dataset_version_id"] == "v1"

    # Test baseline predictions on Model A
    test_input = pd.DataFrame({"x_feature": [4.0, 5.0]})
    pred_v1 = ml_engine.predict(result_v1.experiment_id, best_run_v1, test_input)
    assert pred_v1.provenance["trained_version_id"] == "v1"
    first_pred_val = pred_v1.predictions[0]

    # 2. Simulate Dataset Version 2 with completely different distribution and extra column
    v2_x = np.linspace(100, 200, n)
    v2_y = -5.0 * v2_x + 50.0  # inverse relationship
    df_v2 = pl.DataFrame({"x_feature": v2_x, "y_target": v2_y, "extra_col": [999] * n})

    req_v2 = MLExperimentRequest(
        dataset_id="ds_iso_test",
        dataset_version_id="v2",
        task_type=MLTaskType.REGRESSION,
        target_column="y_target",
        feature_columns=["x_feature"],
        models=["linear_regression"],
        primary_metric="r2",
        random_seed=42,
    )
    result_v2 = ml_engine.execute_experiment(df_v2, req_v2)
    assert result_v2.provenance["dataset_version_id"] == "v2"

    # 3. VERIFY: Model A still produces exact identical output for Version 1
    pred_v1_retest = ml_engine.predict(result_v1.experiment_id, best_run_v1, test_input)
    assert pred_v1_retest.predictions[0] == first_pred_val
    assert pred_v1_retest.provenance["trained_version_id"] == "v1"

    # 4. VERIFY: Incompatible input schema is rejected by Model A
    incompatible_input = pd.DataFrame({"completely_different_col": [1.0, 2.0]})
    with pytest.raises(MLException) as exc:
        ml_engine.predict(result_v1.experiment_id, best_run_v1, incompatible_input)
    assert exc.value.error_code == MLErrorCode.ML_SCHEMA_MISMATCH
