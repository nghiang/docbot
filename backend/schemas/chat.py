"""Chat-related Pydantic schemas."""

from typing import Optional

from pydantic import BaseModel


class SearchRequest(BaseModel):
    """Request schema for document search."""

    query: str
    top_k: int = 5
    files: list[str] | None = None


class AskRequest(BaseModel):
    """Request schema for asking questions."""

    query: str
    conversation_id: Optional[str] = None
    top_k: int = 5
    files: list[str] | None = None


class SourceInfo(BaseModel):
    """Schema for source document information."""

    file_name: str
    page_number: int
    page_storage_path: Optional[str] = None
    score: float


class AskResponse(BaseModel):
    """Response schema for question answers."""

    answer: str
    sources: list[SourceInfo] = []
    conversation_id: Optional[str] = None
