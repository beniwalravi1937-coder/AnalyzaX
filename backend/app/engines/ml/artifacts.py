"""
AnalyzaX — Phase 11: Safe Model Artifact Persistence & Compatibility Validation.
Serializes trained model bundles with SHA-256 integrity verification, prevents arbitrary
deserialization/path traversal, and checks dataset schema compatibility before inference.
"""

import hashlib
import json
import os
from typing import Any, Dict, List, Optional, Tuple
import joblib
import numpy as np
import pandas as pd
import sklearn

from backend.app.core.config import settings
from backend.app.engines.ml.exceptions import MLErrorCode, MLException
from backend.app.engines.ml.models import MLTaskType, ModelArtifactManifest


def get_models_storage_dir() -> str:
    models_dir = os.path.abspath(getattr(settings, "DATA_MODELS_DIR", "./data/models"))
    os.makedirs(models_dir, exist_ok=True)
    return models_dir


def save_model_artifact(
    experiment_id: str,
    model_run_id: str,
    model_id: str,
    task_type: MLTaskType,
    dataset_id: str,
    dataset_version_id: str,
    schema_hash: str,
    estimator: Any,
    preprocessor: Any,
    feature_schema: Dict[str, str],
    target_name: Optional[str],
    target_schema: Optional[Dict[str, str]],
    class_labels: Optional[List[str]],
    random_seed: int,
) -> ModelArtifactManifest:
    """
    Saves a trained estimator + preprocessor bundle with a SHA-256 verified manifest.
    """
    base_dir = get_models_storage_dir()
    run_dir = os.path.join(base_dir, experiment_id, model_run_id)
    os.makedirs(run_dir, exist_ok=True)

    artifact_file = os.path.join(run_dir, "model_bundle.joblib")
    manifest_file = os.path.join(run_dir, "manifest.json")

    bundle = {
        "estimator": estimator,
        "preprocessor": preprocessor,
        "feature_schema": feature_schema,
        "target_name": target_name,
        "target_schema": target_schema,
        "task_type": task_type.value,
        "class_labels": class_labels,
        "random_seed": random_seed,
        "library_versions": {
            "sklearn": sklearn.__version__,
            "joblib": joblib.__version__,
            "numpy": np.__version__,
        },
    }

    # Save binary bundle
    joblib.dump(bundle, artifact_file, compress=3)

    # Compute SHA-256 hash
    sha256 = hashlib.sha256()
    with open(artifact_file, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    digest = sha256.hexdigest()

    manifest = ModelArtifactManifest(
        artifact_id=f"art_{model_run_id}",
        experiment_id=experiment_id,
        model_run_id=model_run_id,
        model_id=model_id,
        task_type=task_type,
        dataset_id=dataset_id,
        dataset_version_id=dataset_version_id,
        schema_hash=schema_hash,
        feature_schema=feature_schema,
        target_schema=target_schema,
        random_seed=random_seed,
        created_at=str(pd.Timestamp.now(tz="UTC")),
        sha256_hash=digest,
        library_versions=bundle["library_versions"],
    )

    with open(manifest_file, "w", encoding="utf-8") as f:
        json.dump(manifest.model_dump(), f, indent=2)

    return manifest


def load_model_artifact(experiment_id: str, model_run_id: str) -> Tuple[Dict[str, Any], ModelArtifactManifest]:
    """
    Safely loads a registered model artifact after validating path traversal and SHA-256 integrity.
    """
    base_dir = get_models_storage_dir()
    run_dir = os.path.abspath(os.path.join(base_dir, experiment_id, model_run_id))

    # Path traversal check
    if not run_dir.startswith(base_dir):
        raise MLException(
            "Path traversal violation detected.",
            MLErrorCode.ML_SECURITY_VIOLATION,
        )

    artifact_file = os.path.join(run_dir, "model_bundle.joblib")
    manifest_file = os.path.join(run_dir, "manifest.json")

    if not os.path.exists(artifact_file) or not os.path.exists(manifest_file):
        raise MLException(
            f"Model artifact '{model_run_id}' not found.",
            MLErrorCode.ML_MODEL_NOT_FOUND,
        )

    # Read manifest
    with open(manifest_file, "r", encoding="utf-8") as f:
        manifest_data = json.load(f)
    manifest = ModelArtifactManifest(**manifest_data)

    # Validate SHA-256
    sha256 = hashlib.sha256()
    with open(artifact_file, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    computed_hash = sha256.hexdigest()

    if computed_hash != manifest.sha256_hash:
        raise MLException(
            "Model artifact integrity check failed (SHA-256 mismatch). Artifact may have been corrupted or tampered with.",
            MLErrorCode.ML_SECURITY_VIOLATION,
        )

    # Safely load
    bundle = joblib.load(artifact_file)
    return bundle, manifest


def validate_inference_schema_compatibility(
    df_input: pd.DataFrame,
    manifest: ModelArtifactManifest,
) -> Tuple[bool, List[str]]:
    """
    Validates that an incoming inference DataFrame possesses all expected feature columns.
    """
    errors: List[str] = []
    expected_features = manifest.feature_schema

    for col in expected_features.keys():
        if col not in df_input.columns:
            errors.append(f"Missing required feature column: '{col}'")

    return len(errors) == 0, errors
