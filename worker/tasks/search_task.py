"""
Celery task for searching documents.
Generates query embedding → searches Qdrant → returns ranked results with metadata.
"""

import logging

from core.celery_app import celery_app
from core.gemini_client import gemini_client
from core.qdrant_client import query_points, ensure_collection_exists
from tasks.basetask import BaseTask

logger = logging.getLogger(__name__)

COLLECTION_NAME = "docbot"


@celery_app.task(bind=True, base=BaseTask, name="app.search_task.search_documents")
def search_documents(
    self,
    query: str,
    top_k: int = 5,
    files: list[str] | None = None,
):
    """Search for relevant document chunks using semantic similarity.

    Args:
        query: User's question or search query.
        top_k: Number of top results to return.
        files: Optional list of minio_url values to restrict search scope.

    Returns:
        List of result dicts with text, metadata, and similarity score.
    """
    total_steps = 3

    try:
        # Step 1 — Generate query embedding
        self.update_progress("PROGRESS", 1, "Generating query embedding", total_steps)
        query_embeddings = gemini_client.generate_embeddings([query])
        query_vector = query_embeddings[0]
        logger.info(f"Generated query embedding ({len(query_vector)} dimensions)")

        # Step 2 — Search Qdrant
        self.update_progress(
            "PROGRESS", 2, f"Searching top {top_k} results in Qdrant", total_steps
        )
        ensure_collection_exists(COLLECTION_NAME)

        results = query_points(
            collection_name=COLLECTION_NAME,
            query_vector=query_vector,
            top_k=top_k,
            files=files or [],
        )
        logger.info(f"Search returned {len(results)} results")

        # Step 3 — Done
        return {
            "status": "success",
            "query": query,
            "results": results,
        }

    except Exception as e:
        logger.error(f"Search failed for query '{query}': {e}", exc_info=True)
        self.update_progress("FAILURE", 0, f"Error: {str(e)}", total_steps)
        raise
