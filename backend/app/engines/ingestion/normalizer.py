import json
import os
from typing import Optional


def normalize_dataset(
    original_path: str,
    format_str: str,
    processed_dir: str,
    sheet_name: Optional[str] = None,
) -> Optional[str]:
    """
    Normalizes complex tabular formats (Excel, JSON) into a standard analytical
    Parquet format stored in processed_dir.

    For native CSV and Parquet, returns None to indicate direct querying
    against the immutable original file (preventing duplicate disk consumption).

    Returns:
        Optional[str]: Path to normalized Parquet file, or None if querying original directly.
    """
    os.makedirs(processed_dir, exist_ok=True)
    target_parquet_path = os.path.join(processed_dir, "data.parquet")

    if format_str == "parquet":
        # Native Parquet: Query directly
        return None

    elif format_str == "csv":
        # Native CSV: DuckDB has high-performance multi-threaded CSV reader
        return None

    elif format_str == "xlsx":
        # Excel: Convert selected worksheet into normalized Parquet
        import polars as pl

        df = pl.read_excel(original_path, sheet_name=sheet_name)
        df.write_parquet(target_parquet_path)
        return target_parquet_path

    elif format_str == "json":
        # JSON: Convert array of objects or JSON lines to normalized Parquet
        import polars as pl

        try:
            df = pl.read_json(original_path)
        except Exception:
            df = pl.read_ndjson(original_path)

        df.write_parquet(target_parquet_path)
        return target_parquet_path

    return None
