"""
Physical Data Type Extractor
Standardizes native DuckDB / Arrow data types into canonical physical types.
"""

def map_duckdb_physical_type(raw_type_str: str) -> str:
    """
    Normalizes a DuckDB SQL type string (e.g. 'BIGINT', 'VARCHAR', 'DOUBLE', 'DECIMAL(10,2)')
    into one of: integer, float, decimal, boolean, string, date, datetime, time, binary.
    """
    t = raw_type_str.strip().upper()
    if any(k in t for k in ("INT", "HUGEINT", "TINYINT", "SMALLINT", "UBIGINT", "UINTEGER")):
        return "integer"
    if any(k in t for k in ("DOUBLE", "FLOAT", "REAL")):
        return "float"
    if "DECIMAL" in t or "NUMERIC" in t:
        return "decimal"
    if "BOOL" in t:
        return "boolean"
    if "DATE" in t and "TIME" not in t:
        return "date"
    if "TIMESTAMP" in t or "DATETIME" in t:
        return "datetime"
    if "TIME" in t and "TIMESTAMP" not in t:
        return "time"
    if "BLOB" in t or "BINARY" in t or "BYTEA" in t:
        return "binary"
    return "string"
