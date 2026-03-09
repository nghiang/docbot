"""
Standalone migration script — runs Alembic upgrade to head.
Stamps existing databases that predate Alembic tracking.
"""

import logging

from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, text

from core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def run_migrations():
    alembic_cfg = Config("alembic.ini")
    engine = create_engine(settings.postgres_url)

    with engine.connect() as conn:
        has_alembic = conn.execute(
            text(
                "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'alembic_version')"
            )
        ).scalar()

        if not has_alembic:
            has_tables = conn.execute(
                text(
                    "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = 'users')"
                )
            ).scalar()
            if has_tables:
                logger.info("Existing database detected — stamping Alembic to head")
                command.stamp(alembic_cfg, "head")
                engine.dispose()
                return

    engine.dispose()
    logger.info("Running migrations to head...")
    command.upgrade(alembic_cfg, "head")
    logger.info("Migrations complete")


if __name__ == "__main__":
    run_migrations()
