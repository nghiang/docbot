"""PostgreSQL client for relational database operations."""

import logging

from sqlmodel import SQLModel, create_engine, Session

from core.config import settings

logger = logging.getLogger(__name__)


class PostgresClient:
    """Client class for PostgreSQL operations."""

    def __init__(self):
        self._engine = create_engine(settings.postgres_url, echo=False)

    @property
    def engine(self):
        """Get the SQLAlchemy engine."""
        return self._engine

    def init_db(self) -> None:
        """Create all tables in PostgreSQL."""
        SQLModel.metadata.create_all(self._engine)
        logger.info("PostgreSQL database initialized")

    def get_session(self):
        """Get a database session (FastAPI dependency).

        Yields:
            Session instance.
        """
        with Session(self._engine) as session:
            yield session


# Singleton instance
postgres_client = PostgresClient()
