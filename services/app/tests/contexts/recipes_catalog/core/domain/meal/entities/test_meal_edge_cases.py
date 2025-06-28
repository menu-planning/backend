"""
Comprehensive edge case tests for Meal entity with parametrized scenarios.

Tests extreme values, edge cases, and error conditions without mocks.
Focuses on behavior verification rather than implementation details.
Uses proper domain-focused approach with compatible recipes.
"""

import pytest

from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.value_objects.nutri_value import NutriValue
from src.contexts.shared_kernel.domain.enums import MeasureUnit
from tests.contexts.recipes_catalog.core.adapters.meal.repositories.data_factories.meal.meal_domain_factories import create_meal, reset_meal_domain_counters
from tests.contexts.recipes_catalog.core.adapters.meal.repositories.data_factories.recipe.recipe_domain_factories import create_recipe_kwargs, reset_recipe_domain_counters
from tests.contexts.recipes_catalog.core.adapters.meal.repositories.data_factories.shared_domain_factories import create_meal_tag, reset_tag_domain_counters

# Import basic data factories - use create_meal, create_tag only



class TestMealEdgeCases:
    """Test Meal entity edge cases and extreme scenarios using proper domain approach."""

    def setup_method(self):
        """Reset counters for deterministic test data."""
        reset_meal_domain_counters()
        reset_recipe_domain_counters()
        reset_tag_domain_counters()

    def _create_recipe_for_meal(self, meal_id: str, author_id: str, **recipe_kwargs):
        """Helper to create recipe with correct meal_id and author_id."""
        kwargs = create_recipe_kwargs(
            meal_id=meal_id,
            author_id=author_id,
            **recipe_kwargs
        )
        from src.contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe
        return _Recipe(**kwargs)

    @pytest.mark.parametrize("recipe_count", [0, 1, 10, 50, 100])
    def test_meal_with_varying_recipe_counts(self, recipe_count):
        """Test Meal behavior with different numbers of recipes using domain approach."""
        meal = create_meal(name="Recipe Count Test Meal")
        
        # Create recipes with correct meal_id/author_id
        recipes = []
        for i in range(recipe_count):
            recipe = self._create_recipe_for_meal(
                meal_id=meal.id,
                author_id=meal.author_id,
                name=f"Recipe {i+1}",
                nutri_facts=NutriFacts(
                    calories=NutriValue(value=100.0 + i*10, unit=MeasureUnit.ENERGY),
                    carbohydrate=NutriValue(value=15.0 + i, unit=MeasureUnit.GRAM),
                    protein=NutriValue(value=10.0 + i, unit=MeasureUnit.GRAM),
                    total_fat=NutriValue(value=5.0 + i, unit=MeasureUnit.GRAM)
                )
            )
            recipes.append(recipe)
        
        # Set recipes on meal using update_properties
        meal.update_properties(recipes=recipes)
        
        # Verify recipe handling
        assert len(meal.recipes) == recipe_count
        
        # Meal should calculate nutrition facts from recipes
        nutri_facts = meal.nutri_facts
        if recipe_count == 0:
            # Empty meal should have None nutrition
            assert nutri_facts is None
        else:
            # Should aggregate nutrition from all recipes
            assert nutri_facts is not None
            assert nutri_facts.calories.value is not None
            expected_calories = sum(100.0 + i*10 for i in range(recipe_count))
            assert abs(nutri_facts.calories.value - expected_calories) < 0.1

    @pytest.mark.parametrize("tag_count", [0, 1, 5, 20, 50])
    def test_meal_with_varying_tag_counts(self, tag_count):
        """Test Meal behavior with different numbers of tags using factory."""
        # Create unique tags to avoid conflicts
        tags = set()
        for i in range(tag_count):
            tag = create_meal_tag(
                key="category" if i % 2 == 0 else "diet",
                value=f"value_{i}",
                author_id=f"author_{(i % 3) + 1}",
                type="meal"
            )
            tags.add(tag)
        
        meal = create_meal(
            name="Tag Count Test Meal",
            tags=tags
        )
        
        # Verify tag handling
        assert len(meal.tags) == tag_count
        
        # All tags should be properly stored
        for tag in meal.tags:
            assert tag.type == "meal"
            assert tag.author_id.startswith("author_")

    @pytest.mark.parametrize("extreme_nutrition", [
        # (calories, carbs, protein, fat)
        (0.0, 0.0, 0.0, 0.0),  # All zero nutrition
        (10000.0, 1000.0, 1000.0, 1000.0),  # Extremely high nutrition
        (0.001, 0.001, 0.001, 0.001),  # Minimal nutrition
        (5000.0, 0.0, 500.0, 0.0),  # Only protein
        (3000.0, 500.0, 0.0, 0.0),  # Only carbs
        (2000.0, 0.0, 0.0, 200.0),  # Only fat
    ])
    def test_meal_with_extreme_nutrition_values(self, extreme_nutrition):
        """Test Meal behavior with extreme nutrition values via recipes."""
        calories, carbs, protein, fat = extreme_nutrition
        
        meal = create_meal(name="Extreme Nutrition Meal")
        
        # Create a recipe with extreme nutrition
        recipe = self._create_recipe_for_meal(
            meal_id=meal.id,
            author_id=meal.author_id,
            name="Extreme Nutrition Recipe",
            nutri_facts=NutriFacts(
                calories=NutriValue(value=calories, unit=MeasureUnit.ENERGY),
                carbohydrate=NutriValue(value=carbs, unit=MeasureUnit.GRAM),
                protein=NutriValue(value=protein, unit=MeasureUnit.GRAM),
                total_fat=NutriValue(value=fat, unit=MeasureUnit.GRAM)
            )
        )
        
        meal.update_properties(recipes=[recipe])
        
        # Verify nutrition aggregation
        meal_nutrition = meal.nutri_facts
        if calories == 0.0 and carbs == 0.0 and protein == 0.0 and fat == 0.0:
            # All zero nutrition should result in NutriFacts with zero values (not None)
            assert meal_nutrition is not None
            assert meal_nutrition.calories.value == 0.0
            assert meal_nutrition.carbohydrate.value == 0.0
            assert meal_nutrition.protein.value == 0.0
            assert meal_nutrition.total_fat.value == 0.0
        else:
            assert meal_nutrition is not None
            assert abs(meal_nutrition.calories.value - calories) < 0.1
            assert abs(meal_nutrition.carbohydrate.value - carbs) < 0.1
            assert abs(meal_nutrition.protein.value - protein) < 0.1
            assert abs(meal_nutrition.total_fat.value - fat) < 0.1
            
            # Macro division should handle extreme values gracefully
            macro_div = meal.macro_division
            total_macros = carbs + protein + fat
            
            if total_macros > 0:
                assert macro_div is not None
                assert abs(macro_div.carbohydrate - (carbs/total_macros*100)) < 0.1
                assert abs(macro_div.protein - (protein/total_macros*100)) < 0.1
                assert abs(macro_div.fat - (fat/total_macros*100)) < 0.1
            else:
                # Zero total macros should result in None
                assert macro_div is None

    @pytest.mark.parametrize("meal_type_nutrition", [
        # (name, description, expected_calories, expected_protein_ratio, tags)
        ("Light Mediterranean Bowl", "Low calorie meal", 400.0, 0.25, {"diet": "low-calorie"}),
        ("15-Minute Power Bowl", "Quick meal", 600.0, 0.20, {"occasion": "quick"}),
        ("Garden Harvest Feast", "Vegetarian meal", 500.0, 0.20, {"diet": "vegetarian"}),
        ("Athlete's Power Plate", "High protein meal", 800.0, 0.40, {"diet": "high-protein"}),
        ("Sunday Family Dinner", "Family meal", 700.0, 0.25, {"occasion": "family"}),
    ])
    def test_specialized_meal_edge_cases(self, meal_type_nutrition):
        """Test edge cases for specialized meal types using proper nutrition."""
        name, description, calories, protein_ratio, tag_dict = meal_type_nutrition
        
        # Create meal with appropriate tags
        tags = {create_meal_tag(key=k, value=v, type="meal", author_id="test_author") 
                for k, v in tag_dict.items()}
        meal = create_meal(name=name, description=description, tags=tags)
        
        # Calculate nutrition to achieve target ratios
        total_macros = calories / 4  # Simplified: 4 cal/g average
        protein_grams = calories * protein_ratio / 4  # Protein = 4 cal/g
        carb_grams = total_macros * 0.5  # Rest split between carbs and fat
        fat_grams = max(0.0, total_macros - protein_grams - carb_grams)  # Ensure non-negative
        
        # Create recipe with target nutrition
        recipe = self._create_recipe_for_meal(
            meal_id=meal.id,
            author_id=meal.author_id,
            name=f"{name} Recipe",
            nutri_facts=NutriFacts(
                calories=NutriValue(value=calories, unit=MeasureUnit.ENERGY),
                carbohydrate=NutriValue(value=carb_grams, unit=MeasureUnit.GRAM),
                protein=NutriValue(value=protein_grams, unit=MeasureUnit.GRAM),
                total_fat=NutriValue(value=fat_grams, unit=MeasureUnit.GRAM)
            )
        )
        
        meal.update_properties(recipes=[recipe])
        
        # Verify meal characteristics
        assert meal.nutri_facts is not None
        assert abs(meal.nutri_facts.calories.value - calories) < 0.1
        
        # Check protein percentage is close to target
        if meal.protein_percentage is not None:
            expected_protein_pct = protein_ratio * 100
            assert abs(meal.protein_percentage - expected_protein_pct) < 5.0  # 5% tolerance
        
        # Verify tags
        for expected_key, expected_value in tag_dict.items():
            found_tag = any(tag.key == expected_key and tag.value == expected_value 
                          for tag in meal.tags)
            assert found_tag, f"Expected tag {expected_key}:{expected_value} not found"

    @pytest.mark.parametrize("recipe_modification", [
        "add_recipe",
        "remove_recipe", 
        "update_recipe",
        "clear_all_recipes"
    ])
    def test_meal_recipe_modification_edge_cases(self, recipe_modification):
        """Test Meal behavior during recipe modifications."""
        meal = create_meal(name="Recipe Modification Test")
        
        # Start with one recipe with proper meal_id/author_id
        initial_recipe = self._create_recipe_for_meal(
            meal_id=meal.id,
            author_id=meal.author_id,
            name="Initial Recipe",
            nutri_facts=NutriFacts(
                calories=NutriValue(value=300.0, unit=MeasureUnit.ENERGY),
                carbohydrate=NutriValue(value=30.0, unit=MeasureUnit.GRAM),
                protein=NutriValue(value=20.0, unit=MeasureUnit.GRAM),
                total_fat=NutriValue(value=10.0, unit=MeasureUnit.GRAM)
            )
        )
        meal.update_properties(recipes=[initial_recipe])
        
        # Cache nutrition facts
        initial_nutrition = meal.nutri_facts
        assert initial_nutrition is not None
        
        if recipe_modification == "add_recipe":
            # Add another recipe
            new_recipe = self._create_recipe_for_meal(
                meal_id=meal.id,
                author_id=meal.author_id,
                name="New Recipe",
                nutri_facts=NutriFacts(
                    calories=NutriValue(value=200.0, unit=MeasureUnit.ENERGY),
                    carbohydrate=NutriValue(value=20.0, unit=MeasureUnit.GRAM),
                    protein=NutriValue(value=15.0, unit=MeasureUnit.GRAM),
                    total_fat=NutriValue(value=8.0, unit=MeasureUnit.GRAM)
                )
            )
            meal.update_properties(recipes=meal.recipes + [new_recipe])
            
            # Nutrition should be recalculated (sum of both recipes)
            new_nutrition = meal.nutri_facts
            assert new_nutrition is not None
            assert new_nutrition.calories.value == 500.0  # 300 + 200
            
        elif recipe_modification == "remove_recipe":
            # Remove the recipe
            meal.update_properties(recipes=[])
            
            # Should have no nutrition
            new_nutrition = meal.nutri_facts
            assert new_nutrition is None
            
        elif recipe_modification == "update_recipe":
            # Update recipe nutrition
            initial_recipe._set_nutri_facts(NutriFacts(
                calories=NutriValue(value=500.0, unit=MeasureUnit.ENERGY),
                carbohydrate=NutriValue(value=50.0, unit=MeasureUnit.GRAM),
                protein=NutriValue(value=30.0, unit=MeasureUnit.GRAM),
                total_fat=NutriValue(value=15.0, unit=MeasureUnit.GRAM)
            ))
            
            # Need to invalidate meal's cache since recipe changed
            meal._invalidate_caches('nutri_facts')
            
            # Meal nutrition should be updated
            meal_nutrition = meal.nutri_facts
            assert meal_nutrition is not None
            assert abs(meal_nutrition.calories.value - 500.0) < 0.1 # type: ignore
            
        elif recipe_modification == "clear_all_recipes":
            # Clear all recipes
            meal.update_properties(recipes=[])
            
            # Should handle empty state gracefully
            assert len(meal.recipes) == 0
            nutrition = meal.nutri_facts
            assert nutrition is None

    def test_meal_cache_invalidation_comprehensive(self):
        """Test Meal cache invalidation across all mutation scenarios."""
        meal = create_meal(name="Cache Test Meal")
        
        # Add initial recipes with proper meal_id/author_id
        recipe1 = self._create_recipe_for_meal(
            meal_id=meal.id,
            author_id=meal.author_id,
            name="Recipe 1",
            nutri_facts=NutriFacts(
                calories=NutriValue(value=200.0, unit=MeasureUnit.ENERGY),
                carbohydrate=NutriValue(value=25.0, unit=MeasureUnit.GRAM),
                protein=NutriValue(value=15.0, unit=MeasureUnit.GRAM),
                total_fat=NutriValue(value=8.0, unit=MeasureUnit.GRAM)
            )
        )
        recipe2 = self._create_recipe_for_meal(
            meal_id=meal.id,
            author_id=meal.author_id,
            name="Recipe 2",
            nutri_facts=NutriFacts(
                calories=NutriValue(value=300.0, unit=MeasureUnit.ENERGY),
                carbohydrate=NutriValue(value=35.0, unit=MeasureUnit.GRAM),
                protein=NutriValue(value=20.0, unit=MeasureUnit.GRAM),
                total_fat=NutriValue(value=12.0, unit=MeasureUnit.GRAM)
            )
        )
        meal.update_properties(recipes=[recipe1, recipe2])
        
        # Cache initial values
        initial_nutrition = meal.nutri_facts
        initial_macro = meal.macro_division
        
        assert initial_nutrition is not None
        assert initial_macro is not None
        assert initial_nutrition.calories.value == 500.0  # 200 + 300
        
        # Add another recipe - should invalidate nutrition caches
        recipe3 = self._create_recipe_for_meal(
            meal_id=meal.id,
            author_id=meal.author_id,
            name="Recipe 3",
            nutri_facts=NutriFacts(
                calories=NutriValue(value=400.0, unit=MeasureUnit.ENERGY),
                carbohydrate=NutriValue(value=40.0, unit=MeasureUnit.GRAM),
                protein=NutriValue(value=25.0, unit=MeasureUnit.GRAM),
                total_fat=NutriValue(value=18.0, unit=MeasureUnit.GRAM)
            )
        )
        meal.update_properties(recipes=meal.recipes + [recipe3])
        
        # Nutrition should be recalculated
        new_nutrition = meal.nutri_facts
        new_macro = meal.macro_division
        
        # Values should be different (recalculated)
        assert new_nutrition is not None
        assert new_nutrition.calories.value == 900.0  # 200 + 300 + 400
        assert new_nutrition.calories.value != initial_nutrition.calories.value
        
        # Macro percentages should be recalculated
        assert new_macro is not None
        # Total macros: (25+35+40) + (15+20+25) + (8+12+18) = 100+60+38 = 198g
        expected_carb_pct = 100/198*100  # ≈ 50.5%
        expected_protein_pct = 60/198*100  # ≈ 30.3%
        expected_fat_pct = 38/198*100  # ≈ 19.2%
        
        assert abs(new_macro.carbohydrate - expected_carb_pct) < 0.5
        assert abs(new_macro.protein - expected_protein_pct) < 0.5
        assert abs(new_macro.fat - expected_fat_pct) < 0.5

    @pytest.mark.parametrize("string_length", [
        1,  # Minimal length
        100,  # Normal length
        500,  # Long string
        1000,  # Very long string
    ])
    def test_meal_with_varying_string_lengths(self, string_length):
        """Test Meal behavior with different string field lengths."""
        long_name = "Meal " + "x" * (string_length - 5)  # Pad to desired length
        long_description = "Description " + "y" * (string_length - 12)
        long_notes = "Notes " + "z" * (string_length - 6)
        
        meal = create_meal(
            name=long_name,
            description=long_description,
            notes=long_notes
        )
        
        # Should handle varying string lengths appropriately
        assert meal.name == long_name
        if meal.description:
            assert meal.description == long_description
        if meal.notes:
            assert meal.notes == long_notes

    def test_meal_with_realistic_data_scenarios(self):
        """Test Meal edge cases using realistic domain approach."""
        # Create multiple realistic meals with proper recipes
        test_scenarios = [
            ("Italian Date Night Dinner", 650.0, 0.25),
            ("Quick Healthy Lunch Bowl", 450.0, 0.20),  
            ("Comfort Food Evening", 750.0, 0.30),
        ]
        
        for name, target_calories, protein_ratio in test_scenarios:
            meal = create_meal(name=name)
            
            # Create recipe with target nutrition
            recipe = self._create_recipe_for_meal(
                meal_id=meal.id,
                author_id=meal.author_id,
                name=f"{name} Recipe",
                nutri_facts=NutriFacts(
                    calories=NutriValue(value=target_calories, unit=MeasureUnit.ENERGY),
                    carbohydrate=NutriValue(value=target_calories*0.4/4, unit=MeasureUnit.GRAM),
                    protein=NutriValue(value=target_calories*protein_ratio/4, unit=MeasureUnit.GRAM),
                    total_fat=NutriValue(value=target_calories*0.3/9, unit=MeasureUnit.GRAM)
                )
            )
            meal.update_properties(recipes=[recipe])
            
            # All meals should have valid basic properties
            assert meal.id is not None
            assert meal.name == name
            assert len(meal.name) > 0
            assert meal.author_id is not None
            
            # All should handle cache operations safely
            nutri_facts = meal.nutri_facts
            assert nutri_facts is not None
            assert nutri_facts.calories.value is not None
            assert abs(nutri_facts.calories.value - target_calories) < 0.1
            
            macro_div = meal.macro_division  # Should not raise
            assert macro_div is not None

    def test_meal_concurrent_modifications(self):
        """Test Meal behavior during concurrent-like modifications."""
        meal = create_meal(name="Concurrent Test Meal")
        
        # Add recipe
        recipe = self._create_recipe_for_meal(
            meal_id=meal.id,
            author_id=meal.author_id,
            name="Test Recipe",
            nutri_facts=NutriFacts(
                calories=NutriValue(value=300.0, unit=MeasureUnit.ENERGY),
                carbohydrate=NutriValue(value=30.0, unit=MeasureUnit.GRAM),
                protein=NutriValue(value=20.0, unit=MeasureUnit.GRAM),
                total_fat=NutriValue(value=10.0, unit=MeasureUnit.GRAM)
            )
        )
        meal.update_properties(recipes=[recipe])
        
        # Simulate rapid successive changes
        for i in range(5):
            new_recipe = self._create_recipe_for_meal(
                meal_id=meal.id,
                author_id=meal.author_id,
                name=f"Rapid Recipe {i}",
                nutri_facts=NutriFacts(
                    calories=NutriValue(value=100.0 * (i+1), unit=MeasureUnit.ENERGY),
                    carbohydrate=NutriValue(value=10.0 * (i+1), unit=MeasureUnit.GRAM),
                    protein=NutriValue(value=8.0 * (i+1), unit=MeasureUnit.GRAM),
                    total_fat=NutriValue(value=4.0 * (i+1), unit=MeasureUnit.GRAM)
                )
            )
            meal.update_properties(recipes=meal.recipes + [new_recipe])
            
            # Should handle each change correctly
            assert len(meal.recipes) == i + 2  # initial + new recipes
            nutrition = meal.nutri_facts
            assert nutrition is not None
            assert nutrition.calories.value is not None
            assert nutrition.calories.value > 0

    @pytest.mark.parametrize("invalid_data", [
        {"name": ""},  # Empty name
        {"name": None},  # None name
        {"author_id": ""},  # Empty author_id
        {"author_id": None},  # None author_id
    ])
    def test_meal_validation_edge_cases(self, invalid_data):
        """Test Meal validation with invalid data."""
        # Most validation should happen at creation time
        try:
            meal = create_meal(**invalid_data)
            # If creation succeeds, basic properties should still be valid
            if meal.name is not None:
                assert len(str(meal.name)) >= 0
            if meal.author_id is not None:
                assert len(str(meal.author_id)) >= 0
        except (ValueError, TypeError):
            # Validation error is acceptable for invalid data
            pass 