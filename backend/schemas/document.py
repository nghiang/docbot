"""Document-related Pydantic schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class PresignRequest(BaseModel):
    """Request schema for presigned URL generation."""

    file_name: str


class PresignResponse(BaseModel):
    """Response schema for presigned URL."""

    upload_url: str
    file_name: str


class UploadCompleteRequest(BaseModel):
    """Request schema for upload completion notification."""

    file_name: str


class UploadResponse(BaseModel):
    """Response schema for document upload."""

    message: str
    file_name: str
    task_id: str


class TaskStatusResponse(BaseModel):
    """Response schema for task status."""

    task_id: str
    status: str
    result: Optional[dict] = None
    progress: Optional[dict] = None


class DocumentResponse(BaseModel):
    """Response schema for a persisted document record."""

    id: int
    file_name: str
    file_type: str
    task_id: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
