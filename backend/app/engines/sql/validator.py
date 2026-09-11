"""
AnalyzaX — Phase 8: SQL Security & Semantic Validator
Strictly enforces read-only access, AST validation, table/column resolution against
active dataset context, typo suggestions via Levenshtein distance, and performance warnings.
"""

import difflib
import re
from typing import List, Optional, Set

from backend.app.engines.sql.models import (
    SQLStatementType,
    SQLValidationError,
    SQLValidationResult,
    SQLValidationWarning,
)
from backend.app.engines.sql.parser import SQLParsedAst, SQLParser

# Blocked statement types and keywords
FORBIDDEN_KEYWORDS = {
    "INSERT",
    "UPDATE",
    "DELETE",
    "DROP",
    "ALTER",
    "CREATE",
    "TRUNCATE",
    "COPY",
    "ATTACH",
    "DETACH",
    "INSTALL",
    "LOAD",
    "CALL",
    "PRAGMA",
    "VACUUM",
    "EXPORT",
    "IMPORT",
    "PREPARE",
    "EXECUTE",
    "SET",
}

# Forbidden functions that bypass table isolation or attempt filesystem access
FORBIDDEN_FUNCTIONS = {
    "read_parquet",
    "read_csv",
    "read_json",
    "read_csv_auto",
    "scan_parquet",
    "scan_csv",
    "parquet_scan",
    "write_parquet",
    "write_csv",
    "copy_to",
    "httpfs",
    "load_extension",
    "install_extension",
}

# Forbidden system catalog tables and views
FORBIDDEN_TABLES = {
    "duckdb_tables",
    "duckdb_views",
    "duckdb_databases",
    "duckdb_extensions",
    "duckdb_settings",
    "duckdb_variables",
    "duckdb_types",
    "duckdb_columns",
    "duckdb_indexes",
    "information_schema",
    "sqlite_master",
    "pg_catalog",
}



class SQLValidator:
    """
    Validates SQL queries against security rules, allowed dialects,
    and schema definitions.
    """

    @classmethod
    def validate(
        cls,
        sql: str,
        valid_tables: Optional[List[str]] = None,
        valid_columns: Optional[List[str]] = None,
    ) -> SQLValidationResult:
        """
        Runs comprehensive security, AST, and semantic validation on a SQL query.
        """
        errors: List[SQLValidationError] = []
        warnings: List[SQLValidationWarning] = []
        suggestions: List[str] = []

        if not sql or not sql.strip():
            return SQLValidationResult(
                is_valid=False,
                statement_type=SQLStatementType.UNKNOWN,
                errors=[SQLValidationError(message="SQL query cannot be empty", error_code="EMPTY_QUERY")],
            )

        # 1. Quick lexical check for forbidden operations (defense-in-depth)
        clean_upper = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)
        clean_upper = re.sub(r"--.*$", "", clean_upper, flags=re.MULTILINE).upper()
        tokens = set(re.findall(r"\b[A-Z_]+\b", clean_upper))

        for kw in FORBIDDEN_KEYWORDS:
            if kw in tokens:
                errors.append(
                    SQLValidationError(
                        message=f"Operation '{kw}' is strictly prohibited. AnalyzaX SQL Studio is read-only.",
                        error_code="OPERATION_NOT_PERMITTED",
                    )
                )

        clean_lower = sql.lower()
        for fn in FORBIDDEN_FUNCTIONS:
            if f"{fn}(" in clean_lower or f"{fn} (" in clean_lower:
                errors.append(
                    SQLValidationError(
                        message=f"Direct file system or extension call '{fn}()' is not permitted. Please query registered dataset tables.",
                        error_code="SECURITY_VIOLATION",
                    )
                )

        if re.search(r"\bduckdb_[a-z0-9_]+\b", clean_lower):
            errors.append(
                SQLValidationError(
                    message="Access to internal database catalog functions or tables ('duckdb_*') is forbidden.",
                    error_code="CATALOG_ACCESS_FORBIDDEN",
                )
            )

        if re.search(r"\binformation_schema\b", clean_lower):
            errors.append(
                SQLValidationError(
                    message="Access to internal database catalog ('information_schema') is forbidden.",
                    error_code="CATALOG_ACCESS_FORBIDDEN",
                )
            )

        if errors:
            return SQLValidationResult(
                is_valid=False,
                statement_type=SQLStatementType.UNKNOWN,
                errors=errors,
            )

        # 2. Parse AST using SQLParser
        parsed_ast, parse_errors = SQLParser.parse(sql)
        if parse_errors:
            return SQLValidationResult(
                is_valid=False,
                statement_type=SQLStatementType.UNKNOWN,
                errors=parse_errors,
            )

        if not parsed_ast:
            return SQLValidationResult(
                is_valid=False,
                statement_type=SQLStatementType.UNKNOWN,
                errors=[SQLValidationError(message="Failed to parse SQL query", error_code="PARSE_FAILED")],
            )

        # Ensure statement type is permitted
        if parsed_ast.statement_type not in (SQLStatementType.SELECT, SQLStatementType.EXPLAIN):
            return SQLValidationResult(
                is_valid=False,
                statement_type=parsed_ast.statement_type,
                errors=[
                    SQLValidationError(
                        message=f"Statement type '{parsed_ast.statement_type}' is not permitted. Only SELECT and EXPLAIN queries are allowed.",
                        error_code="STATEMENT_NOT_ALLOWED",
                    )
                ],
            )

        # Check for forbidden system catalogs
        for tbl in parsed_ast.tables:
            tbl_clean = tbl.lower().strip('"\'`')
            if (
                tbl_clean in FORBIDDEN_TABLES
                or tbl_clean.startswith("duckdb_")
                or tbl_clean.startswith("information_schema")
            ):
                return SQLValidationResult(
                    is_valid=False,
                    statement_type=parsed_ast.statement_type,
                    errors=[
                        SQLValidationError(
                            message=f"Access to internal database catalog or system view '{tbl}' is forbidden.",
                            error_code="CATALOG_ACCESS_FORBIDDEN",
                        )
                    ],
                )

        # 3. Validate referenced tables if valid_tables provided
        if valid_tables:
            # Common CTE names or aliases defined in query might be captured as tables
            # Normalize valid table names to lower case
            valid_set = {t.lower() for t in valid_tables}
            valid_set.add("dataset")  # standard universal alias
            valid_set.add("current_dataset")  # legacy alias
            for tbl in parsed_ast.tables:
                if tbl.lower() not in valid_set:
                    # Find closest match
                    matches = difflib.get_close_matches(tbl.lower(), list(valid_set), n=1, cutoff=0.6)
                    hint = f" Did you mean '{matches[0]}'?" if matches else ""
                    warnings.append(
                        SQLValidationWarning(
                            message=f"Table '{tbl}' may not exist in the current dataset context.{hint}",
                            warning_code="UNKNOWN_TABLE",
                            suggestion=matches[0] if matches else None,
                        )
                    )

        # 4. Validate referenced columns if valid_columns provided
        if valid_columns:
            valid_cols_set = {c.lower() for c in valid_columns}
            for col in parsed_ast.columns:
                if col.lower() not in valid_cols_set:
                    matches = difflib.get_close_matches(col.lower(), list(valid_cols_set), n=1, cutoff=0.7)
                    if matches:
                        warnings.append(
                            SQLValidationWarning(
                                message=f"Column '{col}' not recognized in schema. Did you mean '{matches[0]}'?",
                                warning_code="COLUMN_TYPO",
                                suggestion=matches[0],
                            )
                        )
                        suggestions.append(f"Replace '{col}' with '{matches[0]}'")

        # 5. Performance / Complexity warnings
        if not parsed_ast.has_limit and not parsed_ast.is_explain:
            warnings.append(
                SQLValidationWarning(
                    message="Query does not specify a LIMIT clause. Default maximum result limit (up to 10,000 rows) will apply.",
                    warning_code="MISSING_LIMIT",
                    suggestion="Add 'LIMIT 100' or similar to control result set size",
                )
            )

        if parsed_ast.has_cartesian_join:
            warnings.append(
                SQLValidationWarning(
                    message="Potential Cartesian product (CROSS JOIN) detected without explicit ON condition.",
                    warning_code="CARTESIAN_PRODUCT",
                    suggestion="Verify JOIN condition or add an ON/USING clause",
                )
            )

        return SQLValidationResult(
            is_valid=True,
            statement_type=parsed_ast.statement_type,
            tables=parsed_ast.tables,
            columns=parsed_ast.columns,
            errors=[],
            warnings=warnings,
            suggestions=suggestions,
        )
