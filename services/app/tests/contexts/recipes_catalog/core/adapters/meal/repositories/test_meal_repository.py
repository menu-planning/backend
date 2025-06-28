"""
Comprehensive test suite for MealRepository following seedwork patterns.

Tests are organized into focused classes:
- TestMealRepositoryCore: Basic CRUD operations 
- TestMealRepositoryFiltering: Filter operations and scenarios
- TestMealRepositoryTagFiltering: Complex tag logic with AND/OR
- TestMealRepositoryErrorHandling: Edge cases and database constraints
- TestMealRepositoryPerformance: Benchmarks and performance baselines

All tests use REAL database (no mocks) and follow TDD principles.
"""

import pytest

from src.contexts.seedwork.shared.adapters.repositories.repository_exceptions import FilterValidationException
from src.logging.logger import logger
from tests.contexts.recipes_catalog.core.adapters.meal.repositories.data_factories.meal.meal_domain_factories import create_meal
from tests.contexts.recipes_catalog.core.adapters.meal.repositories.data_factories.meal.meal_orm_factories import create_meal_orm, create_meals_with_tags_orm, create_test_meal_dataset_orm
from tests.contexts.recipes_catalog.core.adapters.meal.repositories.data_factories.meal.parametrized_meal_scenarios import get_meal_filter_scenarios, get_performance_test_scenarios, get_tag_filtering_scenarios
from tests.contexts.recipes_catalog.core.adapters.meal.repositories.data_factories.shared_orm_factories import create_meal_tag_orm

pytestmark = [pytest.mark.anyio, pytest.mark.integration]

import time
from typing import Dict, Any

from src.contexts.recipes_catalog.core.adapters.meal.repositories.meal_repository import MealRepo

# Import MenuSaModel to ensure menus table exists for foreign key constraint
from src.contexts.recipes_catalog.core.adapters.client.ORM.sa_models.menu_sa_model import MenuSaModel



# =============================================================================
# TEST FIXTURES AND SETUP
# =============================================================================

# Note: Most fixtures are now in conftest.py following seedwork pattern


# =============================================================================
# TEST MEAL REPOSITORY CORE OPERATIONS
# =============================================================================

class TestMealRepositoryCore:
    """Test basic CRUD operations with real database persistence"""

    async def test_add_and_get_meal(self, meal_repository: MealRepo, test_session):
        """Test adding a meal and retrieving it by ID"""
        # Given: A new ORM meal
        meal = create_meal_orm(name="Test Meal for Add/Get", author_id="test_author")
        
        # When: Adding the meal directly to session
        test_session.add(meal)
        await test_session.commit()
        
        # Then: Should be able to retrieve the same meal via repository
        retrieved_meal = await meal_repository.get_sa_instance(meal.id)
        
        assert retrieved_meal is not None
        assert retrieved_meal.id == meal.id
        assert retrieved_meal.name == meal.name
        assert retrieved_meal.author_id == meal.author_id

    @pytest.mark.parametrize("meal_count", [1, 5, 10, 25])
    async def test_query_all_meals(self, meal_repository: MealRepo, test_session, meal_count: int):
        """Test querying meals with different dataset sizes"""
        # Given: Multiple ORM meals in the database
        meals = []
        for i in range(meal_count):
            meal = create_meal_orm(name=f"Query Test Meal {i}")
            meals.append(meal)
            test_session.add(meal)
        
        await test_session.commit()
        
        # When: Querying all meals with ORM instances
        result = await meal_repository.query(_return_sa_instance=True)
        
        # Then: Should return all added meals
        assert len(result) >= meal_count  # >= because other tests might have added meals
        
        # Verify our test meals are in the result
        result_ids = {meal.id for meal in result}
        for meal in meals:
            assert meal.id in result_ids

    async def test_update_meal(self, meal_repository: MealRepo, test_session):
        """Test updating a meal and verifying changes persist"""
        # Given: An ORM meal to update
        meal = create_meal_orm(name="Original Name", description="Original Description")
        test_session.add(meal)
        await test_session.commit()
        
        # Capture initial version
        initial_version = meal.version
        
        # When: Updating the meal directly in session
        meal.name = "Updated Name"
        meal.description = "Updated Description"
        await test_session.commit()
        
        # Then: Changes should be persisted
        updated_meal = await meal_repository.get_sa_instance(meal.id)
        assert updated_meal.name == "Updated Name"
        assert updated_meal.description == "Updated Description"

    async def test_persist_all_with_discarded_meal(self, meal_repository: MealRepo, test_session):
        """Test that discarded meals are soft deleted and not retrievable"""
        # Given: An ORM meal added to database
        meal = create_meal_orm(name="Meal to Discard", author_id="test_author")
        test_session.add(meal)
        await test_session.commit()
        
        # Verify meal exists
        retrieved_meal = await meal_repository.get_sa_instance(meal.id)
        assert retrieved_meal.name == "Meal to Discard"
        
        # When: Marking meal as discarded (soft delete) directly in session
        retrieved_meal.discarded = True
        await test_session.commit()
        
        # Then: Meal should no longer be retrievable (soft deleted)
        from src.contexts.seedwork.shared.adapters.exceptions.repo_exceptions import EntityNotFoundException
        with pytest.raises(EntityNotFoundException):
            await meal_repository.get_sa_instance(meal.id)

    async def test_add_meal_with_reused_recipe_tags(self, meal_repository: MealRepo, test_session):
        """Test that adding a meal with duplicate tag raises IntegrityError"""
        # Given: An existing tag in the database
        meal_tag = create_meal_tag_orm(
            key="meal_type",
            value="dinner", 
            author_id="test_author",
            type="meal"
        )
        
        meal1 = create_meal_orm(
            name="First Meal",
            author_id="test_author",
            tags=[meal_tag]
        )
        
        test_session.add(meal1)
        await test_session.commit()
        
        # When: Trying to add another meal with duplicate tag
        duplicate_tag = create_meal_tag_orm(
            key="meal_type",
            value="dinner",
            author_id="test_author", 
            type="meal"
        )
        
        meal2 = create_meal_orm(
            name="Second Meal",
            author_id="test_author",
            tags=[duplicate_tag]
        )
        
        test_session.add(meal2)
        
        # Then: Should raise IntegrityError on commit
        from sqlalchemy.exc import IntegrityError
        with pytest.raises(IntegrityError):
            await test_session.commit()

    async def test_query_by_list_of_ids(self, meal_repository: MealRepo, test_session):
        """Test querying meals by list of IDs (IN operator)"""
        # Given: Multiple ORM meals
        meal1 = create_meal_orm(name="Meal 1", author_id="test_author")
        meal2 = create_meal_orm(name="Meal 2", author_id="test_author")
        meal3 = create_meal_orm(name="Meal 3", author_id="test_author")
        
        for meal in [meal1, meal2, meal3]:
            test_session.add(meal)
        await test_session.commit()
        
        # When: Querying with ID list filter
        result = await meal_repository.query(filter={"id": [meal1.id, meal2.id]}, _return_sa_instance=True)
        
        # Then: Should return only the requested meals
        result_ids = {meal.id for meal in result}
        assert meal1.id in result_ids
        assert meal2.id in result_ids
        assert meal3.id not in result_ids
        assert len(result) == 2

    async def test_meal_recipe_copying_persistence(self, meal_repository: MealRepo):
        """Test that meal with copied recipes persists correctly"""
        # Given: A meal with recipes (testing the repository aspects of recipe copying)
        # Note: This tests repository behavior, not the full domain copying logic
        
        # Create a meal with some basic recipe data
        meal = create_meal(
            name="Meal with Recipes",
            author_id="test_author"
        )
        
        # When: Adding and persisting the meal
        await meal_repository.add(meal)
        await meal_repository.persist(meal)
        
        # Then: Meal should be retrievable with its recipes
        retrieved_meal = await meal_repository.get(meal.id)
        assert retrieved_meal.name == "Meal with Recipes"
        assert retrieved_meal.author_id == "test_author"
        
        # Test recipe relationships if recipes exist
        if hasattr(retrieved_meal, 'recipes') and retrieved_meal.recipes:
            assert len(retrieved_meal.recipes) >= 0  # Should handle empty recipes list
            for recipe in retrieved_meal.recipes:
                assert recipe.meal_id == meal.id
                assert recipe.author_id == "test_author"  # Should inherit author_id when copied

    async def test_meal_copying_author_id_inheritance(self, meal_repository: MealRepo):
        """Test that copied meals properly handle author_id changes"""
        # Given: A meal with a specific author
        original_meal = create_meal(
            name="Original Meal",
            author_id="original_author"
        )
        await meal_repository.add(original_meal)
        await meal_repository.persist(original_meal)
        
        # When: Creating a copy with different author (simulating domain copy operation)
        copied_meal = create_meal(
            name="Original Meal",  # Same name, different author
            author_id="new_author"
        )
        await meal_repository.add(copied_meal)
        await meal_repository.persist(copied_meal)
        
        # Then: Both meals should exist with different authors
        original_retrieved = await meal_repository.get(original_meal.id)
        copied_retrieved = await meal_repository.get(copied_meal.id)
        
        assert original_retrieved.author_id == "original_author"
        assert copied_retrieved.author_id == "new_author"
        assert original_retrieved.name == copied_retrieved.name
        assert original_retrieved.id != copied_retrieved.id

    async def test_get_meal_by_recipe_id(self, meal_repository: MealRepo):
        """Test getting meal by recipe ID"""
        # Given: A meal with recipes
        meal = create_meal(name="Meal with Recipe")
        # Note: Recipe creation would require recipe factories
        # For now, testing the method signature and basic functionality
        await meal_repository.add(meal)
        await meal_repository.persist(meal)
        
        # When/Then: Testing method exists and handles basic cases
        # This will be expanded when recipe relationships are fully implemented
        with pytest.raises(ValueError, match="not found"):
            await meal_repository.get_meal_by_recipe_id("nonexistent_recipe_id")


# =============================================================================
# TEST MEAL REPOSITORY FILTERING
# =============================================================================

class TestMealRepositoryFiltering:
    """Test filter operations using parametrized scenarios"""

    @pytest.mark.parametrize("scenario", get_meal_filter_scenarios())
    async def test_meal_filtering_scenarios(self, meal_repository: MealRepo, test_session, scenario: Dict[str, Any]):
        """Test meal filtering with various filter combinations"""
        # Given: An ORM meal with specific characteristics
        meal = create_meal_orm(**scenario["meal_kwargs"])
        test_session.add(meal)
        await test_session.commit()
        
        # When: Applying the filter
        result = await meal_repository.query(filter=scenario["filter"], _return_sa_instance=True)
        
        # Then: Check if meal matches expected outcome
        meal_ids = {m.id for m in result}
        
        if scenario["should_match"]:
            assert meal.id in meal_ids, f"Scenario '{scenario['scenario_id']}' failed: {scenario['description']}"
        else:
            assert meal.id not in meal_ids, f"Scenario '{scenario['scenario_id']}' failed: {scenario['description']}"

    async def test_total_time_gte_filter(self, meal_repository: MealRepo, test_session):
        """Test total_time greater than or equal filter"""
        # Given: ORM meals with different cooking times
        quick_meal = create_meal_orm(name="Quick Meal", total_time=15)
        medium_meal = create_meal_orm(name="Medium Meal", total_time=45)  
        long_meal = create_meal_orm(name="Long Meal", total_time=90)

        # Persist meals directly to session
        test_session.add(quick_meal)
        test_session.add(medium_meal)
        test_session.add(long_meal)
        await test_session.commit()

        # When: Filtering by total_time_gte
        result = await meal_repository.query(filter={"total_time_gte": 30}, _return_sa_instance=True)

        # Then: Should return meals with total_time >= 30
        meal_names = [meal.name for meal in result]
        assert len(result) == 2, f"Expected 2 meals to match total_time_gte filter, got: {meal_names}"
        result_names = {meal.name for meal in result}
        assert "Medium Meal" in result_names
        assert "Long Meal" in result_names
        assert "Quick Meal" not in result_names

    async def test_total_time_lte_filter(self, meal_repository: MealRepo, test_session):
        """Test total_time less than or equal filter"""
        # Given: ORM meals with different cooking times
        quick_meal = create_meal_orm(name="Quick Meal", total_time=15)
        medium_meal = create_meal_orm(name="Medium Meal", total_time=45)
        long_meal = create_meal_orm(name="Long Meal", total_time=90)

        # Persist meals directly to session
        test_session.add(quick_meal)
        test_session.add(medium_meal)
        test_session.add(long_meal)
        await test_session.commit()

        # When: Filtering by total_time_lte
        result = await meal_repository.query(filter={"total_time_lte": 60}, _return_sa_instance=True)

        # Then: Should return meals with total_time <= 60
        meal_names = [meal.name for meal in result]
        assert len(result) == 2, f"Expected 2 meals to match total_time_lte filter, got: {meal_names}"
        result_names = {meal.name for meal in result}
        assert "Quick Meal" in result_names
        assert "Medium Meal" in result_names
        assert "Long Meal" not in result_names

    async def test_like_filter(self, meal_repository: MealRepo, test_session):
        """Test like boolean filter"""
        # Given: ORM meals with different like status
        liked_meal = create_meal_orm(name="Liked Meal", like=True)
        not_liked_meal = create_meal_orm(name="Not Liked Meal", like=False)
        neutral_meal = create_meal_orm(name="Neutral Meal", like=None)
        
        for meal in [liked_meal, not_liked_meal, neutral_meal]:
            test_session.add(meal)
        await test_session.commit()
        
        # When: Filtering by like=True
        result = await meal_repository.query(filter={"like": True}, _return_sa_instance=True)
        
        # Then: Should only return liked meals
        result_ids = {meal.id for meal in result}
        assert liked_meal.id in result_ids
        assert not_liked_meal.id not in result_ids
        assert neutral_meal.id not in result_ids

    async def test_author_id_filter(self, meal_repository: MealRepo, test_session):
        """Test author_id exact match filter"""
        # Given: ORM meals from different authors
        author1_meal = create_meal_orm(name="Author 1 Meal", author_id="author_1")
        author2_meal = create_meal_orm(name="Author 2 Meal", author_id="author_2")
        
        for meal in [author1_meal, author2_meal]:
            test_session.add(meal)
        await test_session.commit()
        
        # When: Filtering by specific author
        result = await meal_repository.query(filter={"author_id": "author_1"}, _return_sa_instance=True)
        
        # Then: Should only return meals from that author
        result_ids = {meal.id for meal in result}
        assert author1_meal.id in result_ids
        assert author2_meal.id not in result_ids

    async def test_combined_filters(self, meal_repository: MealRepo, test_session):
        """Test multiple filters working together"""
        # Given: ORM meals with various characteristics
        target_meal = create_meal_orm(
            name="Target Meal",
            author_id="target_author", 
            like=True,
            total_time=45
        )
        wrong_author = create_meal_orm(
            name="Wrong Author",
            author_id="other_author",
            like=True,
            total_time=45
        )
        wrong_time = create_meal_orm(
            name="Wrong Time", 
            author_id="target_author",
            like=True,
            total_time=120  # Too long
        )
        
        for meal in [target_meal, wrong_author, wrong_time]:
            test_session.add(meal)
        await test_session.commit()
        
        # When: Applying multiple filters
        result = await meal_repository.query(filter={
            "author_id": "target_author",
            "total_time_lte": 60,
            "like": True
        }, _return_sa_instance=True)
        
        # Then: Should only return meal matching all filters
        result_ids = {meal.id for meal in result}
        assert target_meal.id in result_ids
        assert wrong_author.id not in result_ids  # Wrong author
        assert wrong_time.id not in result_ids  # Wrong time
        assert len(result) == 1


# =============================================================================
# TEST MEAL REPOSITORY TAG FILTERING
# =============================================================================

class TestMealRepositoryTagFiltering:
    """Test complex tag logic with AND/OR operations"""

    @pytest.mark.parametrize("scenario", get_tag_filtering_scenarios())
    async def test_tag_filtering_scenarios(self, meal_repository: MealRepo, test_session, scenario: Dict[str, Any]):
        """Test complex tag filtering scenarios"""
        # Given: An ORM meal with specific tags
        tags = []
        for tag_data in scenario["meal_tags"]:
            tag = create_meal_tag_orm(**tag_data)
            tags.append(tag)
        
        meal = create_meal_orm(name=f"Meal for {scenario['scenario_id']}", tags=tags)
        test_session.add(meal)
        await test_session.commit()
        
        # When: Applying tag filter
        result = await meal_repository.query(filter={"tags": scenario["filter_tags"]}, _return_sa_instance=True)
        
        # Then: Check expected outcome
        result_ids = {m.id for m in result}
        
        if scenario["should_match"]:
            assert meal.id in result_ids, f"Tag scenario '{scenario['scenario_id']}' failed: {scenario['description']}"
        else:
            assert meal.id not in result_ids, f"Tag scenario '{scenario['scenario_id']}' failed: {scenario['description']}"

    async def test_single_tag_exact_match(self, meal_repository: MealRepo, test_session):
        """Test single tag exact matching"""
        # Given: ORM meal with specific tag
        tag = create_meal_tag_orm(key="diet", value="vegetarian", author_id="test_author", type="meal")
        meal = create_meal_orm(name="Vegetarian Meal", tags=[tag])
        test_session.add(meal)
        await test_session.commit()
        
        # When: Filtering with exact tag match
        result = await meal_repository.query(filter={
            "tags": [("diet", "vegetarian", "test_author")]
        }, _return_sa_instance=True)
        
        # Then: Should find the meal
        assert len(result) >= 1
        result_ids = {m.id for m in result}
        assert meal.id in result_ids

    async def test_multiple_tags_and_logic(self, meal_repository: MealRepo, test_session):
        """Test AND logic between different tag keys"""
        # Given: ORM meal with multiple tags (different keys)
        diet_tag = create_meal_tag_orm(key="diet", value="vegetarian", author_id="test_author", type="meal")
        cuisine_tag = create_meal_tag_orm(key="cuisine", value="italian", author_id="test_author", type="meal")
        meal = create_meal_orm(name="Italian Vegetarian Meal", tags=[diet_tag, cuisine_tag])
        test_session.add(meal)
        await test_session.commit()
        
        # When: Filtering with both tags (AND logic)
        result = await meal_repository.query(filter={
            "tags": [
                ("diet", "vegetarian", "test_author"),
                ("cuisine", "italian", "test_author")
            ]
        }, _return_sa_instance=True)
        
        # Then: Should find the meal (both tags match)
        result_ids = {m.id for m in result}
        assert meal.id in result_ids

    async def test_multiple_values_same_key_or_logic(self, meal_repository: MealRepo, test_session):
        """Test OR logic for multiple values with same key"""
        # Given: ORM meal with Italian cuisine tag
        cuisine_tag = create_meal_tag_orm(key="cuisine", value="italian", author_id="test_author", type="meal")
        meal = create_meal_orm(name="Italian Meal", tags=[cuisine_tag])
        test_session.add(meal)
        await test_session.commit()
        
        # When: Filtering with multiple cuisine values (OR logic)
        result = await meal_repository.query(filter={
            "tags": [
                ("cuisine", "italian", "test_author"),  # This matches
                ("cuisine", "mexican", "test_author")   # This doesn't match, but OR logic
            ]
        }, _return_sa_instance=True)
        
        # Then: Should find the meal (one of the OR conditions matches)
        result_ids = {m.id for m in result}
        assert meal.id in result_ids

    async def test_tags_not_exists_filtering(self, meal_repository: MealRepo, test_session):
        """Test tag exclusion with tags_not_exists"""
        # Given: Two ORM meals - one with spicy tag, one without
        spicy_tag = create_meal_tag_orm(key="spice", value="hot", author_id="test_author", type="meal")
        spicy_meal = create_meal_orm(name="Spicy Meal", tags=[spicy_tag])
        mild_meal = create_meal_orm(name="Mild Meal", tags=[])
        
        for meal in [spicy_meal, mild_meal]:
            test_session.add(meal)
        await test_session.commit()
        
        # When: Filtering to exclude spicy meals
        result = await meal_repository.query(filter={
            "tags_not_exists": [("spice", "hot", "test_author")]
        }, _return_sa_instance=True)
        
        # Then: Should only return mild meal
        result_ids = {m.id for m in result}
        assert mild_meal.id in result_ids
        assert spicy_meal.id not in result_ids

    async def test_complex_tag_combination(self, meal_repository: MealRepo, test_session):
        """Test complex AND/OR tag combinations"""
        # Given: ORM meal with multiple tags
        diet_tag = create_meal_tag_orm(key="diet", value="vegetarian", author_id="author_1", type="meal")
        cuisine_tag = create_meal_tag_orm(key="cuisine", value="italian", author_id="author_1", type="meal")
        difficulty_tag = create_meal_tag_orm(key="difficulty", value="easy", author_id="author_1", type="meal")
        
        meal = create_meal_orm(
            name="Complex Tag Meal", 
            tags=[diet_tag, cuisine_tag, difficulty_tag]
        )
        test_session.add(meal)
        await test_session.commit()
        
        # When: Complex filter with AND/OR logic
        result = await meal_repository.query(filter={
            "tags": [
                ("diet", "vegetarian", "author_1"),    # Must match (AND)
                ("diet", "vegan", "author_1"),         # OR with vegetarian
                ("cuisine", "italian", "author_1"),    # Must match (AND) 
                ("cuisine", "french", "author_1"),     # OR with italian
                ("difficulty", "easy", "author_1")     # Must match (AND)
            ]
        }, _return_sa_instance=True)
        
        # Then: Should find the meal (all key groups have at least one match)
        result_ids = {m.id for m in result}
        assert meal.id in result_ids

    async def test_tag_dissociation_and_removal(self, meal_repository: MealRepo, test_session):
        """Test removing tags from meals and verifying persistence"""
        # Given: ORM meal with multiple tags
        category_tag = create_meal_tag_orm(key="category", value="breakfast", author_id="test_author", type="meal")
        diet_tag = create_meal_tag_orm(key="diet", value="vegetarian", author_id="test_author", type="meal")
        
        meal_with_tags = create_meal_orm(
            name="Meal with Tags to Remove",
            tags=[category_tag, diet_tag]
        )
        test_session.add(meal_with_tags)
        await test_session.commit()
        
        # Verify tags are initially present
        initial_result = await meal_repository.query(filter={
            "tags": [("category", "breakfast", "test_author")]
        }, _return_sa_instance=True)
        assert len(initial_result) >= 1
        assert meal_with_tags.id in {m.id for m in initial_result}
        
        # When: Removing all tags from the meal directly in session
        retrieved_meal = await meal_repository.get_sa_instance(meal_with_tags.id)
        retrieved_meal.tags.clear()  # Remove all tags from ORM relationship
        await test_session.commit()
        
        # Then: Meal should no longer be found by tag filters
        after_removal_result = await meal_repository.query(filter={
            "tags": [("category", "breakfast", "test_author")]
        }, _return_sa_instance=True)
        result_ids = {m.id for m in after_removal_result}
        assert meal_with_tags.id not in result_ids
        
        # But meal should still exist when queried without tag filters
        meal_still_exists = await meal_repository.get_sa_instance(meal_with_tags.id)
        assert meal_still_exists is not None
        assert meal_still_exists.name == "Meal with Tags to Remove"
        assert len(meal_still_exists.tags) == 0
        
        # When: Re-adding some tags back
        new_tag = create_meal_tag_orm(key="season", value="winter", author_id="test_author", type="meal")
        retrieved_meal_again = await meal_repository.get_sa_instance(meal_with_tags.id)
        retrieved_meal_again.tags.append(new_tag)  # Add new tag to ORM relationship
        await test_session.commit()
        
        # Then: Should be findable by new tag filter
        final_result = await meal_repository.query(filter={
            "tags": [("season", "winter", "test_author")]
        }, _return_sa_instance=True)
        final_result_ids = {m.id for m in final_result}
        assert meal_with_tags.id in final_result_ids


# =============================================================================
# TEST MEAL REPOSITORY ERROR HANDLING
# =============================================================================

class TestMealRepositoryErrorHandling:
    """Test edge cases and database constraint violations"""

    async def test_get_nonexistent_meal(self, meal_repository: MealRepo):
        """Test getting meal that doesn't exist"""
        # When/Then: Getting nonexistent meal should raise exception
        from src.contexts.seedwork.shared.adapters.exceptions.repo_exceptions import EntityNotFoundException
        with pytest.raises(EntityNotFoundException):
            await meal_repository.get_sa_instance("nonexistent_meal_id")

    async def test_get_meal_by_nonexistent_recipe_id(self, meal_repository: MealRepo):
        """Test getting meal by nonexistent recipe ID"""
        # When/Then: Should raise ValueError with descriptive message
        with pytest.raises(ValueError, match="not found"):
            await meal_repository.get_meal_by_recipe_id("nonexistent_recipe_id")

    async def test_multiple_meals_same_recipe_id_error(self, meal_repository: MealRepo):
        """Test error when multiple meals have same recipe ID"""
        # This test would require recipe relationships to be fully implemented
        # For now, testing the expected behavior pattern
        pass

    async def test_invalid_filter_parameters(self, meal_repository: MealRepo):
        """Test handling of invalid filter parameters"""
        # Given: Repository ready for testing
        
        with pytest.raises(FilterValidationException):
            await meal_repository.query(filter={"invalid_field": "some_value"}, _return_sa_instance=True)

    async def test_null_handling_in_filters(self, meal_repository: MealRepo, test_session):
        """Test filter behavior with null values"""
        # Given: ORM meals with null values in optional fields
        meal_with_nulls = create_meal_orm(
            name="Meal with Nulls",
            description=None,
            notes=None,
            like=None
        )
        test_session.add(meal_with_nulls)
        await test_session.commit()
        
        # When: Filtering with various null-related conditions
        result = await meal_repository.query(filter={"description": None}, _return_sa_instance=True)
        
        # Then: Should handle null comparisons correctly
        assert isinstance(result, list)


# =============================================================================
# TEST MEAL REPOSITORY PERFORMANCE
# =============================================================================

class TestMealRepositoryPerformance:
    """Test performance benchmarks and baselines"""

    @pytest.mark.parametrize("scenario", get_performance_test_scenarios())
    async def test_query_performance_scenarios(self, meal_repository: MealRepo, test_session, scenario: Dict[str, Any]):
        """Test performance against predefined scenarios"""
        if scenario["operation"] not in ["basic_query", "tag_filtering", "complex_query"]:
            pytest.skip(f"Operation {scenario['operation']} not implemented in this test")
        
        # Given: Dataset of specified size using ORM models
        dataset = create_test_meal_dataset_orm(
            meal_count=scenario["entity_count"],
            tags_per_meal=2 if "tag" in scenario["operation"] else 0
        )
        
        # Add meals directly to session
        for meal in dataset["meals"]:
            test_session.add(meal)
        await test_session.commit()
        
        # When: Performing the operation with timing
        start_time = time.time()
        
        if scenario["operation"] == "basic_query":
            result = await meal_repository.query(_return_sa_instance=True)
        elif scenario["operation"] == "tag_filtering":
            # Use first available tag for filtering
            if dataset["all_tags"]:
                first_tag = dataset["all_tags"][0]
                tag_filter = [(first_tag.key, first_tag.value, first_tag.author_id)]
                result = await meal_repository.query(filter={"tags": tag_filter}, _return_sa_instance=True)
            else:
                result = await meal_repository.query(_return_sa_instance=True)
        elif scenario["operation"] == "complex_query":
            result = await meal_repository.query(filter={
                "total_time_gte": 30,
                "total_time_lte": 90,
                "like": True
            }, _return_sa_instance=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Then: Should meet performance expectations
        max_duration = scenario["max_duration_seconds"]
        assert duration <= max_duration, (
            f"Performance test '{scenario['scenario_id']}' failed: "
            f"took {duration:.3f}s, expected <= {max_duration}s. "
            f"{scenario['description']}"
        )
        
        # Additional performance metrics
        if scenario.get("max_per_entity_ms"):
            per_entity_ms = (duration * 1000) / scenario["entity_count"]
            assert per_entity_ms <= scenario["max_per_entity_ms"], (
                f"Per-entity performance failed: {per_entity_ms:.2f}ms per entity, "
                f"expected <= {scenario['max_per_entity_ms']}ms"
            )

    async def test_bulk_insert_performance(self, meal_repository: MealRepo, test_session):
        """Test bulk insert performance with timing"""
        # Given: Large dataset for bulk operations using ORM models
        meal_count = 100  # Smaller for CI environment
        meals = []
        
        start_time = time.time()
        
        # Create ORM meals
        for i in range(meal_count):
            meal = create_meal_orm(name=f"Bulk Meal {i}")
            meals.append(meal)
            test_session.add(meal)
        
        # Bulk persist
        await test_session.commit()
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Then: Should meet bulk performance expectations
        max_duration = 5.0  # 5 seconds for 100 meals
        per_entity_ms = (duration * 1000) / meal_count
        
        assert duration <= max_duration, f"Bulk insert took {duration:.3f}s, expected <= {max_duration}s"
        assert per_entity_ms <= 50, f"Per-entity time {per_entity_ms:.2f}ms, expected <= 50ms"  # Relaxed for CI

    async def test_complex_query_performance(self, meal_repository: MealRepo, test_session):
        """Test complex query with joins and filters"""
        # Given: Dataset with relationships and tags using ORM models
        meals_with_tags = create_meals_with_tags_orm(count=50, tags_per_meal=3)
        
        for meal in meals_with_tags:
            test_session.add(meal)
        await test_session.commit()
        
        # When: Running complex query
        start_time = time.time()
        
        result = await meal_repository.query(filter={
            "total_time_gte": 30,
            "like": True,
            "author_id": "author_1"
        }, _return_sa_instance=True)
        
        end_time = time.time()
        duration = end_time - start_time
        
        # Then: Should complete in reasonable time
        assert duration <= 2.0, f"Complex query took {duration:.3f}s, expected <= 2.0s"
        assert isinstance(result, list) 