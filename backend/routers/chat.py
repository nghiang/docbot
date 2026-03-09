"""Chat routes for Q&A operations."""

from fastapi import APIRouter

from core.dependencies import OptionalUser
from schemas.chat import SearchRequest, AskRequest, AskResponse, SourceInfo
from services.chat_service import chat_service

router = APIRouter(tags=["Chat"])


@router.post("/search")
def search_documents(request: SearchRequest) -> dict:
    """Search indexed documents for relevant content.

    Args:
        request: Search parameters.

    Returns:
        Search results dictionary.
    """
    result = chat_service.search_documents(
        query=request.query,
        top_k=request.top_k,
        files=request.files,
    )
    return result


@router.post("/ask", response_model=AskResponse)
def ask_question(
    request: AskRequest,
    user: OptionalUser,
) -> AskResponse:
    """Ask a question about uploaded documents.

    If authenticated, conversation history is saved and used for context.

    Args:
        request: Question and optional parameters.
        user: Optional authenticated user.

    Returns:
        AskResponse with answer, sources, and conversation_id.
    """
    user_id = user.id if user else None

    result = chat_service.ask_question(
        query=request.query,
        user_id=user_id,
        conversation_id=request.conversation_id,
        top_k=request.top_k,
        files=request.files,
    )

    return AskResponse(
        answer=result["answer"],
        sources=[
            SourceInfo(
                file_name=s["file_name"],
                page_number=s.get("page_number"),
                page_storage_path=s.get("page_storage_path"),
                score=s.get("score"),
            )
            for s in result.get("sources", [])
        ],
        conversation_id=result.get("conversation_id"),
    )
