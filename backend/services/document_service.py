"""Document service for handling file uploads and indexing."""

import logging
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from sqlmodel import Session, select

from core.celery_client import celery_client
from core.config import settings
from core.minio_client import minio_client
from models.document import Document
from schemas.document import UploadResponse, PresignResponse, TaskStatusResponse
from celery.result import AsyncResult

logger = logging.getLogger(__name__)


class DocumentService:
    """Service class for document upload and indexing operations."""

    ALLOWED_EXTENSIONS = {".pdf", ".docx"}
    CONTENT_TYPES = {
        ".pdf": "application/pdf",
        ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    }

    def __init__(self):
        self._bucket = settings.MINIO_BUCKET
        self._minio = minio_client
        self._celery = celery_client

    def _detect_file_type(self, filename: str) -> str:
        """Detect file type from filename extension.

        Args:
            filename: Name of the file.

        Returns:
            File type string ('pdf' or 'docx').

        Raises:
            ValueError: If file type is not supported.
        """
        ext = Path(filename).suffix.lower()
        if ext == ".pdf":
            return "pdf"
        elif ext == ".docx":
            return "docx"
        else:
            raise ValueError(f"Unsupported file type: {ext}")

    def validate_file_extension(self, filename: str) -> bool:
        """Check if file extension is allowed.

        Args:
            filename: Name of the file.

        Returns:
            True if extension is allowed, False otherwise.
        """
        ext = Path(filename).suffix.lower()
        return ext in self.ALLOWED_EXTENSIONS

    def get_allowed_extensions(self) -> set:
        """Get set of allowed file extensions.

        Returns:
            Set of allowed extensions.
        """
        return self.ALLOWED_EXTENSIONS.copy()

    async def upload_and_index(
        self,
        filename: str,
        content: bytes,
        session: Session,
        user_id: int,
    ) -> UploadResponse:
        """Upload a document and trigger indexing.

        Args:
            filename: Name of the file.
            content: File content as bytes.
            session: Database session.
            user_id: ID of the uploading user.

        Returns:
            UploadResponse with task_id for tracking.
        """
        file_type = self._detect_file_type(filename)
        ext = Path(filename).suffix.lower()
        content_type = self.CONTENT_TYPES.get(ext, "application/octet-stream")

        # Upload to MinIO
        self._minio.upload_file(self._bucket, filename, content, content_type)
        logger.info(
            f"Uploaded {filename} ({len(content)} bytes) to MinIO bucket '{self._bucket}'"
        )

        # Trigger indexing task
        task = self._celery.send_task(
            "app.index_task.index_document",
            kwargs={
                "file_name": filename,
                "bucket": self._bucket,
                "file_type": file_type,
            },
            queue="index_queue",
        )

        # Persist document record
        doc = Document(
            user_id=user_id,
            file_name=filename,
            file_type=file_type,
            task_id=task.id,
            status="PENDING",
        )
        session.add(doc)
        session.commit()

        return UploadResponse(
            message="File uploaded successfully. Indexing started.",
            file_name=filename,
            task_id=task.id,
        )

    def generate_presigned_url(self, filename: str) -> PresignResponse:
        """Generate a presigned PUT URL for direct upload.

        Args:
            filename: Name of the file.

        Returns:
            PresignResponse with upload URL.
        """
        presigned_url = self._minio.generate_presigned_put_url(self._bucket, filename)

        # Rewrite internal MinIO URL to go through nginx proxy
        parsed = urlparse(presigned_url)
        public_url = f"/storage{parsed.path}?{parsed.query}"

        return PresignResponse(
            upload_url=public_url,
            file_name=filename,
        )

    def trigger_indexing(
        self, filename: str, session: Session, user_id: int
    ) -> UploadResponse:
        """Trigger indexing for an already-uploaded file.

        Args:
            filename: Name of the file in MinIO.
            session: Database session.
            user_id: ID of the uploading user.

        Returns:
            UploadResponse with task_id for tracking.
        """
        file_type = self._detect_file_type(filename)

        task = self._celery.send_task(
            "app.index_task.index_document",
            kwargs={
                "file_name": filename,
                "bucket": self._bucket,
                "file_type": file_type,
            },
            queue="index_queue",
        )

        # Persist document record
        doc = Document(
            user_id=user_id,
            file_name=filename,
            file_type=file_type,
            task_id=task.id,
            status="PENDING",
        )
        session.add(doc)
        session.commit()

        logger.info(f"Indexing triggered for {filename}, task_id={task.id}")

        return UploadResponse(
            message="Indexing started.",
            file_name=filename,
            task_id=task.id,
        )

    def get_task_status(self, task_id: str) -> TaskStatusResponse:
        """Get the status of a Celery task.

        Args:
            task_id: ID of the task.

        Returns:
            TaskStatusResponse with current status.
        """
        result = AsyncResult(task_id, app=self._celery.app)

        response = TaskStatusResponse(
            task_id=task_id,
            status=result.status,
        )

        if result.state == "PROGRESS":
            response.progress = result.info
        elif result.ready():
            response.result = result.result

        return response

    def get_user_documents(self, session: Session, user_id: int) -> list[Document]:
        """Get all documents for a user, syncing status from Celery."""
        docs = session.exec(
            select(Document)
            .where(Document.user_id == user_id)
            .order_by(Document.created_at.desc())  # type: ignore[union-attr]
        ).all()

        for doc in docs:
            if doc.task_id and doc.status not in ("SUCCESS", "FAILURE"):
                result = AsyncResult(doc.task_id, app=self._celery.app)
                if result.status != doc.status:
                    doc.status = result.status
                    doc.updated_at = datetime.utcnow()
        session.commit()

        return list(docs)

    def delete_document(self, session: Session, doc_id: int, user_id: int) -> bool:
        """Delete a document record belonging to the given user."""
        doc = session.exec(
            select(Document).where(Document.id == doc_id, Document.user_id == user_id)
        ).first()
        if not doc:
            return False
        session.delete(doc)
        session.commit()
        return True


# Singleton instance
document_service = DocumentService()
