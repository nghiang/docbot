"""MongoDB client for document storage operations."""

import logging

from pymongo import MongoClient
from pymongo.database import Database
from pymongo.collection import Collection

from core.config import settings

logger = logging.getLogger(__name__)


class MongoDBClient:
    """Client class for MongoDB operations."""

    def __init__(self):
        self._client: MongoClient | None = None
        self._db: Database | None = None

    @property
    def client(self) -> MongoClient:
        """Get the MongoDB client (lazy initialization)."""
        if self._client is None:
            self._client = MongoClient(settings.mongodb_url)
            logger.info("MongoDB client initialized")
        return self._client

    @property
    def db(self) -> Database:
        """Get the MongoDB database instance."""
        if self._db is None:
            self._db = self.client[settings.MONGODB_DB]
        return self._db

    def get_collection(self, name: str) -> Collection:
        """Get a collection by name.

        Args:
            name: Collection name.

        Returns:
            MongoDB Collection instance.
        """
        return self.db[name]


# Singleton instance
mongodb_client = MongoDBClient()
