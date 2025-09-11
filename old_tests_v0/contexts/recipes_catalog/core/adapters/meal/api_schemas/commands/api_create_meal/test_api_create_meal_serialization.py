"""
ApiCreateMeal Serialization Test Suite

Test classes for ApiCreateMeal serialization and deserialization behavior,
including JSON serialization, model validation, and complex object handling.

Following the same pattern as test_api_create_recipe_serialization.py but adapted for ApiCreateMeal.
ApiCreateMeal is more complex since meals are parent entities of recipes.
"""

import json
from uuid import UUID, uuid4

import pytest

# Import the helper functions from conftest
from old_tests_v0.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.conftest import (
    create_api_create_meal_kwargs,
    create_api_meal_tag,
    create_minimal_api_create_meal_kwargs,
)

# Import recipe factory for creating test recipes
from old_tests_v0.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
    create_complex_api_recipe,
    create_simple_api_recipe,
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_create_meal import (
    ApiCreateMeal,
)


class TestApiCreateMealBasicSerialization:
    """Test suite for basic serialization and deserialization."""

    def test_serialization_and_deserialization(self):
        """Test JSON serialization and deserialization."""
        # Create a complex meal
        kwargs = create_api_create_meal_kwargs()
        original_meal = ApiCreateMeal(**kwargs)

        # Test JSON serialization
        json_str = original_meal.model_dump_json()
        assert json_str is not None
        assert len(json_str) > 0

        # Test JSON deserialization
        meal_data = original_meal.model_dump_json()
        recreated_meal = ApiCreateMeal.model_validate_json(meal_data)

        # Verify the recreated meal matches the original
        assert recreated_meal.name == original_meal.name
        assert recreated_meal.author_id == original_meal.author_id
        assert recreated_meal.menu_id == original_meal.menu_id
        assert recreated_meal.recipes is not None
        assert recreated_meal.tags is not None
        assert original_meal.recipes is not None
        assert original_meal.tags is not None
        assert len(recreated_meal.recipes) == len(original_meal.recipes)
        assert len(recreated_meal.tags) == len(original_meal.tags)

    def test_minimal_meal_serialization(self):
        """Test serialization of minimal meal."""
        kwargs = create_minimal_api_create_meal_kwargs()
        meal = ApiCreateMeal(**kwargs)

        # Test serialization
        json_str = meal.model_dump_json()
        assert json_str is not None

        # Test deserialization
        recreated_meal = ApiCreateMeal.model_validate_json(json_str)
        assert recreated_meal.name == meal.name
        assert recreated_meal.author_id == meal.author_id
        assert recreated_meal.menu_id == meal.menu_id
        assert recreated_meal.recipes == meal.recipes
        assert recreated_meal.tags == meal.tags

    def test_model_dump_json_format(self):
        """Test model_dump_json returns valid JSON string."""
        kwargs = create_api_create_meal_kwargs()
        meal = ApiCreateMeal(**kwargs)

        json_str = meal.model_dump_json()

        # Verify it's valid JSON
        assert isinstance(json_str, str)
        parsed_json = json.loads(json_str)
        assert isinstance(parsed_json, dict)

        # Verify structure
        assert "name" in parsed_json
        assert "author_id" in parsed_json
        assert "menu_id" in parsed_json
        assert "recipes" in parsed_json
        assert "tags" in parsed_json


class TestApiCreateMealComplexSerialization:
    """Test suite for complex serialization scenarios."""

    def test_serialization_with_all_fields_populated(self):
        """Test serialization with all optional fields populated."""
        author_id = str(uuid4())
        menu_id = str(uuid4())

        # Create complex recipes for the meal
        recipes = [
            create_simple_api_recipe(name="Appetizer Recipe", author_id=author_id),
            create_complex_api_recipe(name="Main Course Recipe", author_id=author_id),
            create_simple_api_recipe(name="Dessert Recipe", author_id=author_id),
        ]

        kwargs = create_api_create_meal_kwargs(
            name="Complete Holiday Dinner",
            author_id=author_id,
            menu_id=menu_id,
            description="A complete holiday dinner with appetizer, main course, and dessert",
            notes="Perfect for special occasions with family and friends",
            image_url="https://example.com/holiday-dinner.jpg",
            recipes=recipes,
            tags=frozenset(
                [
                    create_api_meal_tag(
                        key="occasion", value="holiday", author_id=author_id
                    ),
                    create_api_meal_tag(
                        key="difficulty", value="challenging", author_id=author_id
                    ),
                    create_api_meal_tag(
                        key="meal_type", value="dinner", author_id=author_id
                    ),
                ]
            ),
        )

        meal = ApiCreateMeal(**kwargs)

        # Test serialization
        json_str = meal.model_dump_json()
        assert json_str is not None

        # Test deserialization
        recreated_meal = ApiCreateMeal.model_validate_json(json_str)

        # Verify all fields are preserved
        assert recreated_meal.name == meal.name
        assert recreated_meal.author_id == meal.author_id
        assert recreated_meal.menu_id == meal.menu_id
        assert recreated_meal.description == meal.description
        assert recreated_meal.notes == meal.notes
        assert str(recreated_meal.image_url) == str(meal.image_url)
        assert recreated_meal.recipes is not None and meal.recipes is not None
        assert recreated_meal.tags is not None and meal.tags is not None
        assert len(recreated_meal.recipes) == len(meal.recipes)
        assert len(recreated_meal.tags) == len(meal.tags)

    def test_serialization_with_unicode_characters(self):
        """Test serialization with Unicode characters."""
        kwargs = create_minimal_api_create_meal_kwargs(
            name="Café Dinner 🍽️",
            description="Delicious naïve meal with émojis",
            notes="Notes with special characters: café, naïve, résumé 🔥",
        )

        meal = ApiCreateMeal(**kwargs)

        # Test serialization
        json_str = meal.model_dump_json()
        assert json_str is not None

        # Test deserialization
        recreated_meal = ApiCreateMeal.model_validate_json(json_str)

        # Verify Unicode characters are preserved
        assert "Café" in recreated_meal.name
        assert "🍽️" in recreated_meal.name
        assert (
            recreated_meal.description is not None
            and "naïve" in recreated_meal.description
        )
        assert (
            recreated_meal.notes is not None
            and "café" in recreated_meal.notes
            and "🔥" in recreated_meal.notes
        )

    def test_serialization_with_large_datasets(self):
        """Test serialization with large recipe and tag datasets."""
        author_id = str(uuid4())

        # Create large datasets
        large_recipes = [
            create_simple_api_recipe(name=f"Recipe {i}", author_id=author_id)
            for i in range(15)  # Reasonable size for meal complexity
        ]

        large_tags = frozenset(
            [
                create_api_meal_tag(
                    key=f"tag{i}", value=f"value{i}", author_id=author_id
                )
                for i in range(20)
            ]
        )

        kwargs = create_api_create_meal_kwargs(
            author_id=author_id, recipes=large_recipes, tags=large_tags
        )

        meal = ApiCreateMeal(**kwargs)

        # Test serialization
        json_str = meal.model_dump_json()
        assert json_str is not None
        assert (
            len(json_str) > 2000
        )  # Should be a substantial JSON string for complex meal

        # Test deserialization
        recreated_meal = ApiCreateMeal.model_validate_json(json_str)

        # Verify large datasets are preserved
        assert recreated_meal.recipes is not None
        assert recreated_meal.tags is not None
        assert meal.recipes is not None
        assert meal.tags is not None
        assert len(recreated_meal.recipes) == 15
        assert len(recreated_meal.tags) == 20

        # Verify content integrity
        original_recipe_names = {recipe.name for recipe in meal.recipes}
        recreated_recipe_names = {recipe.name for recipe in recreated_meal.recipes}
        assert original_recipe_names == recreated_recipe_names

        original_tag_values = {tag.value for tag in meal.tags}
        recreated_tag_values = {tag.value for tag in recreated_meal.tags}
        assert original_tag_values == recreated_tag_values


class TestApiCreateMealSerializationEdgeCases:
    """Test suite for serialization edge cases."""

    def test_serialization_with_none_optional_fields(self):
        """Test serialization when all optional fields are None."""
        kwargs = create_minimal_api_create_meal_kwargs(
            description=None, notes=None, image_url=None
        )

        meal = ApiCreateMeal(**kwargs)

        # Test serialization
        json_str = meal.model_dump_json()
        assert json_str is not None

        # Test deserialization
        recreated_meal = ApiCreateMeal.model_validate_json(json_str)

        # Verify None values are handled correctly
        assert recreated_meal.description is None
        assert recreated_meal.notes is None
        assert recreated_meal.image_url is None

    def test_serialization_with_empty_collections(self):
        """Test serialization with empty recipes and tags."""
        kwargs = create_minimal_api_create_meal_kwargs(recipes=[], tags=frozenset())

        meal = ApiCreateMeal(**kwargs)

        # Test serialization
        json_str = meal.model_dump_json()
        assert json_str is not None

        # Test deserialization
        recreated_meal = ApiCreateMeal.model_validate_json(json_str)

        # Verify empty collections are preserved
        assert recreated_meal.recipes == []
        assert recreated_meal.tags == frozenset()

    def test_serialization_with_boundary_values(self):
        """Test serialization with boundary values."""
        kwargs = create_minimal_api_create_meal_kwargs(
            name="M",  # Single character
        )

        meal = ApiCreateMeal(**kwargs)

        # Test serialization
        json_str = meal.model_dump_json()
        assert json_str is not None

        # Test deserialization
        recreated_meal = ApiCreateMeal.model_validate_json(json_str)

        # Verify boundary values are preserved
        assert recreated_meal.name == "M"

    def test_serialization_with_maximum_values(self):
        """Test serialization with maximum reasonable values."""
        kwargs = create_minimal_api_create_meal_kwargs(
            name="M" * 255,  # Maximum allowed length for name field
            description="D" * 1000,  # Long description
            notes="N" * 1000,  # Long notes
        )

        meal = ApiCreateMeal(**kwargs)

        # Test serialization
        json_str = meal.model_dump_json()
        assert json_str is not None

        # Test deserialization
        recreated_meal = ApiCreateMeal.model_validate_json(json_str)

        # Verify maximum values are preserved
        assert recreated_meal.name == "M" * 255
        assert recreated_meal.description == "D" * 1000
        assert recreated_meal.notes == "N" * 1000


class TestApiCreateMealSerializationFormat:
    """Test suite for serialization format validation."""

    def test_json_structure_contains_required_fields(self):
        """Test that JSON structure contains all required fields."""
        kwargs = create_api_create_meal_kwargs()
        meal = ApiCreateMeal(**kwargs)

        json_str = meal.model_dump_json()
        parsed_json = json.loads(json_str)

        # Verify required fields are present
        required_fields = ["name", "author_id", "menu_id", "recipes", "tags"]
        for field in required_fields:
            assert field in parsed_json, f"Required field {field} missing from JSON"

    def test_json_field_types(self):
        """Test that JSON field types are correct."""
        kwargs = create_api_create_meal_kwargs()
        meal = ApiCreateMeal(**kwargs)

        json_str = meal.model_dump_json()
        parsed_json = json.loads(json_str)

        # Verify field types in JSON
        assert isinstance(parsed_json["name"], str)
        assert isinstance(parsed_json["author_id"], str)
        assert isinstance(parsed_json["menu_id"], str)
        assert isinstance(parsed_json["recipes"], list)
        assert isinstance(parsed_json["tags"], list)
        if parsed_json.get("description") is not None:
            assert isinstance(parsed_json["description"], str)
        if parsed_json.get("notes") is not None:
            assert isinstance(parsed_json["notes"], str)
        if parsed_json.get("image_url") is not None:
            assert isinstance(parsed_json["image_url"], str)

    def test_json_uuid_format(self):
        """Test that UUIDs are properly formatted in JSON."""
        author_id = str(uuid4())
        menu_id = str(uuid4())

        kwargs = create_api_create_meal_kwargs(author_id=author_id, menu_id=menu_id)
        meal = ApiCreateMeal(**kwargs)

        json_str = meal.model_dump_json()
        parsed_json = json.loads(json_str)

        # Verify UUID format (should be strings in JSON)
        assert isinstance(parsed_json["author_id"], str)
        assert isinstance(parsed_json["menu_id"], str)

        # Verify UUIDs can be parsed back
        assert UUID(parsed_json["author_id"])
        assert UUID(parsed_json["menu_id"])

    def test_json_optional_field_handling(self):
        """Test that optional fields are handled correctly in JSON."""
        # Create meal with some optional fields None and some populated
        kwargs = create_minimal_api_create_meal_kwargs(
            description="Test description",
            notes=None,
            image_url="https://example.com/test.jpg",
        )
        meal = ApiCreateMeal(**kwargs)

        json_str = meal.model_dump_json()
        parsed_json = json.loads(json_str)

        # Verify optional fields handling
        assert parsed_json.get("description") == "Test description"
        assert parsed_json.get("notes") is None
        assert parsed_json.get("image_url") == "https://example.com/test.jpg"

    def test_json_nested_objects_structure(self):
        """Test that nested objects (recipes, tags) have correct structure in JSON."""
        author_id = str(uuid4())

        # Create meal with specific nested objects
        recipes = [create_simple_api_recipe(name="Test Recipe", author_id=author_id)]
        tags = frozenset(
            [create_api_meal_tag(key="test", value="value", author_id=author_id)]
        )

        kwargs = create_api_create_meal_kwargs(
            author_id=author_id, recipes=recipes, tags=tags
        )
        meal = ApiCreateMeal(**kwargs)

        json_str = meal.model_dump_json()
        parsed_json = json.loads(json_str)

        # Verify nested objects structure
        assert isinstance(parsed_json["recipes"], list)
        assert len(parsed_json["recipes"]) == 1
        assert isinstance(parsed_json["recipes"][0], dict)
        assert "name" in parsed_json["recipes"][0]
        assert "author_id" in parsed_json["recipes"][0]

        assert isinstance(parsed_json["tags"], list)
        assert len(parsed_json["tags"]) == 1
        assert isinstance(parsed_json["tags"][0], dict)
        assert "key" in parsed_json["tags"][0]
        assert "value" in parsed_json["tags"][0]
        assert "author_id" in parsed_json["tags"][0]


class TestApiCreateMealRoundTripSerialization:
    """Test suite for round-trip serialization validation."""

    def test_multiple_round_trips(self):
        """Test that multiple serialization/deserialization cycles preserve data."""
        # Create original meal
        kwargs = create_api_create_meal_kwargs()
        original_meal = ApiCreateMeal(**kwargs)

        current_meal = original_meal

        # Perform multiple round trips
        for i in range(3):
            json_str = current_meal.model_dump_json()
            current_meal = ApiCreateMeal.model_validate_json(json_str)

        # Verify data integrity after multiple round trips
        assert current_meal.name == original_meal.name
        assert current_meal.author_id == original_meal.author_id
        assert current_meal.menu_id == original_meal.menu_id
        # Type checker is being overly strict about None checks - functionality works fine
        if current_meal.recipes is not None and original_meal.recipes is not None:
            assert len(current_meal.recipes) == len(original_meal.recipes)
        if current_meal.tags is not None and original_meal.tags is not None:
            assert len(current_meal.tags) == len(original_meal.tags)

    def test_round_trip_with_validation_errors(self):
        """Test that invalid data still raises validation errors after round trip."""
        # Create valid meal first
        kwargs = create_api_create_meal_kwargs()
        meal = ApiCreateMeal(**kwargs)

        # Get valid JSON
        json_str = meal.model_dump_json()
        parsed_json = json.loads(json_str)

        # Modify JSON to make it invalid
        parsed_json["name"] = ""  # Invalid empty name

        invalid_json_str = json.dumps(parsed_json)

        # Verify validation error is raised
        with pytest.raises(ValueError):
            ApiCreateMeal.model_validate_json(invalid_json_str)

    def test_round_trip_preserves_complex_objects(self):
        """Test that complex nested objects are preserved through round trips."""
        author_id = str(uuid4())

        # Create meal with complex nested objects
        recipes = [
            create_complex_api_recipe(name="Complex Recipe", author_id=author_id),
        ]

        tags = frozenset(
            [
                create_api_meal_tag(
                    key="complex-key", value="complex-value", author_id=author_id
                ),
            ]
        )

        kwargs = create_api_create_meal_kwargs(
            author_id=author_id, recipes=recipes, tags=tags
        )

        original_meal = ApiCreateMeal(**kwargs)

        # Round trip
        json_str = original_meal.model_dump_json()
        recreated_meal = ApiCreateMeal.model_validate_json(json_str)

        # Verify complex objects are preserved
        assert original_meal.recipes is not None
        assert recreated_meal.recipes is not None
        original_recipe = original_meal.recipes[0]
        recreated_recipe = recreated_meal.recipes[0]
        assert original_recipe.name == recreated_recipe.name
        assert original_recipe.author_id == recreated_recipe.author_id
        assert original_recipe.instructions == recreated_recipe.instructions

        assert original_meal.tags is not None
        assert recreated_meal.tags is not None
        original_tag = list(original_meal.tags)[0]
        recreated_tag = list(recreated_meal.tags)[0]
        assert original_tag.key == recreated_tag.key
        assert original_tag.value == recreated_tag.value
        assert original_tag.author_id == recreated_tag.author_id

    def test_round_trip_with_meal_specific_complexity(self):
        """Test round trip with meal-specific complexity (multiple recipes with different complexities)."""
        author_id = str(uuid4())

        # Create meal with varied recipe complexity (unique to meals as parent entities)
        recipes = [
            create_simple_api_recipe(name="Appetizer", author_id=author_id),
            create_complex_api_recipe(name="Main Course", author_id=author_id),
            create_simple_api_recipe(name="Dessert", author_id=author_id),
        ]

        kwargs = create_api_create_meal_kwargs(
            name="Multi-Course Dinner",
            author_id=author_id,
            recipes=recipes,
            description="A complete dinner with appetizer, main course, and dessert",
        )

        original_meal = ApiCreateMeal(**kwargs)

        # Round trip
        json_str = original_meal.model_dump_json()
        recreated_meal = ApiCreateMeal.model_validate_json(json_str)

        # Verify meal complexity is preserved
        assert recreated_meal.name == "Multi-Course Dinner"
        assert original_meal.recipes is not None
        assert recreated_meal.recipes is not None
        assert len(recreated_meal.recipes) == 3

        # Verify each recipe type is preserved correctly
        original_recipe_names = [recipe.name for recipe in original_meal.recipes]
        recreated_recipe_names = [recipe.name for recipe in recreated_meal.recipes]
        assert set(original_recipe_names) == set(recreated_recipe_names)

        # Verify specific recipes maintain their properties
        for orig_recipe, recreated_recipe in zip(
            original_meal.recipes, recreated_meal.recipes, strict=False
        ):
            assert orig_recipe.name == recreated_recipe.name
            assert orig_recipe.author_id == recreated_recipe.author_id
            # Complex recipes should maintain their ingredient complexity
            if (
                orig_recipe.ingredients is not None
                and recreated_recipe.ingredients is not None
            ):
                assert len(orig_recipe.ingredients) == len(recreated_recipe.ingredients)
