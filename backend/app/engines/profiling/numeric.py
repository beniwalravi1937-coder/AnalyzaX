"""
Numerical Profiling Module
Computes robust, deterministic summary statistics and distribution metrics for numerical columns via DuckDB.
"""

import math
from typing import Any, Dict, Optional
import duckdb

from backend.app.schemas.profile import NumericMetrics, QuantilesSummary


def _sanitize_float(val: Any) -> Optional[float]:
    """Ensures floats are JSON-serializable (converts NaN, inf, -inf to None)."""
    if val is None:
        return None
    try:
        f = float(val)
        if math.isnan(f) or math.isinf(f):
            return None
        return f
    except (TypeError, ValueError):
        return None


def profile_numeric_column(
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    col_name: str,
    total_rows: int,
) -> Dict[str, Any]:
    """
    Computes statistical and distribution metrics for a numerical column.
    Guarantees zero-crash execution even on all-null, single-row, or infinite value columns.
    """
    escaped_col = col_name.replace('"', '""')
    escaped_table = table_name.replace('"', '""')

    sql = f"""
    SELECT
        COUNT("{escaped_col}") AS non_null_cnt,
        COUNT(*) - COUNT("{escaped_col}") AS null_cnt,
        APPROX_COUNT_DISTINCT("{escaped_col}") AS approx_uniq,
        MIN("{escaped_col}") AS min_val,
        MAX("{escaped_col}") AS max_val,
        AVG(CAST("{escaped_col}" AS DOUBLE)) AS mean_val,
        MEDIAN(CAST("{escaped_col}" AS DOUBLE)) AS median_val,
        STDDEV_SAMP(CAST("{escaped_col}" AS DOUBLE)) AS std_val,
        VAR_SAMP(CAST("{escaped_col}" AS DOUBLE)) AS var_val,
        SKEWNESS(CAST("{escaped_col}" AS DOUBLE)) AS skew_val,
        KURTOSIS(CAST("{escaped_col}" AS DOUBLE)) AS kurt_val,
        QUANTILE_CONT(CAST("{escaped_col}" AS DOUBLE), [0.0, 0.05, 0.25, 0.50, 0.75, 0.95, 1.0]) AS q_arr
    FROM "{escaped_table}"
    """

    try:
        row = conn.execute(sql).fetchone()
    except Exception:
        # Fallback query if advanced statistical aggregate functions fail
        fallback_sql = f"""
        SELECT
            COUNT("{escaped_col}"),
            COUNT(*) - COUNT("{escaped_col}"),
            APPROX_COUNT_DISTINCT("{escaped_col}"),
            MIN("{escaped_col}"),
            MAX("{escaped_col}"),
            AVG(CAST("{escaped_col}" AS DOUBLE)),
            MEDIAN(CAST("{escaped_col}" AS DOUBLE)),
            NULL, NULL, NULL, NULL, NULL
        FROM "{escaped_table}"
        """
        row = conn.execute(fallback_sql).fetchone()

    non_null_cnt = int(row[0] or 0)
    null_cnt = int(row[1] or 0)
    unique_cnt = int(row[2] or 0)

    null_pct = round((null_cnt / total_rows * 100), 2) if total_rows > 0 else 0.0
    unique_pct = round((unique_cnt / non_null_cnt * 100), 2) if non_null_cnt > 0 else 0.0
    cardinality_ratio = round(unique_cnt / non_null_cnt, 4) if non_null_cnt > 0 else 0.0

    if non_null_cnt == 0:
        return {
            "null_count": null_cnt,
            "null_percentage": null_pct,
            "unique_count": 0,
            "unique_percentage": 0.0,
            "cardinality_ratio": 0.0,
            "numeric_metrics": None,
        }

    q_arr = row[11] if row[11] is not None and isinstance(row[11], list) and len(row[11]) == 7 else None
    quantiles = None
    if q_arr:
        p0 = _sanitize_float(q_arr[0])
        p5 = _sanitize_float(q_arr[1])
        p25 = _sanitize_float(q_arr[2])
        p50 = _sanitize_float(q_arr[3])
        p75 = _sanitize_float(q_arr[4])
        p95 = _sanitize_float(q_arr[5])
        p100 = _sanitize_float(q_arr[6])
        iqr = round(p75 - p25, 4) if p75 is not None and p25 is not None else None
        quantiles = QuantilesSummary(
            p0=p0, p5=p5, p25=p25, p50=p50, p75=p75, p95=p95, p100=p100, iqr=iqr
        )

    min_val = _sanitize_float(row[3])
    max_val = _sanitize_float(row[4])
    mean_val = _sanitize_float(row[5])
    median_val = _sanitize_float(row[6])
    std_val = _sanitize_float(row[7])
    var_val = _sanitize_float(row[8])
    skew_val = _sanitize_float(row[9])
    kurt_val = _sanitize_float(row[10])

    metrics = NumericMetrics(
        min=min_val,
        max=max_val,
        mean=round(mean_val, 4) if mean_val is not None else None,
        median=round(median_val, 4) if median_val is not None else None,
        stddev=round(std_val, 4) if std_val is not None else None,
        variance=round(var_val, 4) if var_val is not None else None,
        skewness=round(skew_val, 4) if skew_val is not None else None,
        kurtosis=round(kurt_val, 4) if kurt_val is not None else None,
        quantiles=quantiles,
    )

    return {
        "null_count": null_cnt,
        "null_percentage": null_pct,
        "unique_count": unique_cnt,
        "unique_percentage": unique_pct,
        "cardinality_ratio": cardinality_ratio,
        "numeric_metrics": metrics,
    }
