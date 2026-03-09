"""SQLModel model for uploaded documents."""

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field


class Document(SQLModel, table=True):
    """Tracks uploaded documents and their indexing status."""

    __tablename__ = "documents"  # type: ignore

    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="users.id", index=True)
    file_name: str = Field(max_length=500)
    file_type: str = Field(max_length=10)  # "pdf" or "docx"
    task_id: Optional[str] = Field(default=None, max_length=255)
    status: str = Field(
        default="PENDING", max_length=20
    )  # PENDING, STARTED, PROGRESS, SUCCESS, FAILURE
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
