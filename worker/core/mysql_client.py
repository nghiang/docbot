from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from core.config import settings

pool_settings = {
    "pool_recycle": 1800,
    "echo": False,
    "echo_pool": False,
    "pool_pre_ping": True,
    "pool_timeout": 30,  # Allow waiting for an available connection (prevent failures)
    "pool_size": 30,  # Matches CPU threads for max efficiency
    "max_overflow": 20,  # Allows temporary spike handling (30 + 20 = 50 max)
    "pool_reset_on_return": "commit",  # Instead of `pool_recycle`
}
engine = create_engine(settings.SQLALCHEMY_DATABASE_URI, **pool_settings)

db_session = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)