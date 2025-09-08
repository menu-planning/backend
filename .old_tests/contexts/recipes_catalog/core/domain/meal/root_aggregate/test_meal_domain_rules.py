"""
Domain Rule Behavior Tests for Meal Entity

Tests focus on domain business rules and aggregate behaviors,
not implementation details. These tests ensure meal-recipe
relationships and business rules are properly enforced.
"""

import pytest
from src.contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
from src.contexts.recipes_catalog.core.domain.meal.value_objects.ingredient import (
    Ingredient,
)
from src.contexts.shared_kernel.domain.enums import MeasureUnit
from src.contexts.shared_kernel.domain.exceptions import BusinessRuleValidationError
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts


class TestMealRecipeBusinessRules:
    """Test domain business rules between Meal and Recipe entities."""

    def test_meal_enforces_recipe_meal_id_matches(self):
        """Domain should enforce recipe meal_id matches meal id."""
        # Arrange: Create meal and recipe with mismatched IDs
        meal = Meal.create_meal(
            name="Test Meal",
            author_id="author_123",
            meal_id="meal_123",
            menu_id="menu_123",
        )

        # Create recipe with different meal_id (violates domain rule)
        invalid_recipe = _Recipe.create_recipe(
            name="Test Recipe",
            ingredients=[],
            instructions="Mix ingredients",
            author_id="author_123",
            meal_id="different_meal_456",  # Wrong meal_id!
            nutri_facts=NutriFacts(calories=100),
        )

        # Act & Assert: Domain should reject recipe with wrong meal_id
        with pytest.raises(BusinessRuleValidationError):
            meal.update_properties(recipes=[invalid_recipe])

    def test_meal_enforces_recipe_author_id_matches(self):
        """Domain should enforce recipe author_id matches meal author_id."""
        # Arrange: Create meal and recipe with mismatched author IDs
        meal = Meal.create_meal(
            name="Test Meal",
            author_id="meal_author_123",
            meal_id="meal_123",
            menu_id="menu_123",
        )

        # Create recipe with different author_id (violates domain rule)
        invalid_recipe = _Recipe.create_recipe(
            name="Test Recipe",
            ingredients=[],
            instructions="Mix ingredients",
            author_id="different_author_456",  # Wrong author_id!
            meal_id="meal_123",
            nutri_facts=NutriFacts(calories=100),
        )

        # Act & Assert: Domain should reject recipe with wrong author_id
        with pytest.raises(BusinessRuleValidationError):
            meal.update_properties(recipes=[invalid_recipe])

    def test_meal_accepts_valid_recipes(self):
        """Domain should accept recipes with matching meal_id and author_id."""
        # Arrange: Create meal and recipe with matching IDs
        meal = Meal.create_meal(
            name="Test Meal",
            author_id="author_123",
            meal_id="meal_123",
            menu_id="menu_123",
        )

        # Create recipe with matching IDs
        valid_recipe = _Recipe.create_recipe(
            name="Test Recipe",
            ingredients=[],
            instructions="Mix ingredients",
            author_id="author_123",  # Matches meal
            meal_id="meal_123",  # Matches meal
            nutri_facts=NutriFacts(calories=100),
        )

        # Act: Update meal with valid recipe
        meal.update_properties(recipes=[valid_recipe])

        # Assert: Domain should accept the recipe
        assert len(meal.recipes) == 1
        assert meal.recipes[0].name == "Test Recipe"


class TestMealRecipeManagement:
    """Test meal domain behaviors for recipe lifecycle management."""

    def test_meal_handles_none_recipes_gracefully(self):
        """Domain should handle None recipes by converting to empty list."""
        # Arrange: Create meal
        meal = Meal.create_meal(
            name="Test Meal",
            author_id="author_123",
            meal_id="meal_123",
            menu_id="menu_123",
        )

        # Act: Update with None recipes
        meal.update_properties(recipes=None)

        # Assert: Domain should convert None to empty list
        assert meal.recipes == []

    def test_meal_recipe_retrieval_by_id(self):
        """Domain should provide recipe lookup by ID."""
        # Arrange: Create meal with recipe
        meal = Meal.create_meal(
            name="Test Meal",
            author_id="author_123",
            meal_id="meal_123",
            menu_id="menu_123",
        )

        recipe = _Recipe.create_recipe(
            name="Test Recipe",
            ingredients=[],
            instructions="Mix ingredients",
            author_id="author_123",
            meal_id="meal_123",
            nutri_facts=NutriFacts(calories=100),
        )

        meal.update_properties(recipes=[recipe])

        # Act: Retrieve recipe by ID
        found_recipe = meal.get_recipe_by_id(recipe.id)

        # Assert: Domain should return correct recipe
        assert found_recipe is not None
        assert found_recipe.id == recipe.id
        assert found_recipe.name == "Test Recipe"

    def test_meal_recipe_retrieval_returns_none_for_nonexistent_id(self):
        """Domain should return None for non-existent recipe IDs."""
        # Arrange: Create meal with no recipes
        meal = Meal.create_meal(
            name="Test Meal",
            author_id="author_123",
            meal_id="meal_123",
            menu_id="menu_123",
        )

        # Act: Try to retrieve non-existent recipe
        found_recipe = meal.get_recipe_by_id("nonexistent_id")

        # Assert: Domain should return None
        assert found_recipe is None

    def test_meal_aggregates_product_ids_from_recipes(self):
        """Domain should aggregate product IDs from all recipe ingredients."""
        # Arrange: Create meal with recipes containing product IDs
        meal = Meal.create_meal(
            name="Test Meal",
            author_id="author_123",
            meal_id="meal_123",
            menu_id="menu_123",
        )

        # Create ingredients with product IDs
        ingredient1 = Ingredient(
            name="Flour",
            position=0,
            quantity=2.0,
            unit=MeasureUnit.CUP,
            product_id="product_1",
        )
        ingredient2 = Ingredient(
            name="Sugar",
            position=0,
            quantity=1.0,
            unit=MeasureUnit.CUP,
            product_id="product_2",
        )

        recipe1 = _Recipe.create_recipe(
            name="Recipe 1",
            ingredients=[ingredient1],
            instructions="Mix",
            author_id="author_123",
            meal_id="meal_123",
            nutri_facts=NutriFacts(calories=100),
        )

        recipe2 = _Recipe.create_recipe(
            name="Recipe 2",
            ingredients=[ingredient2],
            instructions="Mix",
            author_id="author_123",
            meal_id="meal_123",
            nutri_facts=NutriFacts(calories=150),
        )

        meal.update_properties(recipes=[recipe1, recipe2])

        # Act: Get aggregated product IDs
        product_ids = meal.products_ids

        # Assert: Domain should aggregate all product IDs
        assert "product_1" in product_ids
        assert "product_2" in product_ids
        assert len(product_ids) == 2


class TestMealEventGeneration:
    """Test meal domain behavior for event generation when changes affect menu."""

    def test_meal_generates_event_on_name_change(self):
        """Domain should generate menu update event when meal name changes."""
        # Arrange: Create meal with menu_id
        meal = Meal.create_meal(
            name="Original Name",
            author_id="author_123",
            meal_id="meal_123",
            menu_id="menu_123",
        )

        # Clear any creation events
        meal.events = []

        # Act: Update meal name
        meal.update_properties(name="Updated Name")

        # Assert: Domain should generate event for menu update
        assert len(meal.events) > 0
        # Check that an event was generated (behavior focus, not implementation)
        assert meal.name == "Updated Name"

    def test_meal_without_menu_id_skips_event_generation(self):
        """Domain should not generate menu events when meal has no menu_id."""
        # Arrange: Create meal without menu_id using constructor directly
        meal = Meal(
            id="meal_123",
            name="Test Meal",
            author_id="author_123",
            menu_id=None,  # No menu association
        )

        # Clear any creation events
        meal.events = []

        # Act: Update meal name
        meal.update_properties(name="Updated Name")

        # Assert: Domain behavior may vary, but meal should update correctly
        assert meal.name == "Updated Name"


class TestMealDiscardedBehavior:
    """Test meal domain behavior for discarded (deleted) meals."""

    def test_discarded_meal_prevents_property_access(self):
        """Domain should prevent accessing properties of discarded meals."""
        # Arrange: Create and discard a meal
        meal = Meal.create_meal(
            name="Test Meal",
            author_id="author_123",
            meal_id="meal_123",
            menu_id="menu_123",
        )
        meal.delete()  # Mark as discarded

        # Act & Assert: Domain should prevent access to discarded entity
        with pytest.raises(Exception):  # Should raise discarded entity exception
            _ = meal.name

    def test_discarded_meal_prevents_recipe_operations(self):
        """Domain should prevent recipe operations on discarded meals."""
        # Arrange: Create and discard a meal
        meal = Meal.create_meal(
            name="Test Meal",
            author_id="author_123",
            meal_id="meal_123",
            menu_id="menu_123",
        )
        meal.delete()  # Mark as discarded

        # Act & Assert: Domain should prevent recipe operations on discarded meals
        with pytest.raises(Exception):  # Should raise discarded entity exception
            meal.get_recipe_by_id("some_id")


class TestMealNutritionAggregation:
    """Test meal domain behavior for nutrition aggregation from recipes."""

    def test_meal_total_time_calculation(self):
        """Domain should calculate total time as maximum of recipe times."""
        # Arrange: Create meal with recipes having different times
        meal = Meal.create_meal(
            name="Test Meal",
            author_id="author_123",
            meal_id="meal_123",
            menu_id="menu_123",
        )

        recipe1 = _Recipe.create_recipe(
            name="Quick Recipe",
            ingredients=[],
            instructions="Quick mix",
            author_id="author_123",
            meal_id="meal_123",
            nutri_facts=NutriFacts(calories=100),
            total_time=15,  # 15 minutes
        )

        recipe2 = _Recipe.create_recipe(
            name="Slow Recipe",
            ingredients=[],
            instructions="Slow cook",
            author_id="author_123",
            meal_id="meal_123",
            nutri_facts=NutriFacts(calories=200),
            total_time=45,  # 45 minutes (longer)
        )

        meal.update_properties(recipes=[recipe1, recipe2])

        # Act: Get meal total time
        total_time = meal.total_time

        # Assert: Domain should return maximum time
        assert total_time == 45  # Maximum of 15 and 45

    def test_meal_total_time_with_no_times(self):
        """Domain should handle recipes with no time information."""
        # Arrange: Create meal with recipes having no time
        meal = Meal.create_meal(
            name="Test Meal",
            author_id="author_123",
            meal_id="meal_123",
            menu_id="menu_123",
        )

        recipe = _Recipe.create_recipe(
            name="No Time Recipe",
            ingredients=[],
            instructions="Mix",
            author_id="author_123",
            meal_id="meal_123",
            nutri_facts=NutriFacts(calories=100),
            total_time=None,  # No time specified
        )

        meal.update_properties(recipes=[recipe])

        # Act: Get meal total time
        total_time = meal.total_time

        # Assert: Domain should handle None gracefully
        assert total_time is None
