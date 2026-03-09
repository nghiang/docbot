"""Conversation-related Pydantic schemas."""

from datetime import datetime
from typing import Optional, Union

from pydantic import BaseModel, field_serializer


class ConversationCreate(BaseModel):
    """Request schema for creating a conversation."""

    title: Optional[str] = None


class ConversationUpdate(BaseModel):
    """Request schema for updating a conversation."""

    title: str


class ConversationResponse(BaseModel):
    """Response schema for conversation information."""

    id: str
    user_id: int
    title: str
    created_at: Union[str, datetime]
    updated_at: Union[str, datetime]

    @field_serializer("created_at", "updated_at")
    @classmethod
    def serialize_dt(cls, v: Union[str, datetime]) -> str:
        if isinstance(v, datetime):
            return v.isoformat()
        return v


class MessageResponse(BaseModel):
    """Response schema for conversation messages."""

    id: str
    role: str
    content: str
    sources: list[dict] = []
    created_at: Union[str, datetime]

    @field_serializer("created_at")
    @classmethod
    def serialize_dt(cls, v: Union[str, datetime]) -> str:
        if isinstance(v, datetime):
            return v.isoformat()
        return v


class ConversationDetailResponse(BaseModel):
    """Response schema for conversation with messages."""

    conversation: ConversationResponse
    messages: list[MessageResponse]


class ConversationListResponse(BaseModel):
    """Response schema for list of conversations."""

    conversations: list[ConversationResponse]
