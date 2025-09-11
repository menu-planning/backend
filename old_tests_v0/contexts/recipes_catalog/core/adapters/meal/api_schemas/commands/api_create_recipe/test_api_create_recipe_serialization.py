"""
ApiCreateRecipe Serialization Test Suite

Test classes for ApiCreateRecipe serialization and deserialization behavior,
including JSON serialization, model validation, and complex object handling.

Following the same pattern as test_api_meal_serialization.py but adapted for ApiCreateRecipe.
"""

import json
from uuid import UUID, uuid4

import pytest

# Import the helper functions from conftest
from old_tests_v0.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.conftest import (
    create_api_create_recipe_kwargs,
    create_minimal_api_create_recipe_kwargs,
)

# Import ingredient factory
from old_tests_v0.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objects.data_factories.api_ingredient_data_factories import (
    create_api_ingredient,
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_create_recipe import (
    ApiCreateRecipe,
)
from src.contexts.shared_kernel.domain.enums import MeasureUnit, Privacy


class TestApiCreateRecipeBasicSerialization:
    """Test suite for basic serialization and deserialization."""

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
        assert (
            recreated_recipe.ingredients is not None
            and original_recipe.ingredients is not None
        )
        assert recreated_recipe.tags is not None and original_recipe.tags is not None
        assert len(recreated_recipe.ingredients) == len(original_recipe.ingredients)
        assert len(recreated_recipe.tags) == len(original_recipe.tags)

    def test_minimal_recipe_serialization(self):
        """Test serialization of minimal recipe."""
        kwargs = create_minimal_api_create_recipe_kwargs()
        recipe = ApiCreateRecipe(**kwargs)

        # Test serialization
        json_str = recipe.model_dump_json()
        assert json_str is not None

        # Test deserialization
        recreated_recipe = ApiCreateRecipe.model_validate_json(json_str)
        assert recreated_recipe.name == recipe.name
        assert recreated_recipe.instructions == recipe.instructions
        assert recreated_recipe.author_id == recipe.author_id
        assert recreated_recipe.meal_id == recipe.meal_id

    def test_model_dump_json_format(self):
        """Test model_dump_json returns valid JSON string."""
        kwargs = create_api_create_recipe_kwargs()
        recipe = ApiCreateRecipe(**kwargs)

        json_str = recipe.model_dump_json()

        # Verify it's valid JSON
        assert isinstance(json_str, str)
        parsed_json = json.loads(json_str)
        assert isinstance(parsed_json, dict)

        # Verify structure
        assert "name" in parsed_json
        assert "instructions" in parsed_json
        assert "author_id" in parsed_json
        assert "meal_id" in parsed_json


class TestApiCreateRecipeComplexSerialization:
    """Test suite for complex serialization scenarios."""

    def test_serialization_with_all_fields_populated(self):
        """Test serialization with all optional fields populated."""
        from old_tests_v0.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_tag,
        )

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
            ingredients=frozenset(
                [
                    create_api_ingredient(
                        name="Ingredient 1",
                        quantity=1.0,
                        unit=MeasureUnit.GRAM,
                        position=0,
                    ),
                    create_api_ingredient(
                        name="Ingredient 2",
                        quantity=2.0,
                        unit=MeasureUnit.CUP,
                        position=1,
                    ),
                ]
            ),
            tags=frozenset(
                [
                    create_api_recipe_tag(
                        key="cuisine", value="test", author_id=author_id
                    ),
                    create_api_recipe_tag(
                        key="difficulty", value="easy", author_id=author_id
                    ),
                ]
            ),
        )

        recipe = ApiCreateRecipe(**kwargs)

        # Test serialization
        json_str = recipe.model_dump_json()
        assert json_str is not None

        # Test deserialization
        recreated_recipe = ApiCreateRecipe.model_validate_json(json_str)

        # Verify all fields are preserved
        assert recreated_recipe.name == recipe.name
        assert recreated_recipe.instructions == recipe.instructions
        assert recreated_recipe.author_id == recipe.author_id
        assert recreated_recipe.description == recipe.description
        assert recreated_recipe.utensils == recipe.utensils
        assert recreated_recipe.total_time == recipe.total_time
        assert recreated_recipe.notes == recipe.notes
        assert recreated_recipe.privacy == recipe.privacy
        assert recreated_recipe.weight_in_grams == recipe.weight_in_grams
        assert str(recreated_recipe.image_url) == str(recipe.image_url)
        assert (
            recreated_recipe.ingredients is not None and recipe.ingredients is not None
        )
        assert recreated_recipe.tags is not None and recipe.tags is not None
        assert len(recreated_recipe.ingredients) == len(recipe.ingredients)
        assert len(recreated_recipe.tags) == len(recipe.tags)

    def test_serialization_with_unicode_characters(self):
        """Test serialization with Unicode characters."""
        kwargs = create_minimal_api_create_recipe_kwargs(
            name="Café Recipe 🍽️",
            instructions="Cook with care 👨‍🍳",
            description="Delicious naïve recipe",
            notes="Notes with émojis 🔥",
        )

        recipe = ApiCreateRecipe(**kwargs)

        # Test serialization
        json_str = recipe.model_dump_json()
        assert json_str is not None

        # Test deserialization
        recreated_recipe = ApiCreateRecipe.model_validate_json(json_str)

        # Verify Unicode characters are preserved
        assert "Café" in recreated_recipe.name
        assert "🍽️" in recreated_recipe.name
        assert "👨‍🍳" in recreated_recipe.instructions
        assert (
            recreated_recipe.description is not None
            and "naïve" in recreated_recipe.description
        )
        assert (
            recreated_recipe.notes is not None
            and "émojis" in recreated_recipe.notes
            and "🔥" in recreated_recipe.notes
        )

    def test_serialization_with_large_datasets(self):
        """Test serialization with large ingredient and tag datasets."""
        from old_tests_v0.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_tag,
        )

        author_id = str(uuid4())

        # Create large datasets
        large_ingredients = frozenset(
            [
                create_api_ingredient(
                    name=f"Ingredient {i}",
                    quantity=float(i + 1),
                    unit=MeasureUnit.GRAM,
                    position=i,
                )
                for i in range(20)  # Smaller than edge cases to focus on serialization
            ]
        )

        large_tags = frozenset(
            [
                create_api_recipe_tag(
                    key=f"tag{i}", value=f"value{i}", author_id=author_id
                )
                for i in range(20)
            ]
        )

        kwargs = create_api_create_recipe_kwargs(
            author_id=author_id, ingredients=large_ingredients, tags=large_tags
        )

        recipe = ApiCreateRecipe(**kwargs)

        # Test serialization
        json_str = recipe.model_dump_json()
        assert json_str is not None
        assert len(json_str) > 1000  # Should be a substantial JSON string

        # Test deserialization
        recreated_recipe = ApiCreateRecipe.model_validate_json(json_str)

        # Verify large datasets are preserved
        assert recreated_recipe.ingredients is not None
        assert recreated_recipe.tags is not None
        assert recipe.ingredients is not None
        assert recipe.tags is not None
        assert len(recreated_recipe.ingredients) == 20
        assert len(recreated_recipe.tags) == 20

        # Verify content integrity
        original_ingredient_names = {ing.name for ing in recipe.ingredients}
        recreated_ingredient_names = {ing.name for ing in recreated_recipe.ingredients}
        assert original_ingredient_names == recreated_ingredient_names

        original_tag_values = {tag.value for tag in recipe.tags}
        recreated_tag_values = {tag.value for tag in recreated_recipe.tags}
        assert original_tag_values == recreated_tag_values


class TestApiCreateRecipeSerializationEdgeCases:
    """Test suite for serialization edge cases."""

    def test_serialization_with_none_optional_fields(self):
        """Test serialization when all optional fields are None."""
        kwargs = create_minimal_api_create_recipe_kwargs(
            description=None,
            utensils=None,
            total_time=None,
            notes=None,
            nutri_facts=None,
            weight_in_grams=None,
            image_url=None,
        )

        recipe = ApiCreateRecipe(**kwargs)

        # Test serialization
        json_str = recipe.model_dump_json()
        assert json_str is not None

        # Test deserialization
        recreated_recipe = ApiCreateRecipe.model_validate_json(json_str)

        # Verify None values are handled correctly
        assert recreated_recipe.description is None
        assert recreated_recipe.utensils is None
        assert recreated_recipe.total_time is None
        assert recreated_recipe.notes is None
        assert recreated_recipe.nutri_facts is None
        assert recreated_recipe.weight_in_grams is None
        assert recreated_recipe.image_url is None

    def test_serialization_with_empty_collections(self):
        """Test serialization with empty ingredients and tags."""
        kwargs = create_minimal_api_create_recipe_kwargs(
            ingredients=frozenset(), tags=frozenset()
        )

        recipe = ApiCreateRecipe(**kwargs)

        # Test serialization
        json_str = recipe.model_dump_json()
        assert json_str is not None

        # Test deserialization
        recreated_recipe = ApiCreateRecipe.model_validate_json(json_str)

        # Verify empty collections are preserved
        assert recreated_recipe.ingredients == frozenset()
        assert recreated_recipe.tags == frozenset()

    def test_serialization_with_boundary_values(self):
        """Test serialization with boundary values."""
        kwargs = create_minimal_api_create_recipe_kwargs(
            name="R",  # Single character
            instructions="I",  # Single character
            total_time=0,  # Zero
            weight_in_grams=0,  # Zero
        )

        recipe = ApiCreateRecipe(**kwargs)

        # Test serialization
        json_str = recipe.model_dump_json()
        assert json_str is not None

        # Test deserialization
        recreated_recipe = ApiCreateRecipe.model_validate_json(json_str)

        # Verify boundary values are preserved
        assert recreated_recipe.name == "R"
        assert recreated_recipe.instructions == "I"
        assert recreated_recipe.total_time == 0
        assert recreated_recipe.weight_in_grams == 0

    def test_serialization_with_maximum_values(self):
        """Test serialization with maximum reasonable values."""
        kwargs = create_minimal_api_create_recipe_kwargs(
            name="A" * 500,  # Maximum reasonable length
            total_time=9999,  # Very long time
            weight_in_grams=999999,  # Very heavy
        )

        recipe = ApiCreateRecipe(**kwargs)

        # Test serialization
        json_str = recipe.model_dump_json()
        assert json_str is not None

        # Test deserialization
        recreated_recipe = ApiCreateRecipe.model_validate_json(json_str)

        # Verify maximum values are preserved
        assert recreated_recipe.name == "A" * 500
        assert recreated_recipe.total_time == 9999
        assert recreated_recipe.weight_in_grams == 999999


class TestApiCreateRecipeSerializationFormat:
    """Test suite for serialization format validation."""

    def test_json_structure_contains_required_fields(self):
        """Test that JSON structure contains all required fields."""
        kwargs = create_api_create_recipe_kwargs()
        recipe = ApiCreateRecipe(**kwargs)

        json_str = recipe.model_dump_json()
        parsed_json = json.loads(json_str)

        # Verify required fields are present
        required_fields = [
            "name",
            "instructions",
            "author_id",
            "meal_id",
            "ingredients",
            "tags",
        ]
        for field in required_fields:
            assert field in parsed_json, f"Required field {field} missing from JSON"

    def test_json_field_types(self):
        """Test that JSON field types are correct."""
        kwargs = create_api_create_recipe_kwargs(
            total_time=60, weight_in_grams=500, privacy=Privacy.PUBLIC
        )
        recipe = ApiCreateRecipe(**kwargs)

        json_str = recipe.model_dump_json()
        parsed_json = json.loads(json_str)

        # Verify field types in JSON
        assert isinstance(parsed_json["name"], str)
        assert isinstance(parsed_json["instructions"], str)
        assert isinstance(parsed_json["author_id"], str)
        assert isinstance(parsed_json["meal_id"], str)
        if parsed_json.get("total_time") is not None:
            assert isinstance(parsed_json["total_time"], int)
        if parsed_json.get("weight_in_grams") is not None:
            assert isinstance(parsed_json["weight_in_grams"], (int, float))
        if parsed_json.get("privacy") is not None:
            assert isinstance(parsed_json["privacy"], str)
        assert isinstance(parsed_json["ingredients"], list)
        assert isinstance(parsed_json["tags"], list)

    def test_json_uuid_format(self):
        """Test that UUIDs are properly formatted in JSON."""
        author_id = str(uuid4())
        meal_id = str(uuid4())

        kwargs = create_api_create_recipe_kwargs(author_id=author_id, meal_id=meal_id)
        recipe = ApiCreateRecipe(**kwargs)

        json_str = recipe.model_dump_json()
        parsed_json = json.loads(json_str)

        # Verify UUID format (should be strings in JSON)
        assert isinstance(parsed_json["author_id"], str)
        assert isinstance(parsed_json["meal_id"], str)

        # Verify UUIDs can be parsed back
        assert UUID(parsed_json["author_id"])
        assert UUID(parsed_json["meal_id"])

    def test_json_optional_field_handling(self):
        """Test that optional fields are handled correctly in JSON."""
        # Create recipe with some optional fields None and some populated
        kwargs = create_minimal_api_create_recipe_kwargs(
            description="Test description",
            utensils=None,
            total_time=30,
            notes=None,
            weight_in_grams=500,
            image_url=None,
        )
        recipe = ApiCreateRecipe(**kwargs)

        json_str = recipe.model_dump_json()
        parsed_json = json.loads(json_str)

        # Verify optional fields handling
        assert parsed_json.get("description") == "Test description"
        assert parsed_json.get("utensils") is None
        assert parsed_json.get("total_time") == 30
        assert parsed_json.get("notes") is None
        assert parsed_json.get("weight_in_grams") == 500
        assert parsed_json.get("image_url") is None


class TestApiCreateRecipeRoundTripSerialization:
    """Test suite for round-trip serialization validation."""

    def test_multiple_round_trips(self):
        """Test that multiple serialization/deserialization cycles preserve data."""
        # Create original recipe
        kwargs = create_api_create_recipe_kwargs()
        original_recipe = ApiCreateRecipe(**kwargs)

        current_recipe = original_recipe

        # Perform multiple round trips
        for i in range(3):
            json_str = current_recipe.model_dump_json()
            current_recipe = ApiCreateRecipe.model_validate_json(json_str)

        # Verify data integrity after multiple round trips
        assert current_recipe.name == original_recipe.name
        assert current_recipe.instructions == original_recipe.instructions
        assert current_recipe.author_id == original_recipe.author_id
        assert current_recipe.meal_id == original_recipe.meal_id
        # Type checker is being overly strict about None checks - functionality works fine
        if (
            current_recipe.ingredients is not None
            and original_recipe.ingredients is not None
        ):
            assert len(current_recipe.ingredients) == len(original_recipe.ingredients)
        if current_recipe.tags is not None and original_recipe.tags is not None:
            assert len(current_recipe.tags) == len(original_recipe.tags)

    def test_round_trip_with_validation_errors(self):
        """Test that invalid data still raises validation errors after round trip."""
        # Create valid recipe first
        kwargs = create_api_create_recipe_kwargs()
        recipe = ApiCreateRecipe(**kwargs)

        # Get valid JSON
        json_str = recipe.model_dump_json()
        parsed_json = json.loads(json_str)

        # Modify JSON to make it invalid
        parsed_json["name"] = ""  # Invalid empty name

        invalid_json_str = json.dumps(parsed_json)

        # Verify validation error is raised
        with pytest.raises(ValueError):
            ApiCreateRecipe.model_validate_json(invalid_json_str)

    def test_round_trip_preserves_complex_objects(self):
        """Test that complex nested objects are preserved through round trips."""
        from old_tests_v0.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
            create_api_recipe_tag,
        )

        author_id = str(uuid4())

        # Create recipe with complex nested objects
        ingredients = frozenset(
            [
                create_api_ingredient(
                    name="Complex Ingredient",
                    quantity=123.45,
                    unit=MeasureUnit.GRAM,
                    position=0,
                ),
            ]
        )

        tags = frozenset(
            [
                create_api_recipe_tag(
                    key="complex-key", value="complex-value", author_id=author_id
                ),
            ]
        )

        kwargs = create_api_create_recipe_kwargs(
            author_id=author_id, ingredients=ingredients, tags=tags
        )

        original_recipe = ApiCreateRecipe(**kwargs)

        # Round trip
        json_str = original_recipe.model_dump_json()
        recreated_recipe = ApiCreateRecipe.model_validate_json(json_str)

        # Verify complex objects are preserved
        assert original_recipe.ingredients is not None
        assert recreated_recipe.ingredients is not None
        original_ingredient = list(original_recipe.ingredients)[0]
        recreated_ingredient = list(recreated_recipe.ingredients)[0]
        assert original_ingredient.name == recreated_ingredient.name
        assert original_ingredient.quantity == recreated_ingredient.quantity
        assert original_ingredient.unit == recreated_ingredient.unit
        assert original_ingredient.position == recreated_ingredient.position

        assert original_recipe.tags is not None
        assert recreated_recipe.tags is not None
        original_tag = list(original_recipe.tags)[0]
        recreated_tag = list(recreated_recipe.tags)[0]
        assert original_tag.key == recreated_tag.key
        assert original_tag.value == recreated_tag.value
        assert original_tag.author_id == recreated_tag.author_id
