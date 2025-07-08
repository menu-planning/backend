"""
ApiMeal Core Functionality Test Suite

Test classes for core ApiMeal functionality including basic conversions,
round-trip validations, and computed properties.

Following the same pattern as test_api_recipe_core.py but adapted for ApiMeal.
"""

import pytest
from uuid import uuid4
from datetime import datetime, timedelta

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import ApiMeal
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import ApiRecipe
from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.meal_sa_model import MealSaModel
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_facts import ApiNutriFacts
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_value import ApiNutriValue
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag

# Import test data factories
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.data_factories.api_meal_data_factories import (
    create_api_meal_with_incorrect_computed_properties,
    validate_computed_property_correction_roundtrip,
    create_api_meal_without_recipes,
    create_api_meal_with_max_recipes,
)


class TestApiMealBasics:
    """
    Test suite for basic ApiMeal conversion methods (>95% coverage target).
    """

    # =============================================================================
    # UNIT TESTS FOR ALL CONVERSION METHODS (>95% COVERAGE TARGET)
    # =============================================================================

    def test_from_domain_basic_conversion(self, domain_meal):
        """Test from_domain basic conversion functionality."""
        api_meal = ApiMeal.from_domain(domain_meal)
        
        assert api_meal.id == domain_meal.id
        assert api_meal.name == domain_meal.name
        assert api_meal.author_id == domain_meal.author_id
        assert api_meal.menu_id == domain_meal.menu_id
        assert api_meal.description == domain_meal.description
        assert api_meal.notes == domain_meal.notes
        assert api_meal.like == domain_meal.like
        assert api_meal.image_url == domain_meal.image_url
        assert isinstance(api_meal, ApiMeal)

    def test_from_domain_nested_objects_conversion(self, domain_meal):
        """Test from_domain properly converts nested objects."""
        api_meal = ApiMeal.from_domain(domain_meal)
        
        # Test recipes conversion
        assert len(api_meal.recipes) == len(domain_meal.recipes)
        assert all(isinstance(recipe, ApiRecipe) for recipe in api_meal.recipes)
        
        # Test tags conversion - should be frozenset
        domain_tags = domain_meal.tags or set()
        assert len(api_meal.tags) == len(domain_tags)
        assert all(isinstance(tag, ApiTag) for tag in api_meal.tags)
        assert isinstance(api_meal.tags, frozenset)
        
        # Test nutri_facts conversion
        if domain_meal.nutri_facts:
            assert isinstance(api_meal.nutri_facts, ApiNutriFacts)
        else:
            assert api_meal.nutri_facts is None

    def test_from_domain_computed_properties(self, domain_meal):
        """Test from_domain correctly handles computed properties."""
        api_meal = ApiMeal.from_domain(domain_meal)
        
        # Computed properties should match domain values
        assert api_meal.weight_in_grams == domain_meal.weight_in_grams
        assert api_meal.calorie_density == domain_meal.calorie_density
        assert api_meal.carbo_percentage == domain_meal.carbo_percentage
        assert api_meal.protein_percentage == domain_meal.protein_percentage
        assert api_meal.total_fat_percentage == domain_meal.total_fat_percentage

    def test_from_domain_with_empty_collections(self, domain_meal):
        """Test from_domain handles empty collections correctly."""
        # Use the existing domain meal but ensure collections are empty
        domain_meal._recipes = []
        domain_meal._tags = set()
        api_meal = ApiMeal.from_domain(domain_meal)
        
        assert api_meal.recipes == []
        assert api_meal.tags == frozenset()

    def test_from_domain_with_nutrition_facts(self, domain_meal_with_nutri_facts):
        """Test from_domain handles nutrition facts conversion."""
        api_meal = ApiMeal.from_domain(domain_meal_with_nutri_facts)
        
        if domain_meal_with_nutri_facts.nutri_facts:
            assert isinstance(api_meal.nutri_facts, ApiNutriFacts)
            # Test that the nutritional values are converted correctly
            assert api_meal.nutri_facts.calories == domain_meal_with_nutri_facts.nutri_facts.calories
            assert api_meal.nutri_facts.protein == domain_meal_with_nutri_facts.nutri_facts.protein
            assert api_meal.nutri_facts.carbohydrate == domain_meal_with_nutri_facts.nutri_facts.carbohydrate
            assert api_meal.nutri_facts.total_fat == domain_meal_with_nutri_facts.nutri_facts.total_fat

    def test_to_domain_basic_conversion(self, simple_api_meal):
        """Test to_domain basic conversion functionality."""
        domain_meal = simple_api_meal.to_domain()
        
        assert isinstance(domain_meal, Meal)
        assert domain_meal.id == simple_api_meal.id
        assert domain_meal.name == simple_api_meal.name
        assert domain_meal.author_id == simple_api_meal.author_id
        assert domain_meal.menu_id == simple_api_meal.menu_id
        assert domain_meal.description == simple_api_meal.description
        assert domain_meal.notes == simple_api_meal.notes
        assert domain_meal.like == simple_api_meal.like
        assert domain_meal.image_url == simple_api_meal.image_url

    def test_to_domain_collection_type_conversion(self, complex_api_meal):
        """Test to_domain converts collections correctly."""
        domain_meal = complex_api_meal.to_domain()
        
        # Tags should be converted from frozenset to set
        assert isinstance(domain_meal.tags, set)
        assert len(domain_meal.tags) == len(complex_api_meal.tags)
        
        # Recipes should be converted from list to list (same type)
        assert isinstance(domain_meal.recipes, list)
        assert len(domain_meal.recipes) == len(complex_api_meal.recipes)

    def test_to_domain_nutrition_facts_conversion(self, complex_api_meal):
        """Test to_domain correctly converts nutrition facts."""
        domain_meal = complex_api_meal.to_domain()
        
        if complex_api_meal.nutri_facts:
            assert domain_meal.nutri_facts is not None
            # Domain nutrition facts should match API values
            assert domain_meal.nutri_facts.calories == complex_api_meal.nutri_facts.calories
            assert domain_meal.nutri_facts.protein == complex_api_meal.nutri_facts.protein
            assert domain_meal.nutri_facts.carbohydrate == complex_api_meal.nutri_facts.carbohydrate
            assert domain_meal.nutri_facts.total_fat == complex_api_meal.nutri_facts.total_fat

    def test_from_orm_model_basic_conversion(self, real_orm_meal):
        """Test from_orm_model basic conversion functionality."""
        api_meal = ApiMeal.from_orm_model(real_orm_meal)
        
        assert api_meal.id == real_orm_meal.id
        assert api_meal.name == real_orm_meal.name
        assert api_meal.author_id == real_orm_meal.author_id
        assert api_meal.menu_id == real_orm_meal.menu_id
        assert api_meal.description == real_orm_meal.description
        assert api_meal.notes == real_orm_meal.notes
        assert api_meal.like == real_orm_meal.like
        assert api_meal.image_url == real_orm_meal.image_url
        assert isinstance(api_meal, ApiMeal)

    def test_from_orm_model_nested_objects_conversion(self, real_orm_meal):
        """Test from_orm_model handles nested objects."""
        api_meal = ApiMeal.from_orm_model(real_orm_meal)
        
        # Should handle collections properly
        assert isinstance(api_meal.recipes, list)
        assert isinstance(api_meal.tags, frozenset)
        assert len(api_meal.recipes) == len(real_orm_meal.recipes)
        assert len(api_meal.tags) == len(real_orm_meal.tags)

    def test_from_orm_model_computed_properties(self, real_orm_meal):
        """Test from_orm_model correctly handles computed properties."""
        api_meal = ApiMeal.from_orm_model(real_orm_meal)
        
        # Computed properties should match ORM values
        assert api_meal.weight_in_grams == real_orm_meal.weight_in_grams
        assert api_meal.calorie_density == real_orm_meal.calorie_density
        assert api_meal.carbo_percentage == real_orm_meal.carbo_percentage
        assert api_meal.protein_percentage == real_orm_meal.protein_percentage
        assert api_meal.total_fat_percentage == real_orm_meal.total_fat_percentage

    def test_to_orm_kwargs_basic_conversion(self, simple_api_meal):
        """Test to_orm_kwargs basic conversion functionality."""
        kwargs = simple_api_meal.to_orm_kwargs()
        
        assert isinstance(kwargs, dict)
        assert kwargs["id"] == simple_api_meal.id
        assert kwargs["name"] == simple_api_meal.name
        assert kwargs["author_id"] == simple_api_meal.author_id
        assert kwargs["menu_id"] == simple_api_meal.menu_id
        assert kwargs["description"] == simple_api_meal.description
        assert kwargs["notes"] == simple_api_meal.notes
        assert kwargs["like"] == simple_api_meal.like
        assert kwargs["image_url"] == simple_api_meal.image_url

    def test_to_orm_kwargs_nested_objects_conversion(self, complex_api_meal):
        """Test to_orm_kwargs converts nested objects correctly."""
        kwargs = complex_api_meal.to_orm_kwargs()
        
        # Recipes should be converted to list of kwargs
        assert isinstance(kwargs["recipes"], list)
        assert len(kwargs["recipes"]) == len(complex_api_meal.recipes)
        
        # Tags should be converted from frozenset to list of kwargs
        assert isinstance(kwargs["tags"], list)
        assert len(kwargs["tags"]) == len(complex_api_meal.tags)

    def test_to_orm_kwargs_nutrition_facts_conversion(self, complex_api_meal):
        """Test to_orm_kwargs handles nutrition facts conversion."""
        kwargs = complex_api_meal.to_orm_kwargs()
        
        if complex_api_meal.nutri_facts:
            from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts_sa_model import NutriFactsSaModel
            assert isinstance(kwargs["nutri_facts"], NutriFactsSaModel)
        else:
            assert kwargs["nutri_facts"] is None

    def test_to_orm_kwargs_computed_properties_conversion(self, complex_api_meal):
        """Test to_orm_kwargs includes computed properties."""
        kwargs = complex_api_meal.to_orm_kwargs()
        
        # Computed properties should be included in ORM kwargs
        assert "weight_in_grams" in kwargs
        assert "calorie_density" in kwargs
        assert "carbo_percentage" in kwargs
        assert "protein_percentage" in kwargs
        assert "total_fat_percentage" in kwargs
        
        # Values should match API values
        assert kwargs["weight_in_grams"] == complex_api_meal.weight_in_grams
        assert kwargs["calorie_density"] == complex_api_meal.calorie_density
        assert kwargs["carbo_percentage"] == complex_api_meal.carbo_percentage
        assert kwargs["protein_percentage"] == complex_api_meal.protein_percentage
        assert kwargs["total_fat_percentage"] == complex_api_meal.total_fat_percentage


class TestApiMealRoundTrip:
    """
    Test suite for round-trip conversion validation tests.
    """

    # =============================================================================
    # ROUND-TRIP CONVERSION VALIDATION TESTS
    # =============================================================================

    def test_domain_to_api_to_domain_round_trip(self, domain_meal):
        """Test complete domain → API → domain round-trip preserves data integrity."""
        # Domain → API
        api_meal = ApiMeal.from_domain(domain_meal)
        
        # API → Domain
        recovered_domain = api_meal.to_domain()
        
        # Use Meal's __eq__ method for comprehensive comparison
        assert recovered_domain == domain_meal, "Domain → API → Domain round-trip failed"

    def test_api_to_domain_to_api_round_trip(self, complex_api_meal):
        """Test API → domain → API round-trip preserves data integrity."""
        # API → Domain
        domain_meal = complex_api_meal.to_domain()
        
        # Domain → API
        recovered_api = ApiMeal.from_domain(domain_meal)
        
        # Verify data integrity for API objects
        assert recovered_api.id == complex_api_meal.id
        assert recovered_api.name == complex_api_meal.name
        assert recovered_api.author_id == complex_api_meal.author_id
        assert len(recovered_api.recipes) == len(complex_api_meal.recipes)
        assert len(recovered_api.tags) == len(complex_api_meal.tags)
        
        # Verify computed properties are preserved
        assert recovered_api.weight_in_grams == complex_api_meal.weight_in_grams
        assert recovered_api.calorie_density == complex_api_meal.calorie_density

    def test_orm_to_api_to_orm_round_trip(self, real_orm_meal):
        """Test ORM → API → ORM round-trip preserves data integrity."""
        # ORM → API
        api_meal = ApiMeal.from_orm_model(real_orm_meal)
        
        # API → ORM kwargs
        orm_kwargs = api_meal.to_orm_kwargs()
        
        # Verify data integrity
        assert orm_kwargs["id"] == real_orm_meal.id
        assert orm_kwargs["name"] == real_orm_meal.name
        assert orm_kwargs["author_id"] == real_orm_meal.author_id
        assert orm_kwargs["menu_id"] == real_orm_meal.menu_id
        assert orm_kwargs["description"] == real_orm_meal.description
        assert orm_kwargs["notes"] == real_orm_meal.notes

    def test_complete_four_layer_round_trip(self, simple_api_meal):
        """Test complete four-layer conversion cycle preserves data integrity."""
        # Start with API object
        original_api = simple_api_meal
        
        # API → Domain
        domain_meal = original_api.to_domain()
        
        # Domain → API
        api_from_domain = ApiMeal.from_domain(domain_meal)
        
        # API → ORM kwargs
        orm_kwargs = api_from_domain.to_orm_kwargs()
        
        # Verify complete data integrity
        assert orm_kwargs["id"] == original_api.id
        assert orm_kwargs["name"] == original_api.name
        assert orm_kwargs["author_id"] == original_api.author_id
        assert orm_kwargs["menu_id"] == original_api.menu_id
        assert orm_kwargs["description"] == original_api.description
        assert orm_kwargs["notes"] == original_api.notes

    @pytest.mark.parametrize("case_name", [
        "empty_recipes",
        "max_recipes", 
        "incorrect_computed_properties",
        "minimal",
        "vegetarian",
        "high_protein",
        "quick",
        "holiday",
        "family"
    ])
    def test_round_trip_with_edge_cases(self, edge_case_meals, case_name):
        """Test round-trip conversion with edge case meals."""
        meal = edge_case_meals[case_name]
        
        # API → Domain → API
        domain_meal = meal.to_domain()
        recovered_api = ApiMeal.from_domain(domain_meal)
        
        # Verify basic integrity for API objects
        assert recovered_api.id == meal.id
        assert recovered_api.name == meal.name
        assert recovered_api.author_id == meal.author_id
        assert len(recovered_api.recipes) == len(meal.recipes)
        assert len(recovered_api.tags) == len(meal.tags)

    def test_round_trip_preserves_computed_properties(self, complex_api_meal):
        """Test that round-trip conversions preserve computed properties."""
        # Store original computed properties
        original_weight = complex_api_meal.weight_in_grams
        original_calorie_density = complex_api_meal.calorie_density
        original_carbo_percentage = complex_api_meal.carbo_percentage
        original_protein_percentage = complex_api_meal.protein_percentage
        original_total_fat_percentage = complex_api_meal.total_fat_percentage
        
        # Round-trip conversion
        domain_meal = complex_api_meal.to_domain()
        recovered_api = ApiMeal.from_domain(domain_meal)
        
        # Verify computed properties are preserved
        assert recovered_api.weight_in_grams == original_weight
        assert recovered_api.calorie_density == original_calorie_density
        assert recovered_api.carbo_percentage == original_carbo_percentage
        assert recovered_api.protein_percentage == original_protein_percentage
        assert recovered_api.total_fat_percentage == original_total_fat_percentage

    def test_round_trip_with_nested_nutrition_facts(self, complex_api_meal):
        """Test round-trip conversion with complex nutrition facts."""
        if complex_api_meal.nutri_facts:
            # Store original nutrition facts
            original_nutri_facts = complex_api_meal.nutri_facts
            
            # Round-trip conversion
            domain_meal = complex_api_meal.to_domain()
            recovered_api = ApiMeal.from_domain(domain_meal)
            
            # Verify nutrition facts are preserved
            assert recovered_api.nutri_facts is not None
            assert recovered_api.nutri_facts.calories == original_nutri_facts.calories
            assert recovered_api.nutri_facts.protein == original_nutri_facts.protein
            assert recovered_api.nutri_facts.carbohydrate == original_nutri_facts.carbohydrate
            assert recovered_api.nutri_facts.total_fat == original_nutri_facts.total_fat

    def test_round_trip_with_complex_recipes(self, complex_api_meal):
        """Test round-trip conversion with complex recipe collections."""
        # Store original recipe count and details
        original_recipe_count = len(complex_api_meal.recipes)
        original_recipe_names = [recipe.name for recipe in complex_api_meal.recipes]
        
        # Round-trip conversion
        domain_meal = complex_api_meal.to_domain()
        recovered_api = ApiMeal.from_domain(domain_meal)
        
        # Verify recipe collection is preserved
        assert len(recovered_api.recipes) == original_recipe_count
        recovered_recipe_names = [recipe.name for recipe in recovered_api.recipes]
        assert set(recovered_recipe_names) == set(original_recipe_names)

    def test_round_trip_with_complex_tags(self, complex_api_meal):
        """Test round-trip conversion with complex tag collections."""
        # Store original tag count and details
        original_tag_count = len(complex_api_meal.tags)
        original_tag_keys = {tag.key for tag in complex_api_meal.tags}
        
        # Round-trip conversion
        domain_meal = complex_api_meal.to_domain()
        recovered_api = ApiMeal.from_domain(domain_meal)
        
        # Verify tag collection is preserved
        assert len(recovered_api.tags) == original_tag_count
        recovered_tag_keys = {tag.key for tag in recovered_api.tags}
        assert recovered_tag_keys == original_tag_keys


class TestApiMealComputedProperties:
    """
    Test suite for computed properties functionality.
    """

    # =============================================================================
    # COMPUTED PROPERTIES TESTS
    # =============================================================================

    def test_computed_properties_correction_round_trip(self):
        """Test that incorrect computed properties are corrected during round-trip."""
        # Create meal with incorrect computed properties
        meal_with_incorrect = create_api_meal_with_incorrect_computed_properties()
        
        # Test that round-trip corrects computed properties
        success, details = validate_computed_property_correction_roundtrip(meal_with_incorrect)
        
        assert success, f"Computed property correction failed: {details}"
        
        # Check specific corrections
        assert details["weight_corrected"], "Weight was not corrected properly"
        assert details["calorie_density_corrected"], "Calorie density was not corrected properly"
        assert details["nutri_facts_corrected"], "Nutrition facts were not corrected properly"

    def test_computed_properties_with_no_recipes(self):
        """Test computed properties when meal has no recipes."""
        empty_meal = create_api_meal_without_recipes()
        
        # Should handle empty meal appropriately
        assert empty_meal.recipes == []
        assert empty_meal.weight_in_grams == 0
        assert empty_meal.calorie_density is None
        assert empty_meal.carbo_percentage is None
        assert empty_meal.protein_percentage is None
        assert empty_meal.total_fat_percentage is None
        assert empty_meal.nutri_facts is None

    def test_computed_properties_with_multiple_recipes(self):
        """Test computed properties aggregation with multiple recipes."""
        multi_recipe_meal = create_api_meal_with_max_recipes()
        
        # Should aggregate from multiple recipes
        assert len(multi_recipe_meal.recipes) >= 5
        
        if multi_recipe_meal.nutri_facts:
            # Should have aggregated nutrition facts
            assert multi_recipe_meal.nutri_facts.calories > 0
            assert multi_recipe_meal.nutri_facts.protein > 0
            assert multi_recipe_meal.nutri_facts.carbohydrate > 0
            
        if multi_recipe_meal.weight_in_grams:
            # Should have aggregated weight
            assert multi_recipe_meal.weight_in_grams > 0

    def test_computed_properties_consistency_through_domain(self, complex_api_meal):
        """Test that computed properties remain consistent through domain conversion."""
        # Convert to domain and back to check consistency
        domain_meal = complex_api_meal.to_domain()
        recovered_api = ApiMeal.from_domain(domain_meal)
        
        # Computed properties should be consistent
        assert recovered_api.weight_in_grams == complex_api_meal.weight_in_grams
        assert recovered_api.calorie_density == complex_api_meal.calorie_density
        assert recovered_api.carbo_percentage == complex_api_meal.carbo_percentage
        assert recovered_api.protein_percentage == complex_api_meal.protein_percentage
        assert recovered_api.total_fat_percentage == complex_api_meal.total_fat_percentage

    def test_computed_nutrition_facts_aggregation(self, complex_api_meal):
        """Test that nutrition facts are correctly aggregated from recipes."""
        if complex_api_meal.nutri_facts and complex_api_meal.recipes:
            calories = complex_api_meal.nutri_facts.calories.value if isinstance(complex_api_meal.nutri_facts.calories, ApiNutriValue) else complex_api_meal.nutri_facts.calories
            protein = complex_api_meal.nutri_facts.protein.value if isinstance(complex_api_meal.nutri_facts.protein, ApiNutriValue) else complex_api_meal.nutri_facts.protein
            carbs = complex_api_meal.nutri_facts.carbohydrate.value if isinstance(complex_api_meal.nutri_facts.carbohydrate, ApiNutriValue) else complex_api_meal.nutri_facts.carbohydrate
            fat = complex_api_meal.nutri_facts.total_fat.value if isinstance(complex_api_meal.nutri_facts.total_fat, ApiNutriValue) else complex_api_meal.nutri_facts.total_fat
            # Calculate expected totals from recipes
            expected_calories = sum(calories if recipe.nutri_facts else 0 for recipe in complex_api_meal.recipes)
            expected_protein = sum(protein if recipe.nutri_facts else 0 for recipe in complex_api_meal.recipes) 
            expected_carbs = sum(carbs if recipe.nutri_facts else 0 for recipe in complex_api_meal.recipes)
            expected_fat = sum(fat if recipe.nutri_facts else 0 for recipe in complex_api_meal.recipes)
            
            # Verify aggregated values match expectations (within reasonable tolerance)
            if expected_calories > 0:
                assert abs(calories - expected_calories) < 10
            if expected_protein > 0:
                assert abs(protein - expected_protein) < 5
            if expected_carbs > 0:
                assert abs(carbs - expected_carbs) < 5
            if expected_fat > 0:
                assert abs(fat - expected_fat) < 5

    def test_computed_weight_aggregation(self, complex_api_meal):
        """Test that weight is correctly aggregated from recipes."""
        if complex_api_meal.recipes:
            # Calculate expected weight from recipes
            expected_weight = sum(recipe.weight_in_grams or 0 for recipe in complex_api_meal.recipes)
            
            # Verify aggregated weight matches expectations
            assert complex_api_meal.weight_in_grams == expected_weight

    def test_computed_calorie_density_calculation(self, complex_api_meal):
        """Test that calorie density is correctly calculated."""
        if complex_api_meal.nutri_facts and complex_api_meal.weight_in_grams and complex_api_meal.weight_in_grams > 0:
            calories = complex_api_meal.nutri_facts.calories.value if isinstance(complex_api_meal.nutri_facts.calories, ApiNutriValue) else complex_api_meal.nutri_facts.calories
            # Calculate expected calorie density
            expected_calorie_density = (calories / complex_api_meal.weight_in_grams) * 100
            
            # Verify calorie density matches expectations (within reasonable tolerance)
            if complex_api_meal.calorie_density is not None:
                assert abs(complex_api_meal.calorie_density - expected_calorie_density) < 1.0

    def test_computed_macro_percentages_calculation(self, complex_api_meal):
        """Test that macro percentages are correctly calculated."""
        if complex_api_meal.nutri_facts:
            protein = complex_api_meal.nutri_facts.protein.value if isinstance(complex_api_meal.nutri_facts.protein, ApiNutriValue) else complex_api_meal.nutri_facts.protein
            carbs = complex_api_meal.nutri_facts.carbohydrate.value if isinstance(complex_api_meal.nutri_facts.carbohydrate, ApiNutriValue) else complex_api_meal.nutri_facts.carbohydrate
            fat = complex_api_meal.nutri_facts.total_fat.value if isinstance(complex_api_meal.nutri_facts.total_fat, ApiNutriValue) else complex_api_meal.nutri_facts.total_fat
            
            if protein is not None and carbs is not None and fat is not None:
                total_macros = protein + carbs + fat
                
                if total_macros > 0:
                    # Calculate expected percentages
                    expected_protein_percentage = (protein / total_macros) * 100
                    expected_carbo_percentage = (carbs / total_macros) * 100
                    expected_fat_percentage = (fat / total_macros) * 100
                    
                    # Verify percentages match expectations (within reasonable tolerance)
                    if complex_api_meal.protein_percentage is not None:
                        assert abs(complex_api_meal.protein_percentage - expected_protein_percentage) < 1.0
                    if complex_api_meal.carbo_percentage is not None:
                        assert abs(complex_api_meal.carbo_percentage - expected_carbo_percentage) < 1.0
                    if complex_api_meal.total_fat_percentage is not None:
                        assert abs(complex_api_meal.total_fat_percentage - expected_fat_percentage) < 1.0

    def test_computed_properties_with_edge_cases(self, edge_case_meals):
        """Test computed properties with various edge cases."""
        # Test with empty recipes
        empty_meal = edge_case_meals["empty_recipes"]
        assert empty_meal.weight_in_grams == 0
        assert empty_meal.calorie_density is None
        assert empty_meal.carbo_percentage is None
        assert empty_meal.protein_percentage is None
        assert empty_meal.total_fat_percentage is None
        
        # Test with max recipes
        max_meal = edge_case_meals["max_recipes"]
        assert max_meal.weight_in_grams >= 0
        if max_meal.nutri_facts:
            assert max_meal.nutri_facts.calories >= 0
            assert max_meal.nutri_facts.protein >= 0
            assert max_meal.nutri_facts.carbohydrate >= 0
            assert max_meal.nutri_facts.total_fat >= 0

    def test_json_with_computed_properties(self, complex_api_meal):
        """Test JSON serialization includes computed properties."""
        json_str = complex_api_meal.model_dump_json()
        
        # Should include computed properties in JSON
        import json
        parsed = json.loads(json_str)
        assert "weight_in_grams" in parsed
        assert "calorie_density" in parsed
        assert "carbo_percentage" in parsed
        assert "protein_percentage" in parsed
        assert "total_fat_percentage" in parsed

    def test_json_with_computed_properties_round_trip(self, complex_api_meal):
        """Test JSON round-trip preserves computed properties."""
        # Serialize to JSON
        json_str = complex_api_meal.model_dump_json()
        
        # Deserialize from JSON
        restored_meal = ApiMeal.model_validate_json(json_str)
        
        # Computed properties should be preserved
        assert restored_meal.weight_in_grams == complex_api_meal.weight_in_grams
        assert restored_meal.calorie_density == complex_api_meal.calorie_density
        assert restored_meal.carbo_percentage == complex_api_meal.carbo_percentage
        assert restored_meal.protein_percentage == complex_api_meal.protein_percentage
        assert restored_meal.total_fat_percentage == complex_api_meal.total_fat_percentage
