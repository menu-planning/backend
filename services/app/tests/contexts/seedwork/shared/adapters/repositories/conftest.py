"""
Main pytest fixtures for seedwork integration tests

This conftest.py provides the core fixtures for integration testing of the
SaGenericRepository, following "Architecture Patterns with Python" principles:

- Real database connections (no mocks)
- Test behavior, not implementation  
- Known DB states via fixtures
- Real DB errors and constraints
- Independent test schema management

Key improvements over v1:
- Independent database setup (doesn't rely on main conftest.py autouse fixtures)
- Explicit test schema and table creation/cleanup
- Proper transaction management and isolation
- Real database constraints and relationships for edge case testing

All test models, entities, mappers, and data factories are imported from
their respective modules for better organization and maintainability.
"""

import pytest
import anyio
from typing import Optional

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

import src.db.database as db
from src.contexts.seedwork.shared.adapters.repositories.seedwork_repository import SaGenericRepository
from src.db.base import SaBase

# Import all test utilities from organized modules
from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.filter_mappers import TEST_EDGE_CASE_FILTER_MAPPERS, TEST_MEAL_FILTER_MAPPERS, TEST_RECIPE_FILTER_MAPPERS
from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
    TEST_SCHEMA, MealSaTestModel, RecipeSaTestModel, CircularTestModelA, 
    SelfReferentialTestModel, SupplierSaTestModel, ProductSaTestModel,
    CategorySaTestModel, OrderSaTestModel, CustomerSaTestModel, IngredientSaTestModel
)
from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.entities import (
    TestMealEntity, TestRecipeEntity, TestCircularEntityA, TestSelfReferentialEntity, TestIngredientEntity
)
from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.mappers import (
    TestMealMapper, TestRecipeMapper, TestCircularMapperA, TestSelfReferentialMapper, TestIngredientMapper
)

from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
    create_test_meal, create_test_recipe, create_test_circular_a, create_test_self_ref,
    create_test_meal_with_recipes, create_test_recipe_with_ingredients,
    create_large_dataset, create_test_supplier, create_test_category, 
    create_test_product, create_test_customer, create_test_order, create_test_ORM_meal
)

# Mark all tests in this module as integration tests
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
def with_timeout():
    """Fixture to add timeout to any async operation"""
    def _timeout_wrapper(seconds: float = 30.0):
        def decorator(coro):
            async def wrapper(*args, **kwargs):
                with anyio.move_on_after(seconds) as cancel_scope:
                    result = await coro(*args, **kwargs)
                    if cancel_scope.cancelled_caught:
                        pytest.fail(f"Operation timed out after {seconds} seconds")
                    return result
            return wrapper
        return decorator
    return _timeout_wrapper

# =============================================================================
# DATABASE SESSION FIXTURES
# =============================================================================

@pytest.fixture(scope="session")
async def test_db_session_factory():
    """Independent session factory for test database"""
    return db.async_db.async_session_factory

@pytest.fixture
async def test_session(test_db_session_factory):
    """Independent test session (not relying on main conftest.py autouse fixtures)"""
    async with test_db_session_factory() as session:
        yield session
        # Note: Rollback is handled by the context manager or explicitly in test_schema_setup
        # Don't do rollback here as session might be closed by test_schema_setup teardown

# =============================================================================
# SCHEMA AND TABLE MANAGEMENT FIXTURES
# =============================================================================

@pytest.fixture
async def test_schema_setup(test_session: AsyncSession):
    """Create test schema and all test tables if they don't exist"""
    try:
        # Create schema first with timeout
        with anyio.move_on_after(30) as schema_scope:
            await test_session.execute(text(f"CREATE SCHEMA IF NOT EXISTS {TEST_SCHEMA}"))
            await test_session.commit()
        
        if schema_scope.cancelled_caught:
            pytest.fail("Schema creation timed out after 30 seconds")
        
        # Create all test tables using SQLAlchemy metadata with timeout
        with anyio.move_on_after(60) as table_scope:
            async with db.async_db._engine.begin() as conn:
                # Use SQLAlchemy's create_all with schema filtering to avoid duplication
                def create_test_tables(sync_conn):
                    # Create only tables in test schema using metadata filtering
                    SaBase.metadata.create_all(
                        sync_conn, 
                        checkfirst=True,
                        tables=[table for table in SaBase.metadata.tables.values() 
                               if table.schema == TEST_SCHEMA]
                    )
                
                await conn.run_sync(create_test_tables)
        
        if table_scope.cancelled_caught:
            pytest.fail("Table creation timed out after 60 seconds")
            
    except Exception as e:
        pytest.fail(f"Schema setup failed: {e}")
    
    yield
    
    # Cleanup: Drop test schema and all its tables with timeout
    # Important: Use a separate connection and ensure all sessions are closed first
    try:
        with anyio.move_on_after(30) as cleanup_scope:
            # Close the test session first to release any locks
            await test_session.rollback()  # Rollback any pending transaction
            await test_session.close()     # Close the session to release connections
            
            # Use a new connection for schema cleanup
            async with db.async_db._engine.begin() as conn:
                await conn.execute(text(f"DROP SCHEMA IF EXISTS {TEST_SCHEMA} CASCADE"))
                # No need to commit here as begin() auto-commits on success
        
        if cleanup_scope.cancelled_caught:
            # Log warning but don't fail the test
            print(f"Warning: Schema cleanup timed out after 30 seconds")
    except Exception as e:
        # Log warning but don't fail the test
        print(f"Warning: Schema cleanup failed: {e}")

@pytest.fixture
async def clean_test_tables(test_session: AsyncSession, test_schema_setup):
    """Clean all test tables before each test"""
    # Clean test tables in correct order (respecting foreign keys) with timeout
    tables_to_clean = [
        f"{TEST_SCHEMA}.test_ratings",
        f"{TEST_SCHEMA}.test_ingredients", 
        f"{TEST_SCHEMA}.test_recipes_tags_association",
        f"{TEST_SCHEMA}.test_recipes",
        f"{TEST_SCHEMA}.test_meals_tags_association", 
        f"{TEST_SCHEMA}.test_meals",
        f"{TEST_SCHEMA}.test_tags",
        f"{TEST_SCHEMA}.test_circular_a",
        f"{TEST_SCHEMA}.test_circular_b", 
        f"{TEST_SCHEMA}.test_self_ref_friends",
        f"{TEST_SCHEMA}.test_self_ref",
    ]
    
    try:
        with anyio.move_on_after(30) as cleanup_scope:
            for table in tables_to_clean:
                try:
                    await test_session.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
                except Exception:
                    # Table might not exist yet
                    pass
            
            await test_session.commit()
        
        if cleanup_scope.cancelled_caught:
            pytest.fail("Table cleanup timed out after 30 seconds")
            
    except Exception as e:
        await test_session.rollback()
        pytest.fail(f"Table cleanup failed: {e}")
    
    yield

# =============================================================================
# REPOSITORY FIXTURES (Real database connections)
# =============================================================================

@pytest.fixture
async def meal_repository(test_session: AsyncSession, clean_test_tables):
    """Repository with real database connection for meals"""
    return SaGenericRepository(
        db_session=test_session,
        data_mapper=TestMealMapper,
        domain_model_type=TestMealEntity,
        sa_model_type=MealSaTestModel,
        filter_to_column_mappers=TEST_MEAL_FILTER_MAPPERS,
    )

@pytest.fixture
async def recipe_repository(test_session: AsyncSession, clean_test_tables):
    """Real recipe repository for complex relationship testing"""
    return SaGenericRepository(
        db_session=test_session,
        data_mapper=TestRecipeMapper,
        domain_model_type=TestRecipeEntity,
        sa_model_type=RecipeSaTestModel,
        filter_to_column_mappers=TEST_RECIPE_FILTER_MAPPERS
    )

@pytest.fixture
async def ingredient_repository(test_session: AsyncSession, clean_test_tables):
    """Real ingredient repository for testing complex join scenarios"""
    return SaGenericRepository(
        db_session=test_session,
        data_mapper=TestIngredientMapper,
        domain_model_type=TestIngredientEntity,
        sa_model_type=IngredientSaTestModel,
        filter_to_column_mappers=[]  # No specific filter mappers needed for ingredients
    )

@pytest.fixture
async def circular_repository(test_session: AsyncSession, clean_test_tables):
    """Repository using circular model A as base"""
    return SaGenericRepository(
        db_session=test_session,
        data_mapper=TestCircularMapperA,
        domain_model_type=TestCircularEntityA,
        sa_model_type=CircularTestModelA,
        filter_to_column_mappers=TEST_EDGE_CASE_FILTER_MAPPERS,
    )

@pytest.fixture
async def self_ref_repository(test_session: AsyncSession, clean_test_tables):
    """Repository using self-referential model"""
    return SaGenericRepository(
        db_session=test_session,
        data_mapper=TestSelfReferentialMapper,
        domain_model_type=TestSelfReferentialEntity,
        sa_model_type=SelfReferentialTestModel,
        filter_to_column_mappers=TEST_EDGE_CASE_FILTER_MAPPERS,
    )

# =============================================================================
# PERFORMANCE AND UTILITY FIXTURES
# =============================================================================

# benchmark_timer fixture is now available from top-level conftest.py

@pytest.fixture
async def large_test_dataset(meal_repository, test_session: AsyncSession):
    """Create a large dataset for performance testing"""
    from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import create_test_ORM_meal
    
    # Create a proper dataset avoiding the ZeroDivisionError from create_large_dataset
    entity_count = 100  # Smaller for CI
    meals = []
    
    # Ensure we have at least one author
    author_count = max(1, entity_count // 10)
    authors = [f"author-{i:06d}" for i in range(author_count)]
    
    for i in range(entity_count):
        meal_kwargs = {
            "name": f"Performance Meal {i}",
            "author_id": authors[i % len(authors)],  # Distribute evenly among authors
            "total_time": 30 + (i % 150),  # Vary from 30 to 180
            "calorie_density": round(100.0 + (i % 400), 2),  # Vary from 100 to 500
            "like": [True, False, None][i % 3],  # Cycle through options
        }
        meals.append(create_test_ORM_meal(**meal_kwargs))
    
    for meal in meals:
        test_session.add(meal)
    
    await test_session.commit()
    return meals

# =============================================================================
# CONVENIENCE FIXTURES FOR COMMON TEST SCENARIOS
# =============================================================================

@pytest.fixture
async def sample_meal_with_recipes(meal_repository, recipe_repository, test_session: AsyncSession):
    """Create a meal with associated recipes for relationship testing"""
    meal, recipes = create_test_meal_with_recipes(recipe_count=3)
    
    await meal_repository.add(meal)
    await test_session.flush()  # Get meal ID for recipes
    
    for recipe in recipes:
        await recipe_repository.add(recipe)
    
    await test_session.commit()
    return meal, recipes

@pytest.fixture
async def meals_with_various_attributes(meal_repository, test_session: AsyncSession):
    """Create meals with different attributes for filtering tests"""
    meals = [
        create_test_meal(name="Quick Salad", total_time=10, calorie_density=150.0),
        create_test_meal(name="Pasta Dish", total_time=30, calorie_density=350.0),
        create_test_meal(name="Slow Roast", total_time=120, calorie_density=450.0),
        create_test_meal(name="Complex Stew", total_time=180, calorie_density=300.0),
    ]
    
    for meal in meals:
        await meal_repository.add(meal)
    
    await test_session.commit()
    return meals

@pytest.fixture
async def circular_entities_setup(circular_repository, test_session: AsyncSession):
    """Create circular entities for edge case testing"""
    entity_a = create_test_circular_a(name="Circular A")
    entity_b = create_test_circular_a(name="Circular B with ref", b_ref_id="some_id")
    
    await circular_repository.add(entity_a)
    await circular_repository.add(entity_b)
    await test_session.commit()
    
    return entity_a, entity_b

@pytest.fixture
async def self_ref_hierarchy(self_ref_repository, test_session: AsyncSession):
    """Create self-referential hierarchy for recursion testing"""
    from .testing_infrastructure.data_factories import create_test_self_ref_hierarchy
    
    entities = create_test_self_ref_hierarchy(depth=4, base_name="test_hierarchy")
    
    for entity in entities:
        await self_ref_repository.add(entity)
    
    await test_session.commit()
    return entities