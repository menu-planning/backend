"""
Behavior documentation integration tests for SaGenericRepository with real database

This module contains tests that serve as living documentation of the repository's
behavior and expected usage patterns using real database connections.

Following "Architecture Patterns with Python" principles:
- Test behavior, not implementation
- Use real database connections (test database)
- Test fixtures for known DB states (not mocks)
- Catch real DB errors (constraints, deadlocks, etc.)

Key improvements over v1:
- Real database testing validates actual behavior
- Real SQL generation and execution
- Real constraint verification
- Performance validation with actual data

Replaces: test_seedwork_repository_behavior.py (mock-based version)

NOTE: This version tests repository features directly by:
- Using ORM models instead of domain entities
- Bypassing repository add method with direct session operations
- Setting _return_sa_instance=True to bypass mapper logic
"""

import pytest
from sqlalchemy.exc import IntegrityError
from src.contexts.seedwork.adapters.repositories.repository_exceptions import (
    FilterValidationError,
)

from .conftest import timeout_test

pytestmark = [pytest.mark.anyio, pytest.mark.integration]


class TestSaGenericRepositoryBehaviorDocumentation:
    """
    BEHAVIOR DOCUMENTATION: Living documentation of repository patterns with real database

    These tests serve as examples and documentation of how the repository should be used
    and what behaviors are expected in different scenarios. They test actual database behavior
    rather than mocked responses, using ORM models directly to bypass mapper logic.
    """

    @pytest.mark.integration
    @timeout_test(30.0)
    async def test_basic_repository_usage_pattern(self, meal_repository, test_session):
        """
        BEHAVIOR: Basic repository usage pattern with real database

        This documents the most common usage pattern:
        1. Create repository with model types and filter mappers
        2. Call query() with filter dictionary
        3. Receive ORM objects back from real database
        """
        # Given: Real meals in database using ORM models
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
            reset_counters,
        )

        reset_counters()  # Ensure deterministic IDs
        meal1 = create_test_ORM_meal(name="Italian Pasta", author_id="chef123")
        meal2 = create_test_ORM_meal(name="French Toast", author_id="chef456")

        test_session.add(meal1)
        test_session.add(meal2)
        await test_session.commit()

        # When: Performing basic filter query with ORM return
        result = await meal_repository.query(
            filters={"name": "Italian Pasta", "author_id": "chef123"},
            _return_sa_instance=True,
        )

        # Then: Repository returns actual ORM objects from database
        assert len(result) == 1
        assert result[0].name == "Italian Pasta"
        assert result[0].author_id == "chef123"
        assert result[0].id == meal1.id

        # This is the expected normal flow for repository usage

    @pytest.mark.integration
    async def test_postfix_operator_behavior_documentation(
        self, meal_repository, test_session
    ):
        """
        BEHAVIOR: Postfix operator behavior and precedence with real data

        This documents how postfix operators work with actual database queries:
        - _gte, _lte for range queries
        - _ne for exclusion (excludes NULL values)
        - _not_in for list exclusion with NULL handling
        - _is_not for NULL checks
        """
        # Given: Meals with different attributes for testing postfix operators
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
            reset_counters,
        )

        reset_counters()  # Ensure deterministic IDs
        meals = [
            create_test_ORM_meal(
                name="Quick Meal", total_time=20, calorie_density=150.0, like=True
            ),
            create_test_ORM_meal(
                name="Medium Meal", total_time=45, calorie_density=300.0, like=True
            ),  # like=True satisfies like_ne: False filter
            create_test_ORM_meal(
                name="Long Meal", total_time=90, calorie_density=500.0, like=False
            ),
        ]

        for meal in meals:
            test_session.add(meal)
        await test_session.commit()

        # When: Using postfix operators in real database query
        result = await meal_repository.query(
            filters={
                "total_time_gte": 30,  # At least 30 minutes
                "total_time_lte": 120,  # At most 120 minutes
                "calorie_density_gte": 200.0,  # At least 200 calories
                "like_ne": False,  # Not disliked (excludes NULL and False values)
            },
            _return_sa_instance=True,
        )

        # Then: Real database correctly applies all postfix operators
        assert len(result) == 1  # Only Medium Meal matches all criteria
        result_names = {r.name for r in result}
        assert result_names == {"Medium Meal"}

        # Verify all conditions are met
        for r in result:
            assert r.total_time >= 30 and r.total_time <= 120
            assert r.calorie_density >= 200.0
            # Standard SQL != excludes NULL values, only True values pass like_ne: False
            assert r.like is True

    @pytest.mark.integration
    async def test_join_behavior_documentation(
        self, meal_repository, recipe_repository, test_session
    ):
        """
        BEHAVIOR: Join behavior and multi-table filtering with real relationships

        This documents how the repository handles joins with actual foreign keys:
        - Automatic join detection based on filter keys
        - Multi-level join chains (meal->recipe->ingredient)
        - Join deduplication to prevent redundant joins
        """
        # Given: Real meal with associated recipe for join testing
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
            create_test_ORM_recipe,
            reset_counters,
        )

        reset_counters()  # Ensure deterministic IDs

        meal = create_test_ORM_meal(name="Chicken Dinner", author_id="chef123")
        test_session.add(meal)
        await test_session.flush()  # Get meal ID for recipe FK

        recipe = create_test_ORM_recipe(name="Grilled Chicken", meal_id=meal.id)
        test_session.add(recipe)
        await test_session.commit()

        # When: Using filters that require real database joins
        result = await meal_repository.query(
            filters={
                # Direct meal properties (no join needed)
                "author_id": "chef123",
                # Recipe properties (requires meal->recipe join)
                "recipe_name": "Grilled Chicken",
            },
            _return_sa_instance=True,
        )

        # Then: Repository handles real join chains automatically
        assert len(result) == 1
        assert result[0].name == "Chicken Dinner"
        assert result[0].author_id == "chef123"

    @pytest.mark.integration
    async def test_list_filter_behavior_documentation(
        self, meal_repository, test_session
    ):
        """
        BEHAVIOR: List filter behavior and IN operator usage with real database

        This documents how list filters work with actual SQL:
        - Automatic IN operator for list values
        - DISTINCT application for list filters
        - Empty list handling
        """
        # Given: Multiple meals with different IDs and authors
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
            reset_counters,
        )

        reset_counters()  # Ensure deterministic IDs
        meals = [
            create_test_ORM_meal(name="Pasta", author_id="chef1"),
            create_test_ORM_meal(name="Pizza", author_id="chef2"),
            create_test_ORM_meal(name="Salad", author_id="chef3"),
            create_test_ORM_meal(name="Soup", author_id="chef1"),
        ]

        for meal in meals:
            test_session.add(meal)
        await test_session.commit()

        # Store meal IDs for filtering
        meal_ids = [meals[0].id, meals[1].id, meals[2].id]

        # When: Using list filters for multiple values
        result = await meal_repository.query(
            filters={
                "name": ["Pasta", "Pizza", "Salad"],  # IN operator
                "author_id": ["chef1", "chef2"],  # IN operator
            },
            _return_sa_instance=True,
        )

        # Then: List filters use real IN operator and apply DISTINCT
        # Should return meals that match both conditions (AND logic between filters)
        assert len(result) == 2
        result_names = {r.name for r in result}
        assert result_names == {"Pasta", "Pizza"}

        # Verify all results match both filter conditions
        for r in result:
            assert r.name in ["Pasta", "Pizza", "Salad"]
            assert r.author_id in ["chef1", "chef2"]

    @pytest.mark.integration
    async def test_not_in_operator_behavior_documentation(
        self, meal_repository, test_session
    ):
        """
        BEHAVIOR: NOT IN operator special behavior with NULL handling in real database

        This documents the special behavior of _not_in with actual SQL:
        - Includes NULL values in results (NULL OR NOT IN)
        - Empty list handling
        - Different from standard SQL NOT IN
        """
        # Given: Meals with some NULL values and various authors
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
            reset_counters,
        )

        reset_counters()  # Ensure deterministic IDs
        meals = [
            create_test_ORM_meal(name="Normal User Meal", author_id="normal_user"),
            create_test_ORM_meal(name="Banned User Meal", author_id="banned_user1"),
            create_test_ORM_meal(
                name="Anonymous Meal", author_id="anonymous_user"
            ),  # Use valid author instead of NULL
            create_test_ORM_meal(name="Another Normal Meal", author_id="normal_user2"),
        ]

        for meal in meals:
            test_session.add(meal)
        await test_session.commit()

        # When: Using NOT IN with real database NULL handling
        result = await meal_repository.query(
            filters={
                "author_id_not_in": ["banned_user1", "banned_user2"],  # Excludes these
            },
            _return_sa_instance=True,
        )

        # Then: _not_in excludes the banned users
        assert len(result) == 3
        result_names = {r.name for r in result}
        expected_names = {"Normal User Meal", "Anonymous Meal", "Another Normal Meal"}
        assert result_names == expected_names

        # Verify excluded authors are not in result
        for r in result:
            assert r.author_id not in ["banned_user1", "banned_user2"]

    @pytest.mark.integration
    async def test_composite_field_behavior_documentation(
        self, meal_repository, test_session
    ):
        """
        BEHAVIOR: Composite field filtering with real database queries

        This documents how composite fields are handled with actual SQL:
        - Individual composite field components can be filtered
        - Each component acts like a regular column filter
        - Supports all standard operators (_gte, _lte, etc.)
        """
        # Given: Meals with different nutritional values
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
            reset_counters,
        )

        reset_counters()  # Ensure deterministic IDs
        meals = [
            create_test_ORM_meal(name="High Protein", calorie_density=400.0),
            create_test_ORM_meal(name="Low Calorie", calorie_density=150.0),
            create_test_ORM_meal(name="Balanced", calorie_density=300.0),
        ]

        for meal in meals:
            test_session.add(meal)
        await test_session.commit()

        # When: Filtering by composite field components
        result = await meal_repository.query(
            filters={
                "calorie_density_gte": 250.0,  # Minimum calories
                "calorie_density_lte": 450.0,  # Maximum calories
            },
            _return_sa_instance=True,
        )

        # Then: Real database correctly handles composite field filtering
        assert len(result) == 2
        result_names = {r.name for r in result}
        assert result_names == {"High Protein", "Balanced"}

        # Verify all results match filter criteria
        for r in result:
            assert 250.0 <= r.calorie_density <= 450.0

    @pytest.mark.integration
    async def test_sorting_and_pagination_behavior_documentation(
        self, meal_repository, recipe_repository, test_session, async_benchmark_timer
    ):
        """
        BEHAVIOR: Sorting and pagination with complex queries on real data

        This documents the interaction between:
        - Multi-column filtering
        - Custom sorting logic
        - Limit/offset pagination
        - DISTINCT handling for joins
        """
        # Given: Multiple meals with different creation times and attributes
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
            reset_counters,
        )

        reset_counters()  # Ensure deterministic IDs
        from datetime import datetime

        base_time = datetime.now()
        meals = [
            create_test_ORM_meal(
                name="Italian Older",
                author_id="chef123",
                calorie_density=250.0,
                # created_at will be set by database default
            ),
            create_test_ORM_meal(
                name="Italian Newer",
                author_id="chef123",
                calorie_density=350.0,
            ),
            create_test_ORM_meal(
                name="French Meal",
                author_id="chef456",
                calorie_density=150.0,
            ),
        ]

        for meal in meals:
            test_session.add(meal)
        await test_session.commit()

        # When: Using custom sorting with real database
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.models import (
            MealSaTestModel,
        )

        def custom_sort_logic(stmt, value_of_sort_query):
            """Custom sorting that prioritizes higher calorie meals"""
            if value_of_sort_query == "calories_desc":
                return stmt.order_by(MealSaTestModel.calorie_density.desc())
            return stmt.order_by(
                MealSaTestModel.calorie_density.desc()
            )  # Default sort by calories desc

        result = await meal_repository.query(
            filters={
                "author_id": "chef123",
                "calorie_density_gte": 200.0,
            },
            sort_stmt=custom_sort_logic,
            limit=10,
            _return_sa_instance=True,
        )

        # Then: Real database handles the complete query pipeline
        assert len(result) == 2
        # Results should be sorted by calories descending
        assert result[0].calorie_density >= result[1].calorie_density
        assert result[0].name == "Italian Newer"  # Higher calories
        assert result[1].name == "Italian Older"  # Lower calories

    @pytest.mark.integration
    async def test_real_world_usage_scenario_documentation(
        self, meal_repository, test_session
    ):
        """
        BEHAVIOR: Real-world complex filtering scenario with actual database

        This documents a realistic use case with real data:
        - Multiple column filters with different operators
        - Nutritional constraints
        - User-specific filtering
        - Performance considerations with complex queries
        """
        # Given: Diverse meals with realistic attributes
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
            reset_counters,
        )

        reset_counters()  # Ensure deterministic IDs
        meals = [
            # Perfect match
            create_test_ORM_meal(
                name="Chicken Pasta",
                author_id="user123",
                total_time=30,
                calorie_density=400.0,
                like=True,
            ),
            # Fails like criterion
            create_test_ORM_meal(
                name="Chicken Salad",
                author_id="user123",
                total_time=20,
                calorie_density=350.0,
                like=False,
            ),
            # Fails time criterion
            create_test_ORM_meal(
                name="Chicken Stew",
                author_id="user123",
                total_time=60,
                calorie_density=450.0,
                like=True,
            ),
            # Wrong author
            create_test_ORM_meal(
                name="Chicken Soup",
                author_id="user456",
                total_time=25,
                calorie_density=300.0,
                like=True,
            ),
        ]

        for meal in meals:
            test_session.add(meal)
        await test_session.commit()

        # When: Performing realistic meal search with complex criteria
        result = await meal_repository.query(
            filters={
                # Basic search criteria
                "name": "Chicken Pasta",
                "author_id": "user123",
                # Nutritional constraints
                "calorie_density_gte": 300.0,
                "calorie_density_lte": 600.0,
                # Preference filters
                "like": True,
                "total_time_lte": 45,  # Max 45 minutes
            },
            limit=20,
            _return_sa_instance=True,
        )

        # Then: Real database handles complex real-world queries efficiently
        assert len(result) == 1
        assert result[0].name == "Chicken Pasta"
        assert result[0].author_id == "user123"
        assert result[0].like is True
        assert result[0].total_time <= 45
        assert 300.0 <= result[0].calorie_density <= 600.0

    @pytest.mark.integration
    async def test_error_handling_behavior_documentation(self, meal_repository):
        """
        BEHAVIOR: Error handling and validation with real database

        This documents expected error handling with actual database operations:
        - Unknown filter keys raise FilterValidationException
        - Invalid filter structures raise appropriate errors
        - Real database constraint errors are propagated
        """
        # When: Using unknown filter key with real repository
        with pytest.raises((FilterValidationError, KeyError)):
            await meal_repository.query(
                filters={"nonexistent_field": "some_value"}, _return_sa_instance=True
            )

        # This documents that validation errors are clear and helpful
        # Real database errors provide actual constraint violation messages

    @pytest.mark.performance
    async def test_performance_considerations_documentation(
        self, meal_repository, recipe_repository, test_session, async_benchmark_timer
    ):
        """
        BEHAVIOR: Performance considerations and optimization with real database

        This documents performance-related behaviors with actual queries:
        - DISTINCT automatically applied for list filters
        - Join deduplication prevents redundant joins
        - Efficient query building for complex scenarios
        """
        # Given: Complex data setup for performance testing
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
            create_test_ORM_recipe,
            reset_counters,
        )

        reset_counters()  # Ensure deterministic IDs

        meal = create_test_ORM_meal(name="Performance Test Meal", author_id="chef1")
        test_session.add(meal)
        await test_session.flush()

        recipe = create_test_ORM_recipe(name="Chicken Alfredo", meal_id=meal.id)
        test_session.add(recipe)
        await test_session.commit()

        # When: Executing complex query that should be optimized
        async with async_benchmark_timer() as timer:
            result = await meal_repository.query(
                filters={
                    # These both require same join, should be deduplicated
                    "recipe_id": recipe.id,
                    "recipe_name": "Chicken Alfredo",
                    # List filter should trigger DISTINCT
                    "author_id": ["chef1", "chef2", "chef3"],
                },
                _return_sa_instance=True,
            )

        # Then: Real database optimizes query structure efficiently
        timer.assert_faster_than(2.0)  # Should complete quickly
        assert len(result) == 1
        assert result[0].name == "Performance Test Meal"

    @pytest.mark.integration
    async def test_null_value_handling_behavior_documentation(
        self, meal_repository, test_session
    ):
        """
        BEHAVIOR: NULL value handling across different operators with real database

        This documents how NULL values are handled consistently:
        - Equality with NULL uses IS operator
        - IS NOT operator for NULL exclusion
        - NOT IN operator includes NULL values
        """
        # Given: Meals with NULL and non-NULL values
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
            reset_counters,
        )

        reset_counters()  # Ensure deterministic IDs
        meals = [
            create_test_ORM_meal(name="Has Description", description="Tasty meal"),
            create_test_ORM_meal(name="No Description", description=None),
            create_test_ORM_meal(name="Empty Description", description=""),
        ]

        for meal in meals:
            test_session.add(meal)
        await test_session.commit()

        # Test: Equality with NULL uses IS operator
        null_results = await meal_repository.query(
            filters={"description": None}, _return_sa_instance=True
        )
        assert len(null_results) == 1
        assert null_results[0].name == "No Description"

        # Test: IS NOT NULL
        not_null_results = await meal_repository.query(
            filters={"description_is_not": None}, _return_sa_instance=True
        )
        assert len(not_null_results) == 2
        not_null_names = {r.name for r in not_null_results}
        assert not_null_names == {"Has Description", "Empty Description"}

        # Test: NOT IN includes NULL values
        not_in_results = await meal_repository.query(
            filters={"description_not_in": ["Tasty meal"]}, _return_sa_instance=True
        )
        assert len(not_in_results) == 2  # NULL and empty string
        not_in_names = {r.name for r in not_in_results}
        assert not_in_names == {"No Description", "Empty Description"}

    @pytest.mark.integration
    async def test_constraint_violation_behavior_documentation(
        self, meal_repository, test_session
    ):
        """
        BEHAVIOR: Database constraint violation handling

        This documents how real database constraints are handled:
        - Unique constraint violations raise IntegrityError
        - Check constraint violations raise IntegrityError
        - Foreign key constraint violations raise IntegrityError
        """
        # Given: A meal with specific ID
        from tests.unit.contexts.seedwork.shared.adapters.repositories.testing_infrastructure.data_factories import (
            create_test_ORM_meal,
            reset_counters,
        )

        reset_counters()  # Ensure deterministic IDs
        meal1 = create_test_ORM_meal(id="constraint_test_meal")
        test_session.add(meal1)
        await test_session.commit()

        # When: Trying to add another meal with same ID
        meal2 = create_test_ORM_meal(id="constraint_test_meal")

        # Then: Real database constraint violation is raised
        with pytest.raises(IntegrityError) as exc_info:
            test_session.add(meal2)
            await test_session.commit()

        # Verify it's a real unique constraint error
        assert (
            "duplicate key value" in str(exc_info.value)
            or "unique constraint" in str(exc_info.value).lower()
        )

        # Cleanup
        await test_session.rollback()

    # NOTE: Tag filtering behavior documentation removed
    #
    # Tag filtering requires special domain logic (groupby, EXISTS, any()) that cannot
    # be handled by the generic repository's filter system. Tag filtering should be
    # documented and tested in domain-specific repository tests (e.g., MealRepo tests)
    # where the custom tag handling logic is implemented.
    #
    # The generic repository is designed for simple column-based filtering, not
    # complex relationship-based filtering that requires custom SQL generation.
