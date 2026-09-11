from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field


class DatasetResponse(BaseModel):
    """Public dataset metadata representation (no internal file paths exposed)."""

    model_config = ConfigDict(from_attributes=True)

    id: str = Field(..., description="Unique dataset identifier (e.g. ds_...)")
    name: str = Field(..., description="Human-friendly dataset display name")
    original_filename: str = Field(..., description="Sanitized original filename")
    format: str = Field(..., description="Detected file format (csv, xlsx, json, parquet)")
    file_size_bytes: int = Field(..., description="File size in bytes")
    status: str = Field(..., description="Ingestion status (UPLOADING, VALIDATING, STORING, INGESTING, READY, FAILED)")
    duckdb_table_name: str = Field(..., description="Safe internal DuckDB SQL identifier")
    sheet_name: Optional[str] = Field(None, description="Selected worksheet name for XLSX files")
    created_at: datetime = Field(..., description="Upload timestamp")
    updated_at: datetime = Field(..., description="Last modification timestamp")
    error_message: Optional[str] = Field(None, description="Error explanation if ingestion failed")


class DatasetListResponse(BaseModel):
    """List of registered datasets in the workspace."""

    datasets: List[DatasetResponse]
    total: int


class DatasetUploadResponse(BaseModel):
    """Initial response returned upon receiving and queueing a dataset upload."""

    dataset_id: str
    status: str
    filename: str
    format: str
    file_size_bytes: int
    duckdb_table_name: str
    message: str = "Dataset successfully uploaded and ingested into analytical engine"
