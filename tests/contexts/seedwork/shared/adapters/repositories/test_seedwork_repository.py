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
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.contexts.seedwork.shared.adapters.repositories.repository_exceptions import (
    FilterValidationError,
)
from tests.contexts.seedwork.shared.adapters.repositories.conftest import timeout_test

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


class TestSaGenericRepositoryCRUD:
    """Test basic CRUD operations with real database"""

    @timeout_test(60.0)  # 60 second timeout for this test
    async def test_add_and_get_entity(self, meal_repository, test_session):
        """Test adding and retrieving entity from real database"""
        # Given: A meal ORM entity
        from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

        meal = create_test_ORM_meal(name="Integration Test Meal", total_time=45)

        # When: Adding to session directly and committing to DB
        test_session.add(meal)
        await test_session.commit()

        # Then: Can retrieve it from database
        retrieved = await meal_repository.get(meal.id, _return_sa_instance=True)
        assert retrieved is not None
        assert retrieved.id == meal.id
        assert retrieved.name == "Integration Test Meal"
        assert retrieved.total_time == 45
        assert retrieved.created_at is not None  # DB should set timestamp

    @timeout_test(30.0)  # 30 second timeout for this test
    async def test_add_duplicate_id_raises_real_integrity_error(
        self, meal_repository, test_session
    ):
        """Test that duplicate IDs raise real database constraint errors"""
        # Given: Meals with specific ID
        from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

        meal_id = "duplicate_test_meal_123"
        meal1 = create_test_ORM_meal(id=meal_id, name="First Meal")
        meal2 = create_test_ORM_meal(id=meal_id, name="Second Meal")

        # When: Adding first meal successfully
        test_session.add(meal1)
        await test_session.commit()

        # Then: Adding second meal with same ID raises real DB constraint error
        with pytest.raises(IntegrityError) as exc_info:
            test_session.add(meal2)
            await test_session.commit()

        # Verify it's a real database error message
        assert "duplicate key value violates unique constraint" in str(exc_info.value)
        await test_session.rollback()

    async def test_get_nonexistent_entity_returns_none(self, meal_repository):
        """Test getting non-existent entity raises EntityNotFoundException"""
        # When: Trying to get entity that doesn't exist
        from src.contexts.seedwork.shared.adapters.exceptions.repo_exceptions import (
            EntityNotFoundError,
        )

        with pytest.raises(EntityNotFoundError):
            await meal_repository.get("nonexistent_meal_id", _return_sa_instance=True)

    async def test_update_entity_persists_changes(self, meal_repository, test_session):
        """Test updating entity persists changes to database"""
        # Given: An existing meal in database
        from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

        meal = create_test_ORM_meal(name="Original Name", total_time=30)
        test_session.add(meal)
        await test_session.commit()

        # When: Updating the entity directly in session
        meal.name = "Updated Name"
        meal.total_time = 60
        await test_session.commit()

        # Then: Changes are persisted in database
        retrieved = await meal_repository.get(meal.id, _return_sa_instance=True)
        assert retrieved.name == "Updated Name"
        assert retrieved.total_time == 60

    async def test_delete_entity_removes_from_database(
        self, meal_repository, test_session
    ):
        """Test deleting entity removes it from database (soft delete with discarded flag)"""
        # Given: An existing meal in database
        from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

        meal = create_test_ORM_meal(name="To Be Deleted")
        test_session.add(meal)
        await test_session.commit()

        # Verify it exists
        assert await meal_repository.get(meal.id, _return_sa_instance=True) is not None

        # When: Marking entity as discarded (soft delete) directly in session
        meal.discarded = True
        await test_session.commit()

        # Then: Entity is no longer accessible via get() (filtered out by discarded=False)
        from src.contexts.seedwork.shared.adapters.exceptions.repo_exceptions import (
            EntityNotFoundError,
        )

        with pytest.raises(EntityNotFoundError):
            await meal_repository.get(meal.id, _return_sa_instance=True)


class TestSaGenericRepositoryFilterOperations:
    """Test filter operations with real database queries"""

    @pytest.fixture
    async def meals_with_various_attributes(self, meal_repository, test_session):
        """Create meals with different attributes for filtering tests"""
        from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

        meals = [
            create_test_ORM_meal(
                name="Quick Salad", total_time=10, calorie_density=150.0
            ),
            create_test_ORM_meal(
                name="Pasta Dish", total_time=30, calorie_density=350.0
            ),
            create_test_ORM_meal(
                name="Slow Roast", total_time=120, calorie_density=450.0
            ),
            create_test_ORM_meal(
                name="Complex Stew", total_time=180, calorie_density=300.0
            ),
        ]

        for meal in meals:
            test_session.add(meal)
        await test_session.commit()

        return meals

    @pytest.mark.parametrize(
        "filter_key,filter_value,expected_count,expected_names,condition_check",
        [
            # Greater than or equal tests
            (
                "total_time_gte",
                60,
                2,
                {"Slow Roast", "Complex Stew"},
                lambda r: r.total_time >= 60,
            ),
            (
                "total_time_gte",
                120,
                2,
                {"Slow Roast", "Complex Stew"},
                lambda r: r.total_time >= 120,
            ),
            (
                "calorie_density_gte",
                300.0,
                3,
                {"Pasta Dish", "Slow Roast", "Complex Stew"},
                lambda r: r.calorie_density >= 300.0,
            ),
            # Less than or equal tests
            (
                "total_time_lte",
                30,
                2,
                {"Quick Salad", "Pasta Dish"},
                lambda r: r.total_time <= 30,
            ),
            (
                "total_time_lte",
                120,
                3,
                {"Quick Salad", "Pasta Dish", "Slow Roast"},
                lambda r: r.total_time <= 120,
            ),
            (
                "calorie_density_lte",
                350.0,
                3,
                {"Quick Salad", "Pasta Dish", "Complex Stew"},
                lambda r: r.calorie_density <= 350.0,
            ),
            # Not equals tests
            (
                "total_time_ne",
                30,
                3,
                {"Quick Salad", "Slow Roast", "Complex Stew"},
                lambda r: r.total_time != 30,
            ),
            (
                "total_time_ne",
                10,
                3,
                {"Pasta Dish", "Slow Roast", "Complex Stew"},
                lambda r: r.total_time != 10,
            ),
            # IN operator with list values
            (
                "name",
                ["Quick Salad", "Slow Roast"],
                2,
                {"Quick Salad", "Slow Roast"},
                lambda r: r.name in ["Quick Salad", "Slow Roast"],
            ),
            (
                "total_time",
                [10, 120],
                2,
                {"Quick Salad", "Slow Roast"},
                lambda r: r.total_time in [10, 120],
            ),
            # NOT IN operator tests
            (
                "total_time_not_in",
                [10, 30],
                2,
                {"Slow Roast", "Complex Stew"},
                lambda r: r.total_time not in [10, 30],
            ),
            (
                "name_not_in",
                ["Quick Salad"],
                3,
                {"Pasta Dish", "Slow Roast", "Complex Stew"},
                lambda r: r.name not in ["Quick Salad"],
            ),
        ],
        ids=[
            "gte_time_60",
            "gte_time_120",
            "gte_calories_300",
            "lte_time_30",
            "lte_time_120",
            "lte_calories_350",
            "ne_time_30",
            "ne_time_10",
            "in_names",
            "in_times",
            "not_in_times",
            "not_in_names",
        ],
    )
    async def test_filter_operations(
        self,
        meal_repository,
        meals_with_various_attributes,
        filter_key,
        filter_value,
        expected_count,
        expected_names,
        condition_check,
    ):
        """Test various filter operations with parametrized values"""
        # When: Applying filter
        results = await meal_repository.query(
            filter={filter_key: filter_value}, _return_sa_instance=True
        )

        # Then: Expected results
        assert len(results) == expected_count
        result_names = {r.name for r in results}
        assert result_names == expected_names

        # Verify condition is met for all results
        assert all(condition_check(r) for r in results)

    async def test_filter_with_is_not_operator(self, meal_repository, test_session):
        """Test filtering with IS NOT operator for NULL values"""
        # Given: Meals with and without descriptions
        from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

        with_desc = create_test_ORM_meal(
            name="Has Description", description="Delicious meal"
        )
        without_desc = create_test_ORM_meal(name="No Description", description=None)

        test_session.add(with_desc)
        test_session.add(without_desc)
        await test_session.commit()

        # When: Filtering for non-null descriptions
        results = await meal_repository.query(
            filter={"description_is_not": None}, _return_sa_instance=True
        )

        # Then: Only meal with description returned
        assert len(results) == 1
        assert results[0].name == "Has Description"
        assert results[0].description == "Delicious meal"

    @pytest.mark.parametrize(
        "like_value,expected_name,expected_count",
        [
            (True, "Liked Meal", 1),
            (False, "Not Liked Meal", 1),
            (None, "Neutral Meal", 1),
        ],
        ids=["boolean_true", "boolean_false", "boolean_null"],
    )
    async def test_filter_with_boolean_column_uses_is_operator(
        self, meal_repository, test_session, like_value, expected_name, expected_count
    ):
        """Test that boolean columns use IS operator behavior with real data"""
        # Given: Meals with different boolean values
        from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

        liked_meal = create_test_ORM_meal(name="Liked Meal", like=True)
        not_liked_meal = create_test_ORM_meal(name="Not Liked Meal", like=False)
        neutral_meal = create_test_ORM_meal(name="Neutral Meal", like=None)

        test_session.add(liked_meal)
        test_session.add(not_liked_meal)
        test_session.add(neutral_meal)
        await test_session.commit()

        # When: Filtering for specific like value
        results = await meal_repository.query(
            filter={"like": like_value}, _return_sa_instance=True
        )

        # Then: Only matching meal returned
        assert len(results) == expected_count
        assert results[0].name == expected_name
        assert results[0].like == like_value

    async def test_string_column_equality_operator(self, meal_repository, test_session):
        """Test that string columns use equality operator with real data"""
        # Given: Meals with exact and partial name matches
        from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

        exact_match = create_test_ORM_meal(name="Exact Match")
        partial_match = create_test_ORM_meal(name="Exact Match Plus More")
        different_name = create_test_ORM_meal(name="Different Name")

        test_session.add(exact_match)
        test_session.add(partial_match)
        test_session.add(different_name)
        await test_session.commit()

        # When: Filtering for exact string match
        results = await meal_repository.query(
            filter={"name": "Exact Match"}, _return_sa_instance=True
        )

        # Then: Only exact match returned (not partial)
        assert len(results) == 1
        assert results[0].name == "Exact Match"

    async def test_postfix_removal_in_filter_mapping(
        self, meal_repository, test_session
    ):
        """Test that postfix operators correctly map to base column names"""
        # Given: Meals with different total times
        from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

        quick_meal = create_test_ORM_meal(name="Quick", total_time=15)
        slow_meal = create_test_ORM_meal(name="Slow", total_time=90)

        test_session.add(quick_meal)
        test_session.add(slow_meal)
        await test_session.commit()

        # When: Using postfix operator that should map to base column "total_time"
        results = await meal_repository.query(
            filter={"total_time_gte": 60}, _return_sa_instance=True
        )  # Should map to total_time column

        # Then: Filtering works correctly (postfix was removed to find column)
        assert len(results) == 1
        assert results[0].name == "Slow"
        assert results[0].total_time >= 60

    async def test_multiple_filters_combined(
        self, meal_repository, meals_with_various_attributes
    ):
        """Test combining multiple filters in single query"""
        # When: Filtering with multiple criteria
        results = await meal_repository.query(
            filter={
                "total_time_gte": 30,  # >= 30 minutes
                "calorie_density_lte": 400.0,  # <= 400 cal/serving
            },
            _return_sa_instance=True,
        )

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
        with pytest.raises((FilterValidationError, KeyError)):
            await meal_repository.query(
                filter={"unknown_filter_key": "some_value"}, _return_sa_instance=True
            )

    @pytest.mark.parametrize(
        "filter_value,description",
        [
            ({}, "empty filter dict"),
            (None, "None filter"),
        ],
        ids=["empty_dict", "none_filter"],
    )
    async def test_empty_and_none_filter_returns_all_entities(
        self, meal_repository, test_session, filter_value, description
    ):
        """Test that empty filter dict and None filter return all entities"""
        # Given: Multiple meals in database
        from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

        meals = [create_test_ORM_meal(name=f"Meal {i}") for i in range(3)]

        for meal in meals:
            test_session.add(meal)
        await test_session.commit()

        # When: Querying with test filter
        results = await meal_repository.query(
            filter=filter_value, _return_sa_instance=True
        )

        # Then: All meals returned
        assert len(results) == 3

    async def test_list_filter_applies_distinct_automatically(
        self, meal_repository, test_session
    ):
        """Test that list filters automatically apply DISTINCT to prevent duplicates"""
        # Given: Setup scenario where joins could create duplicates
        from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

        meal1 = create_test_ORM_meal(name="Meal 1")
        meal2 = create_test_ORM_meal(name="Meal 2")
        meal3 = create_test_ORM_meal(name="Meal 3")

        test_session.add(meal1)
        test_session.add(meal2)
        test_session.add(meal3)
        await test_session.commit()

        # When: Using list filter (should auto-apply DISTINCT)
        results = await meal_repository.query(
            filter={"name": ["Meal 1", "Meal 2"]}, _return_sa_instance=True
        )

        # Then: Results are distinct (no duplicates)
        assert len(results) == 2
        result_names = {r.name for r in results}
        assert result_names == {"Meal 1", "Meal 2"}


class TestSaGenericRepositoryJoinScenarios:
    """Test join scenarios with real foreign key relationships"""

    @pytest.fixture
    async def meal_with_recipes(self, meal_repository, recipe_repository, test_session):
        """Create meal with associated recipes for join testing"""
        from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
            create_test_ORM_recipe,
        )

        # Create meal first
        meal = create_test_ORM_meal(name="Complex Meal")
        test_session.add(meal)
        await test_session.flush()  # Get meal ID for recipes

        # Create recipes associated with meal
        recipe1 = create_test_ORM_recipe(name="Recipe 1", meal_id=meal.id)
        recipe2 = create_test_ORM_recipe(name="Recipe 2", meal_id=meal.id)

        test_session.add(recipe1)
        test_session.add(recipe2)
        await test_session.commit()

        return meal, [recipe1, recipe2]

    async def test_single_table_filtering_no_joins(self, meal_repository, test_session):
        """Test filtering that doesn't require joins (single table)"""
        # Given: Meals with direct attributes (testing single-table filtering)
        from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

        meals = [
            create_test_ORM_meal(name="Direct Filter Test", author_id="user123"),
            create_test_ORM_meal(name="Other Meal", author_id="user456"),
            create_test_ORM_meal(name="Another Test", author_id="user123"),
        ]

        for meal in meals:
            test_session.add(meal)
        await test_session.commit()

        # When: Filtering on direct meal attributes (no joins needed)
        # This tests the critical case where mapper has filters but NO join clauses
        results = await meal_repository.query(
            filter={"name": "Direct Filter Test", "author_id": "user123"},
            _return_sa_instance=True,
        )

        # Then: Correct meal returned without joins
        assert len(results) == 1
        assert results[0].name == "Direct Filter Test"
        assert results[0].author_id == "user123"

        # When: Testing another single-table filter scenario
        author_results = await meal_repository.query(
            filter={"author_id": "user123"}, _return_sa_instance=True
        )

        # Then: All meals by that author returned (2 meals)
        assert len(author_results) == 2
        author_names = {r.name for r in author_results}
        assert author_names == {"Direct Filter Test", "Another Test"}

        # When: Testing filter that should return no results
        no_results = await meal_repository.query(
            filter={"author_id": "nonexistent_user"}, _return_sa_instance=True
        )

        # Then: No results returned
        assert len(no_results) == 0

    async def test_join_filtering_with_recipes(
        self, meal_repository, meal_with_recipes
    ):
        """Test filtering that requires joins to recipe table"""
        meal, recipes = meal_with_recipes

        # When: Filtering by recipe name (requires meal->recipe join)
        results = await meal_repository.query(
            filter={"recipe_name": "Recipe 1"}, _return_sa_instance=True
        )

        # Then: Meal is found via recipe join
        assert len(results) == 1
        assert results[0].id == meal.id
        assert results[0].name == "Complex Meal"

    async def test_multi_level_join_prevents_duplicates(
        self, meal_repository, meal_with_recipes
    ):
        """Test that multi-level joins don't create duplicate results"""
        meal, recipes = meal_with_recipes

        # When: Filtering by multiple recipe criteria (could create duplicates without DISTINCT)
        results = await meal_repository.query(
            filter={
                "recipe_name": ["Recipe 1", "Recipe 2"]  # List filter on joined table
            },
            _return_sa_instance=True,
        )

        # Then: Single meal returned (no duplicates despite multiple recipe matches)
        assert len(results) == 1
        assert results[0].id == meal.id

    async def test_already_joined_tracking_prevents_duplicate_joins(
        self, meal_repository, meal_with_recipes
    ):
        """Test that multiple filters on same joined table don't duplicate joins"""
        meal, recipes = meal_with_recipes

        # When: Multiple filters requiring same join (should not duplicate join)
        results = await meal_repository.query(
            filter={
                "recipe_name": "Recipe 1",  # Requires recipe join
                "recipe_instructions": recipes[0].instructions,  # Same recipe join
            },
            _return_sa_instance=True,
        )

        # Then: Query executes successfully (duplicate joins prevented internally)
        assert len(results) == 1
        assert results[0].id == meal.id


class TestSaGenericRepositoryQueryMethod:
    """Test query method functionality with real database operations"""

    async def test_query_with_limit(self, meal_repository, large_test_dataset):
        """Test query limit functionality with real data"""
        # When: Querying with limit
        results = await meal_repository.query(
            filter={}, limit=5, _return_sa_instance=True
        )

        # Then: Only specified number of results returned
        assert len(results) == 5

    async def test_query_return_sa_instance_flag(self, meal_repository, test_session):
        """Test query returning SQLAlchemy instances vs domain entities"""
        # Given: A meal in database
        from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

        meal = create_test_ORM_meal(name="Test SA Instance")
        test_session.add(meal)
        await test_session.commit()

        # When: Querying with return_sa_instance=True
        sa_results = await meal_repository.query(
            filter={"name": "Test SA Instance"}, _return_sa_instance=True
        )

        # Then: Returns SQLAlchemy model instances
        assert len(sa_results) == 1
        from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
            MealSaTestModel,
        )

        assert isinstance(sa_results[0], MealSaTestModel)
        assert sa_results[0].name == "Test SA Instance"

        # When: Querying with return_sa_instance=False (default)
        entity_results = await meal_repository.query(
            filter={"name": "Test SA Instance"}
        )

        # Then: Returns domain entities
        assert len(entity_results) == 1
        from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.entities import (
            TestMealEntity,
        )

        assert isinstance(entity_results[0], TestMealEntity)
        assert entity_results[0].name == "Test SA Instance"

    async def test_query_with_custom_sort_filter(self, meal_repository, test_session):
        """Test query with custom sorting filter"""
        # Given: Multiple meals with different names
        from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

        meals = [
            create_test_ORM_meal(name="Zebra Meal"),
            create_test_ORM_meal(name="Alpha Meal"),
            create_test_ORM_meal(name="Beta Meal"),
        ]

        for meal in meals:
            test_session.add(meal)
        await test_session.commit()

        results = await meal_repository.query(
            filter={"sort": "-name"}, _return_sa_instance=True
        )

        # Then: Results are sorted in reverse alphabetical order
        result_names = [r.name for r in results]
        assert result_names == ["Zebra Meal", "Beta Meal", "Alpha Meal"]

    async def test_query_with_custom_starting_stmt(self, meal_repository, test_session):
        """Test query with custom starting statement"""
        # Given: Multiple meals with different authors
        from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )
        from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
            MealSaTestModel,
        )

        user_meals = [
            create_test_ORM_meal(name="User Meal 1", author_id="target_user"),
            create_test_ORM_meal(name="User Meal 2", author_id="target_user"),
            create_test_ORM_meal(name="Other Meal", author_id="other_user"),
        ]

        for meal in user_meals:
            test_session.add(meal)
        await test_session.commit()

        # When: Using custom starting statement that pre-filters by author
        custom_stmt = select(MealSaTestModel).where(
            MealSaTestModel.author_id == "target_user"
        )
        results = await meal_repository.query(
            filter={"name": "User Meal 1"},  # Additional filter on pre-filtered results
            starting_stmt=custom_stmt,
            _return_sa_instance=True,
        )

        # Then: Gets correct meal from pre-filtered set
        assert len(results) == 1
        assert results[0].name == "User Meal 1"
        assert results[0].author_id == "target_user"

    async def test_query_with_custom_starting_stmt_different_model(
        self, meal_repository, recipe_repository, test_session
    ):
        """Test query with custom starting statement targeting a different model"""
        # Given: Recipes in database
        from sqlalchemy import select

        from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
            create_test_ORM_recipe,
        )
        from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
            RecipeSaTestModel,
        )

        meal = create_test_ORM_meal(name="Parent Meal")
        test_session.add(meal)
        await test_session.flush()

        recipe = create_test_ORM_recipe(name="Custom Model Test", meal_id=meal.id)
        test_session.add(recipe)
        await test_session.commit()

        # When: Using meal repository but querying recipe model directly via starting_stmt
        results = await meal_repository.query(
            filter={
                "recipe_name": "Custom Model Test"
            },  # Use meal repo's recipe filter key
            starting_stmt=select(RecipeSaTestModel),  # Override to query recipe model
            _return_sa_instance=True,
        )

        # Then: Returns recipe SA instances
        assert len(results) == 1
        assert isinstance(results[0], RecipeSaTestModel)
        assert results[0].name == "Custom Model Test"

    async def test_query_with_already_joined_tracking(
        self, meal_repository, test_session
    ):
        """Test query with explicit already_joined tracking"""
        # Given: A meal setup for join testing
        from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

        meal = create_test_ORM_meal(name="Join Tracking Test")
        test_session.add(meal)
        await test_session.commit()

        # When: Querying with already_joined set (simulating partial join state)
        already_joined = set()  # Start with empty set
        results = await meal_repository.query(
            filter={"name": "Join Tracking Test"},
            already_joined=already_joined,
            _return_sa_instance=True,
        )

        # Then: Query executes successfully with join tracking
        assert len(results) == 1
        assert results[0].name == "Join Tracking Test"

    @pytest.mark.parametrize(
        "filter_value", [{}, None], ids=["empty_dict", "none_filter"]
    )
    async def test_query_empty_and_none_filter_returns_all(
        self, meal_repository, test_session, filter_value
    ):
        """Test that empty filter dict and None filter return all entities"""
        # Given: Multiple meals in database
        from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

        meals = [create_test_ORM_meal(name=f"Meal {i}") for i in range(3)]

        for meal in meals:
            test_session.add(meal)
        await test_session.commit()

        # When: Querying with test filter
        results = await meal_repository.query(
            filter=filter_value, _return_sa_instance=True
        )

        # Then: All meals returned
        assert len(results) == 3


class TestSaGenericRepositoryDatabaseConstraints:
    """Test database constraint violations and error handling"""

    @pytest.mark.parametrize(
        "constraint_type,entity_factory,factory_kwargs,expected_error_keywords",
        [
            (
                "foreign_key",
                "create_test_ORM_recipe",
                {"meal_id": "non_existent_meal_id"},
                ["foreign key constraint", "violates foreign key"],
            ),
            (
                "check_constraint",
                "create_test_ORM_meal",
                {"total_time": -10},
                ["check constraint"],
            ),
            (
                "not_null",
                "create_test_ORM_meal",
                {"author_id": None},
                ["not null constraint", "null value"],
            ),
        ],
        ids=["foreign_key", "check_constraint", "not_null"],
    )
    async def test_database_constraint_violations(
        self,
        meal_repository,
        recipe_repository,
        test_session,
        constraint_type,
        entity_factory,
        factory_kwargs,
        expected_error_keywords,
    ):
        """Test various database constraint violations with real database"""
        # Given: Entity with constraint-violating data
        from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
            create_test_ORM_recipe,
        )

        factory_func = (
            create_test_ORM_recipe
            if entity_factory == "create_test_ORM_recipe"
            else create_test_ORM_meal
        )

        entity = factory_func(**factory_kwargs)

        # When/Then: Constraint fails with real DB error during add()
        with pytest.raises(IntegrityError) as exc_info:
            test_session.add(entity)
            await test_session.commit()

        # Verify it's the expected constraint error
        error_msg = str(exc_info.value).lower()
        assert any(keyword in error_msg for keyword in expected_error_keywords)
        await test_session.rollback()


class TestSaGenericRepositoryPerformance:
    """Performance benchmarks with real database operations"""

    @pytest.mark.parametrize(
        "operation_type,test_params",
        [
            (
                "complex_query",
                {
                    "filter": {"total_time_lte": 60, "calorie_density_gte": 200.0},
                    "time_threshold": 1.0,
                    "validation": lambda results: all(
                        r.total_time <= 60 and r.calorie_density >= 200.0
                        for r in results
                    ),
                },
            ),
            (
                "simple_query",
                {
                    "filter": {"total_time_gte": 30},
                    "time_threshold": 0.5,
                    "validation": lambda results: all(
                        r.total_time >= 30 for r in results
                    ),
                },
            ),
        ],
        ids=["complex_query", "simple_query"],
    )
    async def test_query_performance_baseline(
        self,
        meal_repository,
        large_test_dataset,
        async_benchmark_timer,
        operation_type,
        test_params,
    ):
        """Establish performance baseline for queries on real data"""
        # When: Performing query on large dataset
        async with async_benchmark_timer() as timer:
            results = await meal_repository.query(
                filter=test_params["filter"], _return_sa_instance=True
            )

        # Then: Should complete within reasonable time
        timer.assert_faster_than(test_params["time_threshold"])

        # Verify query correctness
        assert test_params["validation"](results)

    async def test_bulk_add_performance(
        self, meal_repository, test_session, async_benchmark_timer
    ):
        """Test performance of bulk add operations"""
        # Given: Many meals to add
        from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
        )

        meals = [create_test_ORM_meal(name=f"Bulk Meal {i}") for i in range(50)]

        # When: Adding all meals
        async with async_benchmark_timer() as timer:
            for meal in meals:
                test_session.add(meal)
            await test_session.commit()

        # Then: Should complete within reasonable time
        timer.assert_faster_than(2.0)  # 2 seconds for 50 records

        # Verify all meals were added
        all_meals = await meal_repository.query(filter={}, _return_sa_instance=True)
        assert len(all_meals) >= 50

    async def test_sorting_with_joins_applies_filters_correctly(
        self, meal_repository, recipe_repository, test_session
    ):
        """Test that sorting with joins applies filters correctly without double-application"""
        # Given: Meal with recipes for join-based sorting
        from tests.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
            create_test_ORM_recipe,
        )

        meal1 = create_test_ORM_meal(name="Meal A", author_id="user1")
        meal2 = create_test_ORM_meal(name="Meal B", author_id="user2")
        test_session.add(meal1)
        test_session.add(meal2)
        await test_session.flush()

        # Create recipes with different names for sorting
        recipe1 = create_test_ORM_recipe(
            name="Z Recipe", meal_id=meal1.id
        )  # Should sort last
        recipe2 = create_test_ORM_recipe(
            name="A Recipe", meal_id=meal2.id
        )  # Should sort first
        test_session.add(recipe1)
        test_session.add(recipe2)
        await test_session.commit()

        # When: Filtering by author AND sorting by recipe name (requires join)
        # This tests that:
        # 1. Filters are applied correctly in main loop (author_id filter)
        # 2. Sorting joins are handled correctly in sort section
        # 3. No double filter application occurs
        results = await meal_repository.query(
            filter={
                "author_id": "user1",  # Filter: only user1's meals
                "sort": "recipe_name",  # Sort: by recipe name (requires join)
            },
            _return_sa_instance=True,
        )

        # Then: Only user1's meal returned (filter applied correctly)
        assert len(results) == 1
        assert results[0].name == "Meal A"
        assert results[0].author_id == "user1"

        # When: Testing sort without filter to verify join-based sorting works
        all_results = await meal_repository.query(
            filter={"sort": "recipe_name"},  # Sort by recipe name (join required)
            _return_sa_instance=True,
        )

        # Then: Results sorted by recipe name (A Recipe first, Z Recipe last)
        assert len(all_results) == 2
        # Meal B should come first (has "A Recipe")
        # Meal A should come second (has "Z Recipe")
        assert all_results[0].name == "Meal B"  # Has "A Recipe"
        assert all_results[1].name == "Meal A"  # Has "Z Recipe"
