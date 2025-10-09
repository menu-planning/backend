"""FastAPI-optimized async database engine and session factory setup.

This module provides a FastAPI-specific database configuration that enables
connection pooling and optimizations for long-running web applications.
It complements the existing Lambda-optimized database configuration.
"""

import logfire
from sqlalchemy.pool import AsyncAdaptedQueuePool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from src.config.app_config import get_app_settings


class FastAPIDatabase:
    """FastAPI-optimized database configuration with connection pooling.

    This class provides a database configuration specifically optimized for
    FastAPI applications with connection pooling, pre-ping validation, and
    appropriate pool settings for concurrent web requests.

    Attributes:
        async_session_factory: Factory for creating async database sessions.
    """
    
    def __init__(self, db_url: str | None = None) -> None:
        """Create a FastAPI-optimized async engine and session factory.

        Args:
            db_url: SQLAlchemy database URL. Defaults to the configured async
                DSN from application settings.

        Notes:
            Engine configured with REPEATABLE READ isolation and AsyncAdaptedQueuePool
            for optimal FastAPI performance with connection pooling.
        """
        settings = get_app_settings()
        
        self._engine: AsyncEngine = create_async_engine(
            db_url or str(settings.async_sqlalchemy_db_uri),
            isolation_level="REPEATABLE READ",
            # FastAPI-optimized connection pooling
            poolclass=AsyncAdaptedQueuePool,
            pool_size=settings.fastapi_pool_size,
            max_overflow=settings.fastapi_max_overflow,
            pool_pre_ping=settings.fastapi_pool_pre_ping,
            pool_recycle=settings.fastapi_pool_recycle,
            # Additional FastAPI optimizations
            echo=False,  # Disable SQL logging in production
            future=True,  # Enable SQLAlchemy 2.0 features
            # asyncpg-specific optimizations
            connect_args={
                "server_settings": {
                    "application_name": "fastapi_app",
                    "jit": "off",  # Disable JIT for better connection reuse
                }
            },
        )
        logfire.instrument_sqlalchemy(self._engine)
        self.async_session_factory: async_sessionmaker[AsyncSession] = (
            async_sessionmaker(
                bind=self._engine,
                expire_on_commit=False,
                class_=AsyncSession,
                # FastAPI-specific session optimizations
                autoflush=False,  # Manual flush control for better performance
                autocommit=False,  # Explicit transaction control
            )
        )


# Global FastAPI database instance
fastapi_db = FastAPIDatabase()


def get_fastapi_session_factory() -> async_sessionmaker[AsyncSession]:
    """Return the FastAPI-optimized async session factory.

    Returns:
        A cached async session factory bound to the FastAPI-optimized engine.

    Notes:
        Uses the global FastAPIDatabase instance configured at module import.
        This factory is optimized for FastAPI applications with connection pooling.
    """
    return fastapi_db.async_session_factory


def get_fastapi_engine() -> AsyncEngine:
    """Return the FastAPI-optimized async engine.

    Returns:
        The FastAPI-optimized async engine with connection pooling enabled.

    Notes:
        Useful for direct engine operations or health checks.
    """
    return fastapi_db._engine
