"""
Core SaGenericRepository integration tests with real database

This module tests the fundamental operations of SaGenericRepository using real database connections:
- Basic CRUD operations with real constraints
- Filter operations with actual DB queries
- Query method functionality with real data
- Error handling with actual DB exceptions

Following "Architecture Patterns with Python" principles:
- Test behavior, not implementation
- Use real database connections (test database)
- Test fixtures for known DB states (not mocks)
- Catch real DB errors (constraints, deadlocks, etc.)

Replaces: test_seedwork_repository_core.py (mock-based version)
"""


import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select

from src.contexts.seedwork.shared.endpoints.exceptions import BadRequestException
from .conftest import timeout_test

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


class TestSaGenericRepositoryCRUD:
    """Test basic CRUD operations with real database"""
    
    @timeout_test(60.0)  # 60 second timeout for this test
    async def test_add_and_get_entity(self, meal_repository, test_session):
        """Test adding and retrieving entity from real database"""
        # Given: A meal entity
        from .test_data_factories import create_test_meal
        meal = create_test_meal(name="Integration Test Meal", total_time=45)
        
        # When: Adding to repository and committing to DB
        await meal_repository.add(meal)
        await test_session.commit()
        
        # Then: Can retrieve it from database
        retrieved = await meal_repository.get(meal.id)
        assert retrieved is not None
        assert retrieved.id == meal.id
        assert retrieved.name == "Integration Test Meal"
        assert retrieved.total_time == 45
        assert retrieved.created_at is not None  # DB should set timestamp
        
    @timeout_test(30.0)  # 30 second timeout for this test
    async def test_add_duplicate_id_raises_real_integrity_error(self, meal_repository, test_session):
        """Test that duplicate IDs raise real database constraint errors"""
        # Given: A meal with specific ID
        from .test_data_factories import create_test_meal
        meal_id = "duplicate_test_meal_123"
        meal1 = create_test_meal(id=meal_id, name="First Meal")
        meal2 = create_test_meal(id=meal_id, name="Second Meal")
        
        # When: Adding first meal successfully
        await meal_repository.add(meal1)
        await test_session.commit()
        
        # Then: Adding second meal with same ID raises real DB constraint error
        with pytest.raises(IntegrityError) as exc_info:
            await meal_repository.add(meal2)
        
        # Verify it's a real database error message
        assert "duplicate key value violates unique constraint" in str(exc_info.value)
        await test_session.rollback()
        
    async def test_get_nonexistent_entity_returns_none(self, meal_repository):
        """Test getting non-existent entity raises EntityNotFoundException"""
        # When: Trying to get entity that doesn't exist
        from src.contexts.seedwork.shared.adapters.exceptions import EntityNotFoundException
        with pytest.raises(EntityNotFoundException):
            await meal_repository.get("nonexistent_meal_id")
        
    async def test_update_entity_persists_changes(self, meal_repository, test_session):
        """Test updating entity persists changes to database"""
        # Given: An existing meal in database
        from .test_data_factories import create_test_meal
        meal = create_test_meal(name="Original Name", total_time=30)
        await meal_repository.add(meal)
        await test_session.commit()
        
        # When: Updating the entity
        meal.name = "Updated Name"
        meal.total_time = 60
        await meal_repository.persist(meal)
        await test_session.commit()
        
        # Then: Changes are persisted in database
        retrieved = await meal_repository.get(meal.id)
        assert retrieved.name == "Updated Name"
        assert retrieved.total_time == 60
        
    async def test_delete_entity_removes_from_database(self, meal_repository, test_session):
        """Test deleting entity removes it from database (soft delete with discarded flag)"""
        # Given: An existing meal in database
        from .test_data_factories import create_test_meal
        meal = create_test_meal(name="To Be Deleted")
        await meal_repository.add(meal)
        await test_session.commit()
        
        # Verify it exists
        assert await meal_repository.get(meal.id) is not None
        
        # When: Marking entity as discarded (soft delete)
        meal._discard()
        await meal_repository.persist(meal)
        await test_session.commit()
        
        # Then: Entity is no longer accessible via get() (filtered out by discarded=False)
        from src.contexts.seedwork.shared.adapters.exceptions import EntityNotFoundException
        with pytest.raises(EntityNotFoundException):
            await meal_repository.get(meal.id)


class TestSaGenericRepositoryFilterOperations:
    """Test filter operations with real database queries"""
    
    @pytest.fixture
    async def meals_with_various_attributes(self, meal_repository, test_session):
        """Create meals with different attributes for filtering tests"""
        from .test_data_factories import create_test_meal
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
    
    async def test_filter_with_gte_operator(self, meal_repository, meals_with_various_attributes):
        """Test filtering with greater-than-or-equal operator on real data"""
        # When: Filtering for meals taking >= 60 minutes
        results = await meal_repository.query({"total_time_gte": 60})
        
        # Then: Only long-cooking meals returned
        assert len(results) == 2
        assert all(r.total_time >= 60 for r in results)
        result_names = {r.name for r in results}
        assert result_names == {"Slow Roast", "Complex Stew"}
        
    async def test_filter_with_lte_operator(self, meal_repository, meals_with_various_attributes):
        """Test filtering with less-than-or-equal operator on real data"""
        # When: Filtering for quick meals <= 30 minutes
        results = await meal_repository.query({"total_time_lte": 30})
        
        # Then: Only quick meals returned
        assert len(results) == 2
        assert all(r.total_time <= 30 for r in results)
        result_names = {r.name for r in results}
        assert result_names == {"Quick Salad", "Pasta Dish"}
        
    async def test_filter_with_ne_operator(self, meal_repository, meals_with_various_attributes):
        """Test filtering with not-equal operator on real data"""
        # When: Filtering for meals not taking exactly 30 minutes
        results = await meal_repository.query({"total_time_ne": 30})
        
        # Then: All except 30-minute meal returned
        assert len(results) == 3
        assert all(r.total_time != 30 for r in results)
        result_names = {r.name for r in results}
        assert result_names == {"Quick Salad", "Slow Roast", "Complex Stew"}
        
    async def test_filter_with_in_operator_list_value(self, meal_repository, meals_with_various_attributes):
        """Test filtering with IN operator using list values"""
        # When: Filtering for specific meal names
        results = await meal_repository.query({"name": ["Quick Salad", "Slow Roast"]})
        
        # Then: Only specified meals returned
        assert len(results) == 2
        result_names = {r.name for r in results}
        assert result_names == {"Quick Salad", "Slow Roast"}
        
    async def test_filter_with_not_in_operator(self, meal_repository, meals_with_various_attributes):
        """Test filtering with NOT IN operator on real data"""
        # When: Filtering to exclude specific cooking times
        results = await meal_repository.query({"total_time_not_in": [10, 30]})
        
        # Then: Only meals with other cooking times returned
        assert len(results) == 2
        assert all(r.total_time not in [10, 30] for r in results)
        result_names = {r.name for r in results}
        assert result_names == {"Slow Roast", "Complex Stew"}
        
    async def test_filter_with_is_not_operator(self, meal_repository, test_session):
        """Test filtering with IS NOT operator for NULL values"""
        # Given: Meals with and without descriptions
        from .test_data_factories import create_test_meal
        with_desc = create_test_meal(name="Has Description", description="Delicious meal")
        without_desc = create_test_meal(name="No Description", description=None)
        
        await meal_repository.add(with_desc)
        await meal_repository.add(without_desc)
        await test_session.commit()
        
        # When: Filtering for non-null descriptions
        results = await meal_repository.query({"description_is_not": None})
        
        # Then: Only meal with description returned
        assert len(results) == 1
        assert results[0].name == "Has Description"
        assert results[0].description == "Delicious meal"
        
    async def test_filter_with_boolean_column_uses_is_operator(self, meal_repository, test_session):
        """Test that boolean columns use IS operator behavior with real data"""
        # Given: Meals with different boolean values
        from .test_data_factories import create_test_meal
        liked_meal = create_test_meal(name="Liked Meal", like=True)
        not_liked_meal = create_test_meal(name="Not Liked Meal", like=False)
        neutral_meal = create_test_meal(name="Neutral Meal", like=None)
        
        await meal_repository.add(liked_meal)
        await meal_repository.add(not_liked_meal)
        await meal_repository.add(neutral_meal)
        await test_session.commit()
        
        # When: Filtering for liked meals (True)
        liked_results = await meal_repository.query({"like": True})
        
        # Then: Only liked meal returned
        assert len(liked_results) == 1
        assert liked_results[0].name == "Liked Meal"
        
        # When: Filtering for not liked meals (False)
        not_liked_results = await meal_repository.query({"like": False})
        
        # Then: Only not liked meal returned
        assert len(not_liked_results) == 1
        assert not_liked_results[0].name == "Not Liked Meal"
        
        # When: Filtering for neutral meals (None/NULL)
        neutral_results = await meal_repository.query({"like": None})
        
        # Then: Only neutral meal returned
        assert len(neutral_results) == 1
        assert neutral_results[0].name == "Neutral Meal"
        
    async def test_string_column_equality_operator(self, meal_repository, test_session):
        """Test that string columns use equality operator with real data"""
        # Given: Meals with exact and partial name matches
        from .test_data_factories import create_test_meal
        exact_match = create_test_meal(name="Exact Match")
        partial_match = create_test_meal(name="Exact Match Plus More")
        different_name = create_test_meal(name="Different Name")
        
        await meal_repository.add(exact_match)
        await meal_repository.add(partial_match)
        await meal_repository.add(different_name)
        await test_session.commit()
        
        # When: Filtering for exact string match
        results = await meal_repository.query({"name": "Exact Match"})
        
        # Then: Only exact match returned (not partial)
        assert len(results) == 1
        assert results[0].name == "Exact Match"
        
    async def test_postfix_removal_in_filter_mapping(self, meal_repository, test_session):
        """Test that postfix operators correctly map to base column names"""
        # Given: Meals with different total times
        from .test_data_factories import create_test_meal
        quick_meal = create_test_meal(name="Quick", total_time=15)
        slow_meal = create_test_meal(name="Slow", total_time=90)
        
        await meal_repository.add(quick_meal)
        await meal_repository.add(slow_meal)
        await test_session.commit()
        
        # When: Using postfix operator that should map to base column "total_time"
        results = await meal_repository.query({"total_time_gte": 60})  # Should map to total_time column
        
        # Then: Filtering works correctly (postfix was removed to find column)
        assert len(results) == 1
        assert results[0].name == "Slow"
        assert results[0].total_time >= 60
        
    async def test_multiple_filters_combined(self, meal_repository, meals_with_various_attributes):
        """Test combining multiple filters in single query"""
        # When: Filtering with multiple criteria
        results = await meal_repository.query({
            "total_time_gte": 30,  # >= 30 minutes
            "calorie_density_lte": 400.0,  # <= 400 cal/serving
        })
        
        # Then: Only meals meeting both criteria returned
        assert len(results) == 2
        for result in results:
            assert result.total_time >= 30
            assert result.calorie_density <= 400.0
        result_names = {r.name for r in results}
        assert result_names == {"Pasta Dish", "Complex Stew"}
        
    async def test_filter_with_unknown_key_raises_exception(self, meal_repository):
        """Test that filtering with unknown key raises appropriate exception"""
        # When/Then: Filtering with unknown filter key raises exception
        with pytest.raises((BadRequestException, KeyError)):
            await meal_repository.query({"unknown_filter_key": "some_value"})
            
    async def test_empty_filter_returns_all_entities(self, meal_repository, test_session):
        """Test that empty filter dict returns all entities"""
        # Given: Multiple meals in database
        from .test_data_factories import create_test_meal
        meals = [create_test_meal(name=f"Meal {i}") for i in range(3)]
        
        for meal in meals:
            await meal_repository.add(meal)
        await test_session.commit()
        
        # When: Querying with empty filter
        results = await meal_repository.query({})
        
        # Then: All meals returned
        assert len(results) == 3
        
    async def test_none_filter_returns_all_entities(self, meal_repository, test_session):
        """Test that None filter returns all entities"""
        # Given: Multiple meals in database
        from .test_data_factories import create_test_meal
        meals = [create_test_meal(name=f"Meal {i}") for i in range(3)]
        
        for meal in meals:
            await meal_repository.add(meal)
        await test_session.commit()
        
        # When: Querying with None filter
        results = await meal_repository.query(None)
        
        # Then: All meals returned
        assert len(results) == 3
        
    async def test_list_filter_applies_distinct_automatically(self, meal_repository, test_session):
        """Test that list filters automatically apply DISTINCT to prevent duplicates"""
        # Given: Setup scenario where joins could create duplicates
        from .test_data_factories import create_test_meal
        meal1 = create_test_meal(name="Meal 1")
        meal2 = create_test_meal(name="Meal 2")
        meal3 = create_test_meal(name="Meal 3")
        
        await meal_repository.add(meal1)
        await meal_repository.add(meal2)
        await meal_repository.add(meal3)
        await test_session.commit()
        
        # When: Using list filter (should auto-apply DISTINCT)
        results = await meal_repository.query({"name": ["Meal 1", "Meal 2"]})
        
        # Then: Results are distinct (no duplicates)
        assert len(results) == 2
        result_names = {r.name for r in results}
        assert result_names == {"Meal 1", "Meal 2"}


class TestSaGenericRepositoryJoinScenarios:
    """Test join scenarios with real foreign key relationships"""
    
    @pytest.fixture
    async def meal_with_recipes(self, meal_repository, recipe_repository, test_session):
        """Create meal with associated recipes for join testing"""
        from .test_data_factories import create_test_meal, create_test_recipe
        
        # Create meal first
        meal = create_test_meal(name="Complex Meal")
        await meal_repository.add(meal)
        await test_session.flush()  # Get meal ID for recipes
        
        # Create recipes associated with meal
        recipe1 = create_test_recipe(name="Recipe 1", meal_id=meal.id)
        recipe2 = create_test_recipe(name="Recipe 2", meal_id=meal.id)
        
        await recipe_repository.add(recipe1)
        await recipe_repository.add(recipe2)
        await test_session.commit()
        
        return meal, [recipe1, recipe2]
        
    async def test_single_table_filtering_no_joins(self, meal_repository, test_session):
        """Test filtering that doesn't require joins (single table)"""
        # Given: Meals with direct attributes
        from .test_data_factories import create_test_meal
        meals = [
            create_test_meal(name="Direct Filter Test", author_id="user123"),
            create_test_meal(name="Other Meal", author_id="user456"),
        ]
        
        for meal in meals:
            await meal_repository.add(meal)
        await test_session.commit()
        
        # When: Filtering on direct meal attributes (no joins needed)
        results = await meal_repository.query({
            "name": "Direct Filter Test",
            "author_id": "user123"
        })
        
        # Then: Correct meal returned without joins
        assert len(results) == 1
        assert results[0].name == "Direct Filter Test"
        assert results[0].author_id == "user123"
        
    async def test_join_filtering_with_recipes(self, meal_repository, meal_with_recipes):
        """Test filtering that requires joins to recipe table"""
        meal, recipes = meal_with_recipes
        
        # When: Filtering by recipe name (requires meal->recipe join)
        results = await meal_repository.query({"recipe_name": "Recipe 1"})
        
        # Then: Meal is found via recipe join
        assert len(results) == 1
        assert results[0].id == meal.id
        assert results[0].name == "Complex Meal"
        
    async def test_multi_level_join_prevents_duplicates(self, meal_repository, meal_with_recipes):
        """Test that multi-level joins don't create duplicate results"""
        meal, recipes = meal_with_recipes
        
        # When: Filtering by multiple recipe criteria (could create duplicates without DISTINCT)
        results = await meal_repository.query({
            "recipe_name": ["Recipe 1", "Recipe 2"]  # List filter on joined table
        })
        
        # Then: Single meal returned (no duplicates despite multiple recipe matches)
        assert len(results) == 1
        assert results[0].id == meal.id
        
    async def test_already_joined_tracking_prevents_duplicate_joins(self, meal_repository, meal_with_recipes):
        """Test that multiple filters on same joined table don't duplicate joins"""
        meal, recipes = meal_with_recipes
        
        # When: Multiple filters requiring same join (should not duplicate join)
        results = await meal_repository.query({
            "recipe_name": "Recipe 1",  # Requires recipe join
            "recipe_instructions": recipes[0].instructions  # Same recipe join
        })
        
        # Then: Query executes successfully (duplicate joins prevented internally)
        assert len(results) == 1
        assert results[0].id == meal.id


class TestSaGenericRepositoryQueryMethod:
    """Test query method functionality with real database operations"""
    
    async def test_query_with_limit(self, meal_repository, large_test_dataset):
        """Test query limit functionality with real data"""
        # When: Querying with limit
        results = await meal_repository.query({}, limit=5)
        
        # Then: Only specified number of results returned
        assert len(results) == 5
        
    async def test_query_return_sa_instance_flag(self, meal_repository, test_session):
        """Test query returning SQLAlchemy instances vs domain entities"""
        # Given: A meal in database
        from .test_data_factories import create_test_meal
        meal = create_test_meal(name="Test SA Instance")
        await meal_repository.add(meal)
        await test_session.commit()
        
        # When: Querying with return_sa_instance=True
        sa_results = await meal_repository.query(
            {"name": "Test SA Instance"}, 
            return_sa_instance=True
        )
        
        # Then: Returns SQLAlchemy model instances
        assert len(sa_results) == 1
        from .test_models import TestMealSaModel
        assert isinstance(sa_results[0], TestMealSaModel)
        assert sa_results[0].name == "Test SA Instance"
        
        # When: Querying with return_sa_instance=False (default)
        entity_results = await meal_repository.query({"name": "Test SA Instance"})
        
        # Then: Returns domain entities
        assert len(entity_results) == 1
        from .test_entities import TestMealEntity
        assert isinstance(entity_results[0], TestMealEntity)
        assert entity_results[0].name == "Test SA Instance"
        
    async def test_query_with_custom_sort_callback(self, meal_repository, test_session):
        """Test query with custom sorting callback"""
        # Given: Multiple meals with different names
        from .test_data_factories import create_test_meal
        meals = [
            create_test_meal(name="Zebra Meal"),
            create_test_meal(name="Alpha Meal"),
            create_test_meal(name="Beta Meal"),
        ]
        
        for meal in meals:
            await meal_repository.add(meal)
        await test_session.commit()
        
        # When: Querying with custom sort (reverse alphabetical)
        def reverse_name_sort(stmt, _):
            from .test_models import TestMealSaModel
            return stmt.order_by(TestMealSaModel.name.desc())
        
        results = await meal_repository.query({}, sort_callback=reverse_name_sort)
        
        # Then: Results are sorted in reverse alphabetical order
        result_names = [r.name for r in results]
        assert result_names == ["Zebra Meal", "Beta Meal", "Alpha Meal"]
        
    async def test_query_with_starting_stmt(self, meal_repository, test_session):
        """Test query with custom starting statement"""
        # Given: Multiple meals with different authors
        from .test_data_factories import create_test_meal
        from .test_models import TestMealSaModel
        
        user_meals = [
            create_test_meal(name="User Meal 1", author_id="target_user"),
            create_test_meal(name="User Meal 2", author_id="target_user"),
            create_test_meal(name="Other Meal", author_id="other_user"),
        ]
        
        for meal in user_meals:
            await meal_repository.add(meal)
        await test_session.commit()
        
        # When: Using custom starting statement that pre-filters by author
        custom_stmt = select(TestMealSaModel).where(TestMealSaModel.author_id == "target_user")
        results = await meal_repository.query(
            filter={"name": "User Meal 1"},  # Additional filter on pre-filtered results
            starting_stmt=custom_stmt
        )
        
        # Then: Gets correct meal from pre-filtered set
        assert len(results) == 1
        assert results[0].name == "User Meal 1"
        assert results[0].author_id == "target_user"
        
    async def test_query_with_custom_sa_model(self, meal_repository, recipe_repository, test_session):
        """Test query with custom sa_model parameter"""
        # Given: Recipes in database
        from .test_data_factories import create_test_meal, create_test_recipe
        from .test_models import TestRecipeSaModel
        
        meal = create_test_meal(name="Parent Meal")
        await meal_repository.add(meal)
        await test_session.flush()
        
        recipe = create_test_recipe(name="Custom Model Test", meal_id=meal.id)
        await recipe_repository.add(recipe)
        await test_session.commit()
        
        # When: Using meal repository but querying recipe model directly
        results = await meal_repository.query(
            filter={"name": "Custom Model Test"},
            sa_model=TestRecipeSaModel,  # Override default meal model
            return_sa_instance=True
        )
        
        # Then: Returns recipe SA instances
        assert len(results) == 1
        assert isinstance(results[0], TestRecipeSaModel)
        assert results[0].name == "Custom Model Test"
        
    async def test_query_with_already_joined_tracking(self, meal_repository, test_session):
        """Test query with explicit already_joined tracking"""
        # Given: A meal setup for join testing
        from .test_data_factories import create_test_meal
        meal = create_test_meal(name="Join Tracking Test")
        await meal_repository.add(meal)
        await test_session.commit()
        
        # When: Querying with already_joined set (simulating partial join state)
        already_joined = set()  # Start with empty set
        results = await meal_repository.query(
            filter={"name": "Join Tracking Test"},
            already_joined=already_joined
        )
        
        # Then: Query executes successfully with join tracking
        assert len(results) == 1
        assert results[0].name == "Join Tracking Test"
        
    async def test_query_empty_filter_returns_all(self, meal_repository, test_session):
        """Test that empty filter returns all entities"""
        # Given: Multiple meals in database
        from .test_data_factories import create_test_meal
        meals = [create_test_meal(name=f"Meal {i}") for i in range(3)]
        
        for meal in meals:
            await meal_repository.add(meal)
        await test_session.commit()
        
        # When: Querying with empty filter
        results = await meal_repository.query({})
        
        # Then: All meals returned
        assert len(results) == 3
        
    async def test_query_none_filter_returns_all(self, meal_repository, test_session):
        """Test that None filter returns all entities"""
        # Given: Multiple meals in database
        from .test_data_factories import create_test_meal
        meals = [create_test_meal(name=f"Meal {i}") for i in range(3)]
        
        for meal in meals:
            await meal_repository.add(meal)
        await test_session.commit()
        
        # When: Querying with None filter
        results = await meal_repository.query(None)
        
        # Then: All meals returned
        assert len(results) == 3


class TestSaGenericRepositoryDatabaseConstraints:
    """Test database constraint violations and error handling"""
    
    async def test_foreign_key_constraint_violation(self, recipe_repository, test_session):
        """Test foreign key constraint violation with real database"""
        # Given: A recipe referencing non-existent meal
        from .test_data_factories import create_test_recipe
        recipe = create_test_recipe(meal_id="non_existent_meal_id")
        
        # When/Then: Foreign key constraint fails with real DB error
        await recipe_repository.add(recipe)
        with pytest.raises(IntegrityError) as exc_info:
            await test_session.commit()
            
        # Verify it's a real foreign key constraint error
        error_msg = str(exc_info.value).lower()
        assert "foreign key constraint" in error_msg or "violates foreign key" in error_msg
        await test_session.rollback()
        
    async def test_check_constraint_violation(self, meal_repository, test_session):
        """Test check constraint violation with real database"""
        # Given: Meal with invalid data (negative cooking time)
        from .test_data_factories import create_test_meal
        meal = create_test_meal(total_time=-10)  # Violates check constraint
        
        # When/Then: Check constraint fails with real DB error
        await meal_repository.add(meal)
        with pytest.raises(IntegrityError) as exc_info:
            await test_session.commit()
            
        # Verify it's a real check constraint error
        error_msg = str(exc_info.value).lower()
        assert "check constraint" in error_msg
        await test_session.rollback()
        
    async def test_not_null_constraint_violation(self, meal_repository, test_session):
        """Test not null constraint violation with real database"""
        # Given: Meal missing required field
        from .test_data_factories import create_test_meal
        meal = create_test_meal(author_id=None)  # Violates NOT NULL constraint
        
        # When/Then: NOT NULL constraint fails with real DB error
        await meal_repository.add(meal)
        with pytest.raises(IntegrityError) as exc_info:
            await test_session.commit()
            
        # Verify it's a real not null constraint error
        error_msg = str(exc_info.value).lower()
        assert "not null constraint" in error_msg or "null value" in error_msg
        await test_session.rollback()


class TestSaGenericRepositoryPerformance:
    """Performance benchmarks with real database operations"""
    
    async def test_query_performance_baseline(self, meal_repository, large_test_dataset, benchmark_timer):
        """Establish performance baseline for queries on real data"""
        # When: Performing complex query on large dataset
        with benchmark_timer() as timer:
            results = await meal_repository.query({
                "total_time_lte": 60,
                "calorie_density_gte": 200.0,
            })
            
        # Then: Should complete within reasonable time
        timer.assert_faster_than(1.0)  # 1 second threshold for 100 records
        
        # Verify query correctness
        assert all(r.total_time <= 60 for r in results)
        assert all(r.calorie_density >= 200.0 for r in results)
        
    async def test_bulk_add_performance(self, meal_repository, test_session, benchmark_timer):
        """Test performance of bulk add operations"""
        # Given: Many meals to add
        from .test_data_factories import create_test_meal
        meals = [create_test_meal(name=f"Bulk Meal {i}") for i in range(50)]
        
        # When: Adding all meals
        with benchmark_timer() as timer:
            for meal in meals:
                await meal_repository.add(meal)
            await test_session.commit()
            
        # Then: Should complete within reasonable time
        timer.assert_faster_than(2.0)  # 2 seconds for 50 records
        
        # Verify all meals were added
        all_meals = await meal_repository.query({})
        assert len(all_meals) >= 50 