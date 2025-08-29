from abc import ABC, abstractmethod
from types import TracebackType

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker


class UnitOfWork(ABC):
    """Abstract unit of work protocol.

    This class is abstraction over the idea of atomic operations.
    It is the entrypoint for clients of the repositories, it manages the
    database state, collects domain events and can work as a context manager.
    """

    session_factory: async_sessionmaker[AsyncSession]

    def __init__(
        self,
        session_factory: async_sessionmaker[AsyncSession],
    ):
        """Initialize ``UnitOfWork`` class.

        Args:
            session_factory: a :class`async_sessionmaker
            <sqlalchemy.ext.asyncio.async_sessionmaker>` instance
        """
        self.session_factory = session_factory

    @abstractmethod
    async def __aenter__(self):
        """Support the async contextmanager protocol to allow easier visualization of
        what blocks of code are grouped together and initializing database session
        and repositories.
        """
        self.session: AsyncSession = self.session_factory()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None = None,
        exc_value: BaseException | None = None,
        traceback: TracebackType | None = None,
    ):
        """Gracefully closes database sessions."""
        await self.session.rollback()
        await self.session.close()

    async def commit(self):
        await self.session.commit()

    def collect_new_events(self):
        """Collects domain events"""
        for attr_name in self.__dict__:
            attr = getattr(self, attr_name)
            if hasattr(attr, "seen"):
                for obj in attr.seen:
                    if hasattr(obj, "events"):
                        while obj.events:
                            yield obj.events.pop(0)

    async def rollback(self):
        await self.session.rollback()

    async def close(self):
        await self.__aexit__()
