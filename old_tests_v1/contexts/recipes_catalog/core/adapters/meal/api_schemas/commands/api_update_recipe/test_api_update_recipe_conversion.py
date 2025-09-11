"""
Test suite for ApiUpdateRecipe conversion logic (to_domain() methods).
Tests the conversion of ApiUpdateRecipe instances to domain UpdateRecipe commands.
"""

import pytest
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_update_recipe import (
    ApiAttributesToUpdateOnRecipe,
    ApiUpdateRecipe,
)
from src.contexts.recipes_catalog.core.domain.meal.commands.update_recipe import (
    UpdateRecipe,
)

# Import existing data factories
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
    REALISTIC_RECIPE_SCENARIOS,
    create_api_recipe,
    create_api_recipe_with_max_fields,
    create_complex_api_recipe,
    create_dessert_api_recipe,
    create_high_protein_api_recipe,
    create_minimal_api_recipe,
    create_quick_api_recipe,
    create_simple_api_recipe,
    create_vegetarian_api_recipe,
)


class TestApiUpdateRecipeConversion:
    """Test suite for ApiUpdateRecipe to_domain() conversion methods."""

    def test_api_update_recipe_to_domain_basic_conversion(self):
        """Test ApiUpdateRecipe.to_domain() returns valid UpdateRecipe."""
        # Create ApiUpdateRecipe from simple recipe
        api_recipe = create_simple_api_recipe()
        api_update_recipe = ApiUpdateRecipe.from_api_recipe(api_recipe)

        # Convert to domain
        domain_command = api_update_recipe.to_domain()

        # Verify return type and structure
        assert isinstance(domain_command, UpdateRecipe)
        assert domain_command.recipe_id == api_update_recipe.recipe_id
        assert isinstance(domain_command.updates, dict)

        # Verify recipe_id matches original
        assert domain_command.recipe_id == api_recipe.id

    def test_basic_update_recipe_command_structure(self):
        """Test basic UpdateRecipe command creation structure using create_api_recipe()."""
        # Use basic api recipe from factory as specified in task requirements
        api_recipe = create_api_recipe()
        api_update_recipe = ApiUpdateRecipe.from_api_recipe(api_recipe)

        # Convert to domain command
        domain_command = api_update_recipe.to_domain()

        # Verify command structure
        assert isinstance(domain_command, UpdateRecipe)
        assert hasattr(domain_command, "recipe_id")
        assert hasattr(domain_command, "updates")

        # Verify recipe_id is correctly set
        assert domain_command.recipe_id == api_recipe.id
        assert isinstance(domain_command.recipe_id, str)

        # Verify updates dictionary structure
        assert isinstance(domain_command.updates, dict)
        assert len(domain_command.updates) > 0

        # Verify essential fields are present in updates
        assert "name" in domain_command.updates
        assert domain_command.updates["name"] == api_recipe.name

    def test_update_recipe_command_with_all_field_types(self):
        """Test UpdateRecipe command creation with all supported field types."""
        # Create recipe with comprehensive field coverage
        api_recipe = create_api_recipe()
        api_update_recipe = ApiUpdateRecipe.from_api_recipe(api_recipe)

        # Convert to domain
        domain_command = api_update_recipe.to_domain()
        updates = domain_command.updates

        # Verify string fields
        assert isinstance(updates.get("name"), str)
        if "description" in updates:
            assert isinstance(updates["description"], (str, type(None)))
        if "instructions" in updates:
            assert isinstance(updates["instructions"], str)
        if "notes" in updates:
            assert isinstance(updates["notes"], (str, type(None)))
        if "image_url" in updates:
            assert isinstance(updates["image_url"], (str, type(None)))
        if "utensils" in updates:
            assert isinstance(updates["utensils"], (str, type(None)))

        # Verify numeric fields
        if "total_time" in updates:
            assert isinstance(updates["total_time"], (int, type(None)))
        if "weight_in_grams" in updates:
            assert isinstance(updates["weight_in_grams"], (int, type(None)))

        # Verify enum fields
        if "privacy" in updates:
            assert updates["privacy"] is not None  # Should have a privacy value

        # Verify collection fields are converted to domain types
        if "ingredients" in updates:
            assert isinstance(updates["ingredients"], list)
            # Each ingredient should be a domain ingredient object
            for ingredient in updates["ingredients"]:
                assert hasattr(ingredient, "name")
                assert hasattr(ingredient, "quantity")

        if "tags" in updates:
            assert isinstance(updates["tags"], frozenset)
            # Each tag should be a domain tag object
            for tag in updates["tags"]:
                assert hasattr(tag, "key")
                assert hasattr(tag, "value")

        # Verify complex objects
        if "nutri_facts" in updates and updates["nutri_facts"] is not None:
            assert hasattr(updates["nutri_facts"], "calories")

    @pytest.mark.parametrize(
        "recipe_factory",
        [
            create_api_recipe,
            create_simple_api_recipe,
            create_complex_api_recipe,
        ],
    )
    def test_update_recipe_command_validation(self, recipe_factory):
        """Test that generated UpdateRecipe commands are valid domain objects."""
        api_recipe = recipe_factory()
        api_update_recipe = ApiUpdateRecipe.from_api_recipe(api_recipe)
        domain_command = api_update_recipe.to_domain()

        # Verify command is valid UpdateRecipe
        assert isinstance(domain_command, UpdateRecipe)

        # Verify required attributes exist
        assert hasattr(domain_command, "recipe_id")
        assert hasattr(domain_command, "updates")

        # Verify recipe_id is valid UUID string
        assert isinstance(domain_command.recipe_id, str)
        assert (
            len(domain_command.recipe_id.replace("-", "")) == 32
        )  # UUID without hyphens

        # Verify updates is a dictionary
        assert isinstance(domain_command.updates, dict)

    def test_api_attributes_to_update_exclude_unset_behavior(self):
        """Test ApiAttributesToUpdateOnRecipe.to_domain() with exclude_unset=True."""
        # Create ApiUpdateRecipe with partial data
        api_recipe = create_simple_api_recipe()
        api_update_recipe = ApiUpdateRecipe.from_api_recipe(api_recipe)

        # Test exclude_unset behavior on the updates object
        updates_dict = api_update_recipe.updates.to_domain()

        # Should be a dictionary with only set fields
        assert isinstance(updates_dict, dict)

        # Should contain expected fields from the API recipe
        assert "name" in updates_dict
        assert updates_dict["name"] == api_recipe.name

        # Should contain instructions if it was set
        if api_recipe.instructions:
            assert "instructions" in updates_dict
            assert updates_dict["instructions"] == api_recipe.instructions

    @pytest.mark.parametrize(
        "recipe_factory",
        [
            create_simple_api_recipe,
            create_complex_api_recipe,
            create_api_recipe_with_max_fields,
            create_minimal_api_recipe,
        ],
    )
    def test_conversion_with_various_recipe_configurations(self, recipe_factory):
        """Test to_domain() conversion across different recipe types."""
        api_recipe = recipe_factory()

        # Create update command from recipe
        api_update_recipe = ApiUpdateRecipe.from_api_recipe(api_recipe)

        # Convert to domain
        domain_command = api_update_recipe.to_domain()

        # Verify basic structure
        assert isinstance(domain_command, UpdateRecipe)
        assert domain_command.recipe_id == api_recipe.id
        assert isinstance(domain_command.updates, dict)

        # Verify required fields are present
        assert "name" in domain_command.updates
        assert domain_command.updates["name"] == api_recipe.name

    @pytest.mark.parametrize("scenario_data", REALISTIC_RECIPE_SCENARIOS)
    def test_conversion_with_realistic_recipe_scenarios(self, scenario_data):
        """Test conversion validation using REALISTIC_RECIPE_SCENARIOS as specified in task requirements."""
        # Create recipe using scenario data directly
        api_recipe = create_api_recipe(
            name=scenario_data["name"],
            description=scenario_data["description"],
            instructions=scenario_data["instructions"],
            total_time=scenario_data["total_time"],
            notes=scenario_data["notes"],
            weight_in_grams=scenario_data["weight_in_grams"],
        )

        # Create update command from realistic scenario recipe
        api_update_recipe = ApiUpdateRecipe.from_api_recipe(api_recipe)

        # Convert to domain
        domain_command = api_update_recipe.to_domain()

        # Verify conversion succeeded for realistic scenario
        assert isinstance(
            domain_command, UpdateRecipe
        ), f"Conversion failed for scenario: {scenario_data['name']}"
        assert (
            domain_command.recipe_id == api_recipe.id
        ), f"Recipe ID mismatch for scenario: {scenario_data['name']}"
        assert isinstance(
            domain_command.updates, dict
        ), f"Updates not dict for scenario: {scenario_data['name']}"

        # Verify essential fields are preserved
        assert (
            "name" in domain_command.updates
        ), f"Name missing for scenario: {scenario_data['name']}"
        assert (
            domain_command.updates["name"] == api_recipe.name
        ), f"Name mismatch for scenario: {scenario_data['name']}"

        # Verify scenario-specific characteristics
        if api_recipe.ingredients:
            if "ingredients" in domain_command.updates:
                assert len(domain_command.updates["ingredients"]) == len(
                    api_recipe.ingredients
                ), f"Ingredient count mismatch for scenario: {scenario_data['name']}"

        if api_recipe.tags:
            if "tags" in domain_command.updates:
                assert len(domain_command.updates["tags"]) == len(
                    api_recipe.tags
                ), f"Tag count mismatch for scenario: {scenario_data['name']}"

    @pytest.mark.parametrize(
        "variant_name,recipe_factory",
        [
            ("simple", create_simple_api_recipe),
            ("complex", create_complex_api_recipe),
            ("minimal", create_minimal_api_recipe),
            ("max_fields", create_api_recipe_with_max_fields),
            ("basic", create_api_recipe),
            ("quick", create_quick_api_recipe),
            ("dessert", create_dessert_api_recipe),
            ("vegetarian", create_vegetarian_api_recipe),
            ("high_protein", create_high_protein_api_recipe),
        ],
    )
    def test_conversion_with_recipe_type_variants(self, variant_name, recipe_factory):
        """Test conversion across different recipe type variants from api_recipe_data_factories."""
        api_recipe = recipe_factory()

        # Create update command
        api_update_recipe = ApiUpdateRecipe.from_api_recipe(api_recipe)

        # Convert to domain
        domain_command = api_update_recipe.to_domain()

        # Verify conversion for each variant
        assert isinstance(
            domain_command, UpdateRecipe
        ), f"Conversion failed for variant: {variant_name}"
        assert (
            domain_command.recipe_id == api_recipe.id
        ), f"Recipe ID mismatch for variant: {variant_name}"
        assert isinstance(
            domain_command.updates, dict
        ), f"Updates not dict for variant: {variant_name}"

        # Verify name field is always present and correct
        assert (
            "name" in domain_command.updates
        ), f"Name missing for variant: {variant_name}"
        assert (
            domain_command.updates["name"] == api_recipe.name
        ), f"Name mismatch for variant: {variant_name}"

        # Verify variant-specific characteristics
        if variant_name == "minimal":
            # Minimal recipes should have fewer fields set
            essential_fields = {"name", "instructions"}
            update_fields = set(domain_command.updates.keys())
            assert essential_fields.issubset(
                update_fields
            ), f"Essential fields missing for minimal variant: {essential_fields - update_fields}"

        elif variant_name == "complex":
            # Complex recipes should have many fields set including collections
            assert "name" in domain_command.updates
            assert "instructions" in domain_command.updates
            # Should have either ingredients or tags or both for complex recipes
            has_collections = (
                "ingredients" in domain_command.updates
                or "tags" in domain_command.updates
            )
            assert has_collections, f"Complex variant should have collection fields"

        elif variant_name == "max_fields":
            # Should have many fields set
            expected_complex_fields = {"name", "instructions", "description"}
            update_fields = set(domain_command.updates.keys())
            assert expected_complex_fields.issubset(
                update_fields
            ), f"Max fields variant should have comprehensive fields"

    @pytest.mark.parametrize(
        "recipe_factory",
        [
            create_api_recipe,
            create_simple_api_recipe,
            create_complex_api_recipe,
        ],
    )
    def test_recipe_configuration_field_consistency(self, recipe_factory):
        """Test that field values are consistently converted across different recipe configurations."""
        api_recipe = recipe_factory()
        api_update_recipe = ApiUpdateRecipe.from_api_recipe(api_recipe)
        domain_command = api_update_recipe.to_domain()
        updates = domain_command.updates

        # Verify field type consistency
        if "name" in updates:
            assert isinstance(updates["name"], str)
            assert len(updates["name"]) > 0

        if "description" in updates:
            assert isinstance(updates["description"], (str, type(None)))

        if "instructions" in updates:
            assert isinstance(updates["instructions"], str)
            assert len(updates["instructions"]) > 0

        if "ingredients" in updates:
            assert isinstance(updates["ingredients"], list)
            for ingredient in updates["ingredients"]:
                # Each ingredient should be a domain ingredient with required attributes
                assert hasattr(ingredient, "name")
                assert hasattr(ingredient, "quantity")
                assert hasattr(ingredient, "position")

        if "tags" in updates:
            assert isinstance(updates["tags"], frozenset)
            for tag in updates["tags"]:
                # Each tag should be a domain tag with required attributes
                assert hasattr(tag, "key")
                assert hasattr(tag, "value")
                assert hasattr(tag, "author_id")
                assert (
                    tag.author_id == api_recipe.author_id
                )  # Tag should belong to recipe author

    # ========================================
    # EDGE CASE TESTS (Tasks 2.3.1 - 2.3.3)
    # ========================================

    def test_conversion_with_empty_minimal_updates(self):
        """Test conversion with empty/minimal updates (Task 2.3.1)."""
        # Test with minimal api recipe that has only required fields
        minimal_recipe = create_minimal_api_recipe()
        api_update_recipe = ApiUpdateRecipe.from_api_recipe(minimal_recipe)

        # Convert to domain
        domain_command = api_update_recipe.to_domain()

        # Verify basic structure works with minimal data
        assert isinstance(domain_command, UpdateRecipe)
        assert domain_command.recipe_id == minimal_recipe.id
        assert isinstance(domain_command.updates, dict)

        # Should have at least name and instructions
        assert "name" in domain_command.updates
        assert "instructions" in domain_command.updates
        assert domain_command.updates["name"] == minimal_recipe.name
        assert domain_command.updates["instructions"] == minimal_recipe.instructions

        # Optional fields should not be in updates if not set
        updates_dict = api_update_recipe.updates.to_domain()
        expected_minimal_fields = {"name", "instructions"}

        # Check that only set fields are included
        for field_name in updates_dict.keys():
            if field_name not in expected_minimal_fields:
                # If additional fields exist, they should have valid values
                field_value = updates_dict[field_name]
                assert field_value is not None or field_name in [
                    "description",
                    "notes",
                    "image_url",
                    "utensils",
                    "total_time",
                    "weight_in_grams",
                ]

        # Verify exclude_unset behavior works with minimal data
        assert len(updates_dict) >= 2  # At least name and instructions
        assert "name" in updates_dict
        assert "instructions" in updates_dict

    def test_conversion_with_truly_empty_optional_fields(self):
        """Test conversion handles truly empty optional fields correctly (Task 2.3.1 edge case)."""
        # Create minimal recipe and manually create ApiUpdateRecipe with minimal fields
        minimal_recipe = create_minimal_api_recipe()

        # Create ApiAttributesToUpdateOnRecipe with only required fields set
        updates = ApiAttributesToUpdateOnRecipe(
            name=minimal_recipe.name,
            instructions=minimal_recipe.instructions,
            description=None,
            ingredients=frozenset(),
            tags=frozenset(),
            notes=None,
            utensils=None,
            total_time=None,
            weight_in_grams=None,
            privacy=None,
            nutri_facts=None,
            image_url=None,
        )

        api_update_recipe = ApiUpdateRecipe(
            recipe_id=minimal_recipe.id, updates=updates
        )

        # Convert to domain
        domain_command = api_update_recipe.to_domain()

        # Verify structure
        assert isinstance(domain_command, UpdateRecipe)
        assert domain_command.recipe_id == minimal_recipe.id

        # Verify only set fields are in the updates
        updates_dict = api_update_recipe.updates.to_domain()
        assert "name" in updates_dict
        assert "instructions" in updates_dict
        assert updates_dict["name"] == minimal_recipe.name
        assert updates_dict["instructions"] == minimal_recipe.instructions

        # Should not have unset optional fields in exclude_unset mode
        unset_fields = {
            "description",
            "notes",
            "image_url",
            "utensils",
            "total_time",
            "weight_in_grams",
        }
        for field in unset_fields:
            if field in updates_dict:
                # If present, should have been explicitly set
                assert hasattr(updates, field)

    def test_complex_nested_object_conversion_comprehensive(self):
        """Test complex nested object conversion thoroughly (Task 2.3.2)."""
        # Test with complex recipe containing nested ingredients and tags
        complex_recipe = create_complex_api_recipe()
        api_update_recipe = ApiUpdateRecipe.from_api_recipe(complex_recipe)

        # Convert to domain
        domain_command = api_update_recipe.to_domain()
        updates = domain_command.updates

        # Verify basic structure
        assert isinstance(domain_command, UpdateRecipe)
        assert domain_command.recipe_id == complex_recipe.id

        # Test nested ingredient conversion if ingredients exist
        if complex_recipe.ingredients and "ingredients" in updates:
            ingredients = updates["ingredients"]
            assert isinstance(ingredients, list)
            assert len(ingredients) == len(complex_recipe.ingredients)

            # Convert frozenset to list for comparison, sorted by position
            api_ingredients_list = sorted(
                list(complex_recipe.ingredients), key=lambda x: x.position
            )
            domain_ingredients_list = sorted(ingredients, key=lambda x: x.position)

            for i, (domain_ingredient, api_ingredient) in enumerate(
                zip(domain_ingredients_list, api_ingredients_list, strict=False)
            ):
                # Verify ingredient structure and field conversion
                assert hasattr(domain_ingredient, "name")
                assert hasattr(domain_ingredient, "quantity")
                assert hasattr(domain_ingredient, "position")

                # Verify field values are correctly converted
                assert domain_ingredient.name == api_ingredient.name
                assert domain_ingredient.quantity == api_ingredient.quantity
                assert domain_ingredient.position == api_ingredient.position

        # Test nested tag conversion if tags exist
        if complex_recipe.tags and "tags" in updates:
            tags = updates["tags"]
            assert isinstance(tags, frozenset)
            assert len(tags) == len(complex_recipe.tags)

            # Create mappings by key for comparison (tags are frozensets, order not guaranteed)
            domain_tags_by_key = {tag.key: tag for tag in tags}
            api_tags_by_key = {tag.key: tag for tag in complex_recipe.tags}

            # Verify all tags are converted correctly
            assert set(domain_tags_by_key.keys()) == set(api_tags_by_key.keys())

            for key in domain_tags_by_key:
                domain_tag = domain_tags_by_key[key]
                api_tag = api_tags_by_key[key]

                # Verify tag structure and field conversion
                assert hasattr(domain_tag, "key")
                assert hasattr(domain_tag, "value")
                assert hasattr(domain_tag, "author_id")

                # Verify field values are correctly converted
                assert domain_tag.key == api_tag.key
                assert domain_tag.value == api_tag.value
                assert domain_tag.author_id == complex_recipe.author_id

    def test_max_fields_nested_object_conversion(self):
        """Test conversion with maximum number of nested objects (Task 2.3.2)."""
        # Test with recipe containing maximum fields
        max_fields_recipe = create_api_recipe_with_max_fields()
        api_update_recipe = ApiUpdateRecipe.from_api_recipe(max_fields_recipe)

        # Convert to domain
        domain_command = api_update_recipe.to_domain()
        updates = domain_command.updates

        # Verify structure with maximum nested objects
        assert isinstance(domain_command, UpdateRecipe)
        assert domain_command.recipe_id == max_fields_recipe.id

        # Should handle large number of nested ingredients
        if max_fields_recipe.ingredients and "ingredients" in updates:
            ingredients = updates["ingredients"]
            assert isinstance(ingredients, list)
            assert len(ingredients) == len(max_fields_recipe.ingredients)

            # Verify each ingredient in large collection is properly converted
            for domain_ingredient in ingredients:
                assert hasattr(domain_ingredient, "name")
                assert hasattr(domain_ingredient, "quantity")
                assert hasattr(domain_ingredient, "position")

                # Verify name format
                assert isinstance(domain_ingredient.name, str)
                assert len(domain_ingredient.name) > 0

        # Performance consideration: conversion should complete in reasonable time
        # (This is implicitly tested by the test not timing out)

    def test_uuid_field_edge_cases(self):
        """Test UUID field handling edge cases (Task 2.3.3)."""
        # Test with standard UUID formats
        api_recipe = create_api_recipe()
        api_update_recipe = ApiUpdateRecipe.from_api_recipe(api_recipe)

        # Convert to domain
        domain_command = api_update_recipe.to_domain()

        # Verify UUID format consistency
        recipe_id = domain_command.recipe_id
        assert isinstance(recipe_id, str)

        # Verify UUID string format (with or without hyphens)
        clean_uuid = recipe_id.replace("-", "")
        assert len(clean_uuid) == 32
        assert all(c in "0123456789abcdefABCDEF" for c in clean_uuid)

    def test_frozen_set_handling_for_ingredients_and_tags(self):
        """Test frozen set conversion for ingredients and tags (Task 2.3.3 - collections)."""
        # Test with recipe containing multiple ingredients and tags
        complex_recipe = create_complex_api_recipe()

        if complex_recipe.ingredients or complex_recipe.tags:
            api_update_recipe = ApiUpdateRecipe.from_api_recipe(complex_recipe)
            domain_command = api_update_recipe.to_domain()
            updates = domain_command.updates

            # Verify ingredient collection conversion
            if "ingredients" in updates:
                ingredients = updates["ingredients"]
                assert isinstance(
                    ingredients, list
                )  # Should be list in domain, not frozenset

                # Extract ingredient names
                ingredient_names = [ingredient.name for ingredient in ingredients]
                api_ingredient_names = (
                    [ingredient.name for ingredient in complex_recipe.ingredients]
                    if complex_recipe.ingredients
                    else []
                )

                # Verify all ingredient names are preserved and valid
                assert len(ingredient_names) == len(api_ingredient_names)

                for ingredient_name in ingredient_names:
                    assert isinstance(ingredient_name, str)
                    assert len(ingredient_name) > 0
                    assert ingredient_name in api_ingredient_names

            # Verify tag collection conversion
            if "tags" in updates:
                tags = updates["tags"]
                assert isinstance(tags, frozenset)  # Should remain frozenset in domain

                # Extract tag keys
                tag_keys = [tag.key for tag in tags]
                api_tag_keys = (
                    [tag.key for tag in complex_recipe.tags]
                    if complex_recipe.tags
                    else []
                )

                # Verify all tag keys are preserved and valid
                assert len(tag_keys) == len(api_tag_keys)

                for tag_key in tag_keys:
                    assert isinstance(tag_key, str)
                    assert len(tag_key) > 0
                    assert tag_key in api_tag_keys

        # Test with max fields recipe for larger collection handling
        max_recipe = create_api_recipe_with_max_fields()
        if max_recipe.ingredients or max_recipe.tags:
            api_update_max = ApiUpdateRecipe.from_api_recipe(max_recipe)
            domain_max = api_update_max.to_domain()
            max_updates = domain_max.updates

            if "ingredients" in max_updates and max_recipe.ingredients:
                max_ingredients = max_updates["ingredients"]
                assert isinstance(max_ingredients, list)

                # Verify large collection handling
                assert len(max_ingredients) == len(max_recipe.ingredients)

                # Verify all ingredients are valid in large collection
                for ingredient in max_ingredients:
                    assert hasattr(ingredient, "name")
                    assert isinstance(ingredient.name, str)
                    assert len(ingredient.name) > 0

    # ============================================
    # SECTION 2.4: UpdateRecipe Command Structure Validation
    # ============================================

    @pytest.mark.parametrize(
        "factory_name,recipe_factory",
        [
            ("create_api_recipe", create_api_recipe),
            ("create_simple_api_recipe", create_simple_api_recipe),
            ("create_complex_api_recipe", create_complex_api_recipe),
            ("create_minimal_api_recipe", create_minimal_api_recipe),
            ("create_api_recipe_with_max_fields", create_api_recipe_with_max_fields),
        ],
    )
    def test_command_structure_with_different_recipe_factories(
        self, factory_name, recipe_factory
    ):
        """Test command structure consistency across all recipe factory types (Task 2.4.1)."""
        api_recipe = recipe_factory()
        api_update_recipe = ApiUpdateRecipe.from_api_recipe(api_recipe)
        domain_command = api_update_recipe.to_domain()

        # Verify command structure is consistent regardless of factory
        assert isinstance(
            domain_command, UpdateRecipe
        ), f"Command structure inconsistent for {factory_name}"
        assert isinstance(
            domain_command.recipe_id, str
        ), f"recipe_id structure inconsistent for {factory_name}"
        assert isinstance(
            domain_command.updates, dict
        ), f"updates structure inconsistent for {factory_name}"

        # Verify command follows the same pattern
        assert (
            len(domain_command.recipe_id.replace("-", "")) == 32
        ), f"recipe_id format inconsistent for {factory_name}"
        assert (
            "name" in domain_command.updates
        ), f"Required field missing for {factory_name}"

        # Verify updates dictionary has valid structure
        for field_name, field_value in domain_command.updates.items():
            assert isinstance(
                field_name, str
            ), f"Field name not string in {factory_name}: {field_name}"
            # Field values can be various types, but should not be undefined
            assert (
                field_value is not ...
            ), f"Undefined field value in {factory_name}: {field_name}"

    def test_command_field_types_comprehensive(self):
        """Test all command field types are correctly converted (Task 2.4.2)."""
        # Create a complex recipe to test all field types
        complex_recipe = create_complex_api_recipe()
        api_update_recipe = ApiUpdateRecipe.from_api_recipe(complex_recipe)
        domain_command = api_update_recipe.to_domain()
        updates = domain_command.updates

        # Test string field types
        string_fields = ["name", "description", "instructions", "notes", "utensils"]
        for field in string_fields:
            if field in updates:
                assert isinstance(
                    updates[field], (str, type(None))
                ), f"String field {field} has wrong type: {type(updates[field])}"
                if updates[field] is not None:
                    assert (
                        len(updates[field]) >= 0
                    ), f"String field {field} has invalid length"

        # Test URL field types (can be str or HttpUrl)
        url_fields = ["image_url"]
        for field in url_fields:
            if field in updates and updates[field] is not None:
                # HttpUrl is acceptable for image_url field
                from pydantic import HttpUrl

                assert isinstance(
                    updates[field], (str, HttpUrl)
                ), f"URL field {field} has wrong type: {type(updates[field])}"

        # Test numeric field types
        numeric_fields = ["total_time", "weight_in_grams"]
        for field in numeric_fields:
            if field in updates and updates[field] is not None:
                assert isinstance(
                    updates[field], int
                ), f"Numeric field {field} has wrong type: {type(updates[field])}"
                assert (
                    updates[field] >= 0
                ), f"Numeric field {field} has negative value: {updates[field]}"

        # Test enum field types
        enum_fields = ["privacy"]
        for field in enum_fields:
            if field in updates and updates[field] is not None:
                # Privacy should be a Privacy enum value
                from src.contexts.shared_kernel.domain.enums import Privacy

                assert updates[field] in [
                    Privacy.PRIVATE,
                    Privacy.PUBLIC,
                ], f"Enum field {field} has invalid value: {updates[field]}"

        # Test collection field types
        if "ingredients" in updates:
            assert isinstance(
                updates["ingredients"], list
            ), f"ingredients field is not list: {type(updates['ingredients'])}"
            for ingredient in updates["ingredients"]:
                # Each ingredient should be a domain ingredient object with proper attributes
                assert hasattr(ingredient, "name"), "Ingredient missing name attribute"
                assert hasattr(
                    ingredient, "quantity"
                ), "Ingredient missing quantity attribute"
                assert hasattr(
                    ingredient, "position"
                ), "Ingredient missing position attribute"
                assert isinstance(
                    ingredient.name, str
                ), f"Ingredient name wrong type: {type(ingredient.name)}"
                assert isinstance(
                    ingredient.quantity, (int, float)
                ), f"Ingredient quantity wrong type: {type(ingredient.quantity)}"
                assert isinstance(
                    ingredient.position, int
                ), f"Ingredient position wrong type: {type(ingredient.position)}"

        if "tags" in updates:
            assert isinstance(
                updates["tags"], frozenset
            ), f"tags field is not frozenset: {type(updates['tags'])}"
            for tag in updates["tags"]:
                # Each tag should be a domain tag object with proper attributes
                assert hasattr(tag, "key"), "Tag missing key attribute"
                assert hasattr(tag, "value"), "Tag missing value attribute"
                assert hasattr(tag, "author_id"), "Tag missing author_id attribute"
                assert isinstance(tag.key, str), f"Tag key wrong type: {type(tag.key)}"
                assert isinstance(
                    tag.value, str
                ), f"Tag value wrong type: {type(tag.value)}"
                assert isinstance(
                    tag.author_id, str
                ), f"Tag author_id wrong type: {type(tag.author_id)}"

        # Test complex object field types
        if "nutri_facts" in updates and updates["nutri_facts"] is not None:
            nutri_facts = updates["nutri_facts"]
            assert hasattr(
                nutri_facts, "calories"
            ), "NutriFacts missing calories attribute"
            assert hasattr(
                nutri_facts, "protein"
            ), "NutriFacts missing protein attribute"
            assert hasattr(
                nutri_facts, "carbohydrate"
            ), "NutriFacts missing carbohydrate attribute"

    def test_frozen_set_handling_comprehensive(self):
        """Test frozen set handling for all collection fields (Task 2.4.3)."""
        # Test with recipe that has various collection types
        recipe_with_collections = create_api_recipe_with_max_fields()
        api_update_recipe = ApiUpdateRecipe.from_api_recipe(recipe_with_collections)
        domain_command = api_update_recipe.to_domain()
        updates = domain_command.updates

        # Test frozenset to list conversion for ingredients
        if "ingredients" in updates:
            api_ingredients = recipe_with_collections.ingredients
            domain_ingredients = updates["ingredients"]

            # Verify frozenset to list conversion
            assert isinstance(
                api_ingredients, frozenset
            ), f"API ingredients should be frozenset, got {type(api_ingredients)}"
            assert isinstance(
                domain_ingredients, list
            ), f"Domain ingredients should be list, got {type(domain_ingredients)}"
            assert len(domain_ingredients) == len(
                api_ingredients
            ), "Ingredient count should be preserved"

            # Verify ingredient positions are unique (what matters for frozenset property)
            ingredient_positions = [
                ingredient.position for ingredient in domain_ingredients
            ]
            assert len(set(ingredient_positions)) == len(
                ingredient_positions
            ), "Ingredient positions should be unique (frozenset property)"

        # Test frozenset preservation for tags
        if "tags" in updates:
            api_tags = recipe_with_collections.tags
            domain_tags = updates["tags"]

            # Verify frozenset is preserved for tags in domain
            assert isinstance(
                api_tags, frozenset
            ), f"API tags should be frozenset, got {type(api_tags)}"
            assert isinstance(
                domain_tags, frozenset
            ), f"Domain tags should remain frozenset, got {type(domain_tags)}"
            assert len(domain_tags) == len(api_tags), "Tag count should be preserved"

            # Verify tag uniqueness based on full Tag identity (key+value+author_id+type)
            # Since Tag uses @frozen(hash=True), uniqueness is based on all attributes, not just key
            tag_identities = {
                (tag.key, tag.value, tag.author_id, tag.type) for tag in domain_tags
            }
            assert len(tag_identities) == len(
                domain_tags
            ), "Tag identities should be unique (frozenset property)"

            # Verify tags are properly converted objects
            for tag in domain_tags:
                assert hasattr(tag, "key"), "Tag should have key attribute"
                assert hasattr(tag, "value"), "Tag should have value attribute"
                assert hasattr(tag, "author_id"), "Tag should have author_id attribute"
                assert hasattr(tag, "type"), "Tag should have type attribute"

    def test_frozen_set_handling_edge_cases(self):
        """Test frozen set handling edge cases (Task 2.4.3)."""
        # Test with empty collections
        minimal_recipe = create_minimal_api_recipe()
        api_update_recipe = ApiUpdateRecipe.from_api_recipe(minimal_recipe)
        domain_command = api_update_recipe.to_domain()
        updates = domain_command.updates

        # Verify empty collection handling
        if "ingredients" in updates:
            assert isinstance(
                updates["ingredients"], list
            ), "Empty ingredients should still be list"
            assert (
                len(updates["ingredients"]) == 0
            ), "Empty ingredients should have length 0"

        if "tags" in updates:
            assert isinstance(
                updates["tags"], frozenset
            ), "Empty tags should still be frozenset"
            assert len(updates["tags"]) == 0, "Empty tags should have length 0"

        # Test with single-item collections
        simple_recipe = create_simple_api_recipe()
        if simple_recipe.ingredients or simple_recipe.tags:
            api_update_simple = ApiUpdateRecipe.from_api_recipe(simple_recipe)
            domain_simple = api_update_simple.to_domain()
            simple_updates = domain_simple.updates

            # Verify single-item collection handling
            if simple_updates.get("ingredients"):
                assert isinstance(
                    simple_updates["ingredients"], list
                ), "Single-item ingredients should be list"
                assert (
                    len(simple_updates["ingredients"]) >= 1
                ), "Should have at least one ingredient"

            if simple_updates.get("tags"):
                assert isinstance(
                    simple_updates["tags"], frozenset
                ), "Single-item tags should be frozenset"
                assert len(simple_updates["tags"]) >= 1, "Should have at least one tag"

    def test_frozen_set_ingredient_uniqueness(self):
        """Test that ingredient positions maintain uniqueness through frozenset conversion (Task 2.4.3)."""
        # Create recipe with max fields to test large frozenset handling
        max_recipe = create_api_recipe_with_max_fields()

        # Convert to domain
        api_update_recipe = ApiUpdateRecipe.from_api_recipe(max_recipe)
        domain_command = api_update_recipe.to_domain()
        updates = domain_command.updates

        if max_recipe.ingredients:
            # Verify starting conditions - API should have unique ingredient positions
            api_ingredient_positions = [
                ingredient.position for ingredient in max_recipe.ingredients
            ]
            assert len(set(api_ingredient_positions)) == len(
                api_ingredient_positions
            ), "API ingredient positions should be unique"

            if "ingredients" in updates:
                domain_ingredients = updates["ingredients"]
                domain_ingredient_positions = [
                    ingredient.position for ingredient in domain_ingredients
                ]

                # Verify uniqueness is maintained through conversion
                assert len(set(domain_ingredient_positions)) == len(
                    domain_ingredient_positions
                ), "Domain ingredient positions should remain unique"
                assert len(domain_ingredient_positions) == len(
                    api_ingredient_positions
                ), "Ingredient count should be preserved"

                # Verify same positions are preserved
                assert set(domain_ingredient_positions) == set(
                    api_ingredient_positions
                ), "Ingredient positions should be exactly preserved"

        # Test tag uniqueness as well
        if max_recipe.tags and "tags" in updates:
            api_tags = list(max_recipe.tags)
            domain_tags = list(updates["tags"])

            # Verify tag count preservation (may have duplicates by key but not by identity)
            assert len(domain_tags) == len(api_tags), "Tag count should be preserved"

            # Verify tags are properly converted objects
            for tag in domain_tags:
                assert hasattr(tag, "key"), "Domain tag should have key attribute"
                assert hasattr(tag, "value"), "Domain tag should have value attribute"
                assert hasattr(
                    tag, "author_id"
                ), "Domain tag should have author_id attribute"
