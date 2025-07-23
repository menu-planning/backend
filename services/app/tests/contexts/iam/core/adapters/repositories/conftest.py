"""
Conftest for IAM repository tests following seedwork patterns.

This conftest provides fixtures for testing UserRepository with real database:
- Real database session (no mocks)
- Clean test database state
- Performance benchmarking utilities
- Proper transaction management

Following "Architecture Patterns with Python" principles:
- Test behavior, not implementation
- Use real database connections
- Test fixtures for known DB states
- Catch real DB errors
"""

import pytest
import anyio
from typing import Optional
import time

from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.iam.core.adapters.repositories.user_repository import UserRepo

# Import data factories
from tests.contexts.iam.core.adapters.repositories.user_data_factories import (
    create_user_orm,
    create_role_orm,
    create_admin_user_orm,
    create_basic_user_orm,
    create_user_manager_orm,
    create_multi_role_user_orm,
)

# Load integration database fixtures
pytest_plugins = ["tests.integration_conftest"]

# Mark all tests as integration tests
pytestmark = [pytest.mark.anyio, pytest.mark.integration]


# =============================================================================
# TIMEOUT UTILITIES
# =============================================================================

def timeout_test(seconds: float = 60.0):
    """AnyIO-compatible timeout decorator for individual tests"""
    def decorator(func):
        import functools
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            with anyio.move_on_after(seconds) as cancel_scope:
                result = await func(*args, **kwargs)
                if cancel_scope.cancelled_caught:
                    pytest.fail(f"Test '{func.__name__}' timed out after {seconds} seconds")
                return result
        return wrapper
    return decorator


# =============================================================================
# CORE FIXTURES
# =============================================================================

@pytest.fixture
async def user_repository(async_pg_session: AsyncSession) -> UserRepo:
    """Create UserRepository instance for testing"""
    return UserRepo(db_session=async_pg_session)


@pytest.fixture
async def test_session(async_pg_session: AsyncSession):
    """Provide clean test session for direct database operations"""
    yield async_pg_session


# =============================================================================
# PERFORMANCE UTILITIES
# =============================================================================

@pytest.fixture
def benchmark_timer():
    """Simple timer for performance assertions"""
    
    class Timer:
        def __init__(self):
            self.start_time: Optional[float] = None
            self.elapsed: Optional[float] = None
            
        def __enter__(self):
            self.start_time = time.perf_counter()
            return self
            
        def __exit__(self, *args):
            if self.start_time is not None:
                self.elapsed = time.perf_counter() - self.start_time
            
        def assert_faster_than(self, seconds):
            if self.elapsed is None:
                raise ValueError("Timer was not used in context manager")
            assert self.elapsed < seconds, f"Operation took {self.elapsed:.3f}s, expected < {seconds}s"
    
    return Timer


# =============================================================================
# TEST DATA FIXTURES
# =============================================================================

@pytest.fixture
async def sample_users_orm(test_session: AsyncSession):
    """Create sample ORM users for testing"""
    users = []
    
    # Create different types of users
    admin = create_admin_user_orm(id="sample_admin")
    manager = create_user_manager_orm(id="sample_manager") 
    basic = create_basic_user_orm(id="sample_basic")
    
    users = [admin, manager, basic]
    
    # Add roles first, then users
    for user in users:
        for role in user.roles:
            test_session.add(role)
    
    for user in users:
        test_session.add(user)
    
    await test_session.commit()
    return users


@pytest.fixture
async def large_user_dataset(test_session: AsyncSession):
    """Create large dataset for performance testing"""
    users = []
    user_count = 100
    
    for i in range(user_count):
        # Create varied user types
        if i % 4 == 0:
            user = create_admin_user_orm(id=f"perf_admin_{i}")
        elif i % 4 == 1:
            user = create_user_manager_orm(id=f"perf_manager_{i}")
        elif i % 4 == 2:
            user = create_multi_role_user_orm(id=f"perf_multi_{i}")
        else:
            user = create_basic_user_orm(id=f"perf_basic_{i}")
        
        # Some users are discarded for filtering tests
        if i % 10 == 0:
            user.discarded = True
        
        users.append(user)
    
    # Add all roles first
    for user in users:
        for role in user.roles:
            test_session.add(role)
    
    # Add all users
    for user in users:
        test_session.add(user)
    
    await test_session.commit()
    return users


@pytest.fixture
async def role_specific_users(test_session: AsyncSession):
    """Create users with specific roles for role filtering tests"""
    # Create users with specific role combinations
    iam_admin = create_user_orm(
        id="iam_admin",
        roles=[create_role_orm(name="administrator", context="IAM", permissions="read, write, delete, admin")]
    )
    
    recipes_admin = create_user_orm(
        id="recipes_admin", 
        roles=[create_role_orm(name="administrator", context="recipes_catalog", permissions="read, write, delete, admin")]
    )
    
    multi_context_user = create_user_orm(
        id="multi_context",
        roles=[
            create_role_orm(name="user", context="IAM", permissions="read"),
            create_role_orm(name="administrator", context="products_catalog", permissions="read, write, delete, admin"),
            create_role_orm(name="auditor", context="recipes_catalog", permissions="read, audit")
        ]
    )
    
    users = [iam_admin, recipes_admin, multi_context_user]
    
    # Add roles first
    for user in users:
        for role in user.roles:
            test_session.add(role)
    
    # Add users
    for user in users:
        test_session.add(user)
    
    await test_session.commit()
    return users 