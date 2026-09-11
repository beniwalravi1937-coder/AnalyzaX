"""
AnalyzaX — Phase 12: Safe Forecasting Model Artifact Storage.
Persists trained statistical forecasting estimators using joblib with SHA-256 integrity
manifests, path-traversal prevention, and dataset-version compatibility checks.
"""

import hashlib
import json
import os
from pathlib import Path
import time
from typing import Any, Dict, Optional, Tuple
import joblib

from backend.app.core.config import settings
from backend.app.engines.forecasting.exceptions import ForecastErrorCode, ForecastException


def _compute_sha256(filepath: Path) -> str:
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()


def save_forecast_artifact(
    experiment_id: str,
    run_id: str,
    estimator: Any,
    dataset_id: str,
    dataset_version_id: str,
    time_column: str,
    target_column: str,
    frequency: str,
    pandas_frequency_str: str,
    model_id: str,
    parameters: Dict[str, Any],
) -> str:
    """Safely persist a trained forecasting model and manifest."""
    base_dir = Path(settings.DATA_FORECASTING_MODELS_DIR).resolve()
    target_dir = (base_dir / experiment_id / run_id).resolve()

    # Prevent path traversal
    if not str(target_dir).startswith(str(base_dir)):
        raise ForecastException(
            code=ForecastErrorCode.FORECAST_ARTIFACT_ERROR,
            message="Path traversal detected in artifact destination.",
        )

    target_dir.mkdir(parents=True, exist_ok=True)
    model_path = target_dir / "model.joblib"
    manifest_path = target_dir / "manifest.json"

    # Save model
    joblib.dump(estimator, model_path)

    # Check file size limit
    file_size = model_path.stat().st_size
    if file_size > settings.FORECAST_MAX_ARTIFACT_SIZE_BYTES:
        model_path.unlink(missing_ok=True)
        raise ForecastException(
            code=ForecastErrorCode.FORECAST_RESOURCE_LIMIT_EXCEEDED,
            message=f"Forecast artifact size ({file_size} bytes) exceeds limit ({settings.FORECAST_MAX_ARTIFACT_SIZE_BYTES} bytes).",
        )

    checksum = _compute_sha256(model_path)

    manifest = {
        "experiment_id": experiment_id,
        "run_id": run_id,
        "dataset_id": dataset_id,
        "dataset_version_id": dataset_version_id,
        "model_id": model_id,
        "parameters": parameters,
        "time_column": time_column,
        "target_column": target_column,
        "frequency": frequency,
        "pandas_frequency_str": pandas_frequency_str,
        "sha256_checksum": checksum,
        "file_size_bytes": file_size,
        "created_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }

    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)

    return f"forecast_art_{experiment_id}_{run_id}"


def load_forecast_artifact(experiment_id: str, run_id: str) -> Tuple[Any, Dict[str, Any]]:
    """Safely load and verify an existing forecasting model artifact."""
    base_dir = Path(settings.DATA_FORECASTING_MODELS_DIR).resolve()
    target_dir = (base_dir / experiment_id / run_id).resolve()

    if not str(target_dir).startswith(str(base_dir)):
        raise ForecastException(
            code=ForecastErrorCode.FORECAST_ARTIFACT_ERROR,
            message="Path traversal detected in artifact path.",
        )

    model_path = target_dir / "model.joblib"
    manifest_path = target_dir / "manifest.json"

    if not model_path.exists() or not manifest_path.exists():
        raise ForecastException(
            code=ForecastErrorCode.FORECAST_ARTIFACT_ERROR,
            message=f"Model artifact not found for experiment '{experiment_id}', run '{run_id}'.",
        )

    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Verify integrity
    actual_checksum = _compute_sha256(model_path)
    if actual_checksum != manifest.get("sha256_checksum"):
        raise ForecastException(
            code=ForecastErrorCode.FORECAST_ARTIFACT_ERROR,
            message="Artifact SHA-256 checksum verification failed. The file may be corrupt or tampered with.",
        )

    estimator = joblib.load(model_path)
    return estimator, manifest
