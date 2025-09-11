"""
Characterisation tests for Meal aggregate root.

These tests document current behavior before refactoring, including:
- Heavy computed properties (nutri_facts, macro_division)
- Current @lru_cache behavior and shared cache bugs
- Cache invalidation patterns
- Mutation flows and update_properties behavior

Tests marked with xfail document known bugs to be fixed during refactoring.
"""

import pytest
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from tests.contexts.recipes_catalog.data_factories.meal.meal_domain_factories import (
    create_meal,
)
from tests.contexts.recipes_catalog.data_factories.meal.recipe.recipe_domain_factories import (
    create_recipe,
)


class TestMealCharacterisation:
    """Characterisation tests documenting current Meal behavior."""

    def test_meal_creation_basic(self):
        """Document basic meal creation."""
        meal = create_meal(name="Test Meal", recipes=[])
        assert meal.name == "Test Meal"
        assert meal.recipes == []
        assert meal.nutri_facts is None  # No recipes = no nutrition

    def test_meal_with_recipes_nutri_facts_aggregation(self):
        """Document current nutri_facts aggregation behavior."""
        recipes = []
        for i in range(3):
            nutri_facts = NutriFacts(
                calories=100.0 * (i + 1),
                protein=10.0 * (i + 1),
                carbohydrate=20.0 * (i + 1),
                total_fat=5.0 * (i + 1),
                saturated_fat=2.0,
                trans_fat=0.0,
                dietary_fiber=3.0,
                sodium=200.0,
                sugar=5.0,
            )
            recipe = create_recipe(nutri_facts=nutri_facts)
            recipes.append(recipe)

        meal = create_meal(recipes=recipes)
        result = meal.nutri_facts

        # Document expected aggregation: sum of all recipe nutrition
        assert result is not None
        assert result.calories.value == 600.0  # 100 + 200 + 300
        assert result.protein.value == 60.0  # 10 + 20 + 30
        assert result.carbohydrate.value == 120.0  # 20 + 40 + 60

    def test_meal_macro_division_computation(self):
        """Document current macro_division computation."""
        nutri_facts = NutriFacts(
            calories=400.0,
            carbohydrate=40.0,  # Should be 40% of macros
            protein=30.0,  # Should be 30% of macros
            total_fat=30.0,  # Should be 30% of macros
            saturated_fat=10.0,
            trans_fat=0.0,
            dietary_fiber=5.0,
            sodium=500.0,
            sugar=8.0,
        )
        recipe = create_recipe(nutri_facts=nutri_facts)
        meal = create_meal(recipes=[recipe])

        result = meal.macro_division
        assert result is not None
        assert abs(result.carbohydrate - 40.0) < 0.01
        assert abs(result.protein - 30.0) < 0.01
        assert abs(result.fat - 30.0) < 0.01

    def test_meal_weight_calculation(self):
        """Document current weight_in_grams calculation."""
        recipes = []
        for i in range(2):
            recipe = create_recipe(weight_in_grams=100 * (i + 1))
            recipes.append(recipe)

        meal = create_meal(recipes=recipes)
        assert meal.weight_in_grams == 300  # 100 + 200

    @pytest.mark.xfail(reason="Shared @lru_cache bug - different meals may share cache")
    def test_meal_cache_isolation_bug(self):
        """Document known shared cache bug between different meal instances."""
        # Create two meals with different recipes
        recipe1 = create_recipe(
            nutri_facts=NutriFacts(
                calories=100.0,
                protein=10.0,
                carbohydrate=20.0,
                total_fat=5.0,
                saturated_fat=2.0,
                trans_fat=0.0,
                dietary_fiber=3.0,
                sodium=200.0,
                sugar=5.0,
            )
        )
        recipe2 = create_recipe(
            nutri_facts=NutriFacts(
                calories=200.0,
                protein=20.0,
                carbohydrate=40.0,
                total_fat=10.0,
                saturated_fat=4.0,
                trans_fat=0.0,
                dietary_fiber=6.0,
                sodium=400.0,
                sugar=10.0,
            )
        )

        meal1 = create_meal(recipes=[recipe1])
        meal2 = create_meal(recipes=[recipe2])

        # Access properties to populate cache
        nutri1_first = meal1.nutri_facts
        nutri2 = meal2.nutri_facts
        nutri1_second = meal1.nutri_facts

        # With proper instance-level caching, these should be different
        # With shared @lru_cache, they might be incorrectly shared
        assert nutri1_first is not None and nutri1_first.calories.value == 100.0
        assert nutri2 is not None and nutri2.calories.value == 200.0
        assert (
            nutri1_second is not None and nutri1_second.calories.value == 100.0
        )  # This may fail due to shared cache

    def test_meal_update_properties_behavior(self):
        """Document current update_properties behavior."""
        meal = create_meal(name="Original Name", description="Original Description")

        # Document current behavior
        original_version = meal.version
        meal.update_properties(name="New Name", description="New Description")

        assert meal.name == "New Name"
        assert meal.description == "New Description"
        assert meal.version == original_version + 1

    def test_meal_recipe_mutation_through_meal(self):
        """Document current recipe mutation through meal interface."""
        recipe = create_recipe(name="Original Recipe")
        meal = create_meal(recipes=[recipe])

        # Document current mutation patterns
        meal_recipe = meal.recipes[0]
        original_version = meal.version

        # This should work through meal interface
        meal.update_recipes({meal_recipe.id: {"name": "Updated Recipe"}})

        assert meal.recipes[0].name == "Updated Recipe"
        assert meal.version == original_version + 1


class TestMealCacheInvalidation:
    """Document current cache invalidation behavior."""

    def test_cache_invalidation_on_recipes_change(self):
        """Document how cache behaves when recipes are changed."""
        recipe1 = create_recipe(
            nutri_facts=NutriFacts(
                calories=100.0,
                protein=10.0,
                carbohydrate=20.0,
                total_fat=5.0,
                saturated_fat=2.0,
                trans_fat=0.0,
                dietary_fiber=3.0,
                sodium=200.0,
                sugar=5.0,
            )
        )
        meal = create_meal(recipes=[recipe1])

        # Get initial cached value
        initial_nutri = meal.nutri_facts
        assert initial_nutri is not None and initial_nutri.calories.value == 100.0

        # Change recipes using update_properties (new protected setter pattern)
        # Create recipe with correct meal_id to pass aggregate validation
        recipe2 = create_recipe(
            meal_id=meal.id,  # Use correct meal_id
            author_id=meal.author_id,  # Use correct author_id
            nutri_facts=NutriFacts(
                calories=300.0,
                protein=30.0,
                carbohydrate=60.0,
                total_fat=15.0,
                saturated_fat=6.0,
                trans_fat=0.0,
                dietary_fiber=9.0,
                sodium=600.0,
                sugar=15.0,
            ),
        )
        meal.update_properties(recipes=[recipe2])

        # Check if cache was invalidated
        updated_nutri = meal.nutri_facts
        # With proper cache invalidation, this should be different
        assert updated_nutri is not None and updated_nutri.calories.value == 300.0
