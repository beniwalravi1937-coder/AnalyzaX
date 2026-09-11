"""
Categorical & String Profiling Module
Computes frequency distributions, cardinality, and text length characteristics via DuckDB.
"""

from typing import Any, Dict, List
import duckdb

from backend.app.schemas.profile import CategoricalMetrics, CategoryFrequency


def profile_categorical_column(
    conn: duckdb.DuckDBPyConnection,
    table_name: str,
    col_name: str,
    total_rows: int,
    top_n_limit: int = 20,
) -> Dict[str, Any]:
    """
    Computes categorical distribution, top frequent categories, and text characteristics.
    """
    escaped_col = col_name.replace('"', '""')
    escaped_table = table_name.replace('"', '""')

    # Basic counts and string lengths
    stat_sql = f"""
    SELECT
        COUNT("{escaped_col}") AS non_null_cnt,
        COUNT(*) - COUNT("{escaped_col}") AS null_cnt,
        APPROX_COUNT_DISTINCT("{escaped_col}") AS approx_uniq,
        AVG(LENGTH(CAST("{escaped_col}" AS VARCHAR))) AS avg_len,
        MAX(LENGTH(CAST("{escaped_col}" AS VARCHAR))) AS max_len
    FROM "{escaped_table}"
    """

    try:
        row = conn.execute(stat_sql).fetchone()
        non_null_cnt = int(row[0] or 0)
        null_cnt = int(row[1] or 0)
        unique_cnt = int(row[2] or 0)
        avg_len = round(float(row[3]), 1) if row[3] is not None else None
        max_len = int(row[4]) if row[4] is not None else None
    except Exception:
        non_null_cnt = 0
        null_cnt = total_rows
        unique_cnt = 0
        avg_len = None
        max_len = None

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
            "categorical_metrics": CategoricalMetrics(top_categories=[], is_text=False),
        }

    # Frequency ranking
    freq_sql = f"""
    SELECT
        CAST("{escaped_col}" AS VARCHAR) AS val,
        COUNT(*) AS cnt
    FROM "{escaped_table}"
    WHERE "{escaped_col}" IS NOT NULL
    GROUP BY "{escaped_col}"
    ORDER BY cnt DESC
    LIMIT {top_n_limit}
    """

    top_categories: List[CategoryFrequency] = []
    try:
        freq_rows = conn.execute(freq_sql).fetchall()
        for r in freq_rows:
            cat_val = r[0]
            cat_count = int(r[1])
            cat_pct = round((cat_count / non_null_cnt) * 100, 2)
            top_categories.append(CategoryFrequency(value=cat_val, count=cat_count, percentage=cat_pct))
    except Exception:
        pass

    # Heuristic for unstructured text vs discrete categorical
    is_text = False
    if avg_len is not None and max_len is not None:
        if avg_len > 45 or max_len > 150:
            if cardinality_ratio > 0.4:
                is_text = True

    metrics = CategoricalMetrics(
        top_categories=top_categories,
        avg_length=avg_len,
        max_length=max_len,
        is_text=is_text,
    )

    return {
        "null_count": null_cnt,
        "null_percentage": null_pct,
        "unique_count": unique_cnt,
        "unique_percentage": unique_pct,
        "cardinality_ratio": cardinality_ratio,
        "categorical_metrics": metrics,
    }
