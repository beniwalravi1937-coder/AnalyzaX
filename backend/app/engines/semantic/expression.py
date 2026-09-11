"""
AnalyzaX — Phase 25: Metric Expression Safety Engine.
Constrained AST validation preventing arbitrary code execution, SQL injections,
or circular dependencies in governed metric definitions.
"""

import re
from typing import Dict, List, Optional, Set
import sqlglot
from sqlglot import exp

from backend.app.engines.semantic.models import MetricValidationResult


ALLOWLISTED_FUNCTIONS: Set[str] = {
    "SUM",
    "AVG",
    "COUNT",
    "MIN",
    "MAX",
    "ROUND",
    "ABS",
    "COALESCE",
    "NULLIF",
    "FLOOR",
    "CEIL",
    "SQRT",
    "POWER",
}

FORBIDDEN_PATTERNS = [
    r";",
    r"--",
    r"/\*",
    r"\beval\b",
    r"\bexec\b",
    r"\bimport\b",
    r"\b__\w+__\b",
    r"\bdrop\b",
    r"\bdelete\b",
    r"\binsert\b",
    r"\bupdate\b",
    r"\balter\b",
    r"\bcreate\b",
    r"\btruncate\b",
    r"\battach\b",
    r"\bdetach\b",
    r"\bread_parquet\b",
    r"\bread_csv\b",
    r"\bduckdb_\w+\b",
    r"\binformation_schema\b",
]


class MetricExpressionValidator:
    """Validates metric formulas and expressions using safe AST parsing."""

    @classmethod
    def validate_expression(
        cls,
        expression: str,
        available_columns: Optional[List[str]] = None,
        existing_metrics: Optional[Dict[str, List[str]]] = None,  # metric_name -> list of dependent metric names
        current_metric_name: Optional[str] = None,
    ) -> MetricValidationResult:
        """
        Parses and validates a metric expression against allowlists and dependency rules.
        """
        if not expression or not expression.strip():
            return MetricValidationResult(
                is_valid=False,
                error_message="Expression cannot be empty.",
            )

        clean_expr = expression.strip()

        # 1. Lexical security check against injection and code execution
        for pattern in FORBIDDEN_PATTERNS:
            if re.search(pattern, clean_expr, re.IGNORECASE):
                return MetricValidationResult(
                    is_valid=False,
                    error_message=f"Expression contains forbidden token or pattern matching '{pattern}'.",
                )

        # 2. Parse using sqlglot (DuckDB dialect)
        try:
            # Wrap in SELECT to parse expression in context
            parsed_query = sqlglot.parse_one(f"SELECT {clean_expr} AS metric_val", read="duckdb")
        except Exception as e:
            return MetricValidationResult(
                is_valid=False,
                error_message=f"Syntax error in expression: {str(e)}",
            )

        # 3. Extract functions and validate against allowlist
        used_functions: List[str] = []
        for func in parsed_query.find_all(exp.Func):
            func_name = func.key.upper()
            used_functions.append(func_name)
            # Allow standard CASE expressions
            if func_name in ("CASE", "WHEN", "THEN", "ELSE", "IF"):
                continue
            if func_name not in ALLOWLISTED_FUNCTIONS:
                return MetricValidationResult(
                    is_valid=False,
                    error_message=f"Function '{func_name}' is not in the approved metric function allowlist.",
                    parsed_functions=used_functions,
                )

        # 4. Extract referenced columns / identifiers
        referenced_identifiers: Set[str] = set()
        for col in parsed_query.find_all(exp.Column):
            name = col.name
            if name and name.lower() != "metric_val":
                referenced_identifiers.add(name)

        # Check against available dataset columns if provided
        cols_list = sorted(list(referenced_identifiers))
        if available_columns:
            avail_set = {c.lower() for c in available_columns}
            # Allow matching either an available column or a known metric name
            known_metrics = {m.lower() for m in (existing_metrics or {}).keys()}
            for identifier in cols_list:
                if identifier.lower() not in avail_set and identifier.lower() not in known_metrics:
                    return MetricValidationResult(
                        is_valid=False,
                        error_message=f"Identifier '{identifier}' is not a valid dataset column or known metric.",
                        parsed_columns=cols_list,
                        parsed_functions=used_functions,
                    )

        # 5. Cycle Detection in Nested Metric Dependencies
        dependencies = cols_list
        if existing_metrics and current_metric_name:
            curr_lower = current_metric_name.lower().strip()
            visited: Set[str] = set()
            stack: Set[str] = {curr_lower}

            def has_cycle_dfs(node: str) -> bool:
                visited.add(node)
                stack.add(node)
                neighbors = temp_graph.get(node, [])
                for neighbor in neighbors:
                    neigh_lower = neighbor.lower().strip()
                    if neigh_lower not in visited:
                        if has_cycle_dfs(neigh_lower):
                            return True
                    elif neigh_lower in stack:
                        return True
                stack.remove(node)
                return False

            # Simulate adding this metric's dependencies
            temp_graph = {k.lower().strip(): [d.lower().strip() for d in v] for k, v in existing_metrics.items()}
            temp_graph[curr_lower] = [d.lower().strip() for d in dependencies]

            for node in temp_graph:
                if node not in visited:
                    if has_cycle_dfs(node):
                        return MetricValidationResult(
                            is_valid=False,
                            error_message=f"Circular dependency detected involving metric '{current_metric_name}'.",
                            parsed_columns=cols_list,
                            parsed_functions=used_functions,
                            dependencies=dependencies,
                            has_cycle=True,
                        )

        return MetricValidationResult(
            is_valid=True,
            parsed_columns=cols_list,
            parsed_functions=sorted(list(set(used_functions))),
            dependencies=dependencies,
            has_cycle=False,
        )


MetricExpressionParser = MetricExpressionValidator
