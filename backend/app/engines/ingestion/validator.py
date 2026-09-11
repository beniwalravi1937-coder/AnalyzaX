import csv
import json
import os
from typing import Any, Dict, Optional


def validate_csv(file_path: str) -> Dict[str, Any]:
    """
    Validates CSV file readability, detects delimiter and encoding.
    Ensures file is tabular and not corrupt.
    """
    # Detect encoding
    encoding = "utf-8"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            sample = f.read(8192)
    except UnicodeDecodeError:
        encoding = "latin-1"
        with open(file_path, "r", encoding="latin-1") as f:
            sample = f.read(8192)

    if not sample.strip():
        raise ValueError("CSV file is empty.")

    # Detect delimiter
    try:
        sniffer = csv.Sniffer()
        dialect = sniffer.sniff(sample, delimiters=[",", ";", "\t", "|"])
        delimiter = dialect.delimiter
        has_header = sniffer.has_header(sample)
    except Exception:
        # Fallback to comma delimiter
        delimiter = ","
        has_header = True

    # Validate that at least one row can be parsed
    with open(file_path, "r", encoding=encoding, errors="replace") as f:
        reader = csv.reader(f, delimiter=delimiter)
        try:
            first_row = next(reader)
            if not first_row or len(first_row) == 0:
                raise ValueError("CSV file contains no valid columns.")
        except StopIteration:
            raise ValueError("CSV file contains no rows.")

    return {
        "format": "csv",
        "encoding": encoding,
        "delimiter": delimiter,
        "has_header": has_header,
        "column_count_estimate": len(first_row),
    }


def validate_parquet(file_path: str) -> Dict[str, Any]:
    """
    Validates that a Parquet file can be read and contains valid tabular metadata.
    """
    try:
        import pyarrow.parquet as pq

        parquet_file = pq.ParquetFile(file_path)
        schema = parquet_file.schema_arrow
        if len(schema) == 0:
            raise ValueError("Parquet file contains no columns.")

        num_row_groups = parquet_file.num_row_groups
        return {
            "format": "parquet",
            "columns": [field.name for field in schema],
            "column_count": len(schema),
            "num_row_groups": num_row_groups,
        }
    except ImportError:
        # Fallback using DuckDB directly
        import duckdb

        conn = duckdb.connect()
        try:
            rel = conn.execute(f"DESCRIBE SELECT * FROM read_parquet('{file_path.replace(os.sep, '/')}')").fetchall()
            if not rel or len(rel) == 0:
                raise ValueError("Parquet file contains no columns.")
            return {
                "format": "parquet",
                "column_count": len(rel),
            }
        finally:
            conn.close()
    except Exception as e:
        raise ValueError(f"Unable to parse Parquet file: {str(e)}")


def validate_json(file_path: str) -> Dict[str, Any]:
    """
    Validates that JSON file contains a tabular structure (array of objects or JSON lines).
    Rejects nested non-tabular JSON or scalar values cleanly.
    """
    with open(file_path, "r", encoding="utf-8", errors="replace") as f:
        first_char = f.read(1).strip()
        f.seek(0)

        if first_char == "[":
            # Array of objects
            try:
                data = json.load(f)
            except json.JSONDecodeError as e:
                raise ValueError(f"Malformed JSON: {str(e)}")

            if not isinstance(data, list):
                raise ValueError("Top-level JSON structure must be an array of tabular objects.")
            if len(data) == 0:
                raise ValueError("JSON array is empty.")
            if not isinstance(data[0], dict):
                raise ValueError("JSON array elements must be objects (key-value pairs) to be tabular.")

            columns = list(data[0].keys())
            return {
                "format": "json",
                "structure": "array_of_objects",
                "column_count": len(columns),
                "columns": columns,
            }
        else:
            # Check for NDJSON / JSON Lines
            first_line = f.readline().strip()
            try:
                obj = json.loads(first_line)
                if not isinstance(obj, dict):
                    raise ValueError("JSON lines must contain JSON objects.")
                columns = list(obj.keys())
                return {
                    "format": "json",
                    "structure": "json_lines",
                    "column_count": len(columns),
                    "columns": columns,
                }
            except json.JSONDecodeError:
                raise ValueError("JSON file does not contain a valid tabular array or newline-delimited JSON objects.")


def validate_xlsx(file_path: str) -> Dict[str, Any]:
    """
    Validates Excel workbook (.xlsx), lists worksheets, and identifies the default sheet.
    """
    try:
        import openpyxl

        wb = openpyxl.load_workbook(file_path, read_only=True, data_only=True)
        sheet_names = wb.sheetnames
        if not sheet_names:
            raise ValueError("Excel workbook contains no sheets.")

        # Default to first active sheet
        selected_sheet = sheet_names[0]
        ws = wb[selected_sheet]

        # Inspect first row
        first_row = next(ws.iter_rows(values_only=True), None)
        if not first_row or all(cell is None for cell in first_row):
            raise ValueError(f"Worksheet '{selected_sheet}' contains no tabular header or data.")

        wb.close()
        return {
            "format": "xlsx",
            "sheet_names": sheet_names,
            "selected_sheet": selected_sheet,
            "column_count_estimate": len([c for c in first_row if c is not None]),
        }
    except Exception as e:
        raise ValueError(f"Unable to parse Excel workbook: {str(e)}")


def validate_dataset_content(file_path: str, format_str: str) -> Dict[str, Any]:
    """
    Top-level content validator dispatching to the appropriate format validator.
    """
    if format_str == "csv":
        return validate_csv(file_path)
    elif format_str == "parquet":
        return validate_parquet(file_path)
    elif format_str == "json":
        return validate_json(file_path)
    elif format_str == "xlsx":
        return validate_xlsx(file_path)
    else:
        raise ValueError(f"Validation for format '{format_str}' is not supported.")
