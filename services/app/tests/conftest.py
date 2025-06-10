import gc
import logging
import tracemalloc
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager, suppress


import pytest
from src.db.base import SaBase
import src.db.database as db
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.logging.logger import logger
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


@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

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



def clear_tables(connection):
    # Define the actual business schemas that exist in the database
    EXISTING_SCHEMAS = {'recipes_catalog', 'products_catalog', 'iam', 'shared_kernel'}
    
    # Use TRUNCATE ... CASCADE to clear all tables, handling foreign key constraints automatically
    # Only clean tables from existing business schemas, skip test models
    for table in reversed(SaBase.metadata.sorted_tables):
        # Skip tables that don't have a schema or have test/mock schemas
        if table.schema is None or table.schema not in EXISTING_SCHEMAS:
            continue
            
        try:
            connection.execute(text(f"TRUNCATE TABLE {table.schema}.{table.name} CASCADE"))
        except Exception as e:
            # Log but don't fail if a table doesn't exist or can't be truncated
            print(f"Warning: Could not truncate {table.schema}.{table.name}: {e}")
            continue


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

    # 2) Hand out a "fresh" session to the test
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



@pytest.fixture(scope="session")
def memory_tracer(anyio_backend):
    tracemalloc.start()
    tracemalloc.clear_traces()

    filters = (
        # tracemalloc.Filter(True, aiormq.__file__),
        # tracemalloc.Filter(True, pamqp.__file__),
        # tracemalloc.Filter(True, aio_pika.__file__),
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
