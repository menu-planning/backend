"""
Integration Test Database Setup

This conftest provides database fixtures specifically for integration tests.
Only tests marked with @pytest.mark.integration will use these fixtures.

Key improvements:
- Database setup only for tests that need it
- Prevents unit tests from unnecessary database overhead
- Maintains test isolation with proper cleanup
- Supports both integration and e2e test patterns
"""

import logging
from collections.abc import AsyncGenerator

import pytest
from src.db.base import SaBase
import src.db.database as db
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from src.logging.logger import get_logger
from tenacity import (
    AsyncRetrying,
    RetryError,
    after_log,
    before_log,
    stop_after_attempt,
    wait_fixed,
)

MAX_RETRIES = 2
WAIT_SECONDS = 5

@pytest.fixture(scope="session")
async def wait_for_postgres_to_come_up():
    """Wait for PostgreSQL to be ready - only for integration/e2e tests."""
    log = get_logger("integration_test.postgres_wait")
    
    async with db.async_db._engine.begin() as conn:
        try:
            log.info(
                "Starting PostgreSQL connection wait",
                max_retries=MAX_RETRIES,
                wait_seconds=WAIT_SECONDS
            )
            
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(MAX_RETRIES),
                wait=wait_fixed(WAIT_SECONDS),
            ):
                with attempt:
                    log.debug(
                        "Attempting PostgreSQL connection",
                        attempt_number=attempt.retry_state.attempt_number
                    )
                    await conn.execute(text("SELECT 1"))
                    
            log.info("PostgreSQL connection established successfully")
            
        except RetryError as e:
            log.error(
                "Failed to establish PostgreSQL connection after retries",
                max_retries=MAX_RETRIES,
                wait_seconds=WAIT_SECONDS,
                error=str(e)
            )
            raise e

@pytest.fixture(scope="session")
async def populate_roles_table(wait_for_postgres_to_come_up):
    """Populate required roles for integration tests."""
    log = get_logger("integration_test.roles_setup")
    
    async with db.async_db._engine.begin() as conn:
        try:
            log.info("Populating IAM roles table for integration tests")
            
            raw_sql = """
                INSERT INTO iam.roles (name, context, permissions)
                VALUES 
                    ('user', 'IAM', 'access_basic_features'),
                    ('administrator', 'IAM', 'manage_users, manage_roles, view_audit_log')
                ON CONFLICT DO NOTHING;
            """
            await conn.execute(text(raw_sql))
            await conn.commit()
            
            log.info(
                "Successfully populated IAM roles",
                roles=["user", "administrator"]
            )
            
        except Exception as e:
            log.error(
                "Failed to populate IAM roles table",
                error=str(e),
                error_type=type(e).__name__
            )
            raise e

@pytest.fixture(scope="session")
async def async_pg_session_factory(
    wait_for_postgres_to_come_up,
) -> async_sessionmaker[AsyncSession]:
    """Session factory for integration tests."""
    return db.async_db.async_session_factory

def clear_tables(connection):
    """Clear all business tables for test isolation."""
    log = get_logger("integration_test.table_cleanup")
    
    # Define the actual business schemas that exist in the database
    EXISTING_SCHEMAS = {'recipes_catalog', 'products_catalog', 'iam', 'shared_kernel'}
    
    tables_cleared = []
    tables_skipped = []
    tables_failed = []
    
    # Use TRUNCATE ... CASCADE to clear all tables, handling foreign key constraints automatically
    # Only clean tables from existing business schemas, skip test models
    for table in reversed(SaBase.metadata.sorted_tables):
        # Skip tables that don't have a schema or have test/mock schemas
        if table.schema is None or table.schema not in EXISTING_SCHEMAS:
            tables_skipped.append(f"{table.schema or 'public'}.{table.name}")
            continue
            
        try:
            connection.execute(text(f"TRUNCATE TABLE {table.schema}.{table.name} CASCADE"))
            tables_cleared.append(f"{table.schema}.{table.name}")
        except Exception as e:
            # Log but don't fail if a table doesn't exist or can't be truncated
            table_name = f"{table.schema}.{table.name}"
            tables_failed.append({"table": table_name, "error": str(e)})
            log.warning(
                "Could not truncate table",
                table=table_name,
                error=str(e),
                error_type=type(e).__name__
            )
            continue
    
    log.info(
        "Database table cleanup completed",
        tables_cleared_count=len(tables_cleared),
        tables_skipped_count=len(tables_skipped),
        tables_failed_count=len(tables_failed),
        schemas_processed=list(EXISTING_SCHEMAS)
    )
    
    if tables_failed:
        log.debug(
            "Some tables failed to truncate",
            failed_tables=[item["table"] for item in tables_failed]
        )

@pytest.fixture(scope="function")
async def clean_database_before_test(wait_for_postgres_to_come_up):
    """Clean database before each integration test - NOT autouse."""
    log = get_logger("integration_test.pre_test_cleanup")
    
    log.debug("Starting pre-test database cleanup")
    
    # open a transactional connection, clear _all_ tables, commit
    async with db.async_db._engine.begin() as conn:
        await conn.run_sync(clear_tables)
    
    log.debug("Pre-test database cleanup completed")
    # now every test starts with an empty DB

@pytest.fixture
async def clean_async_pg_session(
    async_pg_session_factory: async_sessionmaker[AsyncSession],
    clean_database_before_test,
) -> AsyncGenerator[AsyncSession, None]:
    """Clean session for integration tests with database cleanup."""
    # 1) Database is already cleaned by clean_database_before_test
    # 2) Hand out a "fresh" session to the test
    async with async_pg_session_factory() as session:
        yield session
        # rollback whatever the test did
        await session.rollback()

@pytest.fixture
async def async_pg_session(
    async_pg_session_factory: async_sessionmaker[AsyncSession],
    populate_roles_table,
) -> AsyncGenerator[AsyncSession, None]:
    """Standard session for integration tests."""
    log = get_logger("integration_test.session_management")
    
    async with async_pg_session_factory() as session:
        log.debug("Created PostgreSQL session for integration test")
        yield session
        log.debug("Closing PostgreSQL session and rolling back transactions")
        await session.rollback() 