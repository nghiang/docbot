"""Conversation routes for managing chat history."""

from fastapi import APIRouter, HTTPException, status, Depends

from core.dependencies import CurrentUser, get_current_user
from schemas.conversation import (
    ConversationCreate,
    ConversationUpdate,
    ConversationResponse,
    ConversationDetailResponse,
    ConversationListResponse,
    MessageResponse,
)
from services.conversation_service import conversation_service

router = APIRouter(
    prefix="/conversations",
    tags=["Conversations"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", response_model=ConversationListResponse)
def list_conversations(
    user: CurrentUser,
    limit: int = 20,
) -> ConversationListResponse:
    """List all conversations for the current user.

    Args:
        user: Current authenticated user.
        limit: Maximum number of conversations to return.

    Returns:
        ConversationListResponse with list of conversations.
    """
    conversations = conversation_service.get_by_user(user.id if user.id else 0, limit)

    return ConversationListResponse(
        conversations=[
            ConversationResponse(
                id=conv["id"],
                title=conv["title"],
                created_at=conv["created_at"],
                updated_at=conv["updated_at"],
                user_id=conv["user_id"],
            )
            for conv in conversations
        ]
    )


@router.post("", response_model=ConversationResponse)
def create_conversation(
    user: CurrentUser,
    request: ConversationCreate,
) -> ConversationResponse:
    """Create a new conversation.

    Args:
        user: Current authenticated user.
        request: Conversation creation data.

    Returns:
        ConversationResponse with new conversation data.
    """
    conversation_id = conversation_service.create(
        user.id if user.id else 0, request.title
    )
    conversation = conversation_service.get(conversation_id, user.id if user.id else 0)
    assert conversation is not None
    return ConversationResponse(
        id=conversation["id"],
        title=conversation["title"],
        created_at=conversation["created_at"],
        updated_at=conversation["updated_at"],
        user_id=conversation["user_id"],
    )


@router.get("/{conversation_id}", response_model=ConversationDetailResponse)
def get_conversation(
    conversation_id: str,
    user: CurrentUser,
) -> ConversationDetailResponse:
    """Get a conversation with all its messages.

    Args:
        conversation_id: ID of the conversation.
        user: Current authenticated user.

    Returns:
        ConversationDetailResponse with conversation and messages.

    Raises:
        HTTPException: If conversation not found.
    """
    conversation = conversation_service.get(conversation_id, user.id if user.id else 0)

    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    messages = conversation_service.get_messages(conversation_id)
    assert conversation is not None
    return ConversationDetailResponse(
        conversation=ConversationResponse(
            id=conversation["id"],
            title=conversation["title"],
            created_at=conversation["created_at"],
            updated_at=conversation["updated_at"],
            user_id=conversation["user_id"],
        ),
        messages=[
            MessageResponse(
                id=msg["id"],
                role=msg["role"],
                content=msg["content"],
                sources=msg.get("sources", []),
                created_at=msg["created_at"],
            )
            for msg in messages
        ],
    )


@router.patch("/{conversation_id}", response_model=ConversationResponse)
def update_conversation(
    conversation_id: str,
    request: ConversationUpdate,
    user: CurrentUser,
) -> ConversationResponse:
    """Update a conversation's title.

    Args:
        conversation_id: ID of the conversation.
        request: Update data.
        user: Current authenticated user.

    Returns:
        ConversationResponse with updated data.

    Raises:
        HTTPException: If conversation not found.
    """
    # Check if conversation exists
    conversation = conversation_service.get(conversation_id, user.id if user.id else 0)
    if not conversation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    # Update title
    if request.title:
        conversation_service.update_title(
            conversation_id, user.id if user.id else 0, request.title
        )
        conversation = conversation_service.get(
            conversation_id, user.id if user.id else 0
        )
    assert conversation is not None
    return ConversationResponse(
        id=conversation["id"],
        title=conversation["title"],
        created_at=conversation["created_at"],
        updated_at=conversation["updated_at"],
        user_id=conversation["user_id"],
    )


@router.delete("/{conversation_id}")
def delete_conversation(
    conversation_id: str,
    user: CurrentUser,
) -> dict:
    """Delete a conversation and all its messages.

    Args:
        conversation_id: ID of the conversation.
        user: Current authenticated user.

    Returns:
        Success message.

    Raises:
        HTTPException: If conversation not found.
    """
    success = conversation_service.delete(conversation_id, user.id if user.id else 0)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Conversation not found",
        )

    return {"message": "Conversation deleted successfully"}
