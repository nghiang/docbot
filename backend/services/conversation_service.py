"""Conversation service for handling conversation storage in MongoDB."""

from datetime import datetime
from typing import Optional

from bson import ObjectId

from core.mongodb import mongodb_client


class ConversationService:
    """Service class for conversation operations using MongoDB."""

    CONVERSATIONS_COLLECTION = "conversations"
    MESSAGES_COLLECTION = "messages"

    def __init__(self):
        self._mongodb = mongodb_client

    def _get_db(self):
        """Get MongoDB database instance."""
        return self._mongodb.db

    def create(self, user_id: int, title: Optional[str] = None) -> str:
        """Create a new conversation for a user.

        Args:
            user_id: The user's ID.
            title: Optional conversation title.

        Returns:
            Conversation ID as string.
        """
        db = self._get_db()
        conversation = {
            "user_id": user_id,
            "title": title or "New Conversation",
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow(),
        }
        result = db[self.CONVERSATIONS_COLLECTION].insert_one(conversation)
        return str(result.inserted_id)

    def get(self, conversation_id: str, user_id: int) -> Optional[dict]:
        """Get a conversation by ID, ensuring it belongs to the user.

        Args:
            conversation_id: The conversation's ID.
            user_id: The user's ID.

        Returns:
            Conversation dict if found, None otherwise.
        """
        db = self._get_db()
        try:
            conversation = db[self.CONVERSATIONS_COLLECTION].find_one(
                {
                    "_id": ObjectId(conversation_id),
                    "user_id": user_id,
                }
            )
            if conversation:
                conversation["id"] = str(conversation.pop("_id"))
            return conversation
        except Exception:
            return None

    def get_by_user(self, user_id: int, limit: int = 20) -> list[dict]:
        """Get all conversations for a user, sorted by most recent.

        Args:
            user_id: The user's ID.
            limit: Maximum number of conversations to return.

        Returns:
            List of conversation dicts.
        """
        db = self._get_db()
        conversations = list(
            db[self.CONVERSATIONS_COLLECTION]
            .find({"user_id": user_id})
            .sort("updated_at", -1)
            .limit(limit)
        )
        for conv in conversations:
            conv["id"] = str(conv.pop("_id"))
        return conversations

    def update_title(
        self,
        conversation_id: str,
        user_id: int,
        title: str,
    ) -> bool:
        """Update conversation title.

        Args:
            conversation_id: The conversation's ID.
            user_id: The user's ID.
            title: New title.

        Returns:
            True if updated successfully, False otherwise.
        """
        db = self._get_db()
        try:
            result = db[self.CONVERSATIONS_COLLECTION].update_one(
                {"_id": ObjectId(conversation_id), "user_id": user_id},
                {"$set": {"title": title, "updated_at": datetime.utcnow()}},
            )
            return result.modified_count > 0
        except Exception:
            return False

    def delete(self, conversation_id: str, user_id: int) -> bool:
        """Delete a conversation and all its messages.

        Args:
            conversation_id: The conversation's ID.
            user_id: The user's ID.

        Returns:
            True if deleted successfully, False otherwise.
        """
        db = self._get_db()
        try:
            # Delete messages first
            db[self.MESSAGES_COLLECTION].delete_many(
                {"conversation_id": conversation_id}
            )
            # Delete conversation
            result = db[self.CONVERSATIONS_COLLECTION].delete_one(
                {
                    "_id": ObjectId(conversation_id),
                    "user_id": user_id,
                }
            )
            return result.deleted_count > 0
        except Exception:
            return False

    def add_message(
        self,
        conversation_id: str,
        role: str,
        content: str,
        sources: Optional[list[dict]] = None,
    ) -> str:
        """Add a message to a conversation.

        Args:
            conversation_id: The conversation's ID.
            role: Message role ('user' or 'assistant').
            content: Message content.
            sources: Optional list of source documents.

        Returns:
            Message ID as string.
        """
        db = self._get_db()
        message = {
            "conversation_id": conversation_id,
            "role": role,
            "content": content,
            "sources": sources or [],
            "created_at": datetime.utcnow(),
        }
        result = db[self.MESSAGES_COLLECTION].insert_one(message)

        # Update conversation's updated_at
        try:
            db[self.CONVERSATIONS_COLLECTION].update_one(
                {"_id": ObjectId(conversation_id)},
                {"$set": {"updated_at": datetime.utcnow()}},
            )
        except Exception:
            pass

        return str(result.inserted_id)

    def get_messages(
        self,
        conversation_id: str,
        limit: Optional[int] = None,
    ) -> list[dict]:
        """Get all messages in a conversation.

        Args:
            conversation_id: The conversation's ID.
            limit: Optional maximum number of messages.

        Returns:
            List of message dicts, sorted by creation time.
        """
        db = self._get_db()
        query = (
            db[self.MESSAGES_COLLECTION]
            .find({"conversation_id": conversation_id})
            .sort("created_at", 1)
        )

        if limit:
            query = query.limit(limit)

        messages = list(query)
        for msg in messages:
            msg["id"] = str(msg.pop("_id"))
        return messages

    def get_recent_qa_pairs(
        self,
        conversation_id: str,
        limit: int = 5,
    ) -> list[dict]:
        """Get the most recent Q&A pairs from a conversation.

        Args:
            conversation_id: The conversation's ID.
            limit: Maximum number of pairs to return.

        Returns:
            List of Q&A pair dicts with 'question' and 'answer' keys.
        """
        db = self._get_db()

        # Get last N*2 messages (to get N pairs)
        messages = list(
            db[self.MESSAGES_COLLECTION]
            .find({"conversation_id": conversation_id})
            .sort("created_at", -1)
            .limit(limit * 2)
        )

        # Reverse to get chronological order
        messages.reverse()

        # Build Q&A pairs
        qa_pairs = []
        for i in range(0, len(messages) - 1, 2):
            if messages[i]["role"] == "user" and messages[i + 1]["role"] == "assistant":
                qa_pairs.append(
                    {
                        "question": messages[i]["content"],
                        "answer": messages[i + 1]["content"],
                    }
                )

        return qa_pairs[-limit:] if len(qa_pairs) > limit else qa_pairs


# Singleton instance
conversation_service = ConversationService()
