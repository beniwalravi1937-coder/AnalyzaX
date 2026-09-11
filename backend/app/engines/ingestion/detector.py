import json
import os
import zipfile
from typing import Optional

from backend.app.core.config import settings
from backend.app.models.dataset import SupportedFormat


def detect_bytes_format(data: bytes, filename: str, mime_type: Optional[str] = None) -> str:
    """
    Validates in-memory dataset bytes against binary executables, script polyglots,
    and archive decompression bomb ceilings.
    """
    if not data or len(data) == 0:
        raise ValueError("Uploaded file is empty (0 bytes).")

    ext = os.path.splitext(filename)[1].lower().lstrip(".")

    # Prohibit dangerous script extensions
    DANGEROUS_EXTS = {"exe", "dll", "so", "dylib", "sh", "bat", "cmd", "ps1", "vbs", "php", "py", "rb", "js", "html", "htm", "svg"}
    if ext in DANGEROUS_EXTS:
        raise ValueError(f"Prohibited file extension: '.{ext}'. Executables and scripts are blocked.")

    header = data[:4096]

    # Reject executable binary headers and script polyglots
    if header.startswith(b"MZ"):  # Windows PE / DLL
        raise ValueError("Executable binaries (.exe, .dll) are strictly prohibited.")
    if header.startswith(b"\x7fELF"):  # Linux ELF
        raise ValueError("ELF binary executables are strictly prohibited.")
    if header.startswith((b"\xca\xfe\xba\xbe", b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe", b"\xfe\xed\xfa\xce", b"\xfe\xed\xfa\xcf")):  # Mach-O
        raise ValueError("Mach-O binary executables are strictly prohibited.")
    if header.startswith((b"#!/", b"eval(", b"<?php")):
        raise ValueError("Executable scripts are not valid tabular dataset files.")

    # 1. Parquet check: magic bytes 'PAR1' at start
    if header.startswith(b"PAR1"):
        return SupportedFormat.PARQUET.value

    # 2. XLSX / Zip check
    if header.startswith(b"PK\x03\x04"):
        try:
            import io
            with zipfile.ZipFile(io.BytesIO(data), "r") as zf:
                max_uncompressed_bytes = 500 * 1024 * 1024  # 500 MB ceiling
                total_uncompressed = sum(info.file_size for info in zf.infolist())
                total_compressed = sum(info.compress_size for info in zf.infolist())

                if total_uncompressed > max_uncompressed_bytes:
                    raise ValueError(
                        f"Decompression bomb rejected: uncompressed size ({total_uncompressed // (1024*1024)}MB) exceeds 500MB ceiling."
                    )
                if total_compressed > 0 and (total_uncompressed / total_compressed) > 100.0:
                    raise ValueError(
                        f"Decompression bomb rejected: abnormal compression ratio ({total_uncompressed / total_compressed:.1f}:1)."
                    )
                names = zf.namelist()
                if any("xl/workbook.xml" in name for name in names):
                    return SupportedFormat.XLSX.value
        except zipfile.BadZipFile:
            pass

    # 3. HTML / SVG script check
    try:
        sample_text = header.decode("utf-8", errors="ignore").strip()
        sample_lower = sample_text.lower()
        if sample_lower.startswith(("<html", "<!doctype html", "<svg", "<script")):
            raise ValueError("HTML or SVG files containing markup are not valid tabular datasets.")
    except ValueError:
        raise
    except Exception:
        pass

    if ext in ("csv", "tsv", "json", "parquet", "xlsx"):
        return ext

    return SupportedFormat.CSV.value


def detect_file_format(file_path: str, filename: str, mime_type: Optional[str] = None) -> str:
    """
    Determines and verifies the dataset format using a multi-factor check:
    1. Magic bytes & content signatures
    2. File extension
    3. MIME type inspection

    Returns one of the supported format strings: 'csv', 'xlsx', 'json', 'parquet'.
    Raises ValueError if format is unsupported or file content contradicts format.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    file_size = os.path.getsize(file_path)
    if file_size == 0:
        raise ValueError("Uploaded file is empty (0 bytes).")

    ext = os.path.splitext(filename)[1].lower().lstrip(".")

    # Read the first 4KB for content inspection
    with open(file_path, "rb") as f:
        header = f.read(4096)

    # Reject executable binary headers and script polyglots
    if header.startswith(b"MZ"):  # Windows PE / DLL
        raise ValueError("Executable binaries (.exe, .dll) are strictly prohibited.")
    if header.startswith(b"\x7fELF"):  # Linux ELF
        raise ValueError("ELF binary executables are strictly prohibited.")
    if header.startswith((b"\xca\xfe\xba\xbe", b"\xcf\xfa\xed\xfe", b"\xce\xfa\xed\xfe", b"\xfe\xed\xfa\xce", b"\xfe\xed\xfa\xcf")):  # Mach-O
        raise ValueError("Mach-O binary executables are strictly prohibited.")
    if header.startswith((b"#!/", b"eval(", b"<?php")):
        raise ValueError("Executable scripts are not valid tabular dataset files.")

    # 1. Parquet check: magic bytes 'PAR1' at start
    if header.startswith(b"PAR1"):
        return SupportedFormat.PARQUET.value

    # 2. XLSX check: Zip archive starting with PK\x03\x04
    if header.startswith(b"PK\x03\x04"):
        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                # Decompression bomb defense (Phase 24 / Req 28)
                max_uncompressed_bytes = 500 * 1024 * 1024  # 500 MB limit
                total_uncompressed = sum(info.file_size for info in zf.infolist())
                total_compressed = sum(info.compress_size for info in zf.infolist())

                if total_uncompressed > max_uncompressed_bytes:
                    raise ValueError(
                        f"Decompression bomb rejected: uncompressed size ({total_uncompressed // (1024*1024)}MB) exceeds 500MB ceiling."
                    )
                if total_compressed > 0 and (total_uncompressed / total_compressed) > 100.0:
                    raise ValueError(
                        f"Decompression bomb rejected: abnormal compression ratio ({total_uncompressed / total_compressed:.1f}:1)."
                    )

                # Check for workbook content indicator
                names = zf.namelist()
                if any("xl/workbook.xml" in name for name in names):
                    return SupportedFormat.XLSX.value
        except zipfile.BadZipFile:
            pass

    # 3. Text inspection: check for HTML/SVG script vectors
    try:
        sample_text = header.decode("utf-8", errors="ignore").strip()
        sample_lower = sample_text.lower()
        if sample_lower.startswith(("<html", "<!doctype html", "<svg", "<script")):
            raise ValueError("HTML or SVG files containing markup are not valid tabular datasets.")

        if sample_text.startswith(("[", "{")):
            # Attempt to parse as JSON or JSONL
            if ext in ("json", "jsonl") or (mime_type and "json" in mime_type):
                with open(file_path, "r", encoding="utf-8", errors="ignore") as jf:
                    first_char = jf.read(1)
                    jf.seek(0)
                    if first_char == "[":
                        data = json.load(jf)
                        if isinstance(data, list):
                            return SupportedFormat.JSON.value
                    elif first_char == "{":
                        line = jf.readline()
                        json.loads(line)
                        return SupportedFormat.JSON.value
    except ValueError:
        raise
    except Exception:
        pass

    # 4. CSV check: text based inspection
    try:
        sample_text = header.decode("utf-8", errors="replace")
        delimiters = [",", "\t", ";", "|"]
        has_delimiter = any(d in sample_text for d in delimiters)
        has_newlines = "\n" in sample_text or "\r" in sample_text

        if ext == "csv" or (has_delimiter and has_newlines):
            return SupportedFormat.CSV.value
    except Exception:
        pass

    # Fallback to extension if valid within supported formats
    if ext in settings.SUPPORTED_FORMATS:
        return ext


    raise ValueError(
        f"Unsupported file format: '{ext}'. AnalyzaX currently supports CSV, XLSX, JSON, and Parquet."
    )
