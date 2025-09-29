"""Async database engine and session factory setup.

This module initializes an async SQLAlchemy engine and exposes a session
factory for use across the application. It uses a `NullPool` by default to
avoid connection pooling issues in short-lived or serverless contexts.
"""

from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from src.config.app_config import get_app_settings


class Database:
    """Container for the async SQLAlchemy engine and session factory.

    The engine is configured with the REPEATABLE READ isolation level and a
    `NullPool`. The database URL is read from application settings by default
    but can be overridden.

    Attributes:
        async_session_factory: Factory for creating async database sessions.
    """
    def __init__(self, db_url: str | None = None) -> None:
        """Create an async engine and session factory.

        Args:
            db_url: SQLAlchemy database URL. Defaults to the configured async
                DSN from application settings.

        Notes:
            Engine configured with REPEATABLE READ isolation and NullPool.
        """
        settings = get_app_settings()
        
        self._engine: AsyncEngine = create_async_engine(
            db_url or str(settings.async_sqlalchemy_db_uri),
            # future=True,
            # echo=True,
            isolation_level="REPEATABLE READ",
            # pool_size=settings.sa_pool_size,
            poolclass=NullPool,
            # connect_args={"sslmode": "require"},
        )
        self.async_session_factory: async_sessionmaker[AsyncSession] = (
            async_sessionmaker(
                bind=self._engine,
                expire_on_commit=False,
                class_=AsyncSession,
            )
        )


async_db = Database()


def get_db_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the global async session factory.

    Returns:
        A cached async session factory bound to the global engine.

    Notes:
        Uses the global Database instance configured at module import.
    """
    return async_db.async_session_factory
