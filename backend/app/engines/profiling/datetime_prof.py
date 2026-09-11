"""
Datetime Profiling Module
Computes time boundaries, span duration, and infers cadence/frequency for temporal columns.
"""

from typing import Any, Dict, Optional
import duckdb

from backend.app.schemas.profile import DatetimeMetrics


def profile_datetime_column(
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    col_name: str,
    total_rows: int,
) -> Dict[str, Any]:
    """
    Computes temporal bounds, timespan in days, distinct dates, and approximate periodicity.
    """
    escaped_col = col_name.replace('"', '""')
    escaped_table = table_name.replace('"', '""')

    sql = f"""
    SELECT
        COUNT("{escaped_col}") AS non_null_cnt,
        COUNT(*) - COUNT("{escaped_col}") AS null_cnt,
        APPROX_COUNT_DISTINCT("{escaped_col}") AS approx_uniq,
        MIN("{escaped_col}")::VARCHAR AS min_val,
        MAX("{escaped_col}")::VARCHAR AS max_val,
        APPROX_COUNT_DISTINCT(DATE_TRUNC('day', CAST("{escaped_col}" AS TIMESTAMP))) AS distinct_days
    FROM "{escaped_table}"
    """

    try:
        row = conn.execute(sql).fetchone()
        non_null_cnt = int(row[0] or 0)
        null_cnt = int(row[1] or 0)
        unique_cnt = int(row[2] or 0)
        min_ts = str(row[3]) if row[3] is not None else None
        max_ts = str(row[4]) if row[4] is not None else None
        distinct_days = int(row[5] or 0)
    except Exception:
        non_null_cnt = 0
        null_cnt = total_rows
        unique_cnt = 0
        min_ts = None
        max_ts = None
        distinct_days = 0

    null_pct = round((null_cnt / total_rows * 100), 2) if total_rows > 0 else 0.0
    unique_pct = round((unique_cnt / non_null_cnt * 100), 2) if non_null_cnt > 0 else 0.0
    cardinality_ratio = round(unique_cnt / non_null_cnt, 4) if non_null_cnt > 0 else 0.0

    if non_null_cnt == 0 or not min_ts or not max_ts:
        return {
            "null_count": null_cnt,
            "null_percentage": null_pct,
            "unique_count": unique_cnt,
            "unique_percentage": unique_pct,
            "cardinality_ratio": cardinality_ratio,
            "datetime_metrics": DatetimeMetrics(),
        }

    # Calculate span in days
    span_sql = f"""
    SELECT
        DATE_DIFF('day', MIN(CAST("{escaped_col}" AS TIMESTAMP)), MAX(CAST("{escaped_col}" AS TIMESTAMP))) AS span_d,
        DATE_DIFF('hour', MIN(CAST("{escaped_col}" AS TIMESTAMP)), MAX(CAST("{escaped_col}" AS TIMESTAMP))) AS span_h
    FROM "{escaped_table}"
    WHERE "{escaped_col}" IS NOT NULL
    """

    span_days: Optional[float] = None
    span_hours: Optional[float] = None
    try:
        span_row = conn.execute(span_sql).fetchone()
        if span_row:
            span_days = float(span_row[0]) if span_row[0] is not None else None
            span_hours = float(span_row[1]) if span_row[1] is not None else None
    except Exception:
        pass

    # Infer cadence / frequency
    detected_freq: Optional[str] = None
    if distinct_days > 1 and span_days is not None and span_days > 0:
        ratio = span_days / distinct_days
        if ratio < 0.2 and span_hours and span_hours > 0:
            detected_freq = "hourly"
        elif 0.8 <= ratio <= 1.25:
            detected_freq = "daily"
        elif 6.0 <= ratio <= 8.0:
            detected_freq = "weekly"
        elif 26.0 <= ratio <= 35.0:
            detected_freq = "monthly"
        elif 80.0 <= ratio <= 100.0:
            detected_freq = "quarterly"
        elif 340.0 <= ratio <= 380.0:
            detected_freq = "yearly"
        else:
            detected_freq = "irregular"
    elif distinct_days == 1:
        detected_freq = "daily"

    metrics = DatetimeMetrics(
        min_timestamp=min_ts,
        max_timestamp=max_ts,
        span_days=span_days,
        distinct_dates_count=distinct_days,
        detected_frequency=detected_freq,
    )

    return {
        "null_count": null_cnt,
        "null_percentage": null_pct,
        "unique_count": unique_cnt,
        "unique_percentage": unique_pct,
        "cardinality_ratio": cardinality_ratio,
        "datetime_metrics": metrics,
    }
