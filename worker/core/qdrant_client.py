import logging
import uuid
from typing import List, Optional

from qdrant_client import QdrantClient, models
from qdrant_client.models import (
    Distance,
    FieldCondition,
    FilterSelector,
    MatchValue,
    PointStruct,
    VectorParams,
)

from core.config import settings

logger = logging.getLogger(__name__)

qdrant_client = QdrantClient(
    host=settings.QDRANT_HOST,
    port=settings.QDRANT_PORT,
)


def ensure_collection_exists(collection_name: str, vector_size: int = 1536) -> None:
    """Ensure Qdrant collection exists, create if it doesn't."""
    try:
        collections = qdrant_client.get_collections()
        collection_names = [col.name for col in collections.collections]

        if collection_name not in collection_names:
            qdrant_client.create_collection(
                collection_name=collection_name,
                vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
            )
            logger.info(f"Created collection: {collection_name}")
        else:
            logger.info(f"Collection already exists: {collection_name}")
    except Exception as e:
        logger.error(f"Error ensuring collection exists: {e}")
        raise

def disable_hnsw_index(collection_name: str):
    try:
        qdrant_client.update_collection(
            collection_name=collection_name,
            hnsw_config=models.HnswConfigDiff(
                m=0,
            ),
        )
        logger.info(f"Disabled HNSW index for collection: {collection_name}")
    except Exception as e:
        logger.error(
            f"Error disabling HNSW index for collection {collection_name}: {e}"
        )
        raise

def enable_hnsw_index(collection_name: str, m: int = 16):
    try:
        qdrant_client.update_collection(
            collection_name=collection_name,
            hnsw_config=models.HnswConfigDiff(
                m=m,
            ),
        )
        logger.info(f"Enabled HNSW index for collection: {collection_name}")
    except Exception as e:
        logger.error(f"Error enabling HNSW index for collection {collection_name}: {e}")
        raise


def index_chunks(
    collection_name: str,
    chunks: List[str],
    embeddings: List[List[float]],
    metadata: Optional[List[dict]] = None,
    batch_size: int = 100,
) -> int:
    """Index text chunks with embeddings to Qdrant collection.

    Args:
        collection_name: Name of the Qdrant collection
        chunks: List of text chunks
        embeddings: List of embedding vectors
        metadata: Optional list of metadata dicts for each chunk
        batch_size: Number of points to upload per batch (default: 100)

    Returns:
        Number of points indexed
    """
    if len(chunks) != len(embeddings):
        raise ValueError("Chunks and embeddings must have same length")

    if metadata is None:
        metadata = [{}] * len(chunks)
    elif len(metadata) != len(chunks):
        raise ValueError("Metadata must have same length as chunks")

    points = []
    for chunk, embedding, meta in zip(chunks, embeddings, metadata):
        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=embedding,
                payload={"text": chunk, **meta},
            )
        )

    total_indexed = 0
    for i in range(0, len(points), batch_size):
        batch = points[i : i + batch_size]
        qdrant_client.upsert(
            collection_name=collection_name,
            points=batch,
        )
        total_indexed += len(batch)
        logger.info(
            f"Indexed batch {i // batch_size + 1}: {len(batch)} chunks "
            f"(total: {total_indexed}/{len(points)})"
        )

    logger.info(f"Indexed {len(points)} chunks to collection {collection_name}")
    print(f"Indexed {len(points)} chunks to collection {collection_name}")
    return len(points)


def delete_points(
    collection_name: str,
    project_id: str,
    minio_url: str,
) -> None:
    """Delete Qdrant collection associated with a file.

    Args:
        collection_name: Name of the Qdrant collection
        project_id: Project ID for collection naming
        minio_url: URL to the file in MinIO
    """
    try:
        qdrant_client.delete(
            collection_name=collection_name,
            points_selector=FilterSelector(
                filter=models.Filter(
                    must=[
                        FieldCondition(
                            key="project_id",
                            match=MatchValue(value=project_id),
                        ),
                        FieldCondition(
                            key="minio_url",
                            match=MatchValue(value=minio_url),
                        ),
                    ]
                )
            ),
            wait=True,
        )
        logger.info(f"Deleted collection: {collection_name}")
    except Exception as e:
        logger.error(f"Error deleting collection {collection_name}: {e}")
        raise


def query_points(
    collection_name: str,
    query_vector: List[float],
    top_k: int = 5,
    files: list[str] = [],
) -> List[dict]:
    try:
        response = qdrant_client.query_points(
            collection_name=collection_name,
            query=query_vector,
            limit=top_k,
            query_filter=models.Filter(
                must=[
                    models.FieldCondition(
                        key="minio_url", match=models.MatchAny(any=files)
                    )
                ]
            )
            if files
            else None,
        )
        results = [
            {
                "text": point.payload.get("text", "") if point.payload else "",
                "file_name": point.payload.get("file_name") if point.payload else None,
                "page_number": point.payload.get("page_number") if point.payload else None,
                "chunk_index": point.payload.get("chunk_index") if point.payload else None,
                "page_storage_path": point.payload.get("page_storage_path") if point.payload else None,
                "text_preview": point.payload.get("text_preview") if point.payload else None,
                "minio_url": point.payload.get("minio_url") if point.payload else None,
                "score": point.score,
            }
            for point in response.points
        ]
        return results
    except Exception as e:
        logger.error(f"Error querying points from collection {collection_name}: {e}")
        raise
