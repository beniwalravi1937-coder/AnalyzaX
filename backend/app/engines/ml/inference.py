"""
AnalyzaX — Phase 11: Schema-Validated Inference & Prediction Engine.
Executes predictions against incoming rows or compatible dataset versions without mutating original datasets.
"""

import uuid
from typing import Any, Dict, List, Optional, Union
import numpy as np
import pandas as pd

from backend.app.core.config import settings
from backend.app.engines.ml.artifacts import (
    load_model_artifact,
    validate_inference_schema_compatibility,
)
from backend.app.engines.ml.exceptions import MLErrorCode, MLException
from backend.app.engines.ml.models import MLTaskType, PredictionResult


def execute_model_predictions(
    experiment_id: str,
    model_run_id: str,
    df_input: pd.DataFrame,
    dataset_id: Optional[str] = None,
    dataset_version_id: Optional[str] = None,
) -> PredictionResult:
    """
    Loads registered model artifact, validates input schema, transforms features,
    and runs deterministic inference.
    """
    max_pred_rows = getattr(settings, "ML_MAX_PREDICTION_ROWS", 100_000)
    if len(df_input) > max_pred_rows:
        raise MLException(
            f"Prediction batch size ({len(df_input)}) exceeds maximum permitted rows ({max_pred_rows}).",
            MLErrorCode.ML_RESOURCE_LIMIT_EXCEEDED,
        )

    # Load bundle & manifest
    bundle, manifest = load_model_artifact(experiment_id, model_run_id)

    # Validate schema compatibility
    is_compatible, errors = validate_inference_schema_compatibility(df_input, manifest)
    if not is_compatible:
        raise MLException(
            f"Input schema is incompatible with model '{model_run_id}': {'; '.join(errors)}",
            MLErrorCode.ML_SCHEMA_MISMATCH,
            details={"errors": errors},
        )

    estimator = bundle["estimator"]
    preprocessor = bundle["preprocessor"]
    task_type = MLTaskType(bundle["task_type"])
    class_labels = bundle.get("class_labels")

    # Select only required feature columns in original order
    feature_cols = list(manifest.feature_schema.keys())
    X_input = df_input[feature_cols]

    # Preprocess
    try:
        X_trans = preprocessor.transform(X_input)
    except Exception as e:
        raise MLException(
            f"Preprocessing transform failed on inference data: {e}",
            MLErrorCode.ML_PREPROCESSING_ERROR,
        )

    # Predict
    try:
        raw_preds = estimator.predict(X_trans)
    except Exception as e:
        raise MLException(
            f"Inference execution failed: {e}",
            MLErrorCode.ML_INFERENCE_ERROR,
        )

    # Convert predictions to native Python types
    if task_type == MLTaskType.REGRESSION:
        preds = [round(float(p), 4) for p in raw_preds]
    elif task_type in (MLTaskType.BINARY_CLASSIFICATION, MLTaskType.MULTICLASS_CLASSIFICATION):
        preds = [str(p) for p in raw_preds]
    elif task_type == MLTaskType.CLUSTERING:
        preds = [int(p) for p in raw_preds]
    else:
        preds = [str(p) for p in raw_preds]

    # Probabilities if classification
    prob_list: Optional[List[Dict[str, float]]] = None
    if hasattr(estimator, "predict_proba") and class_labels:
        try:
            raw_probs = estimator.predict_proba(X_trans)
            prob_list = []
            for row in raw_probs:
                prob_dict = {
                    lbl: round(float(p), 4)
                    for lbl, p in zip(class_labels, row)
                }
                prob_list.append(prob_dict)
        except Exception:
            prob_list = None

    pred_id = f"pred_{uuid.uuid4().hex[:10]}"

    return PredictionResult(
        prediction_id=pred_id,
        model_run_id=model_run_id,
        dataset_id=dataset_id,
        dataset_version_id=dataset_version_id,
        row_count=len(df_input),
        task_type=task_type,
        predictions=preds,
        probabilities=prob_list,
        columns=feature_cols,
        status="COMPLETED",
        created_at=str(pd.Timestamp.now(tz="UTC")),
        provenance={
            "experiment_id": experiment_id,
            "model_run_id": model_run_id,
            "trained_dataset_id": manifest.dataset_id,
            "trained_version_id": manifest.dataset_version_id,
            "inference_dataset_id": dataset_id,
            "inference_version_id": dataset_version_id,
        },
    )
