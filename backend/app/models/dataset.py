from enum import Enum
from typing import Optional

from sqlalchemy import BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from backend.app.models.base import Base


class DatasetStatus(str, Enum):
    UPLOADING = "UPLOADING"
    VALIDATING = "VALIDATING"
    STORING = "STORING"
    INGESTING = "INGESTING"
    READY = "READY"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"
    DELETED = "DELETED"


class SupportedFormat(str, Enum):
    CSV = "csv"
    XLSX = "xlsx"
    JSON = "json"
    PARQUET = "parquet"


class DatasetModel(Base):
    """
    SQLAlchemy metadata model for tracking ingested datasets.
    Raw datasets are stored immutably on the filesystem, while structural
    metadata, status transitions, and analytical view names are tracked here.
    """

    __tablename__ = "datasets"

    id: Mapped[str] = mapped_column(String(64), primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    original_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    file_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    format: Mapped[str] = mapped_column(String(16), nullable=False)
    mime_type: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    file_size_bytes: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[str] = mapped_column(String(32), default=DatasetStatus.UPLOADING.value, nullable=False)
    duckdb_table_name: Mapped[str] = mapped_column(String(128), nullable=False, unique=True)
    original_file_path: Mapped[str] = mapped_column(Text, nullable=False)
    processed_file_path: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    sheet_name: Mapped[Optional[str]] = mapped_column(String(128), nullable=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
