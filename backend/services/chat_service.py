"""Chat service for handling Q&A operations."""

import logging
from typing import Optional

from core.celery_client import celery_client
from core.gemini_client import gemini_client
from services.conversation_service import conversation_service

logger = logging.getLogger(__name__)


class ChatService:
    """Service class for chat and Q&A operations."""

    def __init__(self):
        self._conversation_service = conversation_service
        self._celery = celery_client

    def search_documents(
        self,
        query: str,
        top_k: int = 5,
        files: Optional[list[str]] = None,
        timeout: int = 60,
    ) -> dict:
        """Search indexed documents for relevant content.

        Args:
            query: Search query string.
            top_k: Number of top results to return.
            files: Optional list of files to search within.
            timeout: Task timeout in seconds.

        Returns:
            Search results dictionary.
        """
        task = self._celery.send_task(
            "app.search_task.search_documents",
            kwargs={
                "query": query,
                "top_k": top_k,
                "files": files,
            },
            queue="search_queue",
        )
        return task.get(timeout=timeout)

    def ask_question(
        self,
        query: str,
        user_id: Optional[int] = None,
        conversation_id: Optional[str] = None,
        top_k: int = 5,
        files: Optional[list[str]] = None,
    ) -> dict:
        """Ask a question about uploaded documents.

        Args:
            query: User's question.
            user_id: Optional user ID (for saving to conversation).
            conversation_id: Optional existing conversation ID.
            top_k: Number of context chunks to use.
            files: Optional list of files to search within.

        Returns:
            Dictionary with answer, sources, and conversation_id.
        """
        # If authenticated and no conversation_id, create a new conversation
        if user_id and not conversation_id:
            title = query[:50] + ("..." if len(query) > 50 else "")
            conversation_id = self._conversation_service.create(user_id, title)

        # Get conversation history for context
        conversation_history = ""
        if conversation_id and user_id:
            qa_pairs = self._conversation_service.get_recent_qa_pairs(
                conversation_id, limit=5
            )
            if qa_pairs:
                history_parts = [
                    f"User: {qa['question']}\nAssistant: {qa['answer']}"
                    for qa in qa_pairs
                ]
                conversation_history = "\n\n".join(history_parts)

        # Search for relevant chunks
        search_result = self.search_documents(query, top_k, files)
        results = search_result.get("results", [])
        logger.info(f"Search results: {search_result}")
        if not results:
            answer = "No relevant documents found for your question."
            sources = []
        else:
            # Build context from search results
            context_parts = []
            sources = []
            for i, r in enumerate(results):
                context_parts.append(
                    f"[Source {i + 1}] (File: {r.get('file_name', 'unknown')}, "
                    f"Page: {r.get('page_number', 'N/A')}, "
                    f"Score: {r.get('score', 0):.2f})\n{r.get('text', '')}"
                )
                sources.append(
                    {
                        "file_name": r.get("file_name"),
                        "page_number": r.get("page_number"),
                        "page_storage_path": r.get("page_storage_path"),
                        "score": r.get("score"),
                    }
                )

            document_context = "\n\n---\n\n".join(context_parts)

            # Combine conversation history with document context
            if conversation_history:
                full_context = (
                    f"Previous conversation:\n{conversation_history}\n\n---\n\n"
                    f"Relevant documents:\n{document_context}"
                )
            else:
                full_context = document_context

            # Generate answer via Gemini
            answer = gemini_client.generate_answer(query, full_context)

        # Save to conversation if authenticated
        if conversation_id and user_id:
            self._conversation_service.add_message(conversation_id, "user", query)
            self._conversation_service.add_message(
                conversation_id, "assistant", answer, sources
            )

        return {
            "answer": answer,
            "sources": sources,
            "conversation_id": conversation_id,
        }


# Singleton instance
chat_service = ChatService()
