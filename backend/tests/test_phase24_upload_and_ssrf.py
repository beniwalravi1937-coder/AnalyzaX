"""
AnalyzaX — Phase 24 Tests: Upload File Validation, Executable Rejection, Decompression Bomb & SSRF Guard.
"""

import io
import zipfile
import pytest

from backend.app.engines.ingestion.detector import detect_bytes_format
from backend.app.engines.security.ssrf_guard import ssrf_guard


def test_upload_detector_rejects_binary_executables_and_scripts():
    # 1. Windows PE Executable (MZ header)
    pe_bytes = b"MZ\x90\x00\x03\x00\x00\x00\x04\x00\x00\x00\xff\xff\x00\x00" + b"\x00" * 100
    with pytest.raises(ValueError) as pe_err:
        detect_bytes_format(pe_bytes, "payload.csv")
    assert "executable" in str(pe_err.value).lower() or "blocked" in str(pe_err.value).lower()

    # 2. Linux ELF Executable
    elf_bytes = b"\x7fELF\x02\x01\x01\x00\x00\x00\x00\x00\x00\x00\x00\x00" + b"\x00" * 100
    with pytest.raises(ValueError) as elf_err:
        detect_bytes_format(elf_bytes, "dataset.tsv")
    assert "executable" in str(elf_err.value).lower() or "blocked" in str(elf_err.value).lower()

    # 3. Mach-O Executable
    macho_bytes = b"\xfe\xed\xfa\xce\x00\x00\x00\x00" + b"\x00" * 100
    with pytest.raises(ValueError) as macho_err:
        detect_bytes_format(macho_bytes, "data.parquet")
    assert "executable" in str(macho_err.value).lower() or "blocked" in str(macho_err.value).lower()

    # 4. Dangerous script extension
    safe_text = b"id,name\n1,Alice\n2,Bob"
    with pytest.raises(ValueError) as ext_err:
        detect_bytes_format(safe_text, "exploit.exe")
    assert "prohibited" in str(ext_err.value).lower() or "blocked" in str(ext_err.value).lower()

    # 5. HTML/SVG Script injection polyglot
    html_script = b"<html><head><script>alert('XSS')</script></head><body>id,val\n1,2</body></html>"
    with pytest.raises(ValueError) as html_err:
        detect_bytes_format(html_script, "polyglot.csv")
    assert "script" in str(html_err.value).lower() or "blocked" in str(html_err.value).lower() or "markup" in str(html_err.value).lower()


def test_upload_detector_rejects_decompression_bombs():
    # Construct an in-memory zip archive with extreme compression ratio
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        # 20MB of zeros compresses down to a few kilobytes (> 1000:1 ratio)
        zf.writestr("huge_sparse.csv", b"0" * (20 * 1024 * 1024))

    zip_bytes = zip_buffer.getvalue()
    with pytest.raises(ValueError) as bomb_err:
        detect_bytes_format(zip_bytes, "archive.zip")
    assert "decompression bomb" in str(bomb_err.value).lower() or "ratio" in str(bomb_err.value).lower() or "blocked" in str(bomb_err.value).lower()


def test_ssrf_guard_blocks_private_and_cloud_metadata_ips():
    # 1. Loopback addresses
    assert ssrf_guard.is_safe_url("http://127.0.0.1/data.csv") is False
    assert ssrf_guard.is_safe_url("http://127.0.0.2:8000/metrics") is False
    assert ssrf_guard.is_safe_url("http://localhost:8080/data") is False

    # 2. RFC 1918 Private subnets
    assert ssrf_guard.is_safe_url("http://10.0.0.1/data.csv") is False
    assert ssrf_guard.is_safe_url("http://172.16.10.20/export.parquet") is False
    assert ssrf_guard.is_safe_url("http://192.168.1.1/admin") is False

    # 3. AWS / GCP / Azure Cloud Metadata IP (169.254.169.254)
    assert ssrf_guard.is_safe_url("http://169.254.169.254/latest/meta-data/") is False
    assert ssrf_guard.is_safe_url("http://169.254.10.5/secrets") is False

    # 4. Dangerous non-HTTP schemes
    assert ssrf_guard.is_safe_url("file:///etc/passwd") is False
    assert ssrf_guard.is_safe_url("ftp://example.com/dataset.csv") is False
    assert ssrf_guard.is_safe_url("gopher://evil.com/1") is False

    # 5. IPv6 Loopback & Link-local
    assert ssrf_guard.is_safe_url("http://[::1]/data.csv") is False
    assert ssrf_guard.is_safe_url("http://[fe80::1]/data.csv") is False

    # 6. Validate URL raises exception on unsafe target
    with pytest.raises(ValueError) as exc:
        ssrf_guard.validate_url("http://169.254.169.254/latest/meta-data/")
    assert "ssrf" in str(exc.value).lower() or "restricted" in str(exc.value).lower()
