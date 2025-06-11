# Repository Integration Testing Refactor Guide

## 🎯 Philosophy: Real Database, Real Behavior

This guide implements the testing philosophy from "Architecture Patterns with Python" by Harry Percival and Bob Gregory:

1. **Test behavior, not implementation**
2. **Use real database connections** (test database)
3. **Test fixtures for known DB states** (not mocks)
4. **Catch real DB errors** (constraints, deadlocks, etc.)
5. **Live mocks only for external services**, not your own abstractions

## 🏗️ Architecture Overview

### Hybrid ORM Model Strategy

```
┌─────────────────────────────────────────────────────────────┐
│                    SEEDWORK TESTS                           │
│  Uses: Dedicated Test Models in `test_seedwork` schema      │
│  Why: Need edge cases (circular refs, self-referential)     │
│       Control schema/constraints exactly                     │
│       Test generic repository in isolation                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                 DOMAIN-SPECIFIC TESTS                       │
│  Uses: REAL ORM Models from codebase                       │
│  Why: Test actual business logic                           │
│       Catch real ORM quirks                                │
│       Ensure compatibility with production schema           │
└─────────────────────────────────────────────────────────────┘
```

## 📁 File Structure

```
tests/contexts/seedwork/shared/adapters/v2/
├── __init__.py
├── conftest.py                                  # Test models, shared fixtures
├── test_seedwork_repository_v2.py              # Core CRUD operations
├── test_seedwork_repository_behavior_v2.py     # Complex queries, filtering
├── test_seedwork_repository_edge_cases_v2.py   # DB errors, constraints
├── test_seedwork_repository_joins_v2.py        # Join scenarios
├── test_seedwork_repository_performance_v2.py  # Performance benchmarks
├── test_filter_operators_v2.py                 # Filter operators with real DB
└── test_query_builder_v2.py                    # Query builder integration

tests/contexts/recipes_catalog/integration/v2/
├── test_meal_repo_v2.py                        # Using REAL MealSaModel
└── test_recipe_repo_v2.py                      # Using REAL RecipeSaModel

tests/contexts/products_catalog/integration/v2/
└── test_product_repo_v2.py                     # Using REAL ProductSaModel
```

## 🔧 Implementation Steps

### STEP 1: Create v2/conftest.py with Test Models

```python
"""
Integration test fixtures for SaGenericRepository testing

Following "Architecture Patterns with Python" principles:
- Real database connections
- Test behavior, not implementation
- Known DB states via fixtures
- Real DB errors, not mocked
"""

import pytest
import uuid
from datetime import datetime
from typing import Type

from sqlalchemy import Column, Integer, String, Boolean, Float, DateTime, ForeignKey, Table, UniqueConstraint, CheckConstraint, Index
from sqlalchemy.orm import relationship, Mapped, mapped_column, composite
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.seedwork.shared.adapters.repositories.seedwork_repository import (
    SaGenericRepository, FilterColumnMapper
)
from src.contexts.seedwork.shared.adapters.ORM.mappers.mapper import ModelMapper
from src.contexts.seedwork.shared.domain.entity import Entity
from src.db.base import SaBase

# Test schema - isolate from production
TEST_SCHEMA = "test_seedwork"

# [Include all the test models from the v2/conftest.py I started earlier]

# Key fixtures:

@pytest.fixture
async def test_schema_setup(async_pg_session: AsyncSession):
    """Create test schema if it doesn't exist"""
    await async_pg_session.execute(f"CREATE SCHEMA IF NOT EXISTS {TEST_SCHEMA}")
    await async_pg_session.commit()
    yield
    # Cleanup handled by clean_database_before_test

@pytest.fixture
async def meal_repository(async_pg_session: AsyncSession, test_schema_setup):
    """Repository with real database connection"""
    return SaGenericRepository(
        db_session=async_pg_session,
        data_mapper=TestMealMapper,
        domain_model_type=TestMealEntity,
        sa_model_type=TestMealSaModel,
        filter_to_column_mappers=TEST_MEAL_FILTER_MAPPERS,
    )

# Performance benchmark fixture
@pytest.fixture
def benchmark_timer():
    """Simple timer for performance assertions"""
    import time
    
    class Timer:
        def __init__(self):
            self.start_time = None
            self.elapsed = None
            
        def __enter__(self):
            self.start_time = time.perf_counter()
            return self
            
        def __exit__(self, *args):
            self.elapsed = time.perf_counter() - self.start_time
            
        def assert_faster_than(self, seconds):
            assert self.elapsed < seconds, f"Operation took {self.elapsed:.3f}s, expected < {seconds}s"
    
    return Timer
```

### STEP 2: Create Core Repository Tests

```python
# v2/test_seedwork_repository_v2.py
import anyio
import pytest
from sqlalchemy.exc import IntegrityError
from tests.contexts.recipes_catalog.random_refs import random_meal

pytestmark = [pytest.mark.anyio, pytest.mark.integration]

class TestSaGenericRepositoryCRUD:
    """Test basic CRUD operations with real database"""
    
    async def test_add_and_get_entity(self, meal_repository, async_pg_session):
        # Given: A meal entity
        meal = create_test_meal()
        
        # When: Adding to repository
        await meal_repository.add(meal)
        await async_pg_session.commit()
        
        # Then: Can retrieve it
        retrieved = await meal_repository.get(meal.id)
        assert retrieved.id == meal.id
        assert retrieved.name == meal.name
        assert retrieved.created_at is not None  # DB sets this
        
    async def test_duplicate_key_raises_integrity_error(self, meal_repository, async_pg_session):
        # Given: A meal with a specific ID
        meal_id = "unique_meal_123"
        meal1 = create_test_meal(id=meal_id)
        await meal_repository.add(meal1)
        await async_pg_session.commit()
        
        # When: Trying to add another meal with same ID
        meal2 = create_test_meal(id=meal_id)
        
        # Then: Real DB constraint violation
        with pytest.raises(IntegrityError) as exc_info:
            await meal_repository.add(meal2)
            await async_pg_session.commit()
            
        assert "duplicate key value violates unique constraint" in str(exc_info.value)
        await async_pg_session.rollback()
```

### STEP 3: Test Complex Filtering Behavior

```python
# v2/test_seedwork_repository_behavior_v2.py
import anyio
import pytest

pytestmark = [pytest.mark.anyio, pytest.mark.integration]

class TestSaGenericRepositoryFiltering:
    """Test complex filtering scenarios with real database"""
    
    @pytest.fixture
    async def meals_with_various_times(self, meal_repository, async_pg_session):
        """Create meals with different cooking times"""
        meals = [
            create_test_meal(name="Quick Salad", total_time=10),
            create_test_meal(name="Pasta", total_time=30),
            create_test_meal(name="Roast", total_time=120),
            create_test_meal(name="Stew", total_time=180),
        ]
        
        # Add all meals
        for meal in meals:
            await meal_repository.add(meal)
        await async_pg_session.commit()
        
        return meals
    
    async def test_filter_with_gte_operator(self, meal_repository, meals_with_various_times):
        # When: Filtering for meals taking >= 60 minutes
        results = await meal_repository.query({"total_time_gte": 60})
        
        # Then: Only long-cooking meals returned
        assert len(results) == 2
        assert all(r.total_time >= 60 for r in results)
        result_names = {r.name for r in results}
        assert result_names == {"Roast", "Stew"}
        
    async def test_composite_field_filtering(self, meal_repository, async_pg_session):
        # Given: Meals with nutri_facts
        meal1 = create_test_meal(
            name="High Protein",
            nutri_facts=TestNutriFactsSaModel(protein=30.0, calories=200.0)
        )
        meal2 = create_test_meal(
            name="Low Protein", 
            nutri_facts=TestNutriFactsSaModel(protein=5.0, calories=150.0)
        )
        
        await meal_repository.add(meal1)
        await meal_repository.add(meal2)
        await async_pg_session.commit()
        
        # When: Filtering by protein content
        results = await meal_repository.query({"protein_gte": 20.0})
        
        # Then: Composite field filtering works
        assert len(results) == 1
        assert results[0].name == "High Protein"
```

### STEP 4: Test Edge Cases with Real DB Errors

```python
# v2/test_seedwork_repository_edge_cases_v2.py
import anyio
import pytest
from sqlalchemy.exc import DataError, IntegrityError

pytestmark = [pytest.mark.anyio, pytest.mark.integration]

class TestSaGenericRepositoryEdgeCases:
    """Test edge cases and database constraints"""
    
    async def test_foreign_key_constraint_violation(self, recipe_repository, async_pg_session):
        # Given: A recipe referencing non-existent meal
        recipe = create_test_recipe(meal_id="non_existent_meal_id")
        
        # When/Then: Foreign key constraint fails
        with pytest.raises(IntegrityError) as exc_info:
            await recipe_repository.add(recipe)
            await async_pg_session.commit()
            
        assert "foreign key constraint" in str(exc_info.value).lower()
        
    async def test_check_constraint_violation(self, meal_repository, async_pg_session):
        # Given: Meal with negative cooking time (violates check constraint)
        meal = create_test_meal(total_time=-10)
        
        # When/Then: Check constraint fails
        with pytest.raises(IntegrityError) as exc_info:
            await meal_repository.add(meal)
            await async_pg_session.commit()
            
        assert "check constraint" in str(exc_info.value).lower()
        
    async def test_null_handling_in_filters(self, meal_repository, async_pg_session):
        # Given: Meals with and without descriptions
        with_desc = create_test_meal(description="Delicious meal")
        without_desc = create_test_meal(description=None)
        
        await meal_repository.add(with_desc)
        await meal_repository.add(without_desc)
        await async_pg_session.commit()
        
        # When: Filtering for non-null descriptions
        results = await meal_repository.query({"description_is_not": None})
        
        # Then: Only meal with description returned
        assert len(results) == 1
        assert results[0].description == "Delicious meal"
```

### STEP 5: Test Complex Joins

```python
# v2/test_seedwork_repository_joins_v2.py
import anyio
import pytest

pytestmark = [pytest.mark.anyio, pytest.mark.integration]

class TestSaGenericRepositoryJoins:
    """Test join scenarios with real foreign keys"""
    
    @pytest.fixture
    async def meal_with_recipes_and_ingredients(self, async_pg_session):
        """Create complex hierarchy for join testing"""
        # Create meal
        meal = TestMealSaModel(
            id="meal_1",
            name="Complex Meal",
            author_id="test_author",
            preprocessed_name="complex meal"
        )
        
        # Create recipes
        recipe1 = TestRecipeSaModel(
            id="recipe_1",
            name="Recipe 1",
            meal_id="meal_1",
            author_id="test_author",
            preprocessed_name="recipe 1",
            instructions="Cook it"
        )
        
        # Create ingredients
        ingredient1 = TestIngredientSaModel(
            name="Tomato",
            quantity=2.0,
            unit="pieces",
            recipe_id="recipe_1",
            position=1,
            product_id="product_123"
        )
        
        # Add all with proper relationships
        async_pg_session.add(meal)
        await async_pg_session.flush()
        
        async_pg_session.add(recipe1)
        await async_pg_session.flush()
        
        async_pg_session.add(ingredient1)
        await async_pg_session.commit()
        
        return meal, recipe1, ingredient1
        
    async def test_multi_level_join_filtering(
        self, meal_repository, meal_with_recipes_and_ingredients
    ):
        # When: Filtering meals by ingredient product (3-level join)
        results = await meal_repository.query({"products": "product_123"})
        
        # Then: Join traverses Meal -> Recipe -> Ingredient
        assert len(results) == 1
        assert results[0].name == "Complex Meal"
```

### STEP 6: Performance Benchmarks

```python
# v2/test_seedwork_repository_performance_v2.py
import anyio
import pytest

pytestmark = [pytest.mark.anyio, pytest.mark.integration]

class TestSaGenericRepositoryPerformance:
    """Performance benchmarks with real data"""
    
    @pytest.fixture
    async def large_dataset(self, meal_repository, async_pg_session):
        """Create 1000 meals for performance testing"""
        meals = []
        
        # Create in batches for efficiency
        for batch in range(10):
            batch_meals = [
                create_test_meal(
                    name=f"Meal {i}",
                    total_time=i % 120,
                    calorie_density=100.0 + (i % 50),
                    author_id=f"author_{i % 10}"
                )
                for i in range(batch * 100, (batch + 1) * 100)
            ]
            
            # Bulk add
            for meal in batch_meals:
                await meal_repository.add(meal)
            
            await async_pg_session.commit()
            meals.extend(batch_meals)
            
        return meals
        
    async def test_query_performance_baseline(
        self, meal_repository, large_dataset, benchmark_timer
    ):
        # Establish performance baseline
        with benchmark_timer() as timer:
            results = await meal_repository.query({
                "total_time_lte": 60,
                "author_id": "author_5",
                "calorie_density_gte": 120
            })
            
        # Should complete quickly even with 1000 records
        timer.assert_faster_than(0.5)  # 500ms threshold
        
        # Verify correctness
        assert all(r.total_time <= 60 for r in results)
        assert all(r.author_id == "author_5" for r in results)
        assert all(r.calorie_density >= 120 for r in results)
```

### STEP 7: Domain-Specific Repository Tests

```python
# tests/contexts/recipes_catalog/integration/v2/test_meal_repo_v2.py
import anyio
import pytest
from src.contexts.recipes_catalog.core.adapters.ORM.sa_models import (
    MealSaModel, RecipeSaModel, TagSaModel
)
from src.contexts.recipes_catalog.core.adapters.repositories.meal.meal import MealRepo
from tests.contexts.recipes_catalog.random_refs import random_meal, random_tag

pytestmark = [pytest.mark.anyio, pytest.mark.integration]

class TestMealRepositoryIntegration:
    """Test MealRepo with REAL production models"""
    
    async def test_tag_filtering_complex_logic(self, async_pg_session):
        # Setup: Create meal with specific tags
        meal = random_meal(
            tags=[
                random_tag(key="cuisine", value="italian", type="meal"),
                random_tag(key="cuisine", value="mediterranean", type="meal"),
                random_tag(key="diet", value="vegetarian", type="meal"),
            ]
        )
        
        repo = MealRepo(async_pg_session)
        await repo.add(meal)
        await async_pg_session.commit()
        
        # Test: Complex tag filtering (groupby logic)
        results = await repo.query({
            "tags": [
                ("cuisine", "italian", meal.author_id),
                ("diet", "vegetarian", meal.author_id)
            ]
        })
        
        assert len(results) == 1
        assert results[0].id == meal.id
        
    async def test_tag_not_exists_condition(self, async_pg_session):
        # Given: Meals with different tags
        meal_with_gluten = random_meal(
            tags=[random_tag(key="allergen", value="gluten", type="meal")]
        )
        meal_without_gluten = random_meal(
            tags=[random_tag(key="diet", value="healthy", type="meal")]
        )
        
        repo = MealRepo(async_pg_session)
        await repo.add(meal_with_gluten)
        await repo.add(meal_without_gluten)
        await async_pg_session.commit()
        
        # When: Filtering for meals WITHOUT gluten tag
        results = await repo.query({
            "tags_not_exists": [("allergen", "gluten", meal_with_gluten.author_id)]
        })
        
        # Then: Only gluten-free meal returned
        assert len(results) == 1
        assert results[0].id == meal_without_gluten.id
```

## 🔍 Key Testing Patterns

### 1. Given-When-Then Pattern

```python
async def test_example(repository, async_pg_session):
    # Given: Set up known state
    entity = create_test_entity(specific_attributes)
    await repository.add(entity)
    await async_pg_session.commit()
    
    # When: Perform action
    result = await repository.query({"filter": "value"})
    
    # Then: Assert behavior
    assert len(result) == expected_count
    assert result[0].attribute == expected_value
```

### 2. Real Database Constraints

```python
async def test_constraint_violation(repository, async_pg_session):
    # Test REAL constraint errors, not mocked
    with pytest.raises(IntegrityError) as exc_info:
        await repository.add(invalid_entity)
        await async_pg_session.commit()
    
    # Assert on actual DB error message
    assert "constraint_name" in str(exc_info.value)
```

### 3. Performance Assertions

```python
async def test_performance(repository, large_dataset, benchmark_timer):
    with benchmark_timer() as timer:
        results = await repository.complex_query()
    
    timer.assert_faster_than(1.0)  # Must complete in < 1 second
```

### 4. Transaction Rollback Pattern

```python
async def test_with_rollback(repository, async_pg_session):
    try:
        await repository.add(entity)
        await async_pg_session.commit()
        # ... test logic ...
    except Exception:
        await async_pg_session.rollback()
        raise
```

## 📋 Migration Checklist

When migrating existing mock-based tests:

1. **Replace mock models with test models** that use real DB
2. **Replace mock session with real async_pg_session**
3. **Add commits/flushes** where needed for FK constraints
4. **Replace mock exceptions with real DB exceptions**
5. **Add performance benchmarks** for critical paths
6. **Test actual SQL generated** (can log/capture)
7. **Verify cascade behaviors** work correctly

## ⚠️ Important Considerations

### 1. Schema Isolation

```python
# Always use test schema to avoid polluting production schemas
TEST_SCHEMA = "test_seedwork"

class TestModel(SaBase):
    __table_args__ = {"schema": TEST_SCHEMA}
```

### 2. Fixture Dependencies

```python
# Ensure schema exists before using models
@pytest.fixture
async def repository(async_pg_session, test_schema_setup):
    # test_schema_setup ensures schema exists
    return SaGenericRepository(...)
```

### 3. Anyio Best Practices

```python
# Always use anyio for async operations
async with anyio.create_task_group() as tg:
    for item in items:
        tg.start_soon(repository.add, item)

# Use anyio for timeouts
with anyio.fail_after(5):  # 5 second timeout
    await long_running_query()
```

### 4. Test Isolation

- Each test starts with clean DB (via `clean_database_before_test`)
- Use transactions and rollback for additional isolation
- Don't rely on test execution order

## 🚀 Running the Tests

```bash
# Run all integration tests
./manage.py test tests/contexts/seedwork/shared/adapters/v2/ -m integration

# Run specific test file
./manage.py test tests/contexts/seedwork/shared/adapters/v2/test_seedwork_repository_v2.py

# Run with coverage
./manage.py test tests/contexts/seedwork/shared/adapters/v2/ --cov=src.contexts.seedwork.shared.adapters.repositories

# Run performance tests only
./manage.py test tests/contexts/seedwork/shared/adapters/v2/test_seedwork_repository_performance_v2.py
```

## 📊 Success Metrics

Your integration tests are successful when:

1. **No mocks** for database, session, or your own models
2. **Real constraints** are tested (FK, unique, check)
3. **Performance baselines** established and monitored
4. **Edge cases** produce real DB errors
5. **Complex queries** tested with real data
6. **All tests pass** consistently without flakiness

## 🔗 Next Steps

After implementing v2 integration tests:

1. **Compare with v1 tests** - Ensure same behavior
2. **Remove old mock-based tests** - Once confident
3. **Add more edge cases** - As discovered
4. **Monitor performance** - Track regressions
5. **Document findings** - ORM quirks, gotchas

Remember: **The goal is confidence that your code works with a real database, not that your mocks work with other mocks.**