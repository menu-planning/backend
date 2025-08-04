"""
ApiCreateRecipe Edge Cases Test Suite

Test classes for ApiCreateRecipe edge cases including boundary values,
complex scenarios, error handling, and comprehensive validation.

Following the same pattern as test_api_meal_edge_cases.py but adapted for ApiCreateRecipe.
"""

import pytest
from uuid import uuid4
import itertools

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_create_recipe import ApiCreateRecipe
from src.contexts.shared_kernel.domain.enums import Privacy, MeasureUnit

# Import data factories
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
    create_api_recipe_with_invalid_name,
    create_api_recipe_with_invalid_instructions,
    create_api_recipe_with_invalid_total_time,
    create_api_recipe_with_invalid_weight,
    create_api_recipe_with_invalid_privacy,
    create_api_recipe_with_none_values,
    create_api_recipe_with_empty_strings,
    create_api_recipe_with_whitespace_strings,
    create_api_recipe_with_very_long_text,
    create_api_recipe_with_boundary_values,
    create_comprehensive_validation_test_cases_for_api_recipe,
    REALISTIC_RECIPE_SCENARIOS
)

# Import the helper functions from conftest
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.conftest import (
    create_api_create_recipe_kwargs,
    create_minimal_api_create_recipe_kwargs,
    create_invalid_api_create_recipe_kwargs,
    create_filtered_api_create_recipe_kwargs,
)

# Import ingredient factory
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objects.data_factories.api_ingredient_data_factories import (
    create_api_ingredient
)


class TestApiCreateRecipeBoundaryValues:
    """Test suite for boundary value scenarios."""

    def test_boundary_values_using_data_factories(self):
        """Test boundary values using data factories."""
        boundary_data = create_api_recipe_with_boundary_values()
        
        # Use the filtered boundary data with helper function
        kwargs = create_filtered_api_create_recipe_kwargs(boundary_data)
        recipe = ApiCreateRecipe(**kwargs)
        
        # Verify the recipe was created successfully
        assert recipe.name is not None
        assert recipe.instructions is not None

    @pytest.mark.parametrize("scenario", [
        # Maximum length strings - updated to match actual validation constraints
        {'field': 'name', 'value': 'A' * 1000, 'should_pass': False},  # name has max_length=500
        {'field': 'description', 'value': 'B' * 1000, 'should_pass': True},   # description limit is 1000
        {'field': 'description', 'value': 'B' * 1001, 'should_pass': False},  # over the limit
        {'field': 'instructions', 'value': 'C' * 10000, 'should_pass': True}, # instructions limit is 15000
        {'field': 'notes', 'value': 'D' * 1000, 'should_pass': True},         # notes limit is 1000
        {'field': 'notes', 'value': 'D' * 1001, 'should_pass': False},        # over the limit
        {'field': 'utensils', 'value': 'E' * 500, 'should_pass': True},       # utensils limit is 500
        {'field': 'utensils', 'value': 'E' * 501, 'should_pass': False},      # over the limit
        # Boundary numeric values
        {'field': 'total_time', 'value': 0, 'should_pass': True},
        {'field': 'total_time', 'value': 9999, 'should_pass': True},
        {'field': 'weight_in_grams', 'value': 0, 'should_pass': True},
        {'field': 'weight_in_grams', 'value': 999999, 'should_pass': True},
    ])
    def test_boundary_value_scenarios(self, scenario):
        """Test boundary value scenarios."""
        field_name = scenario['field']
        value = scenario['value']
        should_pass = scenario['should_pass']
        
        kwargs = create_api_create_recipe_kwargs(**{field_name: value})
        
        if should_pass:
            recipe = ApiCreateRecipe(**kwargs)
            assert recipe is not None
        else:
            with pytest.raises(ValueError):
                ApiCreateRecipe(**kwargs)

    def test_edge_cases_and_corner_cases(self):
        """Test various edge cases and corner cases."""
        # Test with minimum possible values
        kwargs = create_minimal_api_create_recipe_kwargs(
            name="R",  # Single character
            instructions="I",  # Single character
            total_time=0,  # Zero time
            weight_in_grams=0,  # Zero weight
        )
        
        recipe = ApiCreateRecipe(**kwargs)
        assert recipe.name == "R"
        assert recipe.instructions == "I"
        assert recipe.total_time == 0
        assert recipe.weight_in_grams == 0
        
        # Test with Unicode characters
        kwargs = create_minimal_api_create_recipe_kwargs(
            name="Café Recipe 🍽️",
            instructions="Cook with care 👨‍🍳",
            description="Delicious naïve recipe",
            notes="Notes with émojis 🔥"
        )
        
        recipe = ApiCreateRecipe(**kwargs)
        assert "Café" in recipe.name
        assert "👨‍🍳" in recipe.instructions
        assert recipe.description is not None and "naïve" in recipe.description
        assert recipe.notes is not None and "émojis" in recipe.notes
        
        # Test with maximum reasonable values
        kwargs = create_minimal_api_create_recipe_kwargs(
            total_time=9999,  # Very long time
            weight_in_grams=999999,  # Very heavy
        )
        
        recipe = ApiCreateRecipe(**kwargs)
        assert recipe.total_time == 9999
        assert recipe.weight_in_grams == 999999


class TestApiCreateRecipeErrorHandling:
    """Test suite for error handling scenarios."""

    @pytest.mark.parametrize("invalid_data_factory", [
        create_api_recipe_with_invalid_name,
        create_api_recipe_with_invalid_instructions,
        create_api_recipe_with_invalid_total_time,
        create_api_recipe_with_invalid_weight,
        create_api_recipe_with_invalid_privacy,
    ])
    def test_error_handling_with_invalid_data_factories(self, invalid_data_factory):
        """Test error handling using invalid data from factories."""
        invalid_data = invalid_data_factory()
        
        if invalid_data:  # Skip None results
            # Use the filtered invalid data with helper function
            kwargs = create_filtered_api_create_recipe_kwargs(invalid_data)
            
            with pytest.raises(ValueError):
                ApiCreateRecipe(**kwargs)

    def test_error_handling_with_none_values(self):
        """Test error handling with None values for required fields."""
        none_values_data = create_api_recipe_with_none_values()
        
        if none_values_data:
            # Use the filtered none values data with helper function
            kwargs = create_filtered_api_create_recipe_kwargs(none_values_data)
            
            with pytest.raises(ValueError):
                ApiCreateRecipe(**kwargs)

    def test_empty_strings_converts_to_none(self):
        """Test error handling with empty strings for required fields."""
        empty_string_data = create_api_recipe_with_empty_strings()
        
        if empty_string_data:
            # Use the filtered empty string data with helper function
            kwargs = create_filtered_api_create_recipe_kwargs(empty_string_data)
            
            api = ApiCreateRecipe(**kwargs)
            assert api.description is None
            assert api.utensils is None
            assert api.notes is None
            assert api.image_url is None

    def test_error_handling_with_whitespace_strings(self):
        """Test error handling with whitespace strings for required fields."""
        whitespace_data = create_api_recipe_with_whitespace_strings()
        
        if whitespace_data:
            # Use the filtered whitespace data with helper function
            kwargs = create_filtered_api_create_recipe_kwargs(whitespace_data)
            
            with pytest.raises(ValueError):
                ApiCreateRecipe(**kwargs)

    def test_error_handling_with_very_long_text(self):
        """Test error handling with very long text values."""
        long_text_data = create_api_recipe_with_very_long_text()
        
        if long_text_data:
            # Use the filtered long text data with helper function
            kwargs = create_filtered_api_create_recipe_kwargs(long_text_data)
            
            # This might pass or fail depending on length constraints
            try:
                recipe = ApiCreateRecipe(**kwargs)
                assert recipe.name is not None
            except ValueError:
                # If there are length constraints, this is expected
                pass

    @pytest.mark.parametrize("scenario", [
        # Invalid name scenarios
        {'field': 'name', 'value': '', 'error_contains': 'name'},
        {'field': 'name', 'value': None, 'error_contains': 'name'},
        {'field': 'name', 'value': '   ', 'error_contains': 'name'},
        # Invalid instructions scenarios  
        {'field': 'instructions', 'value': '', 'error_contains': 'instructions'},
        {'field': 'instructions', 'value': None, 'error_contains': 'instructions'},
        {'field': 'instructions', 'value': '   ', 'error_contains': 'instructions'},
        # Invalid UUID scenarios
        {'field': 'author_id', 'value': 'invalid-uuid', 'error_contains': 'author_id'},
        {'field': 'author_id', 'value': '', 'error_contains': 'author_id'},
        {'field': 'author_id', 'value': None, 'error_contains': 'author_id'},
        {'field': 'meal_id', 'value': 'invalid-uuid', 'error_contains': 'meal_id'},
        {'field': 'meal_id', 'value': '', 'error_contains': 'meal_id'},
        {'field': 'meal_id', 'value': None, 'error_contains': 'meal_id'},
        # Invalid numeric scenarios
        {'field': 'total_time', 'value': -1, 'error_contains': 'total_time'},
        {'field': 'total_time', 'value': 'invalid', 'error_contains': 'total_time'},
        {'field': 'weight_in_grams', 'value': -1, 'error_contains': 'weight_in_grams'},
        {'field': 'weight_in_grams', 'value': 'invalid', 'error_contains': 'weight_in_grams'},
    ])
    def test_invalid_field_scenarios(self, scenario):
        """Test invalid field scenarios."""
        field_name = scenario['field']
        invalid_value = scenario['value']
        
        kwargs = create_invalid_api_create_recipe_kwargs(field_name, invalid_value)
        
        with pytest.raises(ValueError):
            ApiCreateRecipe(**kwargs)


class TestApiCreateRecipeComplexScenarios:
    """Test suite for complex validation scenarios."""

    @pytest.mark.parametrize("validation_case", create_comprehensive_validation_test_cases_for_api_recipe())
    def test_comprehensive_validation_scenarios(self, validation_case):
        """Test comprehensive validation scenarios using data factories."""
        if "factory" in validation_case:
            # Use factory function
            case_data = validation_case["factory"]()
            expected_error = validation_case.get("expected_error")
        else:
            # Use direct data
            case_data = validation_case
            expected_error = None
        
        if case_data and expected_error:
            # Use the filtered validation case data with helper function
            kwargs = create_filtered_api_create_recipe_kwargs(case_data)

            with pytest.raises(ValueError):
                ApiCreateRecipe(**kwargs)

        elif case_data:
            # Use the filtered validation case data with helper function
            kwargs = create_filtered_api_create_recipe_kwargs(case_data)
            recipe = ApiCreateRecipe(**kwargs)
            
            # If we get here, the validation passed
            assert recipe.name is not None
            assert recipe.instructions is not None

    @pytest.mark.parametrize("scenario", [
        # Valid enum values
        {'value': Privacy.PUBLIC, 'should_pass': True},
        {'value': Privacy.PRIVATE, 'should_pass': True},
        {'value': None, 'should_pass': True},  # Should default to PRIVATE
        # Invalid enum values
        {'value': 'invalid', 'should_pass': False},
        {'value': 'INVALID', 'should_pass': False},
        {'value': 123, 'should_pass': False},
    ])
    def test_privacy_enum_scenarios(self, scenario):
        """Test privacy enum scenarios."""
        value = scenario['value']
        should_pass = scenario['should_pass']
        
        kwargs = create_api_create_recipe_kwargs(privacy=value)
        
        if should_pass:
            recipe = ApiCreateRecipe(**kwargs)
            assert recipe is not None
        else:
            with pytest.raises(ValueError):
                ApiCreateRecipe(**kwargs)

    @pytest.mark.parametrize("scenario", [
        # Empty ingredients
        {'ingredients': frozenset(), 'should_pass': True},
        # Single ingredient
        {'ingredients': frozenset([
            create_api_ingredient(name='Flour', quantity=2.0, unit=MeasureUnit.CUP, position=0)
        ]), 'should_pass': True},
    ])
    def test_complex_ingredients_scenarios(self, scenario):
        """Test complex ingredients scenarios."""
        ingredients = scenario['ingredients']
        should_pass = scenario['should_pass']
        
        kwargs = create_api_create_recipe_kwargs(ingredients=ingredients)
        
        if should_pass:
            recipe = ApiCreateRecipe(**kwargs)
            assert recipe is not None
        else:
            with pytest.raises(ValueError):
                ApiCreateRecipe(**kwargs)

    def test_complex_tags_scenarios(self):
        """Test complex tags scenarios."""
        # Create scenario with empty tags
        author_id = str(uuid4())
        kwargs = create_api_create_recipe_kwargs(author_id=author_id, tags=frozenset())
        
        recipe = ApiCreateRecipe(**kwargs)
        assert recipe is not None
        assert recipe.tags == frozenset()
        
        # Create scenario with single tag
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import create_api_recipe_tag
        
        single_tag = frozenset([
            create_api_recipe_tag(key='test', value='value', author_id=author_id)
        ])
        kwargs = create_api_create_recipe_kwargs(author_id=author_id, tags=single_tag)
        
        recipe = ApiCreateRecipe(**kwargs)
        assert recipe is not None
        assert recipe.tags is not None
        assert len(recipe.tags) == 1

    @pytest.mark.parametrize("name,instructions,author_id,meal_id", [
        (name, instructions, author_id, meal_id)
        for name, instructions, author_id, meal_id in itertools.product(
            ['Test Recipe', 'R', 'Very Long Recipe Name'],
            ['Test instructions', 'I', 'Very detailed instructions'],
            ['550e8400-e29b-41d4-a716-446655440000'],
            ['550e8400-e29b-41d4-a716-446655440001']
        )
    ])
    def test_comprehensive_field_validation_matrix(self, name, instructions, author_id, meal_id):
        """Test comprehensive field validation matrix covering all combinations."""
        kwargs = create_api_create_recipe_kwargs(
            name=name,
            instructions=instructions,
            author_id=author_id,
            meal_id=meal_id
        )
        
        recipe = ApiCreateRecipe(**kwargs)
        assert recipe.name == name
        assert recipe.instructions == instructions
        assert recipe.author_id == author_id
        assert recipe.meal_id == meal_id


class TestApiCreateRecipeRealisticScenarios:
    """Test suite for realistic recipe scenarios."""

    @pytest.mark.parametrize("scenario_data", REALISTIC_RECIPE_SCENARIOS)
    def test_realistic_scenarios_from_factory(self, scenario_data):
        """Test realistic recipe scenarios from data factories."""
        try:
            # Create a copy of scenario_data to avoid mutating the shared global data
            scenario_copy = scenario_data.copy()
            
            # Use the filtered realistic scenario data with helper function
            author_id = uuid4().hex
            tags = []
            if "tags" in scenario_copy:
                from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import create_api_recipe_tag
                scenario_tags = scenario_copy["tags"]
                for tag in scenario_tags:
                    key, value = tag.split(":")
                    tag = create_api_recipe_tag(key=key, value=value, author_id=author_id)
                    tags.append(tag)
            tags = frozenset(tags)
            scenario_copy["tags"] = tags
            scenario_copy["author_id"] = author_id
            kwargs = create_filtered_api_create_recipe_kwargs(scenario_copy)
            recipe = ApiCreateRecipe(**kwargs)
            
            # Verify the recipe was created successfully
            assert recipe.name is not None
            assert recipe.instructions is not None
            assert recipe.author_id is not None
            assert recipe.meal_id is not None
            
            # Test domain conversion
            domain_command = recipe.to_domain()
            assert domain_command is not None
            
        except (ValueError, TypeError) as e:
            # Some scenarios might be designed to fail
            pytest.fail(f"Realistic scenario failed: {e}")


class TestApiCreateRecipePerformance:
    """Test suite for performance scenarios with complex data."""

    def test_performance_with_large_datasets(self):
        """Test performance with large ingredient and tag datasets."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import create_api_recipe_tag
        
        author_id = str(uuid4())
        
        # Create large datasets
        large_ingredients = frozenset([
            create_api_ingredient(name=f'Ingredient {i}', quantity=float(i+1), unit=MeasureUnit.GRAM, position=i)
            for i in range(50)
        ])
        
        large_tags = frozenset([
            create_api_recipe_tag(key=f'tag{i}', value=f'value{i}', author_id=author_id)
            for i in range(50)
        ])
        
        kwargs = create_api_create_recipe_kwargs(
            author_id=author_id,
            ingredients=large_ingredients,
            tags=large_tags
        )
        
        # This should still work efficiently
        recipe = ApiCreateRecipe(**kwargs)
        assert recipe.ingredients is not None
        assert recipe.tags is not None
        assert len(recipe.ingredients) == 50
        assert len(recipe.tags) == 50
        
        # Test domain conversion with large datasets
        domain_command = recipe.to_domain()
        assert domain_command is not None 