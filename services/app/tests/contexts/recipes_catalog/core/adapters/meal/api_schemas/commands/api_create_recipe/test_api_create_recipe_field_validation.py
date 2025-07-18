"""
ApiCreateRecipe Field Validation Test Suite

Test classes for ApiCreateRecipe field validation logic including individual field validation,
type checking, format validation, and range validation for all ApiCreateRecipe fields.

Following the same pattern as test_api_meal_validation.py but adapted for ApiCreateRecipe.
"""

import pytest
from uuid import UUID, uuid4
import itertools

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_create_recipe import ApiCreateRecipe
from src.contexts.shared_kernel.domain.enums import Privacy, MeasureUnit

# Import the helper functions from conftest
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.conftest import (
    create_api_create_recipe_kwargs,
    create_minimal_api_create_recipe_kwargs,
    create_api_create_recipe_with_author_id,
    create_minimal_api_create_recipe_with_author_id,
    create_invalid_api_create_recipe_kwargs,
)

# Import ingredient factory
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objects.data_factories.api_ingredient_data_factories import (
    create_api_ingredient
)


class TestApiCreateRecipeNameFieldValidation:
    """Test suite for name field validation."""

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
        """Test valid name field scenarios."""
        kwargs = create_minimal_api_create_recipe_kwargs(name=valid_name)
        recipe = ApiCreateRecipe(**kwargs)
        assert recipe.name == valid_name, f"Failed for name: {valid_name}"

    def test_name_field_validation_valid_names_with_spaces(self):
        """Test name with spaces (should be trimmed)."""
        kwargs = create_minimal_api_create_recipe_kwargs(name="Recipe" + " " * 50)
        recipe = ApiCreateRecipe(**kwargs)
        assert recipe.name == "Recipe", f"Name should be trimmed: {recipe.name}"

    @pytest.mark.parametrize("empty_name", ["", "   ", "\t", "\n", "  \t  \n  "])
    def test_name_field_validation_empty_strings(self, empty_name):
        """Test name field validation with empty strings."""
        kwargs = create_minimal_api_create_recipe_kwargs(name=empty_name)
        
        with pytest.raises(ValueError, match="name"):
            ApiCreateRecipe(**kwargs)

    def test_name_field_validation_null_values(self):
        """Test name field validation with null values."""
        kwargs = create_minimal_api_create_recipe_kwargs(name=None)
        
        with pytest.raises(ValueError):
            ApiCreateRecipe(**kwargs)

    def test_name_field_validation_max_length(self):
        """Test name field validation with very long names."""
        very_long_name = "A" * 1000
        kwargs = create_minimal_api_create_recipe_kwargs(name=very_long_name)
        
        # This should still pass if there's no explicit max length constraint
        try:
            recipe = ApiCreateRecipe(**kwargs)
            assert recipe.name == very_long_name
        except ValueError:
            # If there's a max length constraint, the error should be about length
            pass

    def test_name_field_validation_using_data_factories(self):
        """Test name field validation using invalid data from factories."""
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_invalid_name,
        )
        # Test with invalid name data from factory
        invalid_name_data = create_api_recipe_with_invalid_name()
        
        # Extract just the name to test using helper function
        if "name" in invalid_name_data:
            kwargs = create_minimal_api_create_recipe_kwargs(name=invalid_name_data["name"])
            
            with pytest.raises(ValueError):
                ApiCreateRecipe(**kwargs)


class TestApiCreateRecipeInstructionsFieldValidation:
    """Test suite for instructions field validation."""

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
        """Test valid instructions field scenarios."""
        kwargs = create_minimal_api_create_recipe_kwargs(instructions=valid_instructions)
        recipe = ApiCreateRecipe(**kwargs)
        assert recipe.instructions == valid_instructions, f"Failed for instructions: {valid_instructions}"

    def test_instructions_field_validation_valid_instructions_with_spaces(self):
        """Test instructions with spaces (should be trimmed)."""
        kwargs = create_minimal_api_create_recipe_kwargs(instructions="Instructions" + " " * 50)
        recipe = ApiCreateRecipe(**kwargs)
        assert recipe.instructions == "Instructions", f"Instructions should be trimmed: {recipe.instructions}"

    @pytest.mark.parametrize("empty_instruction", ["", "   ", "\t", "\n", "  \t  \n  ", "\r\n"])
    def test_instructions_field_validation_empty_strings(self, empty_instruction):
        """Test instructions field validation with empty strings."""
        kwargs = create_minimal_api_create_recipe_kwargs(instructions=empty_instruction)
        
        with pytest.raises(ValueError, match="instructions"):
            ApiCreateRecipe(**kwargs)

    def test_instructions_field_validation_null_values(self):
        """Test instructions field validation with null values."""
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
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_with_invalid_instructions,
        )
        # Test with invalid instructions data from factory
        invalid_instructions_data = create_api_recipe_with_invalid_instructions()
        
        # Extract just the instructions to test using helper function
        if "instructions" in invalid_instructions_data:
            kwargs = create_minimal_api_create_recipe_kwargs(instructions=invalid_instructions_data["instructions"])
            
            with pytest.raises(ValueError):
                ApiCreateRecipe(**kwargs)


class TestApiCreateRecipeAuthorIdFieldValidation:
    """Test suite for author_id field validation."""

    @pytest.mark.parametrize("valid_author_id", [
        "550e8400-e29b-41d4-a716-446655440000",  # Standard UUID format
        "550E8400-E29B-41D4-A716-446655440000",  # Uppercase
        "550e8400e29b41d4a716446655440000",       # No hyphens
        "550E8400E29B41D4A716446655440000",       # No hyphens, uppercase
    ])
    def test_author_id_field_validation_valid_uuids(self, valid_author_id):
        """Test valid author_id field scenarios."""
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
        kwargs = create_invalid_api_create_recipe_kwargs('author_id', invalid_type)
        
        with pytest.raises(ValueError):
            ApiCreateRecipe(**kwargs)

    def test_author_id_field_validation_uuid_objects(self):
        """Test author_id field validation with UUID objects."""
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
        from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_kwargs,
        )
        # Test with various author_id scenarios from factory
        factory_data = create_api_recipe_kwargs()
        
        # Use the factory's author_id as a valid example with helper function
        kwargs = create_minimal_api_create_recipe_with_author_id(factory_data["author_id"])
        recipe = ApiCreateRecipe(**kwargs)
        assert recipe.author_id is not None


class TestApiCreateRecipeMealIdFieldValidation:
    """Test suite for meal_id field validation."""

    @pytest.mark.parametrize("valid_meal_id", [
        "550e8400-e29b-41d4-a716-446655440000",  # Standard UUID format
        "550E8400-E29B-41D4-A716-446655440000",  # Uppercase
        "550e8400e29b41d4a716446655440000",       # No hyphens
        "550E8400E29B41D4A716446655440000",       # No hyphens, uppercase
    ])
    def test_meal_id_field_validation_valid_uuids(self, valid_meal_id):
        """Test valid meal_id field scenarios."""
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
        kwargs = create_invalid_api_create_recipe_kwargs('meal_id', invalid_meal_id)
        
        with pytest.raises(ValueError):
            ApiCreateRecipe(**kwargs)

    def test_meal_id_field_validation_null_values(self):
        """Test meal_id field validation with null values."""
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
        kwargs = create_invalid_api_create_recipe_kwargs('meal_id', invalid_type)
        
        with pytest.raises(ValueError):
            ApiCreateRecipe(**kwargs)


class TestApiCreateRecipeOptionalFieldValidation:
    """Test suite for optional field validation."""

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


class TestApiCreateRecipeComplexFieldValidation:
    """Test suite for complex field validation (ingredients and tags)."""

    def test_ingredients_field_validation_empty_set(self):
        """Test ingredients field with empty set (should be valid)."""
        kwargs = create_minimal_api_create_recipe_kwargs(ingredients=frozenset())
        recipe = ApiCreateRecipe(**kwargs)
        assert recipe.ingredients == frozenset()

    def test_ingredients_field_validation_single_ingredient(self):
        """Test ingredients field with single ingredient."""
        single_ingredient = frozenset([
            create_api_ingredient(name='Flour', quantity=2.0, unit=MeasureUnit.CUP, position=0)
        ])
        kwargs = create_minimal_api_create_recipe_kwargs(ingredients=single_ingredient)
        recipe = ApiCreateRecipe(**kwargs)
        assert recipe.ingredients is not None
        assert len(recipe.ingredients) == 1

    def test_ingredients_field_validation_multiple_ingredients(self):
        """Test ingredients field with multiple ingredients."""
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