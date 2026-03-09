"""
Document processing module for PDF and DOCX files.
Handles text extraction, OCR for scanned PDFs, page splitting, and text chunking.
"""

import io
import logging
import os
import re
import tempfile
from pathlib import Path
from typing import Optional

import fitz  # pymupdf
from docx import Document

from core.minio_client import minio_client
from core.config import settings

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Text Chunking
# ---------------------------------------------------------------------------


class TextChunker:
    """Splits text into overlapping chunks while preserving sentence boundaries."""

    def __init__(self, chunk_size: int = 1000, overlap: int = 200):
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk(self, text: str) -> list[str]:
        """Split *text* into chunks of roughly *chunk_size* characters
        with *overlap* characters shared between consecutive chunks.
        Splits prefer sentence boundaries so we don't cut mid-sentence.
        """
        if not text or not text.strip():
            return []

        # Normalise whitespace
        text = re.sub(r"\n{3,}", "\n\n", text).strip()

        sentences = self._split_sentences(text)
        chunks: list[str] = []
        current_chunk: list[str] = []
        current_len = 0

        for sentence in sentences:
            sentence_len = len(sentence)

            if current_len + sentence_len > self.chunk_size and current_chunk:
                chunk_text = " ".join(current_chunk).strip()
                if chunk_text:
                    chunks.append(chunk_text)

                # Build overlap from tail of current_chunk
                overlap_chunk: list[str] = []
                overlap_len = 0
                for s in reversed(current_chunk):
                    if overlap_len + len(s) > self.overlap:
                        break
                    overlap_chunk.insert(0, s)
                    overlap_len += len(s)
                current_chunk = overlap_chunk
                current_len = overlap_len

            current_chunk.append(sentence)
            current_len += sentence_len

        # Flush remaining
        if current_chunk:
            chunk_text = " ".join(current_chunk).strip()
            if chunk_text:
                chunks.append(chunk_text)

        return chunks

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        """Naive sentence splitter that keeps the delimiter attached."""
        parts = re.split(r"(?<=[.!?])\s+", text)
        return [p.strip() for p in parts if p.strip()]


# ---------------------------------------------------------------------------
# PDF Processing
# ---------------------------------------------------------------------------


def extract_pdf_text(pdf_bytes: bytes) -> list[dict]:
    """Extract text from a PDF, page by page.

    Returns a list of dicts:
        [{"page_number": 1, "text": "...", "is_scanned": False}, ...]
    """
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    pages: list[dict] = []

    for page_num in range(len(doc)):
        page = doc[page_num]
        text = page.get_text("text").strip() 
        is_scanned = len(text) < 30
        pages.append(
            {
                "page_number": page_num + 1,
                "text": text,
                "is_scanned": is_scanned,
            }
        )

    doc.close()
    return pages


def pdf_page_to_image(pdf_bytes: bytes, page_number: int, dpi: int = 300) -> str:
    """Render a single PDF page as a PNG image. Returns path to temp file."""
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    page = doc[page_number - 1]
    mat = fitz.Matrix(dpi / 72, dpi / 72)
    pix = page.get_pixmap(matrix=mat)

    tmp = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
    pix.save(tmp.name)
    doc.close()
    return tmp.name


def extract_single_page_pdf(pdf_bytes: bytes, page_number: int) -> bytes:
    """Extract a single page from a PDF and return it as PDF bytes."""
    src = fitz.open(stream=pdf_bytes, filetype="pdf")
    dst = fitz.open()
    dst.insert_pdf(src, from_page=page_number - 1, to_page=page_number - 1)
    page_bytes = dst.tobytes()
    dst.close()
    src.close()
    return page_bytes


# ---------------------------------------------------------------------------
# DOCX Processing
# ---------------------------------------------------------------------------


def extract_docx_text(docx_bytes: bytes) -> str:
    """Extract full text from a DOCX file."""
    doc = Document(io.BytesIO(docx_bytes))
    paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
    return "\n".join(paragraphs)


# ---------------------------------------------------------------------------
# MinIO Page Upload
# ---------------------------------------------------------------------------


def upload_page_to_minio(
    bucket: str,
    file_name: str,
    page_number: int,
    page_bytes: bytes,
) -> str:
    """Upload a single PDF page to MinIO.

    Returns the storage path like: pages/{file_name}/page_3.pdf
    """
    base_name = Path(file_name).stem
    object_name = f"pages/{base_name}/page_{page_number}.pdf"

    minio_client.client.put_object(
        bucket_name=bucket,
        object_name=object_name,
        data=io.BytesIO(page_bytes),
        length=len(page_bytes),
        content_type="application/pdf",
    )
    logger.info(f"Uploaded page {page_number} → {object_name}")
    return f"minio://{bucket}/{object_name}"


# ---------------------------------------------------------------------------
# High-Level Processing Pipelines
# ---------------------------------------------------------------------------


def process_pdf(
    pdf_bytes: bytes,
    file_name: str,
    bucket: str,
    ocr_engine=None,
    chunk_size: int = 1000,
    overlap: int = 200,
) -> list[dict]:
    """
    Full PDF processing pipeline.
    """
    pages = extract_pdf_text(pdf_bytes)
    chunker = TextChunker(chunk_size=chunk_size, overlap=overlap)
    all_chunks: list[dict] = []
    chunk_idx = 0

    for page_info in pages:
        page_num = page_info["page_number"]
        text = page_info["text"]

        # OCR fallback for scanned pages
        if page_info["is_scanned"] and ocr_engine is not None:
            logger.info(f"Page {page_num} appears scanned — running OCR")
            img_path = pdf_page_to_image(pdf_bytes, page_num)
            try:
                ocr_texts = ocr_engine.ocr_image(img_path)
                text = "\n".join(ocr_texts) if ocr_texts else text
            finally:
                os.unlink(img_path)

        # Upload individual page to MinIO
        page_pdf_bytes = extract_single_page_pdf(pdf_bytes, page_num)
        page_storage_path = upload_page_to_minio(
            bucket, file_name, page_num, page_pdf_bytes
        )

        # Chunk the page text
        if text.strip():
            page_chunks = chunker.chunk(text)
            for chunk_text in page_chunks:
                all_chunks.append(
                    {
                        "text": chunk_text,
                        "file_name": file_name,
                        "page_number": page_num,
                        "chunk_index": chunk_idx,
                        "page_storage_path": page_storage_path,
                        "text_preview": chunk_text[:200],
                    }
                )
                chunk_idx += 1

    logger.info(
        f"Processed PDF '{file_name}': {len(pages)} pages, {len(all_chunks)} chunks"
    )
    return all_chunks


def process_docx(
    docx_bytes: bytes,
    file_name: str,
    chunk_size: int = 1000,
    overlap: int = 200,
) -> list[dict]:
    """Full DOCX processing pipeline.

    Returns a list of chunk dicts.
    """
    text = extract_docx_text(docx_bytes)
    if not text.strip():
        logger.warning(f"No text extracted from DOCX '{file_name}'")
        return []

    chunker = TextChunker(chunk_size=chunk_size, overlap=overlap)
    chunks = chunker.chunk(text)
    all_chunks: list[dict] = []

    for idx, chunk_text in enumerate(chunks):
        all_chunks.append(
            {
                "text": chunk_text,
                "file_name": file_name,
                "page_number": 1,  # DOCX doesn't have pages
                "chunk_index": idx,
                "page_storage_path": "",
                "text_preview": chunk_text[:200],
            }
        )

    logger.info(f"Processed DOCX '{file_name}': {len(all_chunks)} chunks")
    return all_chunks
