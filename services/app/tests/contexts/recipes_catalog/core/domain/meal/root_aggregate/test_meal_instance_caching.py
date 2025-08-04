"""
Tests for instance-level caching behavior in Meal root aggregate.

These tests verify the correct per-instance caching behavior using @cached_property.
The conversion from @lru_cache to @cached_property has been completed, ensuring
proper instance-level cache isolation and invalidation.

All tests should PASS as they verify the working instance-level caching implementation.
"""

import pytest
from unittest.mock import patch

from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal

from src.contexts.recipes_catalog.core.domain.meal.value_objects.ingredient import Ingredient
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts

from src.contexts.shared_kernel.domain.enums import MeasureUnit


class TestMealInstanceLevelCaching:
    """Test per-instance caching for Meal computed properties."""

    @pytest.fixture
    def sample_ingredient(self):
        """Basic ingredient for testing."""
        return Ingredient(
            name="Test Ingredient",
            product_id="prod-1",
            quantity=100.0,
            unit=MeasureUnit.GRAM,
            position=0
        )

    @pytest.fixture
    def meal_with_nutri_recipes(self, sample_ingredient):
        """Meal with recipes that have nutritional facts."""
        # Create meal
        meal = Meal.create_meal(
            author_id="user-1",
            name="Test Meal with Nutrition",
            meal_id="meal-1",
            menu_id="menu-1"
        )

        # Recipe 1: High carb
        meal.create_recipe(
            name="High Carb Recipe",
            ingredients=[sample_ingredient],
            instructions="Cook with carbs",
            author_id="user-1",
            meal_id="meal-1",
            nutri_facts=NutriFacts(
                calories=400.0,
                carbohydrate=60.0,  # 60g carbs
                protein=20.0,       # 20g protein  
                total_fat=10.0      # 10g fat
            )
        )

        # Recipe 2: High protein
        meal.create_recipe(
            name="High Protein Recipe", 
            ingredients=[sample_ingredient],
            instructions="Cook with protein",
            author_id="user-1",
            meal_id="meal-1",
            nutri_facts=NutriFacts(
                calories=300.0,
                carbohydrate=10.0,  # 10g carbs
                protein=40.0,       # 40g protein
                total_fat=5.0       # 5g fat
            )
        )

        return meal

    @pytest.fixture
    def meal_no_nutrition(self, sample_ingredient):
        """Meal with recipes that have empty nutritional facts."""
        meal = Meal.create_meal(
            author_id="user-2",
            name="Meal with Empty Nutrition",
            meal_id="meal-2",
            menu_id="menu-2"
        )

        # Recipe with empty nutri_facts (zero values)
        meal.create_recipe(
            name="Empty Nutrition Recipe",
            ingredients=[sample_ingredient],
            instructions="Simple recipe",
            author_id="user-2",
            meal_id="meal-2",
            nutri_facts=NutriFacts()  # Empty nutri facts with zero values
        )

        return meal

    @pytest.fixture
    def meal_null_nutrition(self, sample_ingredient):
        """Meal with recipes that have None nutritional facts."""
        meal = Meal.create_meal(
            author_id="user-3",
            name="Meal with Null Nutrition",
            meal_id="meal-3",
            menu_id="menu-3"
        )

        # Recipe with None nutri_facts
        meal.create_recipe(
            name="Null Nutrition Recipe",
            ingredients=[sample_ingredient],
            instructions="Recipe without nutrition data",
            author_id="user-3",
            meal_id="meal-3",
            nutri_facts=None  # Explicitly None nutri facts
        )

        return meal

    def test_nutri_facts_per_instance_caching(self, meal_with_nutri_recipes, meal_no_nutrition, meal_null_nutrition):
        """Test that nutri_facts cache works correctly for all nutrition scenarios."""
        # Scenario 1: Meal with actual nutrition values
        nutri_facts_1 = meal_with_nutri_recipes.nutri_facts
        assert nutri_facts_1 is not None
        # Should be sum of both recipes: 400 + 300 = 700 calories
        assert nutri_facts_1.calories.value == 700.0
        # Should be sum of carbs: 60 + 10 = 70g
        assert nutri_facts_1.carbohydrate.value == 70.0

        # Scenario 2: Meal with empty nutrition (zero values)
        nutri_facts_2 = meal_no_nutrition.nutri_facts
        # Since the recipe has NutriFacts(), the aggregated result should be an empty but valid NutriFacts
        assert nutri_facts_2 is not None
        assert nutri_facts_2.calories.value == 0.0

        # Scenario 3: Meal with None nutrition
        nutri_facts_3 = meal_null_nutrition.nutri_facts
        # When recipes have None nutri_facts, the aggregated result should be None
        assert nutri_facts_3 is None

        # Re-access first meal - should still have correct nutrition
        nutri_facts_1_again = meal_with_nutri_recipes.nutri_facts
        assert nutri_facts_1_again is not None
        assert nutri_facts_1_again.calories.value == 700.0

    def test_macro_division_per_instance_caching(self, meal_with_nutri_recipes, meal_no_nutrition, meal_null_nutrition):
        """Test that macro_division cache works correctly for all nutrition scenarios."""
        # Scenario 1: Meal with actual nutrition values
        # Total macros: 70g carbs + 60g protein + 15g fat = 145g
        # Carb %: 70/145 = ~48.3%
        # Protein %: 60/145 = ~41.4% 
        # Fat %: 15/145 = ~10.3%
        macro_1 = meal_with_nutri_recipes.macro_division
        assert macro_1 is not None
        assert abs(macro_1.carbohydrate - 48.3) < 1.0
        assert abs(macro_1.protein - 41.4) < 1.0
        assert abs(macro_1.fat - 10.3) < 1.0

        # Scenario 2: Meal with empty nutrition (zero values) should return None (no macros to divide)
        macro_2 = meal_no_nutrition.macro_division
        assert macro_2 is None

        # Scenario 3: Meal with None nutrition should return None
        macro_3 = meal_null_nutrition.macro_division
        assert macro_3 is None

        # Re-access first meal - should still have correct macro division
        macro_1_again = meal_with_nutri_recipes.macro_division
        assert macro_1_again is not None
        assert abs(macro_1_again.carbohydrate - 48.3) < 1.0

    def test_nutri_facts_cache_invalidation_on_recipe_change(self, meal_with_nutri_recipes, sample_ingredient):
        """Test that nutri_facts cache is invalidated when recipes change."""
        # Get initial nutrition (should be 700 calories)
        initial_nutri = meal_with_nutri_recipes.nutri_facts
        assert initial_nutri is not None
        assert initial_nutri.calories.value == 700.0

        # Add a new recipe with nutrition
        meal_with_nutri_recipes.create_recipe(
            name="Additional Recipe",
            ingredients=[sample_ingredient],
            instructions="More food",
            author_id="user-1",
            meal_id="meal-1",
            nutri_facts=NutriFacts(
                calories=200.0,
                carbohydrate=15.0,
                protein=10.0,
                total_fat=8.0
            )
        )

        # Nutrition should be recalculated to include new recipe
        # 700 + 200 = 900 calories
        updated_nutri = meal_with_nutri_recipes.nutri_facts
        assert updated_nutri is not None
        assert updated_nutri.calories.value == 900.0

    def test_macro_division_cache_invalidation_on_recipe_change(self, meal_with_nutri_recipes, sample_ingredient):
        """Test that macro_division cache is invalidated when recipes change."""
        # Get initial macro division
        initial_macro = meal_with_nutri_recipes.macro_division
        assert initial_macro is not None
        initial_carb_pct = initial_macro.carbohydrate

        # Remove a recipe (should change macro proportions)
        recipes_list = list(meal_with_nutri_recipes.recipes)
        meal_with_nutri_recipes.delete_recipe(recipes_list[0].id)  # Remove high-carb recipe

        # Macro division should be recalculated
        # Now only has high-protein recipe: 10g carbs, 40g protein, 5g fat = 55g total
        # New carb %: 10/55 = ~18.2% (much lower than before)
        updated_macro = meal_with_nutri_recipes.macro_division
        assert updated_macro is not None
        new_carb_pct = updated_macro.carbohydrate

        # Carbohydrate percentage should be significantly different
        assert abs(initial_carb_pct - new_carb_pct) > 20.0

    def test_cache_invalidation_called_on_mutation(self, meal_with_nutri_recipes, sample_ingredient):
        """Test that _invalidate_caches is called when recipes affecting cached values are modified."""
        # Mock the _invalidate_caches method to track calls
        with patch.object(meal_with_nutri_recipes, '_invalidate_caches') as mock_invalidate:
            # Adding a recipe should invalidate nutrition caches
            meal_with_nutri_recipes.create_recipe(
                name="New Recipe",
                ingredients=[sample_ingredient],
                instructions="New instructions",
                author_id="user-1",
                meal_id="meal-1",
                nutri_facts=NutriFacts(calories=100.0, carbohydrate=5.0, protein=5.0, total_fat=2.0)
            )
            
            # Should call _invalidate_caches with only nutri_facts (macro_division is not cached)
            mock_invalidate.assert_called_with('nutri_facts')

    def test_cache_performance_through_behavior(self, meal_with_nutri_recipes):
        """Test that caching provides expected performance through behavioral verification."""
        # Ensure meal has recipes to avoid empty calculations
        assert len(list(meal_with_nutri_recipes.recipes)) > 0
        
        # Multiple calls should return identical objects for CACHED properties (behavior verification)
        nutri_1 = meal_with_nutri_recipes.nutri_facts
        nutri_2 = meal_with_nutri_recipes.nutri_facts
        nutri_3 = meal_with_nutri_recipes.nutri_facts
        
        # Should be the same object due to caching
        assert nutri_1 is nutri_2 is nutri_3
        
        # Test macro division consistency (NOT cached, so different objects but same values)
        macro_1 = meal_with_nutri_recipes.macro_division
        macro_2 = meal_with_nutri_recipes.macro_division
        
        # macro_division is NOT cached, so different objects but same values
        assert macro_1 == macro_2  # Same values
        assert macro_1 is not macro_2  # Different objects (not cached)
        
        # Verify the values are consistent and correct
        assert nutri_1 is not None
        assert macro_1 is not None
        assert nutri_1.calories.value == 700.0  # Both recipes: 400 + 300

    def test_cache_invalidation_on_recipe_data_change(self, meal_with_nutri_recipes):
        """Test that cached properties are invalidated when recipe nutritional data changes."""
        # Get initial cached nutrition
        initial_nutrition = meal_with_nutri_recipes.nutri_facts
        assert initial_nutrition is not None
        initial_calories = initial_nutrition.calories.value

        # Modify a recipe's nutrition data through the meal
        recipes_list = list(meal_with_nutri_recipes.recipes)
        first_recipe = recipes_list[0]
        
        # Update recipe nutrition via meal's update_recipes method
        meal_with_nutri_recipes.update_recipes({
            first_recipe.id: {
                'nutri_facts': NutriFacts(
                    calories=1000.0,  # Much higher calories
                    carbohydrate=100.0,
                    protein=50.0,
                    total_fat=20.0
                )
            }
        })

        # Nutrition should be recalculated with new values
        updated_nutrition = meal_with_nutri_recipes.nutri_facts
        assert updated_nutrition is not None
        new_calories = updated_nutrition.calories.value

        # Should reflect the change (cache was invalidated)
        assert new_calories != initial_calories
        assert new_calories > initial_calories  # Should be higher due to increased recipe calories 