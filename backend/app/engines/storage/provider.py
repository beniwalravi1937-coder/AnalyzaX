"""
AnalyzaX — Phase 22: Durable Storage Provider Abstraction.
Defines the canonical storage interface for durable dataset and artifact persistence.
"""

from abc import ABC, abstractmethod
from typing import BinaryIO, List, Optional
from pydantic import BaseModel


class StoredFileInfo(BaseModel):
    path: str
    size_bytes: int
    content_type: Optional[str] = None
    created_at: str
    etag: Optional[str] = None


class StorageProvider(ABC):
    """Abstract base class for durable storage backends (Local, S3, MinIO)."""

    @abstractmethod
    def save_file(
        self, relative_path: str, data: bytes, content_type: Optional[str] = None
    ) -> StoredFileInfo:
        """Stores binary data at the given isolated relative path."""
        pass

    @abstractmethod
    def get_file(self, relative_path: str) -> bytes:
        """Retrieves raw binary content for the given isolated relative path."""
        pass

    @abstractmethod
    def file_exists(self, relative_path: str) -> bool:
        """Checks if a file exists."""
        pass

    @abstractmethod
    def delete_file(self, relative_path: str) -> bool:
        """Removes a file from storage."""
        pass

    @abstractmethod
    def list_files(self, prefix: str = "") -> List[StoredFileInfo]:
        """Lists files matching the relative prefix."""
        pass

    @abstractmethod
    def generate_signed_url(
        self, relative_path: str, expires_in_seconds: int = 3600
    ) -> str:
        """Generates a temporary, cryptographically signed URL for authorized access."""
        pass
