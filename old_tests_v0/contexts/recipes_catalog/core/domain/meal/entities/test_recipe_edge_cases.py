"""
Comprehensive edge case tests for Recipe entity with parametrized scenarios.

Tests extreme values, edge cases, and error conditions without mocks.
Focuses on behavior verification rather than implementation details.
Uses existing data factories for consistency and realistic test data.
"""

import pytest
from old_tests_v0.contexts.recipes_catalog.data_factories.meal.recipe.recipe_domain_factories import (
    create_high_protein_recipe,
    create_ingredient,
    create_quick_recipe,
    create_rating,
    create_recipe,
    create_vegetarian_recipe,
)
from src.contexts.shared_kernel.domain.enums import MeasureUnit
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.value_objects.nutri_value import NutriValue


class TestRecipeEdgeCases:
    """Test Recipe entity edge cases and extreme scenarios using data factories."""

    @pytest.mark.parametrize(
        "extreme_calories",
        [
            0.0,  # Zero calories
            0.001,  # Minimal calories
            9999.9,  # Very high calories
            10000.0,  # Extreme high calories
        ],
    )
    def test_recipe_with_extreme_calorie_values(self, extreme_calories):
        """Test Recipe behavior with extreme calorie values."""
        nutri_facts = NutriFacts(
            calories=NutriValue(value=extreme_calories, unit=MeasureUnit.ENERGY),
            carbohydrate=NutriValue(value=50.0, unit=MeasureUnit.GRAM),
            protein=NutriValue(value=25.0, unit=MeasureUnit.GRAM),
            total_fat=NutriValue(value=10.0, unit=MeasureUnit.GRAM),
        )

        recipe = create_recipe(name="Extreme Calorie Recipe", nutri_facts=nutri_facts)

        # Should handle extreme values gracefully
        assert recipe.nutri_facts is not None
        assert recipe.nutri_facts.calories.value == extreme_calories

        # Macro division should work with extreme calories
        macro_div = recipe.macro_division
        if extreme_calories > 0:
            assert macro_div is not None
            # Total macros: 50 + 25 + 10 = 85g
            assert abs(macro_div.carbohydrate - (50 / 85 * 100)) < 0.1
        else:
            # Zero calories might result in None macro division
            assert macro_div is None or macro_div.carbohydrate >= 0

    @pytest.mark.parametrize(
        "extreme_macros",
        [
            # (carbs, protein, fat)
            (0.0, 0.0, 0.0),  # All zero macros
            (1000.0, 0.0, 0.0),  # Only carbs
            (0.0, 1000.0, 0.0),  # Only protein
            (0.0, 0.0, 1000.0),  # Only fat
            (0.001, 0.001, 0.001),  # Minimal macros
            (999.9, 999.9, 999.9),  # Very high macros
        ],
    )
    def test_recipe_with_extreme_macro_values(self, extreme_macros):
        """Test Recipe behavior with extreme macro nutrient values."""
        carbs, protein, fat = extreme_macros

        nutri_facts = NutriFacts(
            calories=NutriValue(value=100.0, unit=MeasureUnit.ENERGY),
            carbohydrate=NutriValue(value=carbs, unit=MeasureUnit.GRAM),
            protein=NutriValue(value=protein, unit=MeasureUnit.GRAM),
            total_fat=NutriValue(value=fat, unit=MeasureUnit.GRAM),
        )

        recipe = create_recipe(name="Extreme Macro Recipe", nutri_facts=nutri_facts)

        # Should handle extreme macro values gracefully
        assert recipe.nutri_facts is not None
        assert recipe.nutri_facts.carbohydrate.value == carbs
        assert recipe.nutri_facts.protein.value == protein
        assert recipe.nutri_facts.total_fat.value == fat

        # Macro division calculation
        total_macros = carbs + protein + fat
        macro_div = recipe.macro_division

        if total_macros > 0:
            assert macro_div is not None
            assert abs(macro_div.carbohydrate - (carbs / total_macros * 100)) < 0.1
            assert abs(macro_div.protein - (protein / total_macros * 100)) < 0.1
            assert abs(macro_div.fat - (fat / total_macros * 100)) < 0.1
        else:
            # Zero total macros should result in None
            assert macro_div is None

    @pytest.mark.parametrize("rating_count", [0, 1, 2, 100, 1000])
    def test_recipe_with_varying_rating_counts(self, rating_count):
        """Test Recipe behavior with different numbers of ratings using factory."""
        recipe = create_recipe(name="Rating Test Recipe")

        # Add multiple ratings using the rating factory
        for i in range(rating_count):
            # Use factory to create varied but valid ratings
            rating = create_rating(
                recipe_id=recipe.id,
                user_id=f"user_{i}",
                taste=(i % 5) + 1,  # Cycle through 1-5
                convenience=((i + 2) % 5) + 1,  # Offset cycle for variety
            )
            recipe.rate(
                user_id=rating.user_id,
                taste=rating.taste,
                convenience=rating.convenience,
            )

        # Verify behavior based on rating count
        if rating_count == 0:
            avg_taste = recipe.average_taste_rating
            avg_convenience = recipe.average_convenience_rating
            assert avg_taste == 0.0 or avg_taste is None
            assert avg_convenience == 0.0 or avg_convenience is None
        else:
            # With ratings 1,2,3,4,5,1,2,3... the average should be approximately 3.0
            avg_taste = recipe.average_taste_rating
            avg_convenience = recipe.average_convenience_rating

            assert avg_taste is not None and avg_taste > 0.0
            assert avg_convenience is not None and avg_convenience > 0.0
            assert 1.0 <= avg_taste <= 5.0
            assert 1.0 <= avg_convenience <= 5.0

            if rating_count >= 5:
                # With full cycle of ratings 1-5, average should be close to 3
                assert abs(avg_taste - 3.0) < 1.0
                assert abs(avg_convenience - 3.0) < 1.0

    @pytest.mark.parametrize("ingredient_count", [0, 1, 10, 50, 100])
    def test_recipe_with_varying_ingredient_counts(self, ingredient_count):
        """Test Recipe behavior with different numbers of ingredients using factory."""
        # Create ingredients list using the ingredient factory
        ingredients = []
        for i in range(ingredient_count):
            ingredient = create_ingredient(
                name=f"Ingredient {i}",
                quantity=1.0 + i,
                position=i,
                product_id=f"product_{i}",
            )
            ingredients.append(ingredient)

        recipe = create_recipe(
            name="Ingredient Count Test Recipe", ingredients=ingredients
        )

        # Verify ingredient handling
        assert len(recipe.ingredients) == ingredient_count

        # All ingredients should be properly stored
        for i, ingredient in enumerate(recipe.ingredients):
            assert ingredient.name == f"Ingredient {i}"
            assert ingredient.quantity == 1.0 + i
            assert ingredient.position == i

    @pytest.mark.parametrize(
        "nutri_facts_scenario",
        [
            "empty",  # Empty NutriFacts (all zeros)
            "partial",  # Some nutrients missing/zero
            "complete",  # Full nutrition data
        ],
    )
    def test_recipe_with_different_nutrition_scenarios(self, nutri_facts_scenario):
        """Test Recipe behavior with different nutrition data scenarios."""
        if nutri_facts_scenario == "empty":
            nutri_facts = NutriFacts()  # Default empty with zeros
        elif nutri_facts_scenario == "partial":
            nutri_facts = NutriFacts(
                calories=NutriValue(value=100.0, unit=MeasureUnit.ENERGY),
                carbohydrate=NutriValue(value=0.0, unit=MeasureUnit.GRAM),  # Zero carbs
                protein=NutriValue(value=10.0, unit=MeasureUnit.GRAM),
                total_fat=NutriValue(value=0.0, unit=MeasureUnit.GRAM),  # Zero fat
            )
        else:  # complete
            nutri_facts = NutriFacts(
                calories=NutriValue(value=250.0, unit=MeasureUnit.ENERGY),
                carbohydrate=NutriValue(value=30.0, unit=MeasureUnit.GRAM),
                protein=NutriValue(value=20.0, unit=MeasureUnit.GRAM),
                total_fat=NutriValue(value=8.0, unit=MeasureUnit.GRAM),
            )

        recipe = create_recipe(
            name="Nutrition Scenario Recipe", nutri_facts=nutri_facts
        )

        # Verify nutrition handling based on scenario
        if nutri_facts_scenario == "empty":
            assert recipe.nutri_facts is not None
            assert recipe.nutri_facts.calories.value == 0.0
            assert recipe.macro_division is None  # No macros to divide
        elif nutri_facts_scenario == "partial":
            assert recipe.nutri_facts is not None
            assert recipe.nutri_facts.calories.value == 100.0
            # Macro division with partial data: only protein (10g)
            macro_div = recipe.macro_division
            if macro_div is not None:
                assert macro_div.protein == 100.0  # 100% protein
                assert macro_div.carbohydrate == 0.0
                assert macro_div.fat == 0.0
        else:  # complete
            assert recipe.nutri_facts is not None
            assert recipe.nutri_facts.calories.value == 250.0
            # Macro division: 30 + 20 + 8 = 58g total
            macro_div = recipe.macro_division
            assert macro_div is not None
            assert abs(macro_div.carbohydrate - (30 / 58 * 100)) < 0.1
            assert abs(macro_div.protein - (20 / 58 * 100)) < 0.1
            assert abs(macro_div.fat - (8 / 58 * 100)) < 0.1

    @pytest.mark.parametrize("invalid_rating_value", [-1, 0, 6, 10, -5, 100])
    def test_recipe_rating_validation_edge_cases(self, invalid_rating_value):
        """Test Recipe rating validation with invalid values.

        NOTE: Domain layer does NOT validate rating ranges - this is handled
        at the API/persistence layer. This test documents actual domain behavior.
        """
        recipe = create_recipe(name="Rating Validation Recipe")

        # Domain layer accepts any integer values without validation
        # This documents actual behavior: validation is API responsibility
        recipe.rate(user_id="test_user", taste=invalid_rating_value, convenience=3)

        # Rating should be accepted and stored as-is
        assert recipe.ratings is not None  # Guard against None type
        assert len(recipe.ratings) == 1
        assert recipe.ratings[0].taste == invalid_rating_value
        assert recipe.ratings[0].convenience == 3

        # Test convenience rating also accepts any value
        recipe.rate(user_id="test_user_2", taste=3, convenience=invalid_rating_value)

        # Should have two ratings now
        assert recipe.ratings is not None  # Guard against None type
        assert len(recipe.ratings) == 2
        assert recipe.ratings[1].taste == 3
        assert recipe.ratings[1].convenience == invalid_rating_value

    @pytest.mark.parametrize(
        "string_length",
        [
            1,  # Minimal length
            100,  # Normal length
            500,  # Long string
            1000,  # Very long string
        ],
    )
    def test_recipe_with_varying_string_lengths(self, string_length):
        """Test Recipe behavior with different string field lengths."""
        long_name = "Recipe " + "x" * (string_length - 7)  # Pad to desired length
        long_instructions = "Instructions " + "y" * (string_length - 12)

        recipe = create_recipe(name=long_name, instructions=long_instructions)

        # Should handle varying string lengths appropriately
        assert recipe.name == long_name
        assert recipe.instructions == long_instructions
        assert len(recipe.name) <= string_length + 10  # Allow some tolerance
        assert len(recipe.instructions) <= string_length + 20

    def test_recipe_rating_duplicate_author_behavior(self):
        """Test Recipe behavior when same author rates multiple times."""
        recipe = create_recipe(name="Duplicate Rating Recipe")

        # First rating
        recipe.rate(user_id="user_1", taste=5, convenience=4)
        first_taste_avg = recipe.average_taste_rating
        first_convenience_avg = recipe.average_convenience_rating

        # Same author rates again - should update, not add
        recipe.rate(user_id="user_1", taste=1, convenience=2)
        second_taste_avg = recipe.average_taste_rating
        second_convenience_avg = recipe.average_convenience_rating

        # Ratings should be updated, not duplicated
        assert second_taste_avg != first_taste_avg
        assert second_convenience_avg != first_convenience_avg
        assert second_taste_avg == 1.0  # Only one rating from user_1
        assert second_convenience_avg == 2.0

    def test_recipe_rating_deletion_edge_cases(self):
        """Test Recipe rating deletion in various scenarios.

        NOTE: This test documents actual domain behavior where empty ratings
        result in None averages, not 0.0 averages.
        """
        recipe = create_recipe(name="Rating Deletion Recipe")

        # Try deleting rating when no ratings exist
        recipe.delete_rate(user_id="nonexistent_user")
        # Should not raise error, just be a no-op

        # Add a rating then delete it
        recipe.rate(user_id="user_1", taste=4, convenience=3)
        assert recipe.average_taste_rating == 4.0

        recipe.delete_rate(user_id="user_1")
        # ACTUAL BEHAVIOR: Domain returns None when no ratings exist
        assert recipe.average_taste_rating is None  # Back to no ratings
        assert recipe.average_convenience_rating is None

        # Try deleting the same rating again - should be a no-op
        recipe.delete_rate(user_id="user_1")

    def test_recipe_cache_invalidation_comprehensive(self):
        """Test Recipe cache invalidation across all mutation scenarios.

        NOTE: This test documents actual domain behavior where empty ratings
        result in None averages, not 0.0 averages.
        """
        nutri_facts = NutriFacts(
            calories=NutriValue(value=200.0, unit=MeasureUnit.ENERGY),
            carbohydrate=NutriValue(value=25.0, unit=MeasureUnit.GRAM),
            protein=NutriValue(value=15.0, unit=MeasureUnit.GRAM),
            total_fat=NutriValue(value=8.0, unit=MeasureUnit.GRAM),
        )

        recipe = create_recipe(name="Cache Test Recipe", nutri_facts=nutri_facts)

        # Cache initial values
        initial_macro = recipe.macro_division
        assert initial_macro is not None

        # Test cache invalidation on rating changes
        recipe.rate(user_id="user_1", taste=5, convenience=4)
        initial_taste = recipe.average_taste_rating
        assert initial_taste == 5.0

        # Change nutrition facts - should invalidate macro_division cache
        new_nutri_facts = NutriFacts(
            calories=NutriValue(value=300.0, unit=MeasureUnit.ENERGY),
            carbohydrate=NutriValue(
                value=50.0, unit=MeasureUnit.GRAM
            ),  # Different carbs
            protein=NutriValue(value=15.0, unit=MeasureUnit.GRAM),
            total_fat=NutriValue(value=8.0, unit=MeasureUnit.GRAM),
        )
        recipe._set_nutri_facts(new_nutri_facts)

        # Macro division should be recalculated
        new_macro = recipe.macro_division
        assert new_macro is not None
        assert new_macro.carbohydrate != initial_macro.carbohydrate

        # Ratings should still be cached and unchanged
        assert recipe.average_taste_rating == 5.0

        # Delete rating - should invalidate rating caches
        recipe.delete_rate(user_id="user_1")
        # ACTUAL BEHAVIOR: Domain returns None when no ratings exist
        assert recipe.average_taste_rating is None  # Cache invalidated and recalculated
        assert recipe.average_convenience_rating is None

    @pytest.mark.parametrize("recipe_type", ["quick", "high_protein", "vegetarian"])
    def test_specialized_recipe_edge_cases(self, recipe_type):
        """Test edge cases for specialized recipe types using factories."""
        if recipe_type == "quick":
            recipe = create_quick_recipe(name="Quick Edge Case Recipe")
            assert recipe.total_time is not None
            assert recipe.total_time <= 20
        elif recipe_type == "high_protein":
            recipe = create_high_protein_recipe(name="High Protein Edge Case Recipe")
            # Should have meaningful protein content
            if (
                recipe.nutri_facts
                and recipe.nutri_facts.protein
                and recipe.nutri_facts.protein.value is not None
            ):
                assert recipe.nutri_facts.protein.value >= 25.0
        elif recipe_type == "vegetarian":
            recipe = create_vegetarian_recipe(name="Vegetarian Edge Case Recipe")
            # Should have vegetarian tag
            vegetarian_tags = [
                tag
                for tag in recipe.tags
                if tag.key == "diet" and tag.value == "vegetarian"
            ]
            assert len(vegetarian_tags) > 0

    def test_recipe_with_realistic_data_scenarios(self):
        """Test Recipe edge cases using realistic data from factories."""
        # Create multiple realistic recipes to test various scenarios
        recipes = [
            create_quick_recipe(),
            create_high_protein_recipe(),
            create_vegetarian_recipe(),
        ]

        for recipe in recipes:
            # All recipes should have valid basic properties
            assert recipe.id is not None
            assert recipe.name is not None
            assert len(recipe.name) > 0
            assert recipe.author_id is not None
            assert recipe.meal_id is not None

            # All should handle cache operations safely
            _ = recipe.macro_division  # Should not raise
            _ = recipe.average_taste_rating  # Should not raise
            _ = recipe.average_convenience_rating  # Should not raise

            # Should handle rating operations
            recipe.rate(user_id="test_user", taste=4, convenience=3)
            assert recipe.average_taste_rating == 4.0
            assert recipe.average_convenience_rating == 3.0
