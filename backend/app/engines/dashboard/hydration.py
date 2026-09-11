"""
Component Hydration Engine for Phase 14 Dashboard.
Resolves bounded analytical data from existing deterministic engines (Phases 3–13).
Preserves analytical truth: strictly forbids ungrounded calculations in presentation layers.
"""

from datetime import datetime, timezone
import os
from typing import Any, Dict, List, Optional, Tuple
import duckdb

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.dashboard.models import (
    ComponentDataResponse,
    ComponentProvenance,
    ComponentStatus,
    ComponentType,
    DashboardComponent,
    DashboardFilter,
    FilterOperator,
)
from backend.app.engines.dashboard.security import DashboardSecurityValidator
from backend.app.engines.visualization.data_preparer import VisualizationDataPreparer
from backend.app.engines.visualization.models import ChartSpec, StructuredFilter


class DashboardHydrator:
    """
    Hydrates data for all dashboard component types deterministically.
    Delegates to source engines and enforces filter safety boundaries.
    """

    def __init__(self):
        self._viz_preparer = VisualizationDataPreparer()

    def hydrate_dashboard(
        self,
        components: List[DashboardComponent],
        active_dataset_id: str,
        active_version_id: str,
        global_filters: List[DashboardFilter],
        parquet_path: Optional[str] = None,
    ) -> Tuple[Dict[str, ComponentDataResponse], List[str], int]:
        """
        Hydrates all components in a dashboard.
        Returns:
            - component_data_map: Dict[component_id, ComponentDataResponse]
            - warnings: List[str]
            - stale_count: int
        """
        results: Dict[str, ComponentDataResponse] = {}
        warnings: List[str] = []
        stale_count = 0

        for cmp in components:
            try:
                # 1. Determine applicable filters for this component
                applicable_filters = self._resolve_filters_for_component(cmp, global_filters)

                # 2. Check stale version
                is_stale = False
                stale_reason = None
                if cmp.dataset_version_id and cmp.dataset_version_id != active_version_id:
                    is_stale = True
                    stale_reason = (
                        f"Component was configured against dataset version '{cmp.dataset_version_id}', "
                        f"but active version is '{active_version_id}'."
                    )
                    stale_count += 1
                    warnings.append(f"Component '{cmp.title}' (ID: {cmp.component_id}) references older dataset version.")

                # 3. Hydrate component data
                data_resp = self.hydrate_single_component(
                    component=cmp,
                    parquet_path=parquet_path,
                    filters=applicable_filters,
                    is_stale=is_stale,
                    stale_reason=stale_reason,
                )
                results[cmp.component_id] = data_resp

            except Exception as e:
                logger.error(f"Failed to hydrate component {cmp.component_id} ('{cmp.title}'): {e}", exc_info=True)
                results[cmp.component_id] = ComponentDataResponse(
                    component_id=cmp.component_id,
                    type=cmp.type,
                    status=ComponentStatus.ERROR,
                    error_message=f"Hydration failed: {str(e)}",
                    provenance=cmp.provenance,
                )
                warnings.append(f"Component '{cmp.title}' failed to load: {str(e)}")

        return results, warnings, stale_count

    def _resolve_filters_for_component(
        self,
        component: DashboardComponent,
        global_filters: List[DashboardFilter],
    ) -> List[DashboardFilter]:
        """
        Resolves active filters applicable to this specific component.
        """
        applicable: List[DashboardFilter] = []
        for flt in global_filters:
            if flt.scope.value == "GLOBAL":
                applicable.append(flt)
            elif flt.scope.value == "COMPONENT" and component.component_id in flt.component_ids:
                applicable.append(flt)
        return applicable

    def hydrate_single_component(
        self,
        component: DashboardComponent,
        parquet_path: Optional[str],
        filters: List[DashboardFilter],
        is_stale: bool = False,
        stale_reason: Optional[str] = None,
    ) -> ComponentDataResponse:
        """
        Hydrates an individual component based on its type.
        """
        status = ComponentStatus.STALE_VERSION if is_stale else ComponentStatus.READY
        requires_recomputation = False
        recomputation_reason = None
        data: Any = None

        has_active_filters = len(filters) > 0

        # Route by ComponentType
        if component.type == ComponentType.CHART:
            data = self._hydrate_chart(component, parquet_path, filters)

        elif component.type == ComponentType.TABLE:
            data = self._hydrate_table(component, parquet_path, filters)

        elif component.type == ComponentType.KPI:
            data = self._hydrate_kpi(component, parquet_path, filters)

        elif component.type == ComponentType.STATISTICS:
            data = component.result_reference or component.configuration.get("result", {})
            if has_active_filters:
                requires_recomputation = True
                recomputation_reason = (
                    "Filtering this view changes the analysis population. "
                    "Re-run analysis in the Statistics engine to update the statistical results."
                )

        elif component.type == ComponentType.ML_RESULT:
            data = component.result_reference or component.configuration.get("result", {})
            if has_active_filters:
                requires_recomputation = True
                recomputation_reason = (
                    "Model metrics represent the certified training/evaluation experiment. "
                    "Dashboard filters do not retrain or re-evaluate the model."
                )

        elif component.type == ComponentType.FORECAST:
            data = component.result_reference or component.configuration.get("result", {})
            if has_active_filters:
                requires_recomputation = True
                recomputation_reason = (
                    "Dashboard filters do not alter the generated forecast horizon. "
                    "Launch a new forecast job in Forecasting to update predictions."
                )

        elif component.type == ComponentType.EDA_FINDING:
            data = component.result_reference or component.configuration.get("finding", {})

        elif component.type == ComponentType.AI_INSIGHT:
            data = component.result_reference or component.configuration.get("insight", {})

        elif component.type == ComponentType.TEXT:
            raw_content = component.configuration.get("content", "")
            data = {"content": DashboardSecurityValidator.sanitize_text(str(raw_content))}

        elif component.type in (ComponentType.DIVIDER, ComponentType.SECTION):
            data = {"title": component.title, "subtitle": component.subtitle}

        else:
            data = component.configuration

        # Provenance
        prov = component.provenance or ComponentProvenance(
            dataset_id=component.dataset_id,
            dataset_version_id=component.dataset_version_id,
            source_engine=component.source.engine if component.source else "core",
            result_id=component.source.result_id if component.source else None,
            chart_id=component.source.chart_id if component.source else None,
            created_at=component.created_at,
            last_refreshed_at=datetime.now(timezone.utc),
            is_stale=is_stale,
            stale_reason=stale_reason,
        )

        return ComponentDataResponse(
            component_id=component.component_id,
            type=component.type,
            status=status,
            data=data,
            is_stale=is_stale,
            stale_reason=stale_reason,
            requires_recomputation=requires_recomputation,
            recomputation_reason=recomputation_reason,
            provenance=prov,
            refreshed_at=datetime.now(timezone.utc),
        )

    # ─────────────────────────────────────────────────────────
    # Component-Specific Hydrators
    # ─────────────────────────────────────────────────────────

    def _hydrate_chart(
        self,
        component: DashboardComponent,
        parquet_path: Optional[str],
        filters: List[DashboardFilter],
    ) -> Dict[str, Any]:
        """
        Hydrates chart data using Phase 9 ChartSpec and VisualizationDataPreparer.
        """
        spec_dict = component.visualization_reference or component.configuration.get("spec")
        if not spec_dict:
            return {"error": "Missing ChartSpec reference"}

        chart_spec = ChartSpec.model_validate(spec_dict)

        # Apply dashboard filters to ChartSpec if parquet path is available
        if parquet_path and os.path.exists(parquet_path):
            converted_filters: List[StructuredFilter] = []
            for flt in filters:
                converted_filters.append(
                    StructuredFilter(
                        field=flt.field,
                        operator=flt.operator.value,
                        value=flt.value,
                        value2=flt.value2,
                    )
                )
            # Combine spec's existing filters with dashboard filters
            chart_spec.filters = (chart_spec.filters or []) + converted_filters

            # Hydrate bounded data using Phase 9 data preparer
            hydrated_spec = self._viz_preparer.prepare_data(parquet_path, chart_spec)
            return hydrated_spec.model_dump()

        return chart_spec.model_dump()

    def _hydrate_table(
        self,
        component: DashboardComponent,
        parquet_path: Optional[str],
        filters: List[DashboardFilter],
    ) -> Dict[str, Any]:
        """
        Hydrates bounded table data directly from DuckDB parquet source with active filters applied.
        """
        if not parquet_path or not os.path.exists(parquet_path):
            # Fallback to static configuration rows if available
            return component.configuration.get("table_data", {"columns": [], "rows": [], "total_rows": 0})

        conn = duckdb.connect(":memory:")
        try:
            safe_path = parquet_path.replace("'", "''").replace("\\", "/")
            conn.execute(f"CREATE VIEW tbl AS SELECT * FROM read_parquet('{safe_path}')")

            # Build where clause
            where_clauses, params = self._build_where_clause(filters)
            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            # Count total matching rows
            total_count = conn.execute(f"SELECT COUNT(*) FROM tbl {where_sql}", params).fetchone()[0]

            # Fetch bounded rows
            limit = min(
                int(component.configuration.get("limit", 50)),
                settings.DASHBOARD_MAX_TABLE_ROWS,
            )
            sort_col = component.configuration.get("sort_by")
            sort_dir = component.configuration.get("sort_dir", "ASC").upper()
            order_sql = ""
            if sort_col:
                DashboardSecurityValidator.validate_field_identifier(sort_col)
                order_sql = f"ORDER BY \"{sort_col}\" { 'DESC' if sort_dir == 'DESC' else 'ASC' }"

            query = f"SELECT * FROM tbl {where_sql} {order_sql} LIMIT {limit}"
            rel = conn.execute(query, params)
            columns = [desc[0] for desc in rel.description]
            rows = [dict(zip(columns, row)) for row in rel.fetchall()]

            return {
                "columns": columns,
                "rows": rows,
                "total_rows": total_count,
                "returned_rows": len(rows),
                "truncated": total_count > len(rows),
            }
        finally:
            conn.close()

    def _hydrate_kpi(
        self,
        component: DashboardComponent,
        parquet_path: Optional[str],
        filters: List[DashboardFilter],
    ) -> Dict[str, Any]:
        """
        Hydrates KPI metric. Either scalar aggregation over parquet or structured metric reference.
        """
        metric = component.configuration.get("metric", "count").lower()
        column = component.configuration.get("column")
        formatting = component.configuration.get("formatting", "compact")
        comparison = component.configuration.get("comparison")

        # If static metric is supplied in configuration or result reference
        if "value" in component.configuration and not parquet_path:
            return {
                "metric": metric,
                "column": column,
                "value": component.configuration.get("value"),
                "formatting": formatting,
                "comparison": comparison,
            }

        if not parquet_path or not os.path.exists(parquet_path):
            val = component.result_reference.get("value") if component.result_reference else None
            return {
                "metric": metric,
                "column": column,
                "value": val,
                "formatting": formatting,
                "comparison": comparison,
            }

        conn = duckdb.connect(":memory:")
        try:
            safe_path = parquet_path.replace("'", "''").replace("\\", "/")
            conn.execute(f"CREATE VIEW tbl AS SELECT * FROM read_parquet('{safe_path}')")

            where_clauses, params = self._build_where_clause(filters)
            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            if metric == "count" and not column:
                sql_expr = "COUNT(*)"
            else:
                if not column:
                    return {"value": 0, "metric": metric, "error": "Column required for metric"}
                DashboardSecurityValidator.validate_field_identifier(column)
                safe_col = f'"{column}"'
                if metric == "sum":
                    sql_expr = f"SUM({safe_col})"
                elif metric == "avg" or metric == "average":
                    sql_expr = f"AVG({safe_col})"
                elif metric == "min":
                    sql_expr = f"MIN({safe_col})"
                elif metric == "max":
                    sql_expr = f"MAX({safe_col})"
                elif metric == "median":
                    sql_expr = f"MEDIAN({safe_col})"
                elif metric in ("distinct_count", "unique"):
                    sql_expr = f"COUNT(DISTINCT {safe_col})"
                else:
                    sql_expr = f"COUNT({safe_col})"

            query = f"SELECT {sql_expr} FROM tbl {where_sql}"
            row = conn.execute(query, params).fetchone()
            val = row[0] if row else 0

            return {
                "metric": metric,
                "column": column,
                "value": val,
                "formatting": formatting,
                "comparison": comparison,
            }
        finally:
            conn.close()

    def _build_where_clause(self, filters: List[DashboardFilter]) -> Tuple[List[str], List[Any]]:
        """
        Builds safe parameterized SQL where clauses from DashboardFilter objects.
        """
        clauses: List[str] = []
        params: List[Any] = []

        for flt in filters:
            DashboardSecurityValidator.validate_field_identifier(flt.field)
            col_sql = f'"{flt.field}"'
            op = flt.operator

            if op == FilterOperator.EQUALS:
                clauses.append(f"{col_sql} = ?")
                params.append(flt.value)
            elif op == FilterOperator.NOT_EQUALS:
                clauses.append(f"{col_sql} != ?")
                params.append(flt.value)
            elif op == FilterOperator.GREATER_THAN:
                clauses.append(f"{col_sql} > ?")
                params.append(flt.value)
            elif op == FilterOperator.GREATER_THAN_OR_EQUAL:
                clauses.append(f"{col_sql} >= ?")
                params.append(flt.value)
            elif op == FilterOperator.LESS_THAN:
                clauses.append(f"{col_sql} < ?")
                params.append(flt.value)
            elif op == FilterOperator.LESS_THAN_OR_EQUAL:
                clauses.append(f"{col_sql} <= ?")
                params.append(flt.value)
            elif op == FilterOperator.IN:
                if isinstance(flt.value, (list, tuple)) and len(flt.value) > 0:
                    placeholders = ", ".join(["?"] * len(flt.value))
                    clauses.append(f"{col_sql} IN ({placeholders})")
                    params.extend(flt.value)
            elif op == FilterOperator.NOT_IN:
                if isinstance(flt.value, (list, tuple)) and len(flt.value) > 0:
                    placeholders = ", ".join(["?"] * len(flt.value))
                    clauses.append(f"{col_sql} NOT IN ({placeholders})")
                    params.extend(flt.value)
            elif op == FilterOperator.BETWEEN:
                if flt.value is not None and flt.value2 is not None:
                    clauses.append(f"{col_sql} BETWEEN ? AND ?")
                    params.extend([flt.value, flt.value2])
            elif op == FilterOperator.CONTAINS:
                clauses.append(f"CAST({col_sql} AS VARCHAR) LIKE ?")
                params.append(f"%{flt.value}%")
            elif op == FilterOperator.STARTS_WITH:
                clauses.append(f"CAST({col_sql} AS VARCHAR) LIKE ?")
                params.append(f"{flt.value}%")
            elif op == FilterOperator.IS_NULL:
                clauses.append(f"{col_sql} IS NULL")
            elif op == FilterOperator.IS_NOT_NULL:
                clauses.append(f"{col_sql} IS NOT NULL")

        return clauses, params
