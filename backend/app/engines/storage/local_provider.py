"""
AnalyzaX — Phase 22: Production Local Durable Storage Provider.
Enforces strict tenant path isolation and prevents directory traversal attacks.
"""

import hashlib
import hmac
import os
import time
from datetime import datetime, timezone
from typing import List, Optional
from urllib.parse import quote

from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.engines.storage.provider import StoredFileInfo, StorageProvider


class LocalStorageProvider(StorageProvider):
    """Production local filesystem storage provider with path isolation."""

    def __init__(self, root_dir: Optional[str] = None) -> None:
        self.root_dir = os.path.abspath(root_dir or settings.DATA_STORAGE_ROOT)
        os.makedirs(self.root_dir, exist_ok=True)
        self._signing_secret = settings.SECRET_KEY.encode("utf-8")

    def _resolve_safe_path(self, relative_path: str) -> str:
        """
        Resolves the absolute path and enforces that it stays strictly within root_dir.
        Blocks directory traversal attempts (e.g. '../', '/etc/passwd').
        """
        # Normalize and remove leading slashes
        clean_rel = os.path.normpath(relative_path).lstrip("/\\")

        # Reject any traversal artifacts
        if ".." in clean_rel.split(os.sep):
            raise ValueError(f"Directory traversal detected in path: '{relative_path}'")

        full_path = os.path.abspath(os.path.join(self.root_dir, clean_rel))

        # Strict containment check
        common = os.path.commonpath([self.root_dir, full_path])
        if common != self.root_dir:
            raise ValueError(f"Access denied: path '{relative_path}' escapes storage root.")

        return full_path

    def save_file(
        self, relative_path: str, data: bytes, content_type: Optional[str] = None
    ) -> StoredFileInfo:
        target_path = self._resolve_safe_path(relative_path)
        os.makedirs(os.path.dirname(target_path), exist_ok=True)

        # Write to temp file first, then atomically replace
        temp_path = f"{target_path}.tmp_{os.getpid()}"
        with open(temp_path, "wb") as f:
            f.write(data)
        os.replace(temp_path, target_path)

        etag = hashlib.sha256(data).hexdigest()
        size_bytes = len(data)

        logger.info(f"Durable storage saved: {relative_path} ({size_bytes} bytes)")
        return StoredFileInfo(
            path=relative_path,
            size_bytes=size_bytes,
            content_type=content_type or "application/octet-stream",
            created_at=datetime.now(timezone.utc).isoformat(),
            etag=etag,
        )

    def get_file(self, relative_path: str) -> bytes:
        target_path = self._resolve_safe_path(relative_path)
        if not os.path.exists(target_path):
            raise FileNotFoundError(f"File not found in storage: '{relative_path}'")
        with open(target_path, "rb") as f:
            return f.read()

    def file_exists(self, relative_path: str) -> bool:
        try:
            target_path = self._resolve_safe_path(relative_path)
            return os.path.exists(target_path)
        except ValueError:
            return False

    def delete_file(self, relative_path: str) -> bool:
        target_path = self._resolve_safe_path(relative_path)
        if os.path.exists(target_path):
            os.remove(target_path)
            logger.info(f"Durable storage removed: {relative_path}")
            return True
        return False

    def list_files(self, prefix: str = "") -> List[StoredFileInfo]:
        try:
            target_dir = self._resolve_safe_path(prefix)
        except ValueError:
            return []

        if not os.path.exists(target_dir):
            return []

        results: List[StoredFileInfo] = []
        for root, _, files in os.walk(target_dir):
            for file in files:
                if file.endswith(".tmp"):
                    continue
                full_p = os.path.join(root, file)
                rel_p = os.path.relpath(full_p, self.root_dir).replace("\\", "/")
                size = os.path.getsize(full_p)
                mtime = os.path.getmtime(full_p)
                results.append(
                    StoredFileInfo(
                        path=rel_p,
                        size_bytes=size,
                        created_at=datetime.fromtimestamp(mtime, tz=timezone.utc).isoformat(),
                    )
                )
        return results

    def generate_signed_url(
        self, relative_path: str, expires_in_seconds: int = 3600
    ) -> str:
        # Validate path
        self._resolve_safe_path(relative_path)
        expires_at = int(time.time()) + expires_in_seconds

        msg = f"{relative_path}:{expires_at}".encode("utf-8")
        signature = hmac.new(self._signing_secret, msg, hashlib.sha256).hexdigest()

        encoded_path = quote(relative_path)
        return f"/api/v1/storage/download?path={encoded_path}&expires={expires_at}&sig={signature}"

    def verify_signed_url(self, relative_path: str, expires_at: int, signature: str) -> bool:
        """Verifies signature authenticity and validity window."""
        if time.time() > expires_at:
            return False  # Expired

        msg = f"{relative_path}:{expires_at}".encode("utf-8")
        expected_sig = hmac.new(self._signing_secret, msg, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected_sig, signature)
