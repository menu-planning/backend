"""
Conftest for meal repository tests following seedwork patterns.

This conftest provides fixtures for testing MealRepository with real database:
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

from src.contexts.recipes_catalog.core.adapters.meal.repositories.meal_repository import MealRepo
from src.contexts.recipes_catalog.core.adapters.meal.repositories.recipe_repository import RecipeRepo

# Import data factories
from tests.contexts.recipes_catalog.data_factories.meal.meal_orm_factories import create_meal_orm

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


@pytest.fixture
async def meal_repository(async_pg_session: AsyncSession) -> MealRepo:
    """Create MealRepository instance for testing"""
    return MealRepo(db_session=async_pg_session)


@pytest.fixture
async def recipe_repository(async_pg_session: AsyncSession) -> RecipeRepo:
    """Create RecipeRepository instance for testing"""
    return RecipeRepo(db_session=async_pg_session)


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
async def sample_meals_orm(test_session: AsyncSession):
    """Create sample ORM meals for testing"""
    meals = []
    for i in range(3):
        meal = create_meal_orm(
            name=f"Sample Meal {i}",
            author_id=f"author_{i}",
            total_time=30 + (i * 30)
        )
        meals.append(meal)
        test_session.add(meal)
    
    await test_session.commit()
    return meals


@pytest.fixture
async def large_meal_dataset(test_session: AsyncSession):
    """Create large dataset for performance testing"""
    meals = []
    meal_count = 100
    
    for i in range(meal_count):
        meal = create_meal_orm(
            name=f"Performance Meal {i}",
            author_id=f"author_{i % 10}",  # 10 different authors
            total_time=30 + (i % 150),  # Vary from 30 to 180
            calorie_density=1.5 + (i % 3),  # Vary from 1.5 to 4.5
            like=[True, False, None][i % 3]  # Cycle through options
        )
        meals.append(meal)
        test_session.add(meal)
    
    await test_session.commit()
    return meals 