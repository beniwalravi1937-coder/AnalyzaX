"""
AnalyzaX — Phase 24 Tests: Signed URLs, Storage Download Authorization & Path Traversal Defenses.
"""

import os
import time
import pytest
from httpx import ASGITransport, AsyncClient

from backend.app.core.config import settings
from backend.app.engines.storage.local_provider import LocalStorageProvider
from backend.app.main import app


def test_storage_signed_url_generation_and_tamper_defenses():
    provider = LocalStorageProvider()
    rel_path = "exports/report_01.pdf"

    # 1. Generate valid signed URL
    url = provider.generate_signed_url(rel_path, expires_in_seconds=60)
    assert "/api/v1/storage/download?" in url
    assert "sig=" in url
    assert "expires=" in url

    # Parse query params
    query = url.split("?")[1]
    params = dict(param.split("=") for param in query.split("&"))
    expires = int(params["expires"])
    sig = params["sig"]

    # 2. Valid signature verification
    assert provider.verify_signed_url(rel_path, expires, sig) is True

    # 3. Tampered path fails
    assert provider.verify_signed_url("exports/report_02.pdf", expires, sig) is False

    # 4. Tampered signature fails
    assert provider.verify_signed_url(rel_path, expires, "bad_signature_hex_value") is False

    # 5. Expired timestamp fails
    past_timestamp = int(time.time()) - 100
    assert provider.verify_signed_url(rel_path, past_timestamp, sig) is False

    # 6. Path traversal blocked
    with pytest.raises(ValueError) as exc:
        provider._resolve_safe_path("../../../etc/passwd")
    assert "traversal" in str(exc.value).lower() or "outside" in str(exc.value).lower()


@pytest.mark.anyio
async def test_storage_download_endpoint_security():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        provider = LocalStorageProvider()

        # Create a test asset in the storage root
        test_dir = os.path.join(settings.DATA_STORAGE_ROOT, "exports")
        os.makedirs(test_dir, exist_ok=True)
        test_file = os.path.join(test_dir, "safe_test_doc.txt")
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("CONFIDENTIAL_ANALYTICS_DATA")

        rel_path = "exports/safe_test_doc.txt"
        valid_url = provider.generate_signed_url(rel_path, expires_in_seconds=300)

        # 1. Valid download request succeeds
        res = await client.get(valid_url)
        assert res.status_code == 200
        assert "CONFIDENTIAL_ANALYTICS_DATA" in res.text

        # 2. Tampered signature rejected with 403
        bad_sig_url = valid_url.replace("sig=", "sig=00000000000000")
        bad_res = await client.get(bad_sig_url)
        assert bad_res.status_code == 403

        # 3. Expired signature rejected with 403
        expired_url = provider.generate_signed_url(rel_path, expires_in_seconds=-10)
        exp_res = await client.get(expired_url)
        assert exp_res.status_code == 403

        # 4. Path traversal in query param rejected
        trav_res = await client.get("/api/v1/storage/download?path=../config.py&expires=9999999999&sig=dummy_sig")
        assert trav_res.status_code in (400, 403)
