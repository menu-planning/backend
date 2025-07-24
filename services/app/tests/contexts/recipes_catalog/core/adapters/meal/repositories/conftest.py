"""
Conftest for meal repository tests following seedwork patterns.

This conftest provides fixtures for testing MealRepository with real database:
- Real database session (no mocks)
- Smart targeted database cleanup (fast, only cleans tables these tests use)
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
from typing import Optional, AsyncGenerator
import time

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.recipes_catalog.core.adapters.meal.repositories.meal_repository import MealRepo
from src.contexts.recipes_catalog.core.adapters.meal.repositories.recipe_repository import RecipeRepo

# Import data factories
from tests.contexts.recipes_catalog.data_factories.meal.meal_orm_factories import create_meal_orm

# Import counter manager for test isolation
from tests.utils.counter_manager import reset_all_counters

# Load integration database fixtures
pytest_plugins = ["tests.integration_conftest"]

# Mark all tests as integration tests
pytestmark = [pytest.mark.anyio, pytest.mark.integration]


# =============================================================================
# SMART DATABASE CLEANUP
# =============================================================================

async def clean_meal_recipe_test_tables(session: AsyncSession):
    """
    Smart cleanup that only targets tables used by meal/recipe repository tests.
    
    This approach is much faster than TRUNCATE CASCADE on all tables since it:
    - Only cleans tables these tests actually use
    - Respects foreign key dependencies 
    - Uses DELETE instead of TRUNCATE to avoid AccessExclusiveLock deadlocks
    
    Order is critical: most dependent tables first, least dependent last.
    """
    # Tables in dependency order (most dependent → least dependent)
    tables_to_clean = [
        # Most dependent: association tables and child entities
        "recipes_catalog.ratings",                    # depends on recipes + users
        "recipes_catalog.ingredients",                # depends on recipes + products  
        "recipes_catalog.meals_tags_association",     # depends on meals + tags
        "recipes_catalog.recipes_tags_association",   # depends on recipes + tags
        
        # Core entities with foreign keys
        "recipes_catalog.recipes",                    # depends on meals
        "recipes_catalog.meals",                      # depends on users via author_id
        
        # Shared entities that may be referenced
        "shared_kernel.tags",                         # depends on users via author_id
        "iam.user_role_association",                  # depends on users + roles
        "iam.users",                                  # core user entity
        "iam.roles",                                  # core role entity
        
        # Product entities if used by ingredients
        "products_catalog.products",                  # depends on sources
        "products_catalog.sources",                   # independent
        
        # Menu entities if used by meals
        "recipes_catalog.menus",                      # may be referenced by meals
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
async def clean_meal_recipe_database(async_pg_session_factory) -> None:
    """
    Clean only the tables used by meal/recipe tests before each test.
    Much faster than cleaning all tables.
    """
    async with async_pg_session_factory() as session:
        await clean_meal_recipe_test_tables(session)
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
# REPOSITORY FIXTURES
# =============================================================================

@pytest.fixture
async def meal_repository(test_session: AsyncSession) -> MealRepo:
    """Create MealRepository instance for testing"""
    return MealRepo(db_session=test_session)


@pytest.fixture
async def recipe_repository(test_session: AsyncSession) -> RecipeRepo:
    """Create RecipeRepository instance for testing"""
    return RecipeRepo(db_session=test_session)


@pytest.fixture
async def test_session(
    async_pg_session_factory,
    clean_meal_recipe_database,  # Ensure database is clean before test
) -> AsyncGenerator[AsyncSession, None]:
    """
    Provide clean test session with targeted database cleanup.
    Uses smart cleanup that only targets tables these tests use.
    """
    async with async_pg_session_factory() as session:
        yield session
        # Rollback any uncommitted changes
        await session.rollback()


# =============================================================================
# PERFORMANCE UTILITIES
# =============================================================================

@pytest.fixture
def benchmark_timer():
    """
    Simple timing utility for performance tests.
    
    Usage:
        with benchmark_timer() as timer:
            # ... test code ...
        print(f"Test took {timer.duration:.3f} seconds")
    """
    import time
    from contextlib import contextmanager
    
    @contextmanager
    def timer():
        class Timer:
            def __init__(self):
                self.start_time: Optional[float] = None
                self.duration: Optional[float] = None
        
        timer_obj = Timer()
        timer_obj.start_time = time.time()
        try:
            yield timer_obj
        finally:
            if timer_obj.start_time is not None:
                timer_obj.duration = time.time() - timer_obj.start_time
    
    return timer


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