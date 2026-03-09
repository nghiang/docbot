"""
Celery task for indexing documents.
Downloads file from MinIO → processes (PDF/DOCX/OCR) → generates embeddings → stores in Qdrant.
"""

import logging
import os
import tempfile

from core.celery_app import celery_app
from core.config import settings
from core.document_processor import process_pdf, process_docx
from core.gemini_client import gemini_client
from core.minio_client import minio_client
from core.qdrant_client import ensure_collection_exists, index_chunks
from tasks.basetask import BaseTask

logger = logging.getLogger(__name__)

COLLECTION_NAME = "docbot"


@celery_app.task(bind=True, base=BaseTask, name="app.index_task.index_document")
def index_document(self, file_name: str, bucket: str, file_type: str):
    """Index a document: extract text, generate embeddings, store in Qdrant.

    Args:
        file_name: Name of the file in MinIO.
        bucket: MinIO bucket name.
        file_type: File type — 'pdf' or 'docx'.
    """
    total_steps = 5

    try:
        # Step 1 — Download file from MinIO
        self.update_progress("PROGRESS", 1, "Downloading file from MinIO", total_steps)
        logger.info(f"Downloading {file_name} from bucket {bucket}")
        file_bytes = minio_client.get_object_bytes(bucket, file_name)
        logger.info(f"Downloaded {len(file_bytes)} bytes")

        # Step 2 — Process document based on type
        self.update_progress(
            "PROGRESS", 2, f"Processing {file_type.upper()} document", total_steps
        )

        ocr_engine = None
        if file_type == "pdf":
            # Use global OCR instance initialized at startup
            from core.paddleocr import get_paddle_ocr

            ocr_engine = get_paddle_ocr()
            if ocr_engine is None:
                logger.warning("PaddleOCR not available, OCR will be skipped")

            chunks = process_pdf(
                pdf_bytes=file_bytes,
                file_name=file_name,
                bucket=bucket,
                ocr_engine=ocr_engine,
            )
        elif file_type == "docx":
            chunks = process_docx(
                docx_bytes=file_bytes,
                file_name=file_name,
            )
        else:
            raise ValueError(f"Unsupported file type: {file_type}")

        if not chunks:
            logger.warning(f"No chunks extracted from {file_name}")
            self.update_progress(
                "SUCCESS", total_steps, "No content extracted", total_steps
            )
            return {"status": "success", "chunks_indexed": 0, "file_name": file_name}

        logger.info(f"Extracted {len(chunks)} chunks from {file_name}")

        # Step 3 — Generate embeddings
        self.update_progress(
            "PROGRESS",
            3,
            f"Generating embeddings for {len(chunks)} chunks",
            total_steps,
        )
        texts = [chunk["text"] for chunk in chunks]
        embeddings = gemini_client.generate_embeddings(texts)
        logger.info(f"Generated {len(embeddings)} embeddings")

        # Step 4 — Store in Qdrant
        self.update_progress("PROGRESS", 4, "Storing embeddings in Qdrant", total_steps)
        ensure_collection_exists(COLLECTION_NAME)

        metadata = [
            {
                "file_name": chunk["file_name"],
                "page_number": chunk["page_number"],
                "chunk_index": chunk["chunk_index"],
                "page_storage_path": chunk.get("page_storage_path", ""),
                "text_preview": chunk.get("text_preview", ""),
                "minio_url": f"minio://{bucket}/{file_name}",
            }
            for chunk in chunks
        ]

        num_indexed = index_chunks(
            collection_name=COLLECTION_NAME,
            chunks=texts,
            embeddings=embeddings,
            metadata=metadata,
        )

        # Step 5 — Done
        result = {
            "status": "success",
            "chunks_indexed": num_indexed,
            "file_name": file_name,
        }
        logger.info(f"Indexing complete: {result}")
        return result

    except Exception as e:
        logger.error(f"Indexing failed for {file_name}: {e}", exc_info=True)
        self.update_progress("FAILURE", 0, f"Error: {str(e)}", total_steps)
        raise
