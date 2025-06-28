"""
Conftest for Client Repository test suite following seedwork patterns.

Provides:
- Automatic reset of data-factory counters before every test for isolation
- ClientRepository and MenuRepository fixtures wired to the real PostgreSQL database
- AsyncSession fixtures for direct ORM operations
- Simple performance benchmarking utility (re-used from meal tests)

All tests are marked as integration tests and run with AnyIO (asyncio) backend.
"""

import pytest
import anyio
import time
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.recipes_catalog.core.adapters.client.repositories.menu_repository import MenuRepo
from src.contexts.recipes_catalog.core.adapters.client.repositories.client_repository import ClientRepo

# Data-factory helpers


from tests.contexts.recipes_catalog.core.adapters.client.repositories.data_factories.client.client_domain_factories import reset_client_counters
from tests.contexts.recipes_catalog.core.adapters.client.repositories.data_factories.client.client_orm_factories import create_client_orm, reset_client_orm_counters
from tests.contexts.recipes_catalog.core.adapters.client.repositories.data_factories.menu.menu_domain_factories import reset_menu_counters
from tests.contexts.recipes_catalog.core.adapters.client.repositories.data_factories.shared_domain_factories import reset_tag_counters
from tests.contexts.recipes_catalog.core.adapters.client.repositories.data_factories.menu.menu_orm_factories import reset_menu_orm_counters
from tests.contexts.recipes_catalog.core.adapters.client.repositories.data_factories.shared_orm_factories import reset_tag_orm_counters

pytestmark = [pytest.mark.anyio, pytest.mark.integration]

# =============================================================================
# GLOBAL AUTOUSE FIXTURE
# =============================================================================


@pytest.fixture(autouse=True)
def _reset_data_factory_counters():
    """Reset menu and client data-factory counters before every test for deterministic behaviour"""
    reset_menu_counters()
    reset_tag_counters()
    reset_menu_orm_counters()
    reset_tag_orm_counters()
    reset_client_counters()
    reset_client_orm_counters()


# =============================================================================
# CORE REPOSITORY / SESSION FIXTURES
# =============================================================================


@pytest.fixture
async def menu_repository(async_pg_session: AsyncSession) -> MenuRepo:
    """Concrete MenuRepo instance bound to a clean async session"""
    return MenuRepo(db_session=async_pg_session)


@pytest.fixture
async def client_repository(async_pg_session: AsyncSession) -> ClientRepo:
    """Concrete ClientRepo instance bound to a clean async session"""
    return ClientRepo(db_session=async_pg_session)


@pytest.fixture
async def test_session(async_pg_session: AsyncSession):
    """Alias for an async session that tests may use for direct ORM operations."""
    yield async_pg_session


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


@pytest.fixture
def benchmark_timer():
    """Context-manager style timer for quick performance assertions."""

    class Timer:
        def __init__(self):
            self.start: Optional[float] = None
            self.elapsed: Optional[float] = None

        def __enter__(self):
            self.start = time.perf_counter()
            return self

        def __exit__(self, *exc):
            if self.start is not None:
                self.elapsed = time.perf_counter() - self.start

        def assert_lt(self, seconds: float):
            if self.elapsed is None:
                raise RuntimeError("Timer not used as context manager")
            assert self.elapsed < seconds, f"Operation took {self.elapsed:.3f}s – expected < {seconds}s"

    return Timer 