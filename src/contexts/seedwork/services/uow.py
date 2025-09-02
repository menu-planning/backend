"""Unit-of-work abstraction for coordinating atomic operations.

Provides transaction boundary management for domain operations with automatic
rollback on context exit and domain event collection from repositories.
"""

from abc import ABC, abstractmethod
from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class UnitOfWork(ABC):
    """Application transaction boundary for atomic operations.

    Manages database session lifecycle, exposes commit/rollback operations,
    and collects domain events from repositories. Supports async context
    manager usage with automatic rollback on context exit.

    Usage:
        async with UnitOfWork(session_factory) as uow: ...

    Transactions:
        Exactly-once commit. Implicit rollback on context exit if not committed.

    Notes:
        Repositories available: session. Calls must occur within an active context.
        Concurrency: async; not thread-safe.
    """

    session_factory: async_sessionmaker[AsyncSession]

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ):
        """Initialize unit-of-work with session factory.

        Args:
            session_factory: SQLAlchemy async session factory for creating
                database sessions.
        """
        self.session_factory = session_factory

    @abstractmethod
    async def __aenter__(self):
        """Open a database session and return self for async context blocks.

        Returns:
            self: The unit-of-work instance with active session.

        Side Effects:
            Creates and stores new AsyncSession instance.
        """
        self.session: AsyncSession = self.session_factory()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: TracebackType | None = None,
    ):
        """Rollback and close the session on context exit.

        Args:
            exc_type: Exception type if exception occurred.
            exc_value: Exception value if exception occurred.
            traceback: Exception traceback if exception occurred.

        Side Effects:
            Always rolls back transaction and closes session regardless
            of success or failure.
        """
        await self.session.rollback()
        await self.session.close()

    async def commit(self):
        """Commit the current transaction.

        Side Effects:
            Persists all changes to database. Caller must handle
            commit failures.
        """
        await self.session.commit()

    def collect_new_events(self):
        """Yield domain events produced by repositories in this UoW.

        Returns:
            Generator yielding domain events from tracked objects.

        Notes:
            Iterates through all attributes looking for objects with
            'seen' tracking and 'events' collections.
        """
        for attr_name in self.__dict__:
            attr = getattr(self, attr_name)
            if hasattr(attr, "seen"):
                for obj in attr.seen:
                    if hasattr(obj, "events"):
                        while obj.events:
                            yield obj.events.pop(0)

    async def rollback(self):
        """Rollback the current transaction.

        Side Effects:
            Discards all uncommitted changes in current transaction.
        """
        await self.session.rollback()

    async def close(self):
        """Close the unit-of-work and cleanup resources.

        Side Effects:
            Rolls back any uncommitted changes and closes session.
            Alias for __aexit__ method.
        """
        await self.__aexit__()
