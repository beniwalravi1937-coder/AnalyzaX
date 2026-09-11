"""
AnalyzaX Ingestion Engine
Domain logic for format detection, sanitization, validation, normalization, and DuckDB registration.
"""

from backend.app.engines.ingestion.detector import detect_file_format
from backend.app.engines.ingestion.duckdb_registrar import register_dataset_view, unregister_dataset_view
from backend.app.engines.ingestion.normalizer import normalize_dataset
from backend.app.engines.ingestion.sanitizer import (
    generate_dataset_id,
    generate_safe_sql_identifier,
    sanitize_filename,
)
from backend.app.engines.ingestion.validator import validate_dataset_content

__all__ = [
    "detect_file_format",
    "register_dataset_view",
    "unregister_dataset_view",
    "normalize_dataset",
    "generate_dataset_id",
    "generate_safe_sql_identifier",
    "sanitize_filename",
    "validate_dataset_content",
]
