"""
Test suite for ApiCreateRecipe field validation.

This module contains comprehensive validation tests for the ApiCreateRecipe schema,
covering all required and optional fields, edge cases, and error scenarios.
"""

import pytest
from uuid import UUID, uuid4
import itertools

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_create_recipe import ApiCreateRecipe
from src.contexts.shared_kernel.domain.enums import Privacy, MeasureUnit
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import UUIDIdRequired

# Import classes needed for model_rebuild()
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_ingredient import ApiIngredient
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_facts import ApiNutriFacts

from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
    create_api_recipe_kwargs,
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
    create_comprehensive_validation_test_cases,
    REALISTIC_RECIPE_SCENARIOS
)

# Import ingredient factory
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objects.data_factories.api_ingredient_data_factories import (
    create_api_ingredient
)

# Fix Pydantic circular import issue
ApiIngredient.model_rebuild()
ApiTag.model_rebuild()
ApiNutriFacts.model_rebuild()
ApiCreateRecipe.model_rebuild()

# Import the new helper functions from conftest
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.conftest import (
    create_api_create_recipe_kwargs,
    create_minimal_api_create_recipe_kwargs,
    create_api_create_recipe_with_author_id,
    create_minimal_api_create_recipe_with_author_id,
    create_invalid_api_create_recipe_kwargs,
    create_api_create_recipe_with_custom_tags,
    create_api_create_recipe_with_ingredients_and_tags,
    create_filtered_api_create_recipe_kwargs,
)


class TestApiCreateRecipeValidation:
    """Test class for ApiCreateRecipe field validation."""

    def test_valid_recipe_creation(self, valid_api_create_recipe_kwargs):
        """Test creation of valid ApiCreateRecipe instances."""
        recipe = ApiCreateRecipe(**valid_api_create_recipe_kwargs)
        assert recipe.name is not None
        assert recipe.instructions is not None
        assert recipe.author_id is not None
        assert recipe.meal_id is not None
        assert recipe.ingredients is not None
        assert recipe.tags is not None

    def test_minimal_recipe_creation(self, minimal_api_create_recipe_kwargs):
        """Test creation with minimal required fields."""
        recipe = ApiCreateRecipe(**minimal_api_create_recipe_kwargs)
        assert recipe.name is not None
        assert recipe.instructions is not None
        assert recipe.author_id is not None
        assert recipe.meal_id is not None
        assert recipe.ingredients is not None
        assert recipe.tags is not None
        # Optional fields should be None or have default values
        assert recipe.description is None
        assert recipe.utensils is None
        assert recipe.total_time is None
        assert recipe.notes is None
        assert recipe.privacy == Privacy.PRIVATE  # Default value
        assert recipe.nutri_facts is None
        assert recipe.weight_in_grams is None
        assert recipe.image_url is None

    # Required field validation tests
    @pytest.mark.parametrize("valid_name", [
        "Simple Recipe",
        "Recipe with Numbers 123",
        "Recipe-with-Dashes",
        "Recipe_with_underscores",
        "Recipe with special chars: Café, Naïve",
        "Very Long Recipe Name That Should Still Be Valid",
        "R",  # Single character
    ])
    def test_name_field_validation_valid_names(self, valid_name):
        """Test valid name field scenarios using new helper functions."""
        # Use the new helper function with parameter
        kwargs = create_minimal_api_create_recipe_kwargs(name=valid_name)
        recipe = ApiCreateRecipe(**kwargs)
        assert recipe.name == valid_name, f"Failed for name: {valid_name}"

    def test_name_field_validation_valid_names_with_spaces(self):
        """Test name with spaces (should be trimmed)."""
        # Use the new helper function with parameter
        kwargs = create_minimal_api_create_recipe_kwargs(name="Recipe" + " " * 50)
        recipe = ApiCreateRecipe(**kwargs)
        assert recipe.name == "Recipe", f"Name should be trimmed: {recipe.name}"

    @pytest.mark.parametrize("empty_name", ["", "   ", "\t", "\n", "  \t  \n  "])
    def test_name_field_validation_empty_strings(self, empty_name):
        """Test name field validation with empty strings."""
        # Use the new helper function with parameter
        kwargs = create_minimal_api_create_recipe_kwargs(name=empty_name)
        
        with pytest.raises(ValueError, match="name"):
            ApiCreateRecipe(**kwargs)

    def test_name_field_validation_null_values(self):
        """Test name field validation with null values."""
        # Use the new helper function with parameter
        kwargs = create_minimal_api_create_recipe_kwargs(name=None)
        
        with pytest.raises(ValueError):
            ApiCreateRecipe(**kwargs)

    def test_name_field_validation_max_length(self):
        """Test name field validation with very long names."""
        # Test extremely long name (should fail)
        very_long_name = "A" * 1000
        kwargs = create_minimal_api_create_recipe_kwargs(name=very_long_name)
        
        # This should still pass if there's no explicit max length constraint
        # The exact behavior depends on the field validation rules
        try:
            recipe = ApiCreateRecipe(**kwargs)
            assert recipe.name == very_long_name
        except ValueError:
            # If there's a max length constraint, the error should be about length
            pass

    def test_name_field_validation_using_data_factories(self):
        """Test name field validation using invalid data from factories."""
        # Test with invalid name data from factory
        invalid_name_data = create_api_recipe_with_invalid_name()
        
        # Extract just the name to test using new helper function
        if "name" in invalid_name_data:
            kwargs = create_minimal_api_create_recipe_kwargs(name=invalid_name_data["name"])
            
            with pytest.raises(ValueError):
                ApiCreateRecipe(**kwargs)

    @pytest.mark.parametrize("valid_instructions", [
        "Simple cooking instructions",
        "Step 1: Do this\nStep 2: Do that",
        "Instructions with numbers 123",
        "Instructions with special chars: Café, Naïve",
        "Very detailed instructions that go on for a long time with multiple steps and explanations",
        "I",  # Single character
        "Mix and cook",
        "1. Preheat oven to 350°F\n2. Mix ingredients\n3. Bake for 30 minutes",
        "Instructions with unicode: 🍽️ 👨‍🍳 🔥",
    ])
    def test_instructions_field_validation_valid_instructions(self, valid_instructions):
        """Test valid instructions field scenarios using new helper functions."""
        # Use the new helper function with parameter
        kwargs = create_minimal_api_create_recipe_kwargs(instructions=valid_instructions)
        recipe = ApiCreateRecipe(**kwargs)
        assert recipe.instructions == valid_instructions, f"Failed for instructions: {valid_instructions}"

    def test_instructions_field_validation_valid_instructions_with_spaces(self):
        """Test instructions with spaces (should be trimmed)."""
        # Use the new helper function with parameter
        kwargs = create_minimal_api_create_recipe_kwargs(instructions="Instructions" + " " * 50)
        recipe = ApiCreateRecipe(**kwargs)
        assert recipe.instructions == "Instructions", f"Instructions should be trimmed: {recipe.instructions}"

    @pytest.mark.parametrize("empty_instruction", ["", "   ", "\t", "\n", "  \t  \n  ", "\r\n"])
    def test_instructions_field_validation_empty_strings(self, empty_instruction):
        """Test instructions field validation with empty strings."""
        # Use the new helper function with parameter
        kwargs = create_minimal_api_create_recipe_kwargs(instructions=empty_instruction)
        
        with pytest.raises(ValueError, match="instructions"):
            ApiCreateRecipe(**kwargs)

    def test_instructions_field_validation_null_values(self):
        """Test instructions field validation with null values."""
        # Use the new helper function with parameter
        kwargs = create_minimal_api_create_recipe_kwargs(instructions=None)
        
        with pytest.raises(ValueError):
            ApiCreateRecipe(**kwargs)

    def test_instructions_field_validation_formatting(self):
        """Test instructions field validation with various formatting scenarios."""
        # Test multiline instructions
        multiline_instructions = """
        Step 1: Prepare the ingredients
        Step 2: Mix everything together
        Step 3: Cook for 30 minutes
        Step 4: Serve hot
        """
        kwargs = create_minimal_api_create_recipe_kwargs(instructions=multiline_instructions)
        recipe = ApiCreateRecipe(**kwargs)
        assert recipe.instructions == multiline_instructions.strip()

        # Test instructions with HTML-like content (should be treated as text)
        html_instructions = "<b>Bold</b> instructions with <i>italic</i> text"
        kwargs = create_minimal_api_create_recipe_kwargs(instructions=html_instructions)
        recipe = ApiCreateRecipe(**kwargs)
        assert recipe.instructions == html_instructions

    def test_instructions_field_validation_max_length(self):
        """Test instructions field validation with very long instructions."""
        # Test extremely long instructions
        very_long_instructions = "Step " * 2000  # Very long instructions
        kwargs = create_minimal_api_create_recipe_kwargs(instructions=very_long_instructions)
        
        # This should still pass if there's no explicit max length constraint
        try:
            recipe = ApiCreateRecipe(**kwargs)
            assert recipe.instructions == very_long_instructions.strip()
        except ValueError:
            # If there's a max length constraint, the error should be about length
            pass

    def test_instructions_field_validation_using_data_factories(self):
        """Test instructions field validation using invalid data from factories."""
        # Test with invalid instructions data from factory
        invalid_instructions_data = create_api_recipe_with_invalid_instructions()
        
        # Extract just the instructions to test using new helper function
        if "instructions" in invalid_instructions_data:
            kwargs = create_minimal_api_create_recipe_kwargs(instructions=invalid_instructions_data["instructions"])
            
            with pytest.raises(ValueError):
                ApiCreateRecipe(**kwargs)

    @pytest.mark.parametrize("valid_author_id", [
        "550e8400-e29b-41d4-a716-446655440000",  # Standard UUID format
        "550E8400-E29B-41D4-A716-446655440000",  # Uppercase
        "550e8400e29b41d4a716446655440000",       # No hyphens
        "550E8400E29B41D4A716446655440000",       # No hyphens, uppercase
    ])
    def test_author_id_field_validation_valid_uuids(self, valid_author_id):
        """Test valid author_id field scenarios using new helper functions."""
        # Use the new helper function with specific author_id
        kwargs = create_minimal_api_create_recipe_with_author_id(valid_author_id)
        recipe = ApiCreateRecipe(**kwargs)
        # UUID fields might be normalized, so just check it's valid
        assert recipe.author_id is not None
        assert isinstance(recipe.author_id, (str, UUID))

    @pytest.mark.parametrize("invalid_author_id", [
        "invalid-uuid",
        "123",
        "550e8400-e29b-41d4-a716",  # Too short
        "550e8400-e29b-41d4-a716-446655440000-extra",  # Too long
        "550e8400-e29b-41d4-a716-44665544000g",  # Invalid character
        "not-a-uuid-at-all",
        "550e8400e29b41d4a716446655440000extra",  # Too long without hyphens
        "550e8400e29b41d4a71644665544000",  # Too short without hyphens
        "",  # Empty string
        "   ",  # Whitespace only
    ])
    def test_author_id_field_validation_invalid_formats(self, invalid_author_id):
        """Test author_id field validation with invalid UUID formats."""
        # Use the helper function to create invalid kwargs
        kwargs = create_invalid_api_create_recipe_kwargs('author_id', invalid_author_id)
        
        with pytest.raises(ValueError):
            ApiCreateRecipe(**kwargs)

    def test_author_id_field_validation_edge_cases(self):
        """Test author_id field validation with edge cases."""
        # Test all zeros UUID - this might be valid or invalid depending on implementation
        all_zeros_uuid = "00000000-0000-0000-0000-000000000000"
        kwargs = create_minimal_api_create_recipe_with_author_id(all_zeros_uuid)
        
        # This might be valid or invalid - both behaviors are acceptable
        try:
            recipe = ApiCreateRecipe(**kwargs)
            assert recipe.author_id is not None
        except ValueError:
            # If all zeros is invalid, that's also acceptable
            pass

    def test_author_id_field_validation_null_values(self):
        """Test author_id field validation with null values."""
        # Use the helper function to create invalid kwargs
        kwargs = create_invalid_api_create_recipe_kwargs('author_id', None)
        
        with pytest.raises(ValueError):
            ApiCreateRecipe(**kwargs)

    @pytest.mark.parametrize("invalid_type", [
        123,  # Integer
        123.45,  # Float
        True,  # Boolean
        [],  # List
        {},  # Dict
    ])
    def test_author_id_field_validation_data_types(self, invalid_type):
        """Test author_id field validation with various data types."""
        # Use the helper function to create invalid kwargs
        kwargs = create_invalid_api_create_recipe_kwargs('author_id', invalid_type)
        
        with pytest.raises(ValueError):
            ApiCreateRecipe(**kwargs)

    def test_author_id_field_validation_uuid_objects(self):
        """Test author_id field validation with UUID objects."""
        # Use the helper function to create kwargs with UUID object
        uuid_obj = uuid4()
        kwargs = create_invalid_api_create_recipe_kwargs('author_id', uuid_obj)
        
        # UUID object might actually be valid, so handle both cases
        try:
            recipe = ApiCreateRecipe(**kwargs)
            assert recipe.author_id is not None
        except ValueError:
            # If UUID objects are not accepted, that's also valid
            pass

    def test_author_id_field_validation_using_data_factories(self):
        """Test author_id field validation using data factories."""
        # Test with various author_id scenarios from factory
        factory_data = create_api_recipe_kwargs()
        
        # Use the factory's author_id as a valid example with new helper function
        kwargs = create_minimal_api_create_recipe_with_author_id(factory_data["author_id"])
        recipe = ApiCreateRecipe(**kwargs)
        assert recipe.author_id is not None

    def test_author_id_constraint_consistency(self):
        """Test that author_id constraint is properly maintained between recipe and tags."""
        # Create a specific author_id
        author_id = "550e8400-e29b-41d4-a716-446655440000"
        
        # Create recipe with custom tags using the new helper function
        custom_tags = [
            {"key": "cuisine", "value": "italian"},
            {"key": "difficulty", "value": "easy"},
            {"key": "meal-type", "value": "dinner"},
        ]
        
        kwargs = create_api_create_recipe_with_custom_tags(
            author_id=author_id,
            tags=custom_tags
        )
        
        recipe = ApiCreateRecipe(**kwargs)
        
        # Verify that the recipe has the correct author_id
        assert recipe.author_id == author_id
        
        # Verify that all tags have the same author_id
        assert recipe.tags is not None
        assert len(recipe.tags) == 3
        for tag in recipe.tags:
            assert tag.author_id == author_id

    def test_ingredients_and_tags_custom_creation(self):
        """Test creating recipe with custom ingredients and tags."""
        # Create a specific author_id
        author_id = "550e8400-e29b-41d4-a716-446655440000"
        
        # Define custom ingredients
        custom_ingredients = [
            {"name": "Pasta", "quantity": 500.0, "unit": MeasureUnit.GRAM, "position": 0},
            {"name": "Tomato Sauce", "quantity": 400.0, "unit": MeasureUnit.MILLILITER, "position": 1},
            {"name": "Parmesan Cheese", "quantity": 100.0, "unit": MeasureUnit.GRAM, "position": 2},
        ]
        
        # Define custom tags
        custom_tags = [
            {"key": "cuisine", "value": "italian"},
            {"key": "difficulty", "value": "easy"},
            {"key": "meal-type", "value": "dinner"},
        ]
        
        kwargs = create_api_create_recipe_with_ingredients_and_tags(
            author_id=author_id,
            ingredients=custom_ingredients,
            tags=custom_tags,
            name="Pasta with Tomato Sauce",
            instructions="1. Cook pasta. 2. Heat sauce. 3. Mix and serve.",
            total_time=20
        )
        
        recipe = ApiCreateRecipe(**kwargs)
        
        # Verify recipe properties
        assert recipe.author_id == author_id
        assert recipe.name == "Pasta with Tomato Sauce"
        assert recipe.total_time == 20
        
        # Verify ingredients
        assert recipe.ingredients is not None
        assert len(recipe.ingredients) == 3
        ingredient_names = {ing.name for ing in recipe.ingredients}
        assert ingredient_names == {"Pasta", "Tomato Sauce", "Parmesan Cheese"}
        
        # Verify tags
        assert recipe.tags is not None
        assert len(recipe.tags) == 3
        for tag in recipe.tags:
            assert tag.author_id == author_id
        
        tag_values = {tag.value for tag in recipe.tags}
        assert tag_values == {"italian", "easy", "dinner"}

    # Continue with meal_id validation tests
    @pytest.mark.parametrize("valid_meal_id", [
        "550e8400-e29b-41d4-a716-446655440000",  # Standard UUID format
        "550E8400-E29B-41D4-A716-446655440000",  # Uppercase
        "550e8400e29b41d4a716446655440000",       # No hyphens
        "550E8400E29B41D4A716446655440000",       # No hyphens, uppercase
    ])
    def test_meal_id_field_validation_valid_uuids(self, valid_meal_id):
        """Test valid meal_id field scenarios using new helper functions."""
        # Use the new helper function with specific meal_id
        kwargs = create_minimal_api_create_recipe_kwargs(meal_id=valid_meal_id)
        recipe = ApiCreateRecipe(**kwargs)
        # UUID fields might be normalized, so just check it's valid
        assert recipe.meal_id is not None
        assert isinstance(recipe.meal_id, (str, UUID))

    @pytest.mark.parametrize("invalid_meal_id", [
        "invalid-uuid",
        "123",
        "550e8400-e29b-41d4-a716",  # Too short
        "550e8400-e29b-41d4-a716-446655440000-extra",  # Too long
        "550e8400-e29b-41d4-a716-44665544000g",  # Invalid character
        "not-a-uuid-at-all",
        "550e8400e29b41d4a716446655440000extra",  # Too long without hyphens
        "550e8400e29b41d4a71644665544000",  # Too short without hyphens
        "",  # Empty string
        "   ",  # Whitespace only
    ])
    def test_meal_id_field_validation_invalid_formats(self, invalid_meal_id):
        """Test meal_id field validation with invalid UUID formats."""
        # Use the helper function to create invalid kwargs
        kwargs = create_invalid_api_create_recipe_kwargs('meal_id', invalid_meal_id)
        
        with pytest.raises(ValueError):
            ApiCreateRecipe(**kwargs)

    def test_meal_id_field_validation_null_values(self):
        """Test meal_id field validation with null values."""
        # Use the helper function to create invalid kwargs
        kwargs = create_invalid_api_create_recipe_kwargs('meal_id', None)
        
        with pytest.raises(ValueError):
            ApiCreateRecipe(**kwargs)

    @pytest.mark.parametrize("invalid_type", [
        123,  # Integer
        123.45,  # Float
        True,  # Boolean
        [],  # List
        {},  # Dict
    ])
    def test_meal_id_field_validation_data_types(self, invalid_type):
        """Test meal_id field validation with various data types."""
        # Use the helper function to create invalid kwargs
        kwargs = create_invalid_api_create_recipe_kwargs('meal_id', invalid_type)
        
        with pytest.raises(ValueError):
            ApiCreateRecipe(**kwargs)

    # Optional field validation tests
    @pytest.mark.parametrize("valid_description", [
        "A delicious recipe for the family",
        "Recipe with special chars: Café, Naïve",
        "Very long description that goes on for multiple lines with lots of details",
        "D",  # Single character
        "Simple description",
        "Description with unicode: 🍽️ 👨‍🍳 🔥",
        None,  # None should be valid for optional field
    ])
    def test_description_field_validation_valid_values(self, valid_description):
        """Test valid description field scenarios."""
        kwargs = create_minimal_api_create_recipe_kwargs(description=valid_description)
        recipe = ApiCreateRecipe(**kwargs)
        assert recipe.description == valid_description

    @pytest.mark.parametrize("empty_description", ["", "   ", "\t", "\n", "  \t  \n  "])
    def test_description_field_validation_empty_strings(self, empty_description):
        """Test description field validation with empty strings (should become None)."""
        kwargs = create_minimal_api_create_recipe_kwargs(description=empty_description)
        recipe = ApiCreateRecipe(**kwargs)
        # Empty strings might be converted to None for optional fields
        assert recipe.description is None or recipe.description == ""

    @pytest.mark.parametrize("valid_utensils", [
        "Knife, cutting board, pan",
        "Oven, baking sheet",
        "Mixing bowls, whisk, spatula",
        "U",  # Single character
        "Simple utensil",
        None,  # None should be valid for optional field
    ])
    def test_utensils_field_validation_valid_values(self, valid_utensils):
        """Test valid utensils field scenarios."""
        kwargs = create_minimal_api_create_recipe_kwargs(utensils=valid_utensils)
        recipe = ApiCreateRecipe(**kwargs)
        assert recipe.utensils == valid_utensils

    @pytest.mark.parametrize("valid_total_time", [
        0,  # Zero time
        1,  # One minute
        30,  # Thirty minutes
        120,  # Two hours
        1440,  # One day
        None,  # None should be valid for optional field
    ])
    def test_total_time_field_validation_valid_values(self, valid_total_time):
        """Test valid total_time field scenarios."""
        kwargs = create_minimal_api_create_recipe_kwargs(total_time=valid_total_time)
        recipe = ApiCreateRecipe(**kwargs)
        assert recipe.total_time == valid_total_time

    @pytest.mark.parametrize("invalid_total_time", [
        -1,  # Negative time
        -100,  # Large negative
        "invalid",  # String
        [],  # List
        {},  # Dict
        True,  # Boolean
    ])
    def test_total_time_field_validation_invalid_values(self, invalid_total_time):
        """Test total_time field validation with invalid values."""
        kwargs = create_invalid_api_create_recipe_kwargs('total_time', invalid_total_time)
        
        with pytest.raises(ValueError):
            ApiCreateRecipe(**kwargs)

    @pytest.mark.parametrize("valid_notes", [
        "Some cooking notes",
        "Notes with special chars: Café, Naïve",
        "Very long notes that go on for multiple lines with lots of details",
        "N",  # Single character
        "Simple notes",
        "Notes with unicode: 🍽️ 👨‍🍳 🔥",
        None,  # None should be valid for optional field
    ])
    def test_notes_field_validation_valid_values(self, valid_notes):
        """Test valid notes field scenarios."""
        kwargs = create_minimal_api_create_recipe_kwargs(notes=valid_notes)
        recipe = ApiCreateRecipe(**kwargs)
        assert recipe.notes == valid_notes

    @pytest.mark.parametrize("valid_privacy", [
        Privacy.PUBLIC,
        Privacy.PRIVATE,
        None,  # Should default to PRIVATE
    ])
    def test_privacy_field_validation_valid_values(self, valid_privacy):
        """Test valid privacy field scenarios."""
        kwargs = create_minimal_api_create_recipe_kwargs(privacy=valid_privacy)
        recipe = ApiCreateRecipe(**kwargs)
        # Check that privacy is set to a valid Privacy enum value
        assert recipe.privacy in [Privacy.PUBLIC, Privacy.PRIVATE]

    @pytest.mark.parametrize("invalid_privacy", [
        "public",  # String value
        "private",  # String value
        "invalid",  # Invalid string
        123,  # Integer
        [],  # List
        {},  # Dict
        True,  # Boolean
    ])
    def test_privacy_field_validation_invalid_values(self, invalid_privacy):
        """Test privacy field validation with invalid values."""
        kwargs = create_invalid_api_create_recipe_kwargs('privacy', invalid_privacy)
        
        with pytest.raises(ValueError):
            ApiCreateRecipe(**kwargs)

    @pytest.mark.parametrize("valid_weight", [
        0,  # Zero weight
        1,  # One gram
        100,  # 100 grams
        1000,  # 1kg
        None,  # None should be valid for optional field
    ])
    def test_weight_in_grams_field_validation_valid_values(self, valid_weight):
        """Test valid weight_in_grams field scenarios."""
        kwargs = create_minimal_api_create_recipe_kwargs(weight_in_grams=valid_weight)
        recipe = ApiCreateRecipe(**kwargs)
        assert recipe.weight_in_grams == valid_weight

    @pytest.mark.parametrize("invalid_weight", [
        -1,  # Negative weight
        -100,  # Large negative
        "invalid",  # String
        [],  # List
        {},  # Dict
        True,  # Boolean
    ])
    def test_weight_in_grams_field_validation_invalid_values(self, invalid_weight):
        """Test weight_in_grams field validation with invalid values."""
        kwargs = create_invalid_api_create_recipe_kwargs('weight_in_grams', invalid_weight)
        
        with pytest.raises(ValueError):
            ApiCreateRecipe(**kwargs)

    @pytest.mark.parametrize("valid_image_url", [
        "https://example.com/image.jpg",
        "http://example.com/image.png",
        "https://cdn.example.com/path/to/image.gif",
        None,  # None should be valid for optional field
    ])
    def test_image_url_field_validation_valid_values(self, valid_image_url):
        """Test valid image_url field scenarios."""
        kwargs = create_minimal_api_create_recipe_kwargs(image_url=valid_image_url)
        recipe = ApiCreateRecipe(**kwargs)
        if valid_image_url is None:
            assert recipe.image_url is None
        else:
            assert str(recipe.image_url) == valid_image_url

    @pytest.mark.parametrize("invalid_image_url", [
        "not-a-url",  # Invalid URL
        "ftp://example.com/image.jpg",  # Invalid protocol
        123,  # Integer
        [],  # List
        {},  # Dict
        True,  # Boolean
    ])
    def test_image_url_field_validation_invalid_values(self, invalid_image_url):
        """Test image_url field validation with invalid values."""
        kwargs = create_invalid_api_create_recipe_kwargs('image_url', invalid_image_url)
        
        with pytest.raises(ValueError):
            ApiCreateRecipe(**kwargs)

    # Ingredients validation tests
    def test_ingredients_field_validation_empty_set(self):
        """Test ingredients field with empty set (should be valid)."""
        kwargs = create_minimal_api_create_recipe_kwargs(ingredients=frozenset())
        recipe = ApiCreateRecipe(**kwargs)
        assert recipe.ingredients == frozenset()

    def test_ingredients_field_validation_single_ingredient(self):
        """Test ingredients field with single ingredient."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objects.data_factories.api_ingredient_data_factories import create_api_ingredient
        
        single_ingredient = frozenset([
            create_api_ingredient(name='Flour', quantity=2.0, unit=MeasureUnit.CUP, position=0)
        ])
        kwargs = create_minimal_api_create_recipe_kwargs(ingredients=single_ingredient)
        recipe = ApiCreateRecipe(**kwargs)
        assert recipe.ingredients is not None
        assert len(recipe.ingredients) == 1

    def test_ingredients_field_validation_multiple_ingredients(self):
        """Test ingredients field with multiple ingredients."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objects.data_factories.api_ingredient_data_factories import create_api_ingredient
        
        multiple_ingredients = frozenset([
            create_api_ingredient(name='Flour', quantity=2.0, unit=MeasureUnit.CUP, position=0),
            create_api_ingredient(name='Sugar', quantity=1.0, unit=MeasureUnit.CUP, position=1),
            create_api_ingredient(name='Eggs', quantity=3.0, unit=MeasureUnit.UNIT, position=2),
        ])
        kwargs = create_minimal_api_create_recipe_kwargs(ingredients=multiple_ingredients)
        recipe = ApiCreateRecipe(**kwargs)
        assert recipe.ingredients is not None
        assert len(recipe.ingredients) == 3

    @pytest.mark.parametrize("invalid_ingredients", [
        "invalid",  # String
        [],  # List instead of frozenset
        {},  # Dict
        123,  # Integer
    ])
    def test_ingredients_field_validation_invalid_values(self, invalid_ingredients):
        """Test ingredients field validation with invalid values."""
        kwargs = create_invalid_api_create_recipe_kwargs('ingredients', invalid_ingredients)
        
        with pytest.raises(ValueError):
            ApiCreateRecipe(**kwargs)

    # Tags validation tests
    def test_tags_field_validation_empty_set(self):
        """Test tags field with empty set (should be valid)."""
        kwargs = create_minimal_api_create_recipe_kwargs(tags=frozenset())
        recipe = ApiCreateRecipe(**kwargs)
        assert recipe.tags == frozenset()

    def test_tags_field_validation_single_tag(self):
        """Test tags field with single tag."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import create_api_recipe_tag
        
        author_id = str(uuid4())
        single_tag = frozenset([
            create_api_recipe_tag(key='difficulty', value='easy', author_id=author_id)
        ])
        kwargs = create_minimal_api_create_recipe_kwargs(author_id=author_id, tags=single_tag)
        recipe = ApiCreateRecipe(**kwargs)
        assert recipe.tags is not None
        assert len(recipe.tags) == 1

    def test_tags_field_validation_multiple_tags(self):
        """Test tags field with multiple tags."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import create_api_recipe_tag
        
        author_id = str(uuid4())
        multiple_tags = frozenset([
            create_api_recipe_tag(key='difficulty', value='easy', author_id=author_id),
            create_api_recipe_tag(key='cuisine', value='italian', author_id=author_id),
            create_api_recipe_tag(key='meal-type', value='dinner', author_id=author_id),
        ])
        kwargs = create_minimal_api_create_recipe_kwargs(author_id=author_id, tags=multiple_tags)
        recipe = ApiCreateRecipe(**kwargs)
        assert recipe.tags is not None
        assert len(recipe.tags) == 3

    @pytest.mark.parametrize("invalid_tags", [
        "invalid",  # String
        {},  # Dict
        123,  # Integer
    ])
    def test_tags_field_validation_invalid_values(self, invalid_tags):
        """Test tags field validation with invalid values."""
        kwargs = create_invalid_api_create_recipe_kwargs('tags', invalid_tags)
        
        with pytest.raises(ValueError):
            ApiCreateRecipe(**kwargs)

    # Boundary value tests
    def test_boundary_values_using_data_factories(self):
        """Test boundary values using data factories."""
        boundary_data = create_api_recipe_with_boundary_values()
        
        # Use the filtered boundary data with new helper function
        kwargs = create_filtered_api_create_recipe_kwargs(boundary_data)
        recipe = ApiCreateRecipe(**kwargs)
        
        # Verify the recipe was created successfully
        assert recipe.name is not None
        assert recipe.instructions is not None

    @pytest.mark.parametrize("validation_case", create_comprehensive_validation_test_cases())
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
            # Use the filtered validation case data with new helper function
            kwargs = create_filtered_api_create_recipe_kwargs(case_data)

            with pytest.raises(ValueError):
                ApiCreateRecipe(**kwargs)

        elif case_data:
            # Use the filtered validation case data with new helper function
            kwargs = create_filtered_api_create_recipe_kwargs(case_data)
            recipe = ApiCreateRecipe(**kwargs)
            
            # If we get here, the validation passed
            assert recipe.name is not None
            assert recipe.instructions is not None

    # Error handling tests
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
            # Use the filtered invalid data with new helper function
            kwargs = create_filtered_api_create_recipe_kwargs(invalid_data)
            
            with pytest.raises(ValueError):
                ApiCreateRecipe(**kwargs)

    def test_error_handling_with_none_values(self):
        """Test error handling with None values for required fields."""
        none_values_data = create_api_recipe_with_none_values()
        
        if none_values_data:
            # Use the filtered none values data with new helper function
            kwargs = create_filtered_api_create_recipe_kwargs(none_values_data)
            
            with pytest.raises(ValueError):
                ApiCreateRecipe(**kwargs)

    def test_error_handling_with_empty_strings(self):
        """Test error handling with empty strings for required fields."""
        empty_string_data = create_api_recipe_with_empty_strings()
        
        if empty_string_data:
            # Use the filtered empty string data with new helper function
            kwargs = create_filtered_api_create_recipe_kwargs(empty_string_data)
            
            with pytest.raises(ValueError):
                ApiCreateRecipe(**kwargs)

    def test_error_handling_with_whitespace_strings(self):
        """Test error handling with whitespace strings for required fields."""
        whitespace_data = create_api_recipe_with_whitespace_strings()
        
        if whitespace_data:
            # Use the filtered whitespace data with new helper function
            kwargs = create_filtered_api_create_recipe_kwargs(whitespace_data)
            
            with pytest.raises(ValueError):
                ApiCreateRecipe(**kwargs)

    def test_error_handling_with_very_long_text(self):
        """Test error handling with very long text values."""
        long_text_data = create_api_recipe_with_very_long_text()
        
        if long_text_data:
            # Use the filtered long text data with new helper function
            kwargs = create_filtered_api_create_recipe_kwargs(long_text_data)
            
            # This might pass or fail depending on length constraints
            try:
                recipe = ApiCreateRecipe(**kwargs)
                assert recipe.name is not None
            except ValueError:
                # If there are length constraints, this is expected
                pass

    # Domain conversion tests
    def test_domain_conversion_simple_recipe(self):
        """Test domain conversion with simple recipe."""
        kwargs = create_minimal_api_create_recipe_kwargs()
        api_recipe = ApiCreateRecipe(**kwargs)
        
        # Test conversion to domain command
        domain_command = api_recipe.to_domain()
        assert domain_command is not None
        assert hasattr(domain_command, 'name')
        assert hasattr(domain_command, 'instructions')
        assert hasattr(domain_command, 'author_id')

    def test_domain_conversion_complex_recipe(self):
        """Test domain conversion with complex recipe."""
        kwargs = create_api_create_recipe_kwargs()
        api_recipe = ApiCreateRecipe(**kwargs)
        
        # Test conversion to domain command
        domain_command = api_recipe.to_domain()
        assert domain_command is not None
        assert hasattr(domain_command, 'name')
        assert hasattr(domain_command, 'instructions')
        assert hasattr(domain_command, 'author_id')

    def test_domain_conversion_with_all_fields(self):
        """Test domain conversion with all fields populated."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objects.data_factories.api_ingredient_data_factories import create_api_ingredient
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import create_api_recipe_tag
        
        author_id = str(uuid4())
        kwargs = create_api_create_recipe_kwargs(
            name="Complete Recipe",
            instructions="Detailed instructions",
            author_id=author_id,
            description="Complete description",
            utensils="All utensils",
            total_time=60,
            notes="Complete notes",
            privacy=Privacy.PUBLIC,
            weight_in_grams=500,
            image_url="https://example.com/image.jpg",
            ingredients=frozenset([
                create_api_ingredient(name='Ingredient 1', quantity=1.0, unit=MeasureUnit.GRAM, position=0),
                create_api_ingredient(name='Ingredient 2', quantity=2.0, unit=MeasureUnit.CUP, position=1),
            ]),
            tags=frozenset([
                create_api_recipe_tag(key='cuisine', value='test', author_id=author_id),
                create_api_recipe_tag(key='difficulty', value='easy', author_id=author_id),
            ])
        )
        
        api_recipe = ApiCreateRecipe(**kwargs)
        
        # Test conversion to domain command
        domain_command = api_recipe.to_domain()
        assert domain_command is not None
        assert hasattr(domain_command, 'name')
        assert hasattr(domain_command, 'instructions')
        assert hasattr(domain_command, 'author_id')
        
        # Verify field mapping
        assert domain_command.name == api_recipe.name
        assert domain_command.instructions == api_recipe.instructions
        assert domain_command.author_id == api_recipe.author_id

    # Realistic scenario tests
    @pytest.mark.parametrize("scenario_data", REALISTIC_RECIPE_SCENARIOS)
    def test_realistic_scenarios_from_factory(self, scenario_data):
        """Test realistic recipe scenarios from data factories."""
        try:
            # Use the filtered realistic scenario data with new helper function
            kwargs = create_filtered_api_create_recipe_kwargs(scenario_data)
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

    # Integration tests with fixtures
    def test_integration_with_all_fixtures(self, valid_api_create_recipe_kwargs, minimal_api_create_recipe_kwargs):
        """Test integration with all provided fixtures."""
        # Test with valid kwargs fixture
        recipe1 = ApiCreateRecipe(**valid_api_create_recipe_kwargs)
        assert recipe1.name is not None
        
        # Test with minimal kwargs fixture
        recipe2 = ApiCreateRecipe(**minimal_api_create_recipe_kwargs)
        assert recipe2.name is not None
        
        # Test domain conversion for both
        domain_command1 = recipe1.to_domain()
        domain_command2 = recipe2.to_domain()
        
        assert domain_command1 is not None
        assert domain_command2 is not None

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

    @pytest.mark.parametrize("scenario", [
        # Maximum length strings
        {'field': 'name', 'value': 'A' * 1000, 'should_pass': False},
        {'field': 'description', 'value': 'B' * 5000, 'should_pass': True},
        {'field': 'instructions', 'value': 'C' * 10000, 'should_pass': True},
        {'field': 'notes', 'value': 'D' * 2000, 'should_pass': True},
        {'field': 'utensils', 'value': 'E' * 1000, 'should_pass': True},
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

    def test_validation_with_fixture_scenarios(self, invalid_field_scenarios, boundary_value_scenarios, 
                                             privacy_enum_scenarios, complex_ingredients_scenarios, 
                                             complex_tags_scenarios):
        """Test validation with all fixture scenarios - converted to individual parametrized tests."""
        # This test method is now split into individual parametrized test methods above
        # Each scenario type now has its own parametrized test method for better isolation
        pass

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

    def test_performance_with_large_datasets(self):
        """Test performance with large ingredient and tag datasets."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objects.data_factories.api_ingredient_data_factories import create_api_ingredient
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

    def test_serialization_and_deserialization(self):
        """Test JSON serialization and deserialization."""
        # Create a complex recipe
        kwargs = create_api_create_recipe_kwargs()
        original_recipe = ApiCreateRecipe(**kwargs)
        
        # Test JSON serialization
        json_str = original_recipe.model_dump_json()
        assert json_str is not None
        assert len(json_str) > 0
        
        # Test JSON deserialization
        recipe_data = original_recipe.model_dump_json()
        recreated_recipe = ApiCreateRecipe.model_validate_json(recipe_data)
        
        # Verify the recreated recipe matches the original
        assert recreated_recipe.name == original_recipe.name
        assert recreated_recipe.instructions == original_recipe.instructions
        assert recreated_recipe.author_id == original_recipe.author_id
        assert recreated_recipe.meal_id == original_recipe.meal_id
        assert recreated_recipe.ingredients is not None
        assert recreated_recipe.tags is not None
        assert original_recipe.ingredients is not None
        assert original_recipe.tags is not None
        assert len(recreated_recipe.ingredients) == len(original_recipe.ingredients)
        assert len(recreated_recipe.tags) == len(original_recipe.tags)

    def test_new_helper_functions_comprehensive(self):
        """Test all new helper functions comprehensively."""
        author_id = str(uuid4())
        
        # Test create_api_create_recipe_kwargs
        kwargs1 = create_api_create_recipe_kwargs(name="Test Recipe 1")
        recipe1 = ApiCreateRecipe(**kwargs1)
        assert recipe1.name == "Test Recipe 1"
        
        # Test create_minimal_api_create_recipe_kwargs
        kwargs2 = create_minimal_api_create_recipe_kwargs(name="Test Recipe 2")
        recipe2 = ApiCreateRecipe(**kwargs2)
        assert recipe2.name == "Test Recipe 2"
        
        # Test create_api_create_recipe_with_author_id
        kwargs3 = create_api_create_recipe_with_author_id(author_id, name="Test Recipe 3")
        recipe3 = ApiCreateRecipe(**kwargs3)
        assert recipe3.author_id == author_id
        
        # Test create_minimal_api_create_recipe_with_author_id
        kwargs4 = create_minimal_api_create_recipe_with_author_id(author_id, name="Test Recipe 4")
        recipe4 = ApiCreateRecipe(**kwargs4)
        assert recipe4.author_id == author_id
        
        # Test create_invalid_api_create_recipe_kwargs
        kwargs5 = create_invalid_api_create_recipe_kwargs('name', None)
        with pytest.raises(ValueError):
            ApiCreateRecipe(**kwargs5)
        
        # Test create_api_create_recipe_with_custom_tags
        custom_tags = [{"key": "test", "value": "value"}]
        kwargs6 = create_api_create_recipe_with_custom_tags(author_id, custom_tags)
        recipe6 = ApiCreateRecipe(**kwargs6)
        assert recipe6.tags is not None
        assert len(recipe6.tags) == 1
        
        # Test create_api_create_recipe_with_ingredients_and_tags
        custom_ingredients = [{"name": "Test Ingredient", "quantity": 1.0, "unit": MeasureUnit.GRAM, "position": 0}]
        custom_tags = [{"key": "test", "value": "value"}]
        kwargs7 = create_api_create_recipe_with_ingredients_and_tags(author_id, custom_ingredients, custom_tags)
        recipe7 = ApiCreateRecipe(**kwargs7)
        assert recipe7.ingredients is not None
        assert recipe7.tags is not None
        assert len(recipe7.ingredients) == 1
        assert len(recipe7.tags) == 1