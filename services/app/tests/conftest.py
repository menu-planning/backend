import contextlib
import gc
import logging
import tracemalloc
import uuid
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress

import aio_pika
import aiormq
import anyio
import pamqp
import pytest
import src.contexts.iam.fastapi.deps as iam_deps
import src.contexts.seedwork.fastapi.deps as seedwork_deps
from src.db.base import SaBase
import src.db.database as db
from fastapi import FastAPI
from httpx import AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src import main
from src.config.api_config import api_settings
from src.contexts.iam.shared.domain.entities.user import User
from src.logging.logger import logger
from src.rabbitmq.config import rabbitmq_settings
from tenacity import (
    AsyncRetrying,
    RetryError,
    after_log,
    before_log,
    stop_after_attempt,
    wait_fixed,
)

pytestmark = pytest.mark.anyio

MAX_RETRIES = 2
WAIT_SECONDS = 5


# @pytest.fixture(scope="session")
# def event_loop():
#     loop = asyncio.get_event_loop_policy().new_event_loop()
#     yield loop
#     loop.close()


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest.fixture(scope="session")
def app(anyio_backend) -> FastAPI:
    return main.app

@pytest.fixture(scope="session", autouse=True)
async def wait_for_postgres_to_come_up(anyio_backend):
    async with db.async_db._engine.begin() as conn:
        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(MAX_RETRIES),
                wait=wait_fixed(WAIT_SECONDS),
                before=before_log(logger, logging.INFO),
                after=after_log(logger, logging.WARN),
            ):
                with attempt:
                    await conn.execute(text("SELECT 1"))
        except RetryError as e:
            logger.error(e)
            raise e
    # try:
    #     async for attempt in AsyncRetrying(
    #         stop=stop_after_attempt(MAX_RETRIES),
    #         wait=wait_fixed(WAIT_SECONDS),
    #         before=before_log(logger, logging.INFO),
    #         after=after_log(logger, logging.WARN),
    #     ):
    #         with attempt:
    #             with anyio.fail_after(WAIT_SECONDS - 1):
    #                 try:
    #                     engine = db.async_db._engine
    #                     # engine.echo = True
    #                     async with engine.begin() as con:
    #                         await con.run_sync(db.SaBase.metadata.drop_all)
    #                         await con.run_sync(db.SaBase.metadata.create_all)
    #                         await con.execute(text("SELECT 1"))
    #                     # await engine.dispose()
    #                 except Exception as e:
    #                     logger.error(e)
    #                     raise e
    # except RetryError as e:
    #     logger.error(e)
    #     raise e


@pytest.fixture(scope="session", autouse=True)
async def populate_roles_table(anyio_backend, wait_for_postgres_to_come_up):
    async with db.async_db._engine.begin() as conn:
        try:
            raw_sql = """
                INSERT INTO iam.roles (name, context, permissions)
                VALUES 
                    ('user', 'IAM', 'access_basic_features'),
                    ('administrator', 'IAM', 'manage_users, manage_roles, view_audit_log')
                ON CONFLICT DO NOTHING;
            """
            await conn.execute(text(raw_sql))
            await conn.commit()
        except RetryError as e:
            logger.error(e)
            raise e


@pytest.fixture(scope="session")
async def async_pg_db(
    anyio_backend,
    # wait_for_postgres_to_come_up,
) -> db.Database:
    return db.async_db


@pytest.fixture(scope="session")
async def async_pg_session_factory(
    anyio_backend,
    async_pg_db: db.Database,
) -> async_sessionmaker[AsyncSession]:
    return async_pg_db.async_session_factory


# @pytest.fixture()
# async def postgres_async_engine():
#     engine = create_async_engine(
#         app_settings.async_sqlalchemy_db_uri,
#         future=True,
#         isolation_level="REPEATABLE READ",
#         pool_size=app_settings.sa_pool_size,
#     )
#     yield engine
#     await engine.dispose()


# @pytest.fixture()
# async def async_pg_session_factory(
#     postgres_async_engine,
# ) -> async_sessionmaker[AsyncSession]:
#     return async_sessionmaker(bind=postgres_async_engine, expire_on_commit=False)


# def clear_tables(connection):
#     with contextlib.closing(connection) as con:
#         trans = con.begin()
#         for table in reversed(SaBase.metadata.sorted_tables):
#             con.execute(table.delete())
#         trans.commit()

def clear_tables(connection):
    # assume the caller has already begun a transaction
    for table in reversed(SaBase.metadata.sorted_tables):
        connection.execute(table.delete())


@pytest.fixture(scope="function", autouse=True)
async def clean_database_before_test():
    # open a transactional connection, clear _all_ tables, commit
    async with db.async_db._engine.begin() as conn:
        await conn.run_sync(clear_tables)
    # now every test starts with an empty DB


@pytest.fixture
async def clean_async_pg_session(
    # event_loop,
    async_pg_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    # async with db.async_db._engine.connect() as conn:
    #     await conn.run_sync(clear_tables)
    # async with async_pg_session_factory() as session:
    #     yield session
    #     await session.flush()
    #     print("closing clean pg session")
    #     await session.rollback()

    # 1) Open a single transaction, clear all tables, and commit
    async with db.async_db._engine.begin() as conn:
        await conn.run_sync(clear_tables)

    # 2) Hand out a “fresh” session to the test
    async with async_pg_session_factory() as session:
        yield session
        # rollback whatever the test did
        await session.rollback()


@pytest.fixture
async def async_pg_session(
    # event_loop,
    anyio_backend,
    async_pg_session_factory: async_sessionmaker[AsyncSession],
) -> AsyncGenerator[AsyncSession, None]:
    async with async_pg_session_factory() as session:
        yield session
        # await session.flush()
        print("closing pg session")
        await session.rollback()


# @pytest.fixture(autouse=True)
# async def every_test():
#     print(threading.active_count())
#     print(async_db._engine.pool.status())
#     assert False


# @pytest.fixture()
# async def async_pg_session(
#     postgres_async_engine,
# ) -> AsyncSession:
#     async with postgres_async_engine.begin() as connection:
#         async with async_session(bind=connection) as session:
#             yield session
#             await session.flush()
#             await session.rollback()


@pytest.fixture(scope="session")
async def wait_for_rabbitmq_to_come_up(anyio_backend):
    try:
        async for attempt in AsyncRetrying(
            stop=stop_after_attempt(MAX_RETRIES),
            wait=wait_fixed(WAIT_SECONDS),
            before=before_log(logger, logging.INFO),
            after=after_log(logger, logging.WARN),
        ):
            with attempt:
                with anyio.fail_after(WAIT_SECONDS - 1):
                    try:
                        connection = await aio_pika.connect_robust(
                            rabbitmq_settings.rabbitmq_url
                        )
                        await connection.close()
                    except Exception as e:
                        logger.error(e)
                        raise e
    except RetryError as e:
        logger.error(e)
        raise e


@pytest.fixture(scope="session")
async def httpx_client(app) -> AsyncGenerator:
    async with AsyncClient(app=app, base_url=str(api_settings.api_url)) as c:
        yield c
    # conn = await aio_pika_connection.get_connection()
    # await conn.close()


@pytest.fixture
async def make_client_with_user_id(app):
    @asynccontextmanager
    async def _client_with_user_id_override(user_id: str):
        async def mock_current_user_id():
            return user_id

        app.dependency_overrides[seedwork_deps.current_user_id] = mock_current_user_id

        try:
            async with AsyncClient(app=app, base_url=str(api_settings.api_url)) as c:
                yield c
        finally:
            # conn = await aio_pika_connection.get_connection()
            # await conn.close()
            app.dependency_overrides.clear()

    return _client_with_user_id_override


@pytest.fixture
async def make_client_with_active_user(app):
    @asynccontextmanager
    async def _client_with_user_override(User: User):
        async def mock_current_user():
            return User

        app.dependency_overrides[iam_deps.current_active_user] = mock_current_user

        try:
            async with AsyncClient(app=app, base_url=str(api_settings.api_url)) as c:
                yield c
        finally:
            # conn = await aio_pika_connection.get_connection()
            # await conn.close()
            app.dependency_overrides.clear()

    return _client_with_user_override


@pytest.fixture(scope="session")
def memory_tracer(anyio_backend):
    tracemalloc.start()
    tracemalloc.clear_traces()

    filters = (
        tracemalloc.Filter(True, aiormq.__file__),
        tracemalloc.Filter(True, pamqp.__file__),
        tracemalloc.Filter(True, aio_pika.__file__),
    )

    snapshot_before = tracemalloc.take_snapshot().filter_traces(filters)

    try:
        yield

        with suppress(Exception):
            gc.collect()

        snapshot_after = tracemalloc.take_snapshot().filter_traces(filters)

        top_stats = snapshot_after.compare_to(
            snapshot_before,
            "lineno",
            cumulative=True,
        )

        assert not top_stats
    finally:
        tracemalloc.stop()


def pytest_addoption(parser):
    parser.addoption("--e2e", action="store_true", help="run e2e tests")
    parser.addoption("--integration", action="store_true", help="run integration tests")


def pytest_runtest_setup(item):
    if "e2e" in item.keywords and not item.config.getvalue("e2e"):
        pytest.skip("need --e2e option to run")
    if "integration" in item.keywords and not item.config.getvalue("integration"):
        pytest.skip("need --integration option to run")
