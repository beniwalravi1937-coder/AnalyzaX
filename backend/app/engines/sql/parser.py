"""
AnalyzaX — Phase 8: SQL Parser & AST Inspector
Performs dual-layer AST extraction using DuckDB's native parser and sqlglot
to identify statement types, referenced identifiers, joins, and syntax errors.
"""

from typing import List, Optional, Set, Tuple
import duckdb
import sqlglot
from sqlglot import exp

from backend.app.engines.sql.models import SQLStatementType, SQLValidationError


class SQLParsedAst:
    """Holds parsed metadata extracted from an AST."""

    def __init__(
        self,
        raw_sql: str,
        statement_type: SQLStatementType,
        statement_count: int,
        tables: List[str],
        columns: List[str],
        has_cartesian_join: bool = False,
        has_limit: bool = False,
        limit_value: Optional[int] = None,
        is_explain: bool = False,
        ast_expression: Optional[exp.Expression] = None,
    ):
        self.raw_sql = raw_sql
        self.statement_type = statement_type
        self.statement_count = statement_count
        self.tables = tables
        self.columns = columns
        self.has_cartesian_join = has_cartesian_join
        self.has_limit = has_limit
        self.limit_value = limit_value
        self.is_explain = is_explain
        self.ast_expression = ast_expression


class SQLParser:
    """
    Parses and inspects SQL statements with deep AST tree analysis.
    """

    @classmethod
    def parse(cls, sql: str) -> Tuple[Optional[SQLParsedAst], List[SQLValidationError]]:
        """
        Parses SQL string and returns parsed AST metadata or validation errors.
        """
        errors: List[SQLValidationError] = []
        if not sql or not sql.strip():
            return None, [SQLValidationError(message="SQL query cannot be empty", error_code="EMPTY_QUERY")]

        clean_sql = sql.strip()

        # Step 1: DuckDB native statement extraction
        try:
            temp_conn = duckdb.connect()
            duck_stmts = temp_conn.extract_statements(clean_sql)
            stmt_count = len(duck_stmts)

            if stmt_count == 0:
                return None, [SQLValidationError(message="No executable SQL statements found", error_code="EMPTY_QUERY")]

            if stmt_count > 1:
                return None, [
                    SQLValidationError(
                        message=f"Multiple SQL statements detected ({stmt_count}). Only single read-only statements are permitted.",
                        error_code="MULTIPLE_STATEMENTS",
                    )
                ]

            first_stmt = duck_stmts[0]
            stmt_type_str = str(first_stmt.type).replace("StatementType.", "")

        except Exception as e:
            err_msg = str(e)
            line_no = None
            col_no = None
            # Attempt to extract line and column numbers from DuckDB error
            if "LINE " in err_msg:
                try:
                    parts = err_msg.split("LINE ")[1].split(":")[0]
                    line_no = int(parts.strip())
                except Exception:
                    pass
            return None, [SQLValidationError(message=err_msg, line=line_no, column=col_no, error_code="SYNTAX_ERROR")]

        # Step 2: Map statement type
        is_explain = False
        if stmt_type_str == "SELECT":
            stmt_type = SQLStatementType.SELECT
        elif stmt_type_str == "EXPLAIN":
            stmt_type = SQLStatementType.EXPLAIN
            is_explain = True
        else:
            stmt_type = SQLStatementType.UNKNOWN

        # Step 3: sqlglot AST parsing for detailed inspection
        tables: Set[str] = set()
        columns: Set[str] = set()
        has_cartesian = False
        has_limit = False
        limit_val = None
        parsed_tree = None

        try:
            # Parse using DuckDB dialect
            parsed_expressions = sqlglot.parse(clean_sql, read="duckdb")
            if parsed_expressions:
                parsed_tree = parsed_expressions[0]

                # Check if EXPLAIN wrapped
                if clean_sql.upper().startswith("EXPLAIN") or getattr(parsed_tree, "key", "") == "explain":
                    is_explain = True
                    stmt_type = SQLStatementType.EXPLAIN

                # Extract Tables
                for table_exp in parsed_tree.find_all(exp.Table):
                    tbl_name = table_exp.name
                    if tbl_name and not tbl_name.startswith("_"):
                        tables.add(tbl_name)

                # Extract Columns
                for col_exp in parsed_tree.find_all(exp.Column):
                    col_name = col_exp.name
                    if col_name and col_name != "*":
                        columns.add(col_name)

                # Detect LIMIT clause
                limit_exp = parsed_tree.find(exp.Limit)
                if limit_exp:
                    has_limit = True
                    try:
                        limit_val = int(limit_exp.expression.this)
                    except Exception:
                        pass

                # Detect Cartesian joins (cross joins or comma joins without ON/WHERE conditions)
                for join_exp in parsed_tree.find_all(exp.Join):
                    kind = str(join_exp.kind or "").upper()
                    on_clause = join_exp.args.get("on")
                    using_clause = join_exp.args.get("using")
                    if "CROSS" in kind or (not on_clause and not using_clause):
                        has_cartesian = True

        except Exception as e:
            # If sqlglot fails but DuckDB succeeded, log and proceed with DuckDB baseline
            pass

        parsed_ast = SQLParsedAst(
            raw_sql=clean_sql,
            statement_type=stmt_type,
            statement_count=stmt_count,
            tables=sorted(list(tables)),
            columns=sorted(list(columns)),
            has_cartesian_join=has_cartesian,
            has_limit=has_limit,
            limit_value=limit_val,
            is_explain=is_explain,
            ast_expression=parsed_tree,
        )

        return parsed_ast, errors
