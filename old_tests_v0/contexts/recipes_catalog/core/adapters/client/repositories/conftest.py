"""
Conftest for Client Repository test suite following seedwork patterns.

Provides:
- Automatic reset of data-factory counters before every test for isolation
- ClientRepository and MenuRepository fixtures wired to the real PostgreSQL database
- AsyncSession fixtures for direct ORM operations with targeted database cleanup
- Simple performance benchmarking utility (re-used from meal tests)

All tests are marked as integration tests and run with AnyIO (asyncio) backend.
"""

from collections.abc import AsyncGenerator

import pytest

# Data-factory helpers
from old_tests_v0.contexts.recipes_catalog.core.adapters.client.repositories.data_factories.client.client_orm_factories import (
    create_client_orm,
)

# Import counter manager for test isolation
from old_tests_v0.utils.counter_manager import reset_all_counters
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.recipes_catalog.core.adapters.client.repositories.client_repository import (
    ClientRepo,
)
from src.contexts.recipes_catalog.core.adapters.client.repositories.menu_repository import (
    MenuRepo,
)

# Integration database fixtures are loaded from top-level conftest.py

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


# =============================================================================
# SMART DATABASE CLEANUP
# =============================================================================


async def clean_client_test_tables(session: AsyncSession):
    """
    Smart cleanup that only targets tables used by client/menu repository tests.

    This approach is much faster than TRUNCATE CASCADE on all tables since it:
    - Only cleans tables these tests actually use
    - Respects foreign key dependencies
    - Uses DELETE instead of TRUNCATE to avoid AccessExclusiveLock deadlocks

    Order is critical: most dependent tables first, least dependent last.
    Based on foreign key analysis:
    - menus.client_id -> clients.id
    - meals.menu_id -> menus.id
    - recipes.meal_id -> meals.id
    - association tables -> their referenced entities
    """
    # Tables in dependency order (most dependent → least dependent)
    tables_to_clean = [
        # Association tables first (most dependent)
        "recipes_catalog.recipes_tags_association",  # depends on recipes + tags
        "recipes_catalog.meals_tags_association",  # depends on meals + tags
        "recipes_catalog.menus_tags_association",  # depends on menus + tags
        "recipes_catalog.clients_tags_association",  # depends on clients + tags
        # Child entities with foreign keys
        "recipes_catalog.ratings",  # depends on recipes + users
        "recipes_catalog.ingredients",  # depends on recipes + products
        "recipes_catalog.recipes",  # depends on meals
        "recipes_catalog.meals",  # depends on menus (optional)
        "recipes_catalog.menus",  # depends on clients
        "recipes_catalog.clients",  # depends on users via author_id
        # Shared entities that may be referenced
        "shared_kernel.tags",  # depends on users via author_id
        "iam.user_role_association",  # depends on users + roles
        "iam.users",  # core user entity
        "iam.roles",  # core role entity
    ]

    for table in tables_to_clean:
        try:
            # Use DELETE instead of TRUNCATE to avoid AccessExclusiveLock deadlocks
            # DELETE uses row-level locks which are less aggressive and won't deadlock
            await session.execute(text(f"DELETE FROM {table}"))
        except Exception as e:
            # Table might not exist or be empty - log but continue
            print(f"Info: Could not delete from {table}: {e}")
            continue


@pytest.fixture(scope="function")
async def clean_client_database(async_pg_session_factory) -> None:
    """
    Clean only the tables used by client/menu tests before each test.
    Much faster than cleaning all tables.
    """
    async with async_pg_session_factory() as session:
        await clean_client_test_tables(session)
        await session.commit()


# =============================================================================
# TEST ISOLATION
# =============================================================================


@pytest.fixture(autouse=True)
def reset_counters():
    """
    Auto-reset all counters before each test for proper test isolation.

    This ensures that each test gets fresh, predictable counter values,
    preventing ID collisions and ensuring deterministic test behavior.
    """
    reset_all_counters()
    yield
    # Could add cleanup here if needed, but counters will be reset
    # for the next test anyway


# =============================================================================
# CORE REPOSITORY / SESSION FIXTURES
# =============================================================================


@pytest.fixture
async def menu_repository(test_session: AsyncSession) -> MenuRepo:
    """Concrete MenuRepo instance bound to a clean async session"""
    return MenuRepo(db_session=test_session)


@pytest.fixture
async def client_repository(test_session: AsyncSession) -> ClientRepo:
    """Concrete ClientRepo instance bound to a clean async session"""
    return ClientRepo(db_session=test_session)


@pytest.fixture
async def test_session(
    async_pg_session_factory,
    clean_client_database,  # Ensure database is clean before test
) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide clean test session with targeted database cleanup.
    Uses smart cleanup that only targets tables these tests use.
    """
    async with async_pg_session_factory() as session:
        yield session
        # Rollback any uncommitted changes
        await session.rollback()


@pytest.fixture
async def test_clients(test_session: AsyncSession):
    """Create test clients that can be referenced by menus."""
    clients = []
    for i in range(5):  # Create 5 test clients with IDs client_001 to client_005
        client = create_client_orm(id=f"client_{i+1:03d}")
        test_session.add(client)
        clients.append(client)

    await test_session.commit()
    return clients


# =============================================================================
# PERFORMANCE BENCHMARK FIXTURE
# =============================================================================


# benchmark_timer fixture is now available from top-level conftest.py
