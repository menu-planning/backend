from sqlalchemy import NullPool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from src.config.app_config import app_settings


class Database:
    def __init__(self, db_url: str = str(app_settings.async_sqlalchemy_db_uri)) -> None:
        self._engine: AsyncEngine = create_async_engine(
            db_url,
            # future=True,
            # echo=True,
            isolation_level="REPEATABLE READ",
            # pool_size=app_settings.sa_pool_size,
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
    return async_db.async_session_factory