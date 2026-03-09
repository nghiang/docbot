"""Document routes for file upload and indexing."""

from fastapi import APIRouter, UploadFile, File, HTTPException, status

from core.dependencies import CurrentUser, DbSession
from schemas.document import (
    PresignRequest,
    PresignResponse,
    UploadCompleteRequest,
    UploadResponse,
    TaskStatusResponse,
    DocumentResponse,
)
from services.document_service import document_service

router = APIRouter(tags=["Documents"])


@router.get("/documents", response_model=list[DocumentResponse])
def list_documents(
    session: DbSession,
    user: CurrentUser,
) -> list[DocumentResponse]:
    """List all documents for the authenticated user."""
    docs = document_service.get_user_documents(session, user.id)  # type: ignore[arg-type]
    return [
        DocumentResponse(
            id=d.id,  # type: ignore[arg-type]
            file_name=d.file_name,
            file_type=d.file_type,
            task_id=d.task_id,
            status=d.status,
            created_at=d.created_at,
            updated_at=d.updated_at,
        )
        for d in docs
    ]


@router.delete("/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(
    doc_id: int,
    session: DbSession,
    user: CurrentUser,
):
    """Delete a document record."""
    deleted = document_service.delete_document(session, doc_id, user.id)  # type: ignore[arg-type]
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(...),
    session: DbSession = None,  # type: ignore[assignment]
    user: CurrentUser = None,  # type: ignore[assignment]
) -> UploadResponse:
    """Upload a document and trigger indexing."""
    if not document_service.validate_file_extension(
        file.filename if file.filename else ""
    ):
        allowed = ", ".join(document_service.get_allowed_extensions())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {allowed}",
        )

    content = await file.read()

    return await document_service.upload_and_index(
        file.filename if file.filename else "",
        content,
        session,
        user.id,  # type: ignore[union-attr]
    )


@router.post("/upload/presign", response_model=PresignResponse)
def get_presigned_url(request: PresignRequest) -> PresignResponse:
    """Get a presigned URL for direct upload to storage."""
    if not document_service.validate_file_extension(request.file_name):
        allowed = ", ".join(document_service.get_allowed_extensions())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {allowed}",
        )

    return document_service.generate_presigned_url(request.file_name)


@router.post("/upload/complete", response_model=UploadResponse)
def upload_complete(
    request: UploadCompleteRequest,
    session: DbSession,
    user: CurrentUser,
) -> UploadResponse:
    """Signal that upload is complete and trigger indexing."""
    if not document_service.validate_file_extension(request.file_name):
        allowed = ", ".join(document_service.get_allowed_extensions())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file type. Allowed: {allowed}",
        )

    return document_service.trigger_indexing(request.file_name, session, user.id)  # type: ignore[arg-type]


@router.get("/task/{task_id}", response_model=TaskStatusResponse)
def get_task_status(task_id: str) -> TaskStatusResponse:
    """Get the status of an indexing task."""
    return document_service.get_task_status(task_id)
