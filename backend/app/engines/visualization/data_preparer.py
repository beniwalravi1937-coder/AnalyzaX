"""
Server-side data preparation for visualization.
Executes deterministic aggregations, safe filtering, Top-N grouping, and bounded sampling.
"""

from typing import Any, Dict, List, Optional, Tuple
import duckdb
import numpy as np

from backend.app.core.config import settings
from backend.app.engines.visualization.models import (
    AggregationType,
    ChartSamplingMetadata,
    ChartSpec,
    ChartType,
    SortBy,
    SortDirection,
    StructuredFilter,
)


class VisualizationDataPreparer:
    """
    Prepares and bounds data for visual rendering using in-memory DuckDB.
    Guarantees no unbounded payloads reach the client.
    """

    def prepare_data(
        self,
        parquet_path: str,
        spec: ChartSpec,
    ) -> ChartSpec:
        """
        Processes parquet data according to the ChartSpec encodings, filters,
        aggregation, top-n, and sampling rules. Returns an updated ChartSpec.
        """
        conn = duckdb.connect(":memory:")
        try:
            # Register parquet table as 'source_data'
            # Sanitize path to prevent injection
            safe_path = parquet_path.replace("'", "''").replace("\\", "/")
            conn.execute(f"CREATE VIEW source_data AS SELECT * FROM read_parquet('{safe_path}')")

            # 1. Base row count
            total_rows = conn.execute("SELECT COUNT(*) FROM source_data").fetchone()[0]

            # 2. Build safe WHERE clause from structured filters
            where_sql, params = self._build_where_clause(spec.filters)

            # 3. Route by chart type and aggregation
            if spec.chart_type == ChartType.HISTOGRAM:
                data, sampling = self._prepare_histogram(conn, spec, where_sql, params, total_rows)
            elif spec.chart_type == ChartType.BOX:
                data, sampling = self._prepare_boxplot(conn, spec, where_sql, params, total_rows)
            elif spec.chart_type in (ChartType.SCATTER, ChartType.BUBBLE):
                data, sampling = self._prepare_scatter(conn, spec, where_sql, params, total_rows)
            elif spec.chart_type == ChartType.HEATMAP:
                data, sampling = self._prepare_heatmap(conn, spec, where_sql, params, total_rows)
            else:
                # Standard categorical / temporal aggregation (bar, line, area, donut, etc.)
                data, sampling = self._prepare_aggregated(conn, spec, where_sql, params, total_rows)

            # Create updated copy with hydrated data
            spec_copy = spec.model_copy(deep=True)
            spec_copy.data = data
            spec_copy.sampling = sampling
            return spec_copy

        finally:
            conn.close()

    @staticmethod
    def _fetch_dicts(conn: duckdb.DuckDBPyConnection, query: str, params: List[Any]) -> List[Dict[str, Any]]:
        cursor = conn.execute(query, params)
        if not cursor.description:
            return []
        cols = [desc[0] for desc in cursor.description]
        return [dict(zip(cols, row)) for row in cursor.fetchall()]

    def _build_where_clause(
        self, filters: List[StructuredFilter]
    ) -> Tuple[str, List[Any]]:
        if not filters:
            return "", []

        clauses = []
        params = []
        for f in filters:
            field = f'"{f.field}"'
            op = f.operator.lower()

            if op == "equals":
                clauses.append(f"{field} = ?")
                params.append(f.value)
            elif op == "not_equals":
                clauses.append(f"{field} != ?")
                params.append(f.value)
            elif op == "greater_than":
                clauses.append(f"{field} > ?")
                params.append(f.value)
            elif op == "greater_than_or_equal":
                clauses.append(f"{field} >= ?")
                params.append(f.value)
            elif op == "less_than":
                clauses.append(f"{field} < ?")
                params.append(f.value)
            elif op == "less_than_or_equal":
                clauses.append(f"{field} <= ?")
                params.append(f.value)
            elif op == "contains" and isinstance(f.value, str):
                clauses.append(f"{field} ILIKE ?")
                params.append(f"%{f.value}%")
            elif op == "starts_with" and isinstance(f.value, str):
                clauses.append(f"{field} ILIKE ?")
                params.append(f"{f.value}%")
            elif op == "between" and f.value2 is not None:
                clauses.append(f"{field} BETWEEN ? AND ?")
                params.extend([f.value, f.value2])
            elif op == "in" and isinstance(f.value, list) and f.value:
                placeholders = ", ".join(["?"] * len(f.value))
                clauses.append(f"{field} IN ({placeholders})")
                params.extend(f.value)
            elif op == "not_in" and isinstance(f.value, list) and f.value:
                placeholders = ", ".join(["?"] * len(f.value))
                clauses.append(f"{field} NOT IN ({placeholders})")
                params.extend(f.value)
            elif op == "is_null":
                clauses.append(f"{field} IS NULL")
            elif op == "is_not_null":
                clauses.append(f"{field} IS NOT NULL")

        if clauses:
            return "WHERE " + " AND ".join(clauses), params
        return "", []

    def _prepare_aggregated(
        self,
        conn: duckdb.DuckDBPyConnection,
        spec: ChartSpec,
        where_sql: str,
        params: List[Any],
        total_rows: int,
    ) -> Tuple[List[Dict[str, Any]], ChartSamplingMetadata]:
        x_col = f'"{spec.x}"' if spec.x else None
        y_col = f'"{spec.y}"' if spec.y else None
        series_col = f'"{spec.series}"' if spec.series else None

        agg_func = (spec.aggregation or "sum").upper()
        if agg_func == "AVG":
            agg_expr = f"AVG({y_col})" if y_col else "COUNT(*)"
        elif agg_func == "COUNT":
            agg_expr = "COUNT(*)"
        elif agg_func == "COUNT_DISTINCT":
            agg_expr = f"COUNT(DISTINCT {y_col})" if y_col else "COUNT(*)"
        elif agg_func == "MIN":
            agg_expr = f"MIN({y_col})" if y_col else "COUNT(*)"
        elif agg_func == "MAX":
            agg_expr = f"MAX({y_col})" if y_col else "COUNT(*)"
        elif agg_func == "MEDIAN":
            agg_expr = f"MEDIAN({y_col})" if y_col else "COUNT(*)"
        else:
            agg_expr = f"SUM({y_col})" if y_col else "COUNT(*)"

        # Grouping fields
        group_fields = []
        select_fields = []
        if x_col:
            group_fields.append(x_col)
            select_fields.append(f"{x_col} AS x")
        if series_col:
            group_fields.append(series_col)
            select_fields.append(f"{series_col} AS series")

        if not group_fields:
            # Single value KPI
            query = f"SELECT {agg_expr} AS value FROM source_data {where_sql}"
            row = conn.execute(query, params).fetchone()
            val = row[0] if row else 0
            return [{"value": val}], ChartSamplingMetadata(original_row_count=total_rows, displayed_points=1)

        select_sql = ", ".join(select_fields)
        group_sql = ", ".join(group_fields)

        # Ordering
        order_sql = ""
        if spec.sort_direction:
            direction = spec.sort_direction.value.upper()
            if spec.sort_by == SortBy.CATEGORY:
                order_sql = f"ORDER BY x {direction}"
            elif spec.sort_by == SortBy.CHRONOLOGICAL:
                order_sql = f"ORDER BY x {direction}"
            else:
                order_sql = f"ORDER BY y {direction}"
        else:
            order_sql = "ORDER BY y DESC"

        # Limit
        limit_n = settings.VISUALIZATION_MAX_CATEGORIES
        if spec.top_n and spec.top_n.n:
            limit_n = spec.top_n.n

        query = f"""
            SELECT {select_sql}, {agg_expr} AS y
            FROM source_data
            {where_sql}
            GROUP BY {group_sql}
            {order_sql}
            LIMIT {limit_n}
        """
        rows = self._fetch_dicts(conn, query, params)

        # Top-N "Other" aggregation if requested
        if spec.top_n and spec.top_n.include_other and len(rows) >= limit_n:
            top_x_values = [r["x"] for r in rows if r.get("x") is not None]
            if top_x_values:
                placeholders = ", ".join(["?"] * len(top_x_values))
                other_where = f"{where_sql} AND {x_col} NOT IN ({placeholders})" if where_sql else f"WHERE {x_col} NOT IN ({placeholders})"
                subquery = f"SELECT {agg_expr} AS other_val FROM source_data {other_where}"
                sub_params = list(params) + top_x_values
                other_res = conn.execute(subquery, sub_params).fetchone()
                if other_res and other_res[0] is not None and other_res[0] > 0:
                    rows.append({"x": spec.top_n.other_label, "y": other_res[0]})

        sampling = ChartSamplingMetadata(
            is_sampled=(len(rows) < total_rows),
            original_row_count=total_rows,
            displayed_points=len(rows),
            sampling_method="top_n" if spec.top_n else "aggregation",
        )
        return rows, sampling

    def _prepare_scatter(
        self,
        conn: duckdb.DuckDBPyConnection,
        spec: ChartSpec,
        where_sql: str,
        params: List[Any],
        total_rows: int,
    ) -> Tuple[List[Dict[str, Any]], ChartSamplingMetadata]:
        x_col = f'"{spec.x}"'
        y_col = f'"{spec.y}"'
        series_col = f', "{spec.series}" AS series' if spec.series else ""
        color_col = f', "{spec.color}" AS color' if spec.color else ""

        max_points = settings.MAX_SCATTER_POINTS
        is_sampled = total_rows > max_points

        sample_clause = f"USING SAMPLE {max_points} (reservoir, 42)" if is_sampled else ""
        query = f"""
            SELECT {x_col} AS x, {y_col} AS y {series_col} {color_col}
            FROM source_data {sample_clause}
            {where_sql}
            WHERE {x_col} IS NOT NULL AND {y_col} IS NOT NULL
            LIMIT {max_points}
        """
        rows = self._fetch_dicts(conn, query, params)
        sampling = ChartSamplingMetadata(
            is_sampled=is_sampled,
            original_row_count=total_rows,
            displayed_points=len(rows),
            sampling_method="reservoir" if is_sampled else "exact",
        )
        return rows, sampling

    def _prepare_histogram(
        self,
        conn: duckdb.DuckDBPyConnection,
        spec: ChartSpec,
        where_sql: str,
        params: List[Any],
        total_rows: int,
    ) -> Tuple[List[Dict[str, Any]], ChartSamplingMetadata]:
        col = f'"{spec.x or spec.y}"'
        query = f"SELECT {col} FROM source_data {where_sql} WHERE {col} IS NOT NULL"
        vals = [r[0] for r in conn.execute(query, params).fetchall() if r[0] is not None]

        if not vals:
            return [], ChartSamplingMetadata(original_row_count=total_rows, displayed_points=0)

        counts, bin_edges = np.histogram(vals, bins=20)
        bins = []
        for i in range(len(counts)):
            bins.append({
                "x": f"{bin_edges[i]:.2f} - {bin_edges[i+1]:.2f}",
                "bin_start": float(bin_edges[i]),
                "bin_end": float(bin_edges[i+1]),
                "y": int(counts[i]),
                "count": int(counts[i]),
            })

        sampling = ChartSamplingMetadata(
            is_sampled=False,
            original_row_count=len(vals),
            displayed_points=len(bins),
            sampling_method="aggregation",
        )
        return bins, sampling

    def _prepare_boxplot(
        self,
        conn: duckdb.DuckDBPyConnection,
        spec: ChartSpec,
        where_sql: str,
        params: List[Any],
        total_rows: int,
    ) -> Tuple[List[Dict[str, Any]], ChartSamplingMetadata]:
        col = f'"{spec.y or spec.x}"'
        group_col = f'"{spec.x}"' if spec.x and spec.y else None

        if group_col:
            # Grouped box plot
            cat_query = f"SELECT DISTINCT {group_col} FROM source_data {where_sql} LIMIT 15"
            cats = [r[0] for r in conn.execute(cat_query, params).fetchall() if r[0] is not None]
            result = []
            for cat in cats:
                cat_params = list(params) + [cat]
                where_clause = f"{where_sql} {'AND' if where_sql else 'WHERE'} {group_col} = ? AND {col} IS NOT NULL"
                vals = [r[0] for r in conn.execute(f"SELECT {col} FROM source_data {where_clause}", cat_params).fetchall() if r[0] is not None]
                if vals:
                    q1, med, q3 = np.percentile(vals, [25, 50, 75])
                    result.append({
                        "x": str(cat),
                        "min": float(np.min(vals)),
                        "q1": float(q1),
                        "median": float(med),
                        "q3": float(q3),
                        "max": float(np.max(vals)),
                        "count": len(vals),
                    })
            return result, ChartSamplingMetadata(original_row_count=total_rows, displayed_points=len(result))
        else:
            # Single numeric box plot
            query = f"SELECT {col} FROM source_data {where_sql} WHERE {col} IS NOT NULL"
            vals = [r[0] for r in conn.execute(query, params).fetchall() if r[0] is not None]
            if not vals:
                return [], ChartSamplingMetadata(original_row_count=total_rows, displayed_points=0)

            q1, med, q3 = np.percentile(vals, [25, 50, 75])
            result = [{
                "x": spec.x or spec.y or "Overall",
                "min": float(np.min(vals)),
                "q1": float(q1),
                "median": float(med),
                "q3": float(q3),
                "max": float(np.max(vals)),
                "count": len(vals),
            }]
            return result, ChartSamplingMetadata(original_row_count=total_rows, displayed_points=1)

    def _prepare_heatmap(
        self,
        conn: duckdb.DuckDBPyConnection,
        spec: ChartSpec,
        where_sql: str,
        params: List[Any],
        total_rows: int,
    ) -> Tuple[List[Dict[str, Any]], ChartSamplingMetadata]:
        x_col = f'"{spec.x}"'
        y_col = f'"{spec.y}"'
        val_col = f'"{spec.color}"' if spec.color else None
        agg = f"SUM({val_col})" if val_col else "COUNT(*)"

        query = f"""
            SELECT {x_col} AS x, {y_col} AS y, {agg} AS value
            FROM source_data
            {where_sql}
            WHERE {x_col} IS NOT NULL AND {y_col} IS NOT NULL
            GROUP BY {x_col}, {y_col}
            ORDER BY x, y
            LIMIT 400
        """
        rows = self._fetch_dicts(conn, query, params)
        return rows, ChartSamplingMetadata(
            is_sampled=(len(rows) < total_rows),
            original_row_count=total_rows,
            displayed_points=len(rows),
            sampling_method="aggregation",
        )
