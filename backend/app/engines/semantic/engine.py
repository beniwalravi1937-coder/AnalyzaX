"""
AnalyzaX — Phase 25: Semantic Intelligence Engine.
Coordinates natural language term resolution, semantic ambiguity detection,
and deterministic metric calculations over DuckDB.
"""

import difflib
import time
from typing import Any, Dict, List, Optional, Tuple

from backend.app.core.logging import logger
from backend.app.engines.semantic.models import (
    MetricCalculationResult,
    MetricDefinition,
    MetricStatus,
)
from backend.app.engines.semantic.repository import SemanticRepository, semantic_repo
from backend.app.engines.sql.executor import SQLExecutor


class SemanticEngine:
    """Natural language metric resolution and deterministic metric evaluation engine."""

    def __init__(self, repository: Optional[SemanticRepository] = None) -> None:
        self._repo = repository or semantic_repo

    def resolve_term(
        self,
        query_term: str,
        workspace_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Tuple[Optional[MetricDefinition], List[MetricDefinition], bool]:
        """
        Resolves a user's natural language phrase to a governed metric.
        Returns: (resolved_metric, candidate_list, is_ambiguous)
        """
        if not query_term or not query_term.strip():
            return None, [], False

        clean_term = query_term.lower().strip()
        metrics = self._repo.list_metrics(workspace_id=workspace_id, project_id=project_id, status=MetricStatus.ACTIVE)

        # 1. Exact match on metric name or synonym
        for m in metrics:
            if m.name.lower().strip() == clean_term:
                return m, [m], False
            if any(syn.lower().strip() == clean_term for syn in m.synonyms):
                return m, [m], False

        # 2. Substring match
        substring_matches: List[MetricDefinition] = []
        for m in metrics:
            if clean_term in m.name.lower():
                substring_matches.append(m)
            elif any(clean_term in syn.lower() for syn in m.synonyms):
                substring_matches.append(m)

        if len(substring_matches) == 1:
            return substring_matches[0], substring_matches, False
        if len(substring_matches) > 1:
            # Ambiguity detected! e.g., 'margin' matches 'Gross Margin' and 'Net Margin'
            return None, substring_matches, True

        # 3. Fuzzy match fallback
        candidates: List[Tuple[float, MetricDefinition]] = []
        for m in metrics:
            all_names = [m.name] + m.synonyms
            best_ratio = max(difflib.SequenceMatcher(None, clean_term, n.lower()).ratio() for n in all_names)
            if best_ratio >= 0.70:
                candidates.append((best_ratio, m))

        if not candidates:
            return None, [], False

        candidates.sort(key=lambda x: x[0], reverse=True)
        if len(candidates) > 1 and (candidates[0][0] - candidates[1][0]) < 0.10:
            # Two metrics are almost equally close -> ambiguous
            return None, [c[1] for c in candidates[:3]], True

        return candidates[0][1], [c[1] for c in candidates], False

    @classmethod
    def detect_ambiguity(
        cls,
        query_text: str,
        metrics: Optional[List[MetricDefinition]] = None,
    ) -> List[MetricDefinition]:
        if not metrics:
            return []
        clean_text = query_text.lower()
        matched: List[MetricDefinition] = []
        for m in metrics:
            all_names = [m.name.lower()] + [s.lower() for s in m.synonyms]
            for n in all_names:
                if n in clean_text or any(word in clean_text.split() for word in n.split()):
                    matched.append(m)
                    break
        return matched if len(matched) > 1 else []

    @classmethod
    def resolve_term(
        cls,
        query_term: str,
        metrics: Optional[List[MetricDefinition]] = None,
        workspace_id: Optional[str] = None,
        project_id: Optional[str] = None,
    ) -> Optional[MetricDefinition]:
        if metrics:
            clean = query_term.lower().strip()
            for m in metrics:
                if m.name.lower().strip() == clean or any(s.lower().strip() == clean for s in m.synonyms):
                    return m
                if clean in m.name.lower() or any(clean in s.lower() for s in m.synonyms):
                    return m
            return None
        res, _, _ = semantic_engine.resolve_term(query_term, workspace_id, project_id)
        return res

    @classmethod
    def calculate_metric(
        cls,
        metric: MetricDefinition,
        storage_path: Optional[str] = None,
        dataset_id: str = "default",
        version_id: str = "v1",
        dimension_breakdown: Optional[str] = None,
        filter_clause: Optional[str] = None,
        dataset_path: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None,
    ) -> MetricCalculationResult:
        """
        Deterministically evaluates a governed metric expression over the target dataset Parquet file.
        """
        start_time = time.perf_counter()
        actual_path = dataset_path or storage_path or ""

        # Build execution SQL
        expr = metric.expression.strip()
        where_parts: List[str] = []
        if metric.filters:
            where_parts.append(f"({metric.filters})")
        if filter_clause:
            where_parts.append(f"({filter_clause})")

        where_str = f" WHERE {' AND '.join(where_parts)}" if where_parts else ""

        if dimension_breakdown:
            dim = dimension_breakdown.strip()
            sql = f"SELECT {dim}, {expr} AS metric_value FROM dataset{where_str} GROUP BY {dim} ORDER BY metric_value DESC LIMIT 100;"
        else:
            sql = f"SELECT {expr} AS metric_value FROM dataset{where_str};"

        try:
            exec_res = SQLExecutor.execute(
                sql=sql,
                storage_path=actual_path,
                dataset_id=dataset_id,
                version_id=version_id,
            )

            execution_ms = round((time.perf_counter() - start_time) * 1000, 2)

            if exec_res.status.value != "COMPLETED":
                logger.error(f"Metric calculation failed: {exec_res.error_message}")
                return MetricCalculationResult(
                    metric_id=metric.metric_id,
                    metric_name=metric.name,
                    value=None,
                    execution_time_ms=execution_ms,
                    sql_executed=sql,
                )

            if dimension_breakdown:
                breakdown = exec_res.rows
                return MetricCalculationResult(
                    metric_id=metric.metric_id,
                    metric_name=metric.name,
                    unit=metric.unit,
                    format=metric.format,
                    breakdown=breakdown,
                    rows_scanned=exec_res.scanned_rows,
                    sql_executed=sql,
                    execution_time_ms=execution_ms,
                )
            else:
                val = None
                if exec_res.rows and "metric_value" in exec_res.rows[0]:
                    raw_val = exec_res.rows[0]["metric_value"]
                    if raw_val is not None:
                        try:
                            val = float(raw_val)
                        except (ValueError, TypeError):
                            val = None

                # Format value based on metric format
                formatted = None
                if val is not None:
                    if metric.format == "currency":
                        formatted = f"${val:,.2f}"
                    elif metric.format == "percentage":
                        formatted = f"{val:.2f}%"
                    elif metric.format == "integer":
                        formatted = f"{int(val):,}"
                    else:
                        formatted = f"{val:,.2f}"

                return MetricCalculationResult(
                    metric_id=metric.metric_id,
                    metric_name=metric.name,
                    value=val,
                    formatted_value=formatted,
                    unit=metric.unit,
                    rows_scanned=exec_res.scanned_rows,
                    sql_executed=sql,
                    execution_time_ms=execution_ms,
                )

        except Exception as e:
            logger.error(f"Unexpected error calculating metric '{metric.name}': {e}")
            return MetricCalculationResult(
                metric_id=metric.metric_id,
                metric_name=metric.name,
                value=None,
                execution_time_ms=round((time.perf_counter() - start_time) * 1000, 2),
                sql_executed=sql,
            )


semantic_engine = SemanticEngine()
