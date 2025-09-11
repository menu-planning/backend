"""
Test suite for ApiUpdateRecipe.from_api_recipe() factory method.
Tests the conversion of ApiRecipe instances to ApiUpdateRecipe instances.
"""

import pytest

# Import existing data factories
from old_tests_v0.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
    REALISTIC_RECIPE_SCENARIOS,
    create_api_recipe,
    create_api_recipe_kwargs,
    create_api_recipe_with_incorrect_averages,
    create_api_recipe_with_max_fields,
    create_complex_api_recipe,
    create_dessert_api_recipe,
    create_high_protein_api_recipe,
    create_minimal_api_recipe,
    create_quick_api_recipe,
    create_recipe_collection,
    create_simple_api_recipe,
    create_vegetarian_api_recipe,
)
from pydantic import HttpUrl
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_update_recipe import (
    ApiAttributesToUpdateOnRecipe,
    ApiUpdateRecipe,
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_ingredient import (
    ApiIngredient,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import (
    ApiTag,
)


class TestApiUpdateRecipeFromApiRecipe:
    """Test suite for ApiUpdateRecipe.from_api_recipe() factory method."""

    def test_factory_method_exists(self):
        """Test that the from_api_recipe factory method exists."""
        assert hasattr(ApiUpdateRecipe, "from_api_recipe")
        assert callable(ApiUpdateRecipe.from_api_recipe)

    def test_factory_method_returns_api_update_recipe(self):
        """Test that factory method returns ApiUpdateRecipe instance."""
        api_recipe = create_simple_api_recipe()
        update_recipe = ApiUpdateRecipe.from_api_recipe(api_recipe)

        assert isinstance(update_recipe, ApiUpdateRecipe)
        assert isinstance(update_recipe.updates, ApiAttributesToUpdateOnRecipe)
        assert update_recipe.recipe_id == api_recipe.id

    def test_simple_recipe_conversion(self):
        """Test factory method with simple recipe configuration."""
        # Create simple recipe with basic fields
        simple_recipe = create_simple_api_recipe()

        # Convert to update recipe
        update_recipe = ApiUpdateRecipe.from_api_recipe(simple_recipe)

        # Verify basic structure
        assert update_recipe.recipe_id == simple_recipe.id
        assert update_recipe.updates.name == simple_recipe.name
        assert update_recipe.updates.description == simple_recipe.description
        assert update_recipe.updates.instructions == simple_recipe.instructions
        assert update_recipe.updates.notes == simple_recipe.notes
        assert update_recipe.updates.utensils == simple_recipe.utensils
        assert update_recipe.updates.total_time == simple_recipe.total_time
        assert update_recipe.updates.weight_in_grams == simple_recipe.weight_in_grams
        assert update_recipe.updates.privacy == simple_recipe.privacy
        # image_url should be preserved as HttpUrl
        assert update_recipe.updates.image_url == simple_recipe.image_url

        # Verify complex fields
        if simple_recipe.nutri_facts:
            assert update_recipe.updates.nutri_facts is not None
            assert (
                update_recipe.updates.nutri_facts.calories
                == simple_recipe.nutri_facts.calories
            )
        else:
            assert update_recipe.updates.nutri_facts is None

        # Verify collections
        assert simple_recipe.ingredients is not None
        assert simple_recipe.tags is not None
        assert update_recipe.updates.ingredients is not None
        assert update_recipe.updates.tags is not None
        assert len(update_recipe.updates.ingredients) == len(simple_recipe.ingredients)
        assert len(update_recipe.updates.tags) == len(simple_recipe.tags)

        # Verify ingredients mapping
        for ingredient in update_recipe.updates.ingredients:
            assert any(ing.name == ingredient.name for ing in simple_recipe.ingredients)
            assert any(
                ing.quantity == ingredient.quantity for ing in simple_recipe.ingredients
            )

        # Verify tags mapping
        original_tags = {
            (tag.key, tag.value, tag.author_id) for tag in simple_recipe.tags
        }
        update_tags = {
            (tag.key, tag.value, tag.author_id) for tag in update_recipe.updates.tags
        }
        assert original_tags == update_tags

    def test_minimal_recipe_conversion(self):
        """Test factory method with minimal recipe configuration."""
        # Create recipe with only required fields
        minimal_recipe = create_minimal_api_recipe()

        # Convert to update recipe
        update_recipe = ApiUpdateRecipe.from_api_recipe(minimal_recipe)

        # Verify required fields
        assert update_recipe.recipe_id == minimal_recipe.id
        assert update_recipe.updates.name == minimal_recipe.name
        assert update_recipe.updates.instructions == minimal_recipe.instructions

        # Verify optional fields are properly handled
        assert update_recipe.updates.description == minimal_recipe.description
        assert update_recipe.updates.notes == minimal_recipe.notes
        assert update_recipe.updates.utensils == minimal_recipe.utensils
        assert update_recipe.updates.total_time == minimal_recipe.total_time
        assert update_recipe.updates.weight_in_grams == minimal_recipe.weight_in_grams
        assert update_recipe.updates.image_url == minimal_recipe.image_url
        assert update_recipe.updates.privacy == minimal_recipe.privacy
        assert update_recipe.updates.nutri_facts == minimal_recipe.nutri_facts

        # Verify collections
        assert minimal_recipe.ingredients is not None
        assert minimal_recipe.tags is not None
        assert update_recipe.updates.ingredients is not None
        assert update_recipe.updates.tags is not None
        assert len(update_recipe.updates.ingredients) == len(minimal_recipe.ingredients)
        assert len(update_recipe.updates.tags) == len(minimal_recipe.tags)

    def test_complex_recipe_conversion(self):
        """Test factory method with complex recipe configuration."""
        # Create complex recipe with multiple ingredients and tags
        complex_recipe = create_complex_api_recipe()

        # Convert to update recipe
        update_recipe = ApiUpdateRecipe.from_api_recipe(complex_recipe)

        # Verify basic structure
        assert update_recipe.recipe_id == complex_recipe.id
        assert update_recipe.updates.name == complex_recipe.name
        assert update_recipe.updates.description == complex_recipe.description
        assert update_recipe.updates.instructions == complex_recipe.instructions
        assert update_recipe.updates.notes == complex_recipe.notes
        assert update_recipe.updates.utensils == complex_recipe.utensils
        assert update_recipe.updates.total_time == complex_recipe.total_time
        assert update_recipe.updates.weight_in_grams == complex_recipe.weight_in_grams
        assert update_recipe.updates.privacy == complex_recipe.privacy
        assert update_recipe.updates.image_url == complex_recipe.image_url

        # Verify nutritional facts
        if complex_recipe.nutri_facts:
            assert update_recipe.updates.nutri_facts is not None
            assert (
                update_recipe.updates.nutri_facts.calories
                == complex_recipe.nutri_facts.calories
            )
            assert (
                update_recipe.updates.nutri_facts.protein
                == complex_recipe.nutri_facts.protein
            )

        # Verify complex collections
        assert complex_recipe.ingredients is not None
        assert complex_recipe.tags is not None
        assert update_recipe.updates.ingredients is not None
        assert update_recipe.updates.tags is not None
        assert len(update_recipe.updates.ingredients) == len(complex_recipe.ingredients)
        assert len(update_recipe.updates.tags) == len(complex_recipe.tags)

        # Verify all ingredients are correctly mapped
        original_ingredients = {
            (ing.name, ing.quantity, ing.unit) for ing in complex_recipe.ingredients
        }
        update_ingredients = {
            (ing.name, ing.quantity, ing.unit)
            for ing in update_recipe.updates.ingredients
        }
        assert original_ingredients == update_ingredients

        # Verify all tags are correctly mapped
        original_tags = {
            (tag.key, tag.value, tag.author_id) for tag in complex_recipe.tags
        }
        update_tags = {
            (tag.key, tag.value, tag.author_id) for tag in update_recipe.updates.tags
        }
        assert original_tags == update_tags

    def test_recipe_with_max_fields_conversion(self):
        """Test factory method with maximum field configuration."""
        # Create recipe with maximum fields
        max_fields_recipe = create_api_recipe_with_max_fields()

        # Convert to update recipe
        update_recipe = ApiUpdateRecipe.from_api_recipe(max_fields_recipe)

        # Verify basic structure
        assert update_recipe.recipe_id == max_fields_recipe.id
        assert update_recipe.updates.name == max_fields_recipe.name

        # Verify all fields are properly handled
        assert update_recipe.updates.description == max_fields_recipe.description
        assert update_recipe.updates.instructions == max_fields_recipe.instructions
        assert update_recipe.updates.notes == max_fields_recipe.notes
        assert update_recipe.updates.utensils == max_fields_recipe.utensils
        assert update_recipe.updates.total_time == max_fields_recipe.total_time
        assert (
            update_recipe.updates.weight_in_grams == max_fields_recipe.weight_in_grams
        )
        assert update_recipe.updates.privacy == max_fields_recipe.privacy
        assert update_recipe.updates.image_url == max_fields_recipe.image_url

        # Verify nutritional facts with all fields
        if max_fields_recipe.nutri_facts:
            assert update_recipe.updates.nutri_facts is not None
            assert (
                update_recipe.updates.nutri_facts.calories
                == max_fields_recipe.nutri_facts.calories
            )
            assert (
                update_recipe.updates.nutri_facts.protein
                == max_fields_recipe.nutri_facts.protein
            )
            assert (
                update_recipe.updates.nutri_facts.carbohydrate
                == max_fields_recipe.nutri_facts.carbohydrate
            )
            assert (
                update_recipe.updates.nutri_facts.total_fat
                == max_fields_recipe.nutri_facts.total_fat
            )

        # Verify large collections handling
        assert max_fields_recipe.ingredients is not None
        assert max_fields_recipe.tags is not None
        assert update_recipe.updates.ingredients is not None
        assert update_recipe.updates.tags is not None
        assert len(update_recipe.updates.ingredients) == len(
            max_fields_recipe.ingredients
        )
        assert len(update_recipe.updates.tags) == len(max_fields_recipe.tags)

    def test_recipe_with_incorrect_averages_conversion(self):
        """Test factory method with recipes having incorrect computed averages."""
        # Create recipe with potentially incorrect computed properties
        recipe_with_computed = create_api_recipe_with_incorrect_averages()

        # Convert to update recipe
        update_recipe = ApiUpdateRecipe.from_api_recipe(recipe_with_computed)

        # Verify basic structure
        assert update_recipe.recipe_id == recipe_with_computed.id
        assert update_recipe.updates.name == recipe_with_computed.name

        # Verify all fields are properly mapped regardless of computed property state
        assert update_recipe.updates.description == recipe_with_computed.description
        assert update_recipe.updates.instructions == recipe_with_computed.instructions
        assert update_recipe.updates.notes == recipe_with_computed.notes
        assert update_recipe.updates.utensils == recipe_with_computed.utensils
        assert update_recipe.updates.total_time == recipe_with_computed.total_time
        assert (
            update_recipe.updates.weight_in_grams
            == recipe_with_computed.weight_in_grams
        )
        assert update_recipe.updates.privacy == recipe_with_computed.privacy
        assert update_recipe.updates.image_url == recipe_with_computed.image_url
        assert update_recipe.updates.nutri_facts == recipe_with_computed.nutri_facts

        # Verify collections are handled correctly
        assert recipe_with_computed.ingredients is not None
        assert recipe_with_computed.tags is not None
        assert update_recipe.updates.ingredients is not None
        assert update_recipe.updates.tags is not None
        assert len(update_recipe.updates.ingredients) == len(
            recipe_with_computed.ingredients
        )
        assert len(update_recipe.updates.tags) == len(recipe_with_computed.tags)

    def test_field_mapping_accuracy_all_fields(self):
        """Test that all ApiRecipe fields correctly map to ApiUpdateRecipe."""
        # Create recipe with all possible field combinations
        recipe_kwargs = create_api_recipe_kwargs(
            name="Test Recipe Field Mapping",
            description="Comprehensive field mapping test",
            instructions="Test all field mappings thoroughly",
            notes="Testing all field mappings",
            utensils="Various utensils for testing",
            total_time=45,
            weight_in_grams=500,
            image_url="https://example.com/recipe-image.jpg",
        )

        # Create the recipe
        test_recipe = create_api_recipe(**recipe_kwargs)

        # Convert to update recipe
        update_recipe = ApiUpdateRecipe.from_api_recipe(test_recipe)

        # Verify all scalar fields are correctly mapped
        assert update_recipe.recipe_id == test_recipe.id
        assert update_recipe.updates.name == test_recipe.name
        assert update_recipe.updates.description == test_recipe.description
        assert update_recipe.updates.instructions == test_recipe.instructions
        assert update_recipe.updates.notes == test_recipe.notes
        assert update_recipe.updates.utensils == test_recipe.utensils
        assert update_recipe.updates.total_time == test_recipe.total_time
        assert update_recipe.updates.weight_in_grams == test_recipe.weight_in_grams
        assert update_recipe.updates.privacy == test_recipe.privacy
        assert update_recipe.updates.image_url == test_recipe.image_url
        assert update_recipe.updates.nutri_facts == test_recipe.nutri_facts

        # Verify collection fields are correctly mapped
        assert update_recipe.updates.ingredients == test_recipe.ingredients
        assert update_recipe.updates.tags == test_recipe.tags

    @pytest.mark.parametrize(
        "field_combination",
        [
            {
                "name": "Recipe 1",
                "description": "Test 1",
                "notes": None,
                "total_time": 30,
            },
            {
                "name": "Recipe 2",
                "description": None,
                "notes": "Test 2",
                "total_time": None,
            },
            {
                "name": "Recipe 3",
                "description": "Test 3",
                "notes": "Test 3",
                "total_time": 15,
            },
            {
                "name": "Recipe 4",
                "description": None,
                "notes": None,
                "total_time": None,
            },
        ],
    )
    def test_field_mapping_with_various_combinations(self, field_combination):
        """Test field mapping with various field combinations."""
        # Create recipe with specific field combination
        test_recipe = create_api_recipe(**field_combination)

        # Convert to update recipe
        update_recipe = ApiUpdateRecipe.from_api_recipe(test_recipe)

        # Verify all fields are correctly mapped
        assert update_recipe.recipe_id == test_recipe.id
        assert update_recipe.updates.name == test_recipe.name
        assert update_recipe.updates.description == test_recipe.description
        assert update_recipe.updates.instructions == test_recipe.instructions
        assert update_recipe.updates.notes == test_recipe.notes
        assert update_recipe.updates.total_time == test_recipe.total_time

        # Verify collections maintain their structure
        assert test_recipe.ingredients is not None
        assert test_recipe.tags is not None
        assert update_recipe.updates.ingredients is not None
        assert update_recipe.updates.tags is not None
        assert len(update_recipe.updates.ingredients) == len(test_recipe.ingredients)
        assert len(update_recipe.updates.tags) == len(test_recipe.tags)

    def test_field_mapping_preserves_data_types(self):
        """Test that field mapping preserves all data types correctly."""
        # Create recipe with diverse data types
        test_recipe = create_api_recipe()

        # Convert to update recipe
        update_recipe = ApiUpdateRecipe.from_api_recipe(test_recipe)

        # Verify data types are preserved
        assert type(update_recipe.recipe_id) == type(test_recipe.id)
        assert type(update_recipe.updates.name) == type(test_recipe.name)
        assert type(update_recipe.updates.instructions) == type(
            test_recipe.instructions
        )

        # Verify optional fields maintain their types (or None)
        if test_recipe.description is not None:
            assert type(update_recipe.updates.description) == type(
                test_recipe.description
            )
        else:
            assert update_recipe.updates.description is None

        if test_recipe.notes is not None:
            assert type(update_recipe.updates.notes) == type(test_recipe.notes)
        else:
            assert update_recipe.updates.notes is None

        if test_recipe.total_time is not None:
            assert type(update_recipe.updates.total_time) == type(
                test_recipe.total_time
            )
        else:
            assert update_recipe.updates.total_time is None

        if test_recipe.weight_in_grams is not None:
            assert type(update_recipe.updates.weight_in_grams) == type(
                test_recipe.weight_in_grams
            )
        else:
            assert update_recipe.updates.weight_in_grams is None

        if test_recipe.image_url is not None:
            # image_url should remain as HttpUrl (no conversion to string)
            assert type(update_recipe.updates.image_url) == type(test_recipe.image_url)
            assert update_recipe.updates.image_url == test_recipe.image_url
        else:
            assert update_recipe.updates.image_url is None

        # Verify privacy enum is preserved
        if test_recipe.privacy is not None:
            assert type(update_recipe.updates.privacy) == type(test_recipe.privacy)
        else:
            assert update_recipe.updates.privacy is None

        # Verify collection types are preserved
        assert type(update_recipe.updates.ingredients) == type(test_recipe.ingredients)
        assert type(update_recipe.updates.tags) == type(test_recipe.tags)

    @pytest.mark.parametrize("scenario_data", REALISTIC_RECIPE_SCENARIOS)
    def test_all_realistic_recipe_scenarios(self, scenario_data):
        """Test all existing ApiRecipe fixtures with REALISTIC_RECIPE_SCENARIOS."""
        # Create recipe using scenario data directly
        api_recipe = create_api_recipe(
            name=scenario_data["name"],
            description=scenario_data["description"],
            instructions=scenario_data["instructions"],
            notes=scenario_data["notes"],
            total_time=scenario_data["total_time"],
            privacy=scenario_data["privacy"],
        )

        # Convert to update recipe
        update_recipe = ApiUpdateRecipe.from_api_recipe(api_recipe)

        # Verify basic structure for the scenario
        assert (
            update_recipe.recipe_id == api_recipe.id
        ), f"Failed for scenario: {scenario_data['name']}"
        assert (
            update_recipe.updates.name == api_recipe.name
        ), f"Failed for scenario: {scenario_data['name']}"
        assert (
            update_recipe.updates.description == api_recipe.description
        ), f"Failed for scenario: {scenario_data['name']}"
        assert (
            update_recipe.updates.instructions == api_recipe.instructions
        ), f"Failed for scenario: {scenario_data['name']}"
        assert (
            update_recipe.updates.notes == api_recipe.notes
        ), f"Failed for scenario: {scenario_data['name']}"
        assert (
            update_recipe.updates.total_time == api_recipe.total_time
        ), f"Failed for scenario: {scenario_data['name']}"
        assert (
            update_recipe.updates.privacy == api_recipe.privacy
        ), f"Failed for scenario: {scenario_data['name']}"

        # Verify image_url remains as HttpUrl (no conversion to string)
        assert (
            update_recipe.updates.image_url == api_recipe.image_url
        ), f"Failed for scenario: {scenario_data['name']}"

        # Verify collections are correctly mapped
        assert api_recipe.ingredients is not None
        assert api_recipe.tags is not None
        assert update_recipe.updates.ingredients is not None
        assert update_recipe.updates.tags is not None
        assert len(update_recipe.updates.ingredients) == len(
            api_recipe.ingredients
        ), f"Failed for scenario: {scenario_data['name']}"
        assert len(update_recipe.updates.tags) == len(
            api_recipe.tags
        ), f"Failed for scenario: {scenario_data['name']}"

        # Verify ingredients are correctly mapped
        original_ingredients = {
            (ing.name, ing.quantity, ing.unit) for ing in api_recipe.ingredients
        }
        update_ingredients = {
            (ing.name, ing.quantity, ing.unit)
            for ing in update_recipe.updates.ingredients
        }
        assert (
            original_ingredients == update_ingredients
        ), f"Failed for scenario: {scenario_data['name']}"

        # Verify tags are correctly mapped
        original_tags = {(tag.key, tag.value, tag.author_id) for tag in api_recipe.tags}
        update_tags = {
            (tag.key, tag.value, tag.author_id) for tag in update_recipe.updates.tags
        }
        assert (
            original_tags == update_tags
        ), f"Failed for scenario: {scenario_data['name']}"

    @pytest.mark.parametrize("recipe_index", list(range(10)))
    def test_recipe_collection_fixtures(self, recipe_index):
        """Test all existing ApiRecipe fixtures with create_recipe_collection()."""
        # Create collection of recipes
        recipe_collection = create_recipe_collection(count=10)

        # Get the specific recipe for this test
        api_recipe = recipe_collection[recipe_index]

        # Convert to update recipe
        update_recipe = ApiUpdateRecipe.from_api_recipe(api_recipe)

        # Verify basic structure
        assert (
            update_recipe.recipe_id == api_recipe.id
        ), f"Failed for recipe {recipe_index} in collection"
        assert (
            update_recipe.updates.name == api_recipe.name
        ), f"Failed for recipe {recipe_index} in collection"
        assert (
            update_recipe.updates.instructions == api_recipe.instructions
        ), f"Failed for recipe {recipe_index} in collection"

        # Verify collections are properly handled
        assert api_recipe.ingredients is not None
        assert api_recipe.tags is not None
        assert update_recipe.updates.ingredients is not None
        assert update_recipe.updates.tags is not None
        assert len(update_recipe.updates.ingredients) == len(
            api_recipe.ingredients
        ), f"Failed for recipe {recipe_index} in collection"
        assert len(update_recipe.updates.tags) == len(
            api_recipe.tags
        ), f"Failed for recipe {recipe_index} in collection"

        # Verify instance type
        assert isinstance(
            update_recipe, ApiUpdateRecipe
        ), f"Failed for recipe {recipe_index} in collection"
        assert isinstance(
            update_recipe.updates, ApiAttributesToUpdateOnRecipe
        ), f"Failed for recipe {recipe_index} in collection"

    @pytest.mark.parametrize(
        "recipe_factory",
        [
            create_simple_api_recipe,
            create_complex_api_recipe,
            create_minimal_api_recipe,
            create_api_recipe_with_max_fields,
            create_quick_api_recipe,
            create_dessert_api_recipe,
            create_vegetarian_api_recipe,
            create_high_protein_api_recipe,
        ],
    )
    def test_validate_created_api_update_recipe_instances(self, recipe_factory):
        """Validate created ApiUpdateRecipe instances follow validation patterns."""
        # Create recipe using the factory function
        api_recipe = recipe_factory()

        # Convert to update recipe
        update_recipe = ApiUpdateRecipe.from_api_recipe(api_recipe)

        # Validate ApiUpdateRecipe instance structure
        assert isinstance(
            update_recipe, ApiUpdateRecipe
        ), "Must be ApiUpdateRecipe instance"
        assert hasattr(update_recipe, "recipe_id"), "Must have recipe_id attribute"
        assert hasattr(update_recipe, "updates"), "Must have updates attribute"
        assert isinstance(
            update_recipe.updates, ApiAttributesToUpdateOnRecipe
        ), "Updates must be ApiAttributesToUpdateOnRecipe instance"

        # Validate recipe_id is valid UUID string
        assert isinstance(update_recipe.recipe_id, str), "recipe_id must be string"
        assert len(update_recipe.recipe_id) == 36, "recipe_id must be valid UUID length"
        assert (
            update_recipe.recipe_id.count("-") == 4
        ), "recipe_id must be valid UUID format"

        # Validate required fields in updates
        assert hasattr(
            update_recipe.updates, "name"
        ), "Updates must have name attribute"
        assert hasattr(
            update_recipe.updates, "instructions"
        ), "Updates must have instructions attribute"
        assert isinstance(update_recipe.updates.name, str), "Name must be string"
        assert isinstance(
            update_recipe.updates.instructions, str
        ), "Instructions must be string"
        assert len(update_recipe.updates.name.strip()) > 0, "Name must not be empty"
        assert (
            len(update_recipe.updates.instructions.strip()) > 0
        ), "Instructions must not be empty"

        # Validate optional fields in updates
        optional_fields = [
            "description",
            "notes",
            "utensils",
            "total_time",
            "weight_in_grams",
            "image_url",
            "privacy",
        ]
        for field in optional_fields:
            assert hasattr(
                update_recipe.updates, field
            ), f"Updates must have {field} attribute"
            field_value = getattr(update_recipe.updates, field)
            if field_value is not None:
                if field == "image_url":
                    assert isinstance(
                        field_value, HttpUrl
                    ), f"{field} must be HttpUrl when not None"
                elif field in ["description", "notes", "utensils"]:
                    assert isinstance(
                        field_value, str
                    ), f"{field} must be string when not None"
                elif field in ["total_time", "weight_in_grams"]:
                    assert isinstance(
                        field_value, int
                    ), f"{field} must be int when not None"
                elif field == "privacy":
                    from src.contexts.shared_kernel.domain.enums import Privacy

                    assert isinstance(
                        field_value, Privacy
                    ), f"{field} must be Privacy enum when not None"

        # Validate collections in updates
        assert hasattr(
            update_recipe.updates, "ingredients"
        ), "Updates must have ingredients attribute"
        assert hasattr(
            update_recipe.updates, "tags"
        ), "Updates must have tags attribute"
        assert isinstance(
            update_recipe.updates.ingredients, frozenset
        ), "Ingredients must be frozenset"
        assert isinstance(
            update_recipe.updates.tags, frozenset
        ), "Tags must be frozenset"

        # Validate ingredient instances in collection
        for ingredient in update_recipe.updates.ingredients:
            assert isinstance(
                ingredient, ApiIngredient
            ), "Each ingredient must be ApiIngredient instance"
            assert hasattr(ingredient, "name"), "Ingredient must have name attribute"
            assert hasattr(
                ingredient, "quantity"
            ), "Ingredient must have quantity attribute"
            assert hasattr(ingredient, "unit"), "Ingredient must have unit attribute"

        # Validate tag instances in collection
        for tag in update_recipe.updates.tags:
            assert isinstance(tag, ApiTag), "Each tag must be ApiTag instance"
            assert hasattr(tag, "key"), "Tag must have key attribute"
            assert hasattr(tag, "value"), "Tag must have value attribute"
            assert hasattr(tag, "author_id"), "Tag must have author_id attribute"
            assert isinstance(tag.key, str), "Tag key must be string"
            assert isinstance(tag.value, str), "Tag value must be string"
            assert isinstance(tag.author_id, str), "Tag author_id must be string"

    def test_validate_field_completeness(self):
        """Validate that all expected fields from ApiRecipe are present in ApiUpdateRecipe."""
        # Create comprehensive recipe
        api_recipe = create_complex_api_recipe()
        update_recipe = ApiUpdateRecipe.from_api_recipe(api_recipe)

        # Check all expected fields are present in updates
        expected_fields = [
            "name",
            "description",
            "instructions",
            "notes",
            "utensils",
            "total_time",
            "weight_in_grams",
            "image_url",
            "privacy",
            "ingredients",
            "tags",
            "nutri_facts",
        ]

        for field in expected_fields:
            assert hasattr(update_recipe.updates, field), f"Missing field: {field}"

        # Verify no unexpected fields exist
        actual_fields = set(ApiAttributesToUpdateOnRecipe.model_fields.keys())
        expected_fields_set = set(expected_fields)

        # Allow for additional fields that might be added in the future
        # but ensure all expected fields are present
        assert expected_fields_set.issubset(
            actual_fields
        ), "Missing required fields in ApiAttributesToUpdateOnRecipe"

    @pytest.mark.parametrize(
        "recipe_factory",
        [
            create_simple_api_recipe,
            create_complex_api_recipe,
            create_minimal_api_recipe,
            create_api_recipe_with_max_fields,
            create_quick_api_recipe,
            create_dessert_api_recipe,
        ],
    )
    def test_validate_conversion_completeness(self, recipe_factory):
        """Validate that conversion preserves all data without loss."""
        # Create recipe using the factory function
        api_recipe = recipe_factory()
        update_recipe = ApiUpdateRecipe.from_api_recipe(api_recipe)

        # Verify no data loss in conversion
        assert update_recipe.recipe_id == api_recipe.id, "recipe_id conversion failed"
        assert update_recipe.updates.name == api_recipe.name, "name conversion failed"
        assert (
            update_recipe.updates.description == api_recipe.description
        ), "description conversion failed"
        assert (
            update_recipe.updates.instructions == api_recipe.instructions
        ), "instructions conversion failed"
        assert (
            update_recipe.updates.notes == api_recipe.notes
        ), "notes conversion failed"
        assert (
            update_recipe.updates.utensils == api_recipe.utensils
        ), "utensils conversion failed"
        assert (
            update_recipe.updates.total_time == api_recipe.total_time
        ), "total_time conversion failed"
        assert (
            update_recipe.updates.weight_in_grams == api_recipe.weight_in_grams
        ), "weight_in_grams conversion failed"
        assert (
            update_recipe.updates.privacy == api_recipe.privacy
        ), "privacy conversion failed"

        # Verify image_url remains as HttpUrl (no conversion to string)
        if api_recipe.image_url is not None:
            assert (
                update_recipe.updates.image_url == api_recipe.image_url
            ), "image_url conversion failed"
        else:
            assert (
                update_recipe.updates.image_url is None
            ), "image_url None conversion failed"

        # Verify nutri_facts preservation
        if api_recipe.nutri_facts is not None:
            assert (
                update_recipe.updates.nutri_facts is not None
            ), "nutri_facts should not be None"
            assert (
                update_recipe.updates.nutri_facts.calories
                == api_recipe.nutri_facts.calories
            ), "nutri_facts calories conversion failed"
        else:
            assert (
                update_recipe.updates.nutri_facts is None
            ), "nutri_facts None conversion failed"

        # Verify collection size preservation
        assert api_recipe.ingredients is not None
        assert api_recipe.tags is not None
        assert update_recipe.updates.ingredients is not None
        assert update_recipe.updates.tags is not None
        assert len(update_recipe.updates.ingredients) == len(
            api_recipe.ingredients
        ), "ingredients collection size changed"
        assert len(update_recipe.updates.tags) == len(
            api_recipe.tags
        ), "tags collection size changed"

        # Verify ingredient data preservation
        original_ingredients = {
            (ing.name, ing.quantity, ing.unit) for ing in api_recipe.ingredients
        }
        update_ingredients = {
            (ing.name, ing.quantity, ing.unit)
            for ing in update_recipe.updates.ingredients
        }
        assert (
            original_ingredients == update_ingredients
        ), "ingredients data conversion failed"

        # Verify tag data preservation
        original_tags = {(tag.key, tag.value, tag.author_id) for tag in api_recipe.tags}
        update_tags = {
            (tag.key, tag.value, tag.author_id) for tag in update_recipe.updates.tags
        }
        assert original_tags == update_tags, "tags data conversion failed"
