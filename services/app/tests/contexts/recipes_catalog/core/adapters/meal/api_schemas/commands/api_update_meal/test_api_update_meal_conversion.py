"""
Test suite for ApiUpdateMeal conversion logic (to_domain() methods).
Tests the conversion of ApiUpdateMeal instances to domain UpdateMeal commands.
"""

import pytest

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_update_meal import (
    ApiUpdateMeal,
    ApiAttributesToUpdateOnMeal
)
from src.contexts.recipes_catalog.core.domain.meal.commands.update_meal import UpdateMeal

# Import existing data factories
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.data_factories.api_meal_data_factories import (
    create_api_meal,
    create_simple_api_meal,
    create_complex_api_meal,
    create_minimal_api_meal,
    create_api_meal_with_max_recipes,
    create_conversion_method_test_scenarios,
    create_type_conversion_test_scenarios,
    REALISTIC_MEAL_SCENARIOS,
)


class TestApiUpdateMealConversion:
    """Test suite for ApiUpdateMeal to_domain() conversion methods."""

    def test_api_update_meal_to_domain_basic_conversion(self):
        """Test ApiUpdateMeal.to_domain() returns valid UpdateMeal."""
        # Create ApiUpdateMeal from simple meal
        api_meal = create_simple_api_meal()
        api_update_meal = ApiUpdateMeal.from_api_meal(api_meal)
        
        # Convert to domain
        domain_command = api_update_meal.to_domain()
        
        # Verify return type and structure
        assert isinstance(domain_command, UpdateMeal)
        assert domain_command.meal_id == api_update_meal.meal_id
        assert isinstance(domain_command.updates, dict)
        
        # Verify meal_id matches original
        assert domain_command.meal_id == api_meal.id

    def test_basic_update_meal_command_structure(self):
        """Test basic UpdateMeal command creation structure using create_api_meal()."""
        # Use basic api meal from factory as specified in task requirements
        api_meal = create_api_meal()
        api_update_meal = ApiUpdateMeal.from_api_meal(api_meal)
        
        # Convert to domain command
        domain_command = api_update_meal.to_domain()
        
        # Verify command structure
        assert isinstance(domain_command, UpdateMeal)
        assert hasattr(domain_command, 'meal_id')
        assert hasattr(domain_command, 'updates')
        
        # Verify meal_id is correctly set
        assert domain_command.meal_id == api_meal.id
        assert isinstance(domain_command.meal_id, str)
        
        # Verify updates dictionary structure
        assert isinstance(domain_command.updates, dict)
        assert len(domain_command.updates) > 0
        
        # Verify essential fields are present in updates
        assert "name" in domain_command.updates
        assert domain_command.updates["name"] == api_meal.name

    def test_update_meal_command_with_all_field_types(self):
        """Test UpdateMeal command creation with all supported field types."""
        # Create meal with comprehensive field coverage
        api_meal = create_api_meal()
        api_update_meal = ApiUpdateMeal.from_api_meal(api_meal)
        
        # Convert to domain
        domain_command = api_update_meal.to_domain()
        updates = domain_command.updates
        
        # Verify string fields
        assert isinstance(updates.get("name"), str)
        if "description" in updates:
            assert isinstance(updates["description"], (str, type(None)))
        if "notes" in updates:
            assert isinstance(updates["notes"], (str, type(None)))
        if "image_url" in updates:
            assert isinstance(updates["image_url"], (str, type(None)))
        
        # Verify UUID fields
        if "menu_id" in updates:
            assert isinstance(updates["menu_id"], (str, type(None)))
        
        # Verify boolean fields
        if "like" in updates:
            assert isinstance(updates["like"], (bool, type(None)))
        
        # Verify collection fields are converted to domain types
        if "recipes" in updates:
            assert isinstance(updates["recipes"], list)
            # Each recipe should be a domain recipe object
            for recipe in updates["recipes"]:
                assert hasattr(recipe, 'id')
                assert hasattr(recipe, 'name')
                
        if "tags" in updates:
            assert isinstance(updates["tags"], set)
            # Each tag should be a domain tag object
            for tag in updates["tags"]:
                assert hasattr(tag, 'key')
                assert hasattr(tag, 'value')

    @pytest.mark.parametrize("meal_factory", [
        create_api_meal,
        create_simple_api_meal,
        create_complex_api_meal,
    ])
    def test_update_meal_command_validation(self, meal_factory):
        """Test that generated UpdateMeal commands are valid domain objects."""
        api_meal = meal_factory()
        api_update_meal = ApiUpdateMeal.from_api_meal(api_meal)
        domain_command = api_update_meal.to_domain()
        
        # Verify command is valid UpdateMeal
        assert isinstance(domain_command, UpdateMeal)
        
        # Verify required attributes exist
        assert hasattr(domain_command, 'meal_id')
        assert hasattr(domain_command, 'updates')
        
        # Verify meal_id is valid UUID string
        assert isinstance(domain_command.meal_id, str)
        assert len(domain_command.meal_id.replace('-', '')) == 32  # UUID without hyphens
        
        # Verify updates is a dictionary
        assert isinstance(domain_command.updates, dict)

    def test_api_attributes_to_update_exclude_unset_behavior(self):
        """Test ApiAttributesToUpdateOnMeal.to_domain() with exclude_unset=True."""
        # Create ApiUpdateMeal with partial data
        api_meal = create_simple_api_meal()
        api_update_meal = ApiUpdateMeal.from_api_meal(api_meal)
        
        # Test exclude_unset behavior on the updates object
        updates_dict = api_update_meal.updates.to_domain()
        
        # Should be a dictionary with only set fields
        assert isinstance(updates_dict, dict)
        
        # Should contain expected fields from the API meal
        assert "name" in updates_dict
        assert updates_dict["name"] == api_meal.name
        
        # Should contain menu_id if it was set
        if api_meal.menu_id:
            assert "menu_id" in updates_dict
            assert updates_dict["menu_id"] == api_meal.menu_id

    @pytest.mark.parametrize("meal_factory", [
        create_simple_api_meal,
        create_complex_api_meal,
        create_api_meal_with_max_recipes,
        create_minimal_api_meal,
    ])
    def test_conversion_with_various_meal_configurations(self, meal_factory):
        """Test to_domain() conversion across different meal types."""
        api_meal = meal_factory()
        
        # Create update command from meal
        api_update_meal = ApiUpdateMeal.from_api_meal(api_meal)
        
        # Convert to domain
        domain_command = api_update_meal.to_domain()
        
        # Verify basic structure
        assert isinstance(domain_command, UpdateMeal)
        assert domain_command.meal_id == api_meal.id
        assert isinstance(domain_command.updates, dict)
        
        # Verify required fields are present
        assert "name" in domain_command.updates
        assert domain_command.updates["name"] == api_meal.name

    @pytest.mark.parametrize("scenario_data", REALISTIC_MEAL_SCENARIOS)
    def test_conversion_with_realistic_meal_scenarios(self, scenario_data):
        """Test conversion validation using REALISTIC_MEAL_SCENARIOS as specified in task requirements."""
        # Create meal using scenario data directly
        api_meal = create_api_meal(
            name=scenario_data["name"],
            description=scenario_data["description"],
            notes=scenario_data["notes"],
            like=scenario_data["like"]
        )
        
        # Create update command from realistic scenario meal
        api_update_meal = ApiUpdateMeal.from_api_meal(api_meal)
        
        # Convert to domain
        domain_command = api_update_meal.to_domain()
        
        # Verify conversion succeeded for realistic scenario
        assert isinstance(domain_command, UpdateMeal), f"Conversion failed for scenario: {scenario_data['name']}"
        assert domain_command.meal_id == api_meal.id, f"Meal ID mismatch for scenario: {scenario_data['name']}"
        assert isinstance(domain_command.updates, dict), f"Updates not dict for scenario: {scenario_data['name']}"
        
        # Verify essential fields are preserved
        assert "name" in domain_command.updates, f"Name missing for scenario: {scenario_data['name']}"
        assert domain_command.updates["name"] == api_meal.name, f"Name mismatch for scenario: {scenario_data['name']}"
        
        # Verify scenario-specific characteristics
        if api_meal.recipes:
            if "recipes" in domain_command.updates:
                assert len(domain_command.updates["recipes"]) == len(api_meal.recipes), \
                    f"Recipe count mismatch for scenario: {scenario_data['name']}"
        
        if api_meal.tags:
            if "tags" in domain_command.updates:
                assert len(domain_command.updates["tags"]) == len(api_meal.tags), \
                    f"Tag count mismatch for scenario: {scenario_data['name']}"

    @pytest.mark.parametrize("variant_name,meal_factory", [
        ("simple", create_simple_api_meal),
        ("complex", create_complex_api_meal),
        ("minimal", create_minimal_api_meal),
        ("with_max_recipes", create_api_meal_with_max_recipes),
        ("basic", create_api_meal),
    ])
    def test_conversion_with_meal_type_variants(self, variant_name, meal_factory):
        """Test conversion across different meal type variants from api_meal_data_factories."""
        api_meal = meal_factory()
        
        # Create update command
        api_update_meal = ApiUpdateMeal.from_api_meal(api_meal)
        
        # Convert to domain
        domain_command = api_update_meal.to_domain()
        
        # Verify conversion for each variant
        assert isinstance(domain_command, UpdateMeal), f"Conversion failed for variant: {variant_name}"
        assert domain_command.meal_id == api_meal.id, f"Meal ID mismatch for variant: {variant_name}"
        assert isinstance(domain_command.updates, dict), f"Updates not dict for variant: {variant_name}"
        
        # Verify name field is always present and correct
        assert "name" in domain_command.updates, f"Name missing for variant: {variant_name}"
        assert domain_command.updates["name"] == api_meal.name, f"Name mismatch for variant: {variant_name}"
        
        # Verify variant-specific characteristics
        if variant_name == "minimal":
            # Minimal meals should have fewer fields set
            essential_fields = {"name", "menu_id"}
            update_fields = set(domain_command.updates.keys())
            assert essential_fields.issubset(update_fields), \
                f"Essential fields missing for minimal variant: {essential_fields - update_fields}"
        
        elif variant_name == "complex":
            # Complex meals should have many fields set including collections
            assert "name" in domain_command.updates
            # Should have either recipes or tags or both for complex meals
            has_collections = "recipes" in domain_command.updates or "tags" in domain_command.updates
            assert has_collections, f"Complex variant should have collection fields"
        
        elif variant_name == "with_max_recipes":
            # Should have recipes collection
            if "recipes" in domain_command.updates:
                assert len(domain_command.updates["recipes"]) > 0, \
                    f"Max recipes variant should have recipes"

    @pytest.mark.parametrize("meal_factory", [
        create_api_meal,
        create_simple_api_meal,
        create_complex_api_meal,
    ])
    def test_meal_configuration_field_consistency(self, meal_factory):
        """Test that field values are consistently converted across different meal configurations."""
        api_meal = meal_factory()
        api_update_meal = ApiUpdateMeal.from_api_meal(api_meal)
        domain_command = api_update_meal.to_domain()
        updates = domain_command.updates
        
        # Verify field type consistency
        if "name" in updates:
            assert isinstance(updates["name"], str)
            assert len(updates["name"]) > 0
        
        if "description" in updates:
            assert isinstance(updates["description"], (str, type(None)))
        
        if "menu_id" in updates:
            assert isinstance(updates["menu_id"], (str, type(None)))
            if updates["menu_id"]:
                # Should be valid UUID format
                assert len(updates["menu_id"].replace('-', '')) == 32
        
        if "recipes" in updates:
            assert isinstance(updates["recipes"], list)
            for recipe in updates["recipes"]:
                # Each recipe should be a domain recipe with required attributes
                assert hasattr(recipe, 'id')
                assert hasattr(recipe, 'name')
                assert hasattr(recipe, 'meal_id')
                assert recipe.meal_id == api_meal.id  # Recipe should belong to this meal
        
        if "tags" in updates:
            assert isinstance(updates["tags"], set)
            for tag in updates["tags"]:
                # Each tag should be a domain tag with required attributes
                assert hasattr(tag, 'key')
                assert hasattr(tag, 'value')
                assert hasattr(tag, 'author_id')
                assert tag.author_id == api_meal.author_id  # Tag should belong to meal author 

    # ========================================
    # EDGE CASE TESTS (Tasks 2.3.1 - 2.3.3)
    # ========================================

    def test_conversion_with_empty_minimal_updates(self):
        """Test conversion with empty/minimal updates (Task 2.3.1)."""
        # Test with minimal api meal that has only required fields
        minimal_meal = create_minimal_api_meal()
        api_update_meal = ApiUpdateMeal.from_api_meal(minimal_meal)
        
        # Convert to domain
        domain_command = api_update_meal.to_domain()
        
        # Verify basic structure works with minimal data
        assert isinstance(domain_command, UpdateMeal)
        assert domain_command.meal_id == minimal_meal.id
        assert isinstance(domain_command.updates, dict)
        
        # Should have at least name and menu_id
        assert "name" in domain_command.updates
        assert "menu_id" in domain_command.updates
        assert domain_command.updates["name"] == minimal_meal.name
        assert domain_command.updates["menu_id"] == minimal_meal.menu_id
        
        # Optional fields should not be in updates if not set
        updates_dict = api_update_meal.updates.to_domain()
        expected_minimal_fields = {"name", "menu_id"}
        
        # Check that only set fields are included
        for field_name in updates_dict.keys():
            if field_name not in expected_minimal_fields:
                # If additional fields exist, they should have valid values
                field_value = updates_dict[field_name]
                assert field_value is not None or field_name in ["description", "notes", "image_url", "like"]
        
        # Verify exclude_unset behavior works with minimal data
        assert len(updates_dict) >= 2  # At least name and menu_id
        assert "name" in updates_dict
        assert "menu_id" in updates_dict

    def test_conversion_with_truly_empty_optional_fields(self):
        """Test conversion handles truly empty optional fields correctly (Task 2.3.1 edge case)."""
        # Create minimal meal and manually create ApiUpdateMeal with minimal fields
        minimal_meal = create_minimal_api_meal()
        
        # Create ApiAttributesToUpdateOnMeal with only required fields set
        updates = ApiAttributesToUpdateOnMeal(
            name=minimal_meal.name,
            menu_id=minimal_meal.menu_id,
            description=None,
            recipes=[],
            tags=frozenset(),
            notes=None,
            like=None,
            image_url=None
        )
        
        api_update_meal = ApiUpdateMeal(
            meal_id=minimal_meal.id,
            updates=updates
        )
        
        # Convert to domain
        domain_command = api_update_meal.to_domain()
        
        # Verify structure
        assert isinstance(domain_command, UpdateMeal)
        assert domain_command.meal_id == minimal_meal.id
        
        # Verify only set fields are in the updates
        updates_dict = api_update_meal.updates.to_domain()
        assert "name" in updates_dict
        assert "menu_id" in updates_dict
        assert updates_dict["name"] == minimal_meal.name
        assert updates_dict["menu_id"] == minimal_meal.menu_id
        
        # Should not have unset optional fields in exclude_unset mode
        unset_fields = {"description", "notes", "image_url", "like"}
        for field in unset_fields:
            if field in updates_dict:
                # If present, should have been explicitly set
                assert hasattr(updates, field)

    def test_complex_nested_object_conversion_comprehensive(self):
        """Test complex nested object conversion thoroughly (Task 2.3.2)."""
        # Test with complex meal containing nested recipes and tags
        complex_meal = create_complex_api_meal()
        api_update_meal = ApiUpdateMeal.from_api_meal(complex_meal)
        
        # Convert to domain
        domain_command = api_update_meal.to_domain()
        updates = domain_command.updates
        
        # Verify basic structure
        assert isinstance(domain_command, UpdateMeal)
        assert domain_command.meal_id == complex_meal.id
        
        # Test nested recipe conversion if recipes exist
        if complex_meal.recipes and "recipes" in updates:
            recipes = updates["recipes"]
            assert isinstance(recipes, list)
            assert len(recipes) == len(complex_meal.recipes)
            
            for i, domain_recipe in enumerate(recipes):
                api_recipe = complex_meal.recipes[i]
                
                # Verify recipe structure and field conversion
                assert hasattr(domain_recipe, 'id')
                assert hasattr(domain_recipe, 'name')
                assert hasattr(domain_recipe, 'meal_id')
                assert hasattr(domain_recipe, 'author_id')
                
                # Verify field values are correctly converted
                assert domain_recipe.id == api_recipe.id
                assert domain_recipe.name == api_recipe.name
                assert domain_recipe.meal_id == complex_meal.id
                assert domain_recipe.author_id == complex_meal.author_id
                
                # Verify nested tags within recipes if they exist
                if hasattr(api_recipe, 'tags') and api_recipe.tags:
                    assert hasattr(domain_recipe, 'tags')
                    assert isinstance(domain_recipe.tags, set)
                    assert len(domain_recipe.tags) == len(api_recipe.tags)
        
        # Test nested tag conversion if tags exist
        if complex_meal.tags and "tags" in updates:
            tags = updates["tags"]
            assert isinstance(tags, set)
            assert len(tags) == len(complex_meal.tags)
            
            # Create mappings by key for comparison (tags are sets, order not guaranteed)
            domain_tags_by_key = {tag.key: tag for tag in tags}
            api_tags_by_key = {tag.key: tag for tag in complex_meal.tags}
            
            # Verify all tags are converted correctly
            assert set(domain_tags_by_key.keys()) == set(api_tags_by_key.keys())
            
            for key in domain_tags_by_key.keys():
                domain_tag = domain_tags_by_key[key]
                api_tag = api_tags_by_key[key]
                
                # Verify tag structure and field conversion
                assert hasattr(domain_tag, 'key')
                assert hasattr(domain_tag, 'value')
                assert hasattr(domain_tag, 'author_id')
                
                # Verify field values are correctly converted
                assert domain_tag.key == api_tag.key
                assert domain_tag.value == api_tag.value
                assert domain_tag.author_id == complex_meal.author_id

    def test_max_recipes_nested_object_conversion(self):
        """Test conversion with maximum number of nested recipes (Task 2.3.2)."""
        # Test with meal containing maximum recipes
        max_recipes_meal = create_api_meal_with_max_recipes()
        api_update_meal = ApiUpdateMeal.from_api_meal(max_recipes_meal)
        
        # Convert to domain
        domain_command = api_update_meal.to_domain()
        updates = domain_command.updates
        
        # Verify structure with maximum nested objects
        assert isinstance(domain_command, UpdateMeal)
        assert domain_command.meal_id == max_recipes_meal.id
        
        # Should handle large number of nested recipes
        if max_recipes_meal.recipes and "recipes" in updates:
            recipes = updates["recipes"]
            assert isinstance(recipes, list)
            assert len(recipes) == len(max_recipes_meal.recipes)
            
            # Verify each recipe in large collection is properly converted
            for domain_recipe in recipes:
                assert hasattr(domain_recipe, 'id')
                assert hasattr(domain_recipe, 'name')
                assert hasattr(domain_recipe, 'meal_id')
                assert domain_recipe.meal_id == max_recipes_meal.id
                
                # Verify ID format (should be UUID string)
                assert isinstance(domain_recipe.id, str)
                assert len(domain_recipe.id.replace('-', '')) == 32
        
        # Performance consideration: conversion should complete in reasonable time
        # (This is implicitly tested by the test not timing out)

    def test_uuid_field_edge_cases(self):
        """Test UUID field handling edge cases (Task 2.3.3)."""
        # Test with standard UUID formats
        api_meal = create_api_meal()
        api_update_meal = ApiUpdateMeal.from_api_meal(api_meal)
        
        # Convert to domain
        domain_command = api_update_meal.to_domain()
        
        # Verify UUID format consistency
        meal_id = domain_command.meal_id
        assert isinstance(meal_id, str)
        
        # Verify UUID string format (with or without hyphens)
        clean_uuid = meal_id.replace('-', '')
        assert len(clean_uuid) == 32
        assert all(c in '0123456789abcdefABCDEF' for c in clean_uuid)
        
        # Test with None menu_id (should handle gracefully)
        minimal_meal = create_minimal_api_meal()
        if minimal_meal.menu_id is None:
            api_update_minimal = ApiUpdateMeal.from_api_meal(minimal_meal)
            domain_minimal = api_update_minimal.to_domain()
            updates = domain_minimal.updates
            
            # Should handle None menu_id appropriately
            if "menu_id" in updates:
                assert updates["menu_id"] is None or isinstance(updates["menu_id"], str)

    @pytest.mark.parametrize("scenario_name,scenario_data", 
                            [(name, data) for name, data in create_type_conversion_test_scenarios().get("uuid_string_conversions", {}).items()])
    def test_uuid_field_validation_comprehensive(self, scenario_name, scenario_data):
        """Test UUID field validation across all scenarios (Task 2.3.3)."""
        # Extract the meal from the scenario data
        api_meal = scenario_data["meal"]  # This is already an ApiMeal instance
        api_update_meal = ApiUpdateMeal.from_api_meal(api_meal)
        
        # Convert to domain
        domain_command = api_update_meal.to_domain()
        updates = domain_command.updates
        
        # Verify meal_id is always a valid UUID string
        assert isinstance(domain_command.meal_id, str)
        assert len(domain_command.meal_id.replace('-', '')) == 32
        assert domain_command.meal_id == api_meal.id
        
        # Verify menu_id UUID handling if present
        if "menu_id" in updates and updates["menu_id"] is not None:
            menu_id = updates["menu_id"]
            assert isinstance(menu_id, str)
            assert len(menu_id.replace('-', '')) == 32
            assert menu_id == api_meal.menu_id
        
        # Verify recipe IDs are valid UUIDs if recipes exist
        if "recipes" in updates and updates["recipes"]:
            for recipe in updates["recipes"]:
                assert isinstance(recipe.id, str)
                assert len(recipe.id.replace('-', '')) == 32
                assert isinstance(recipe.meal_id, str)
                assert recipe.meal_id == api_meal.id

    def test_frozen_set_handling_for_recipe_ids(self):
        """Test frozen set conversion for recipe IDs (Task 2.3.3 - collections)."""
        # Test with meal containing multiple recipes to test frozenset handling
        complex_meal = create_complex_api_meal()
        
        if complex_meal.recipes:
            api_update_meal = ApiUpdateMeal.from_api_meal(complex_meal)
            domain_command = api_update_meal.to_domain()
            updates = domain_command.updates
            
            # Verify recipe collection conversion
            if "recipes" in updates:
                recipes = updates["recipes"]
                assert isinstance(recipes, list)  # Should be list in domain, not frozenset
                
                # Extract recipe IDs
                recipe_ids = [recipe.id for recipe in recipes]
                api_recipe_ids = [recipe.id for recipe in complex_meal.recipes]
                
                # Verify all recipe IDs are preserved and valid
                assert len(recipe_ids) == len(api_recipe_ids)
                
                for recipe_id in recipe_ids:
                    assert isinstance(recipe_id, str)
                    assert len(recipe_id.replace('-', '')) == 32
                    assert recipe_id in api_recipe_ids
                
                # Verify no duplicate recipe IDs
                assert len(set(recipe_ids)) == len(recipe_ids)
        
        # Test with max recipes meal for larger frozenset handling
        max_meal = create_api_meal_with_max_recipes()
        if max_meal.recipes:
            api_update_max = ApiUpdateMeal.from_api_meal(max_meal)
            domain_max = api_update_max.to_domain()
            max_updates = domain_max.updates
            
            if "recipes" in max_updates:
                max_recipes = max_updates["recipes"]
                assert isinstance(max_recipes, list)
                
                # Verify large collection handling
                assert len(max_recipes) == len(max_meal.recipes)
                
                # Verify all UUIDs are valid in large collection
                for recipe in max_recipes:
                    assert isinstance(recipe.id, str)
                    assert len(recipe.id.replace('-', '')) == 32 

    # ============================================
    # SECTION 2.4: UpdateMeal Command Structure Validation
    # ============================================

    @pytest.mark.parametrize("scenario_name,scenario_data", 
                            [(name, data) for name, data in create_conversion_method_test_scenarios().get("api_to_domain_conversion", {}).items() if "setup" in data])
    def test_command_structure_consistency_comprehensive(self, scenario_name, scenario_data):
        """Test command structure consistency across different meal types (Task 2.4.1)."""
        # Get the API meal from the scenario
        api_meal = scenario_data["setup"]()
        api_update_meal = ApiUpdateMeal.from_api_meal(api_meal)
        
        # Convert to domain command
        domain_command = api_update_meal.to_domain()
        
        # Verify consistent command structure
        assert isinstance(domain_command, UpdateMeal), f"Command type inconsistent for scenario: {scenario_name}"
        assert hasattr(domain_command, 'meal_id'), f"Missing meal_id for scenario: {scenario_name}"
        assert hasattr(domain_command, 'updates'), f"Missing updates for scenario: {scenario_name}"
        
        # Verify meal_id consistency
        assert isinstance(domain_command.meal_id, str), f"meal_id type inconsistent for scenario: {scenario_name}"
        assert domain_command.meal_id == api_meal.id, f"meal_id value inconsistent for scenario: {scenario_name}"
        
        # Verify updates structure consistency
        assert isinstance(domain_command.updates, dict), f"updates type inconsistent for scenario: {scenario_name}"
        
        # Verify required fields are always present
        assert "name" in domain_command.updates, f"name missing from updates for scenario: {scenario_name}"
        assert isinstance(domain_command.updates["name"], str), f"name type inconsistent for scenario: {scenario_name}"
        assert domain_command.updates["name"] == api_meal.name, f"name value inconsistent for scenario: {scenario_name}"

    @pytest.mark.parametrize("factory_name,meal_factory", [
        ("create_api_meal", create_api_meal),
        ("create_simple_api_meal", create_simple_api_meal),
        ("create_complex_api_meal", create_complex_api_meal),
        ("create_minimal_api_meal", create_minimal_api_meal),
        ("create_api_meal_with_max_recipes", create_api_meal_with_max_recipes),
    ])
    def test_command_structure_with_different_meal_factories(self, factory_name, meal_factory):
        """Test command structure consistency across all meal factory types (Task 2.4.1)."""
        api_meal = meal_factory()
        api_update_meal = ApiUpdateMeal.from_api_meal(api_meal)
        domain_command = api_update_meal.to_domain()
        
        # Verify command structure is consistent regardless of factory
        assert isinstance(domain_command, UpdateMeal), f"Command structure inconsistent for {factory_name}"
        assert isinstance(domain_command.meal_id, str), f"meal_id structure inconsistent for {factory_name}"
        assert isinstance(domain_command.updates, dict), f"updates structure inconsistent for {factory_name}"
        
        # Verify command follows the same pattern
        assert len(domain_command.meal_id.replace('-', '')) == 32, f"meal_id format inconsistent for {factory_name}"
        assert "name" in domain_command.updates, f"Required field missing for {factory_name}"
        
        # Verify updates dictionary has valid structure
        for field_name, field_value in domain_command.updates.items():
            assert isinstance(field_name, str), f"Field name not string in {factory_name}: {field_name}"
            # Field values can be various types, but should not be undefined
            assert field_value is not ..., f"Undefined field value in {factory_name}: {field_name}"

    def test_command_field_types_comprehensive(self):
        """Test all command field types are correctly converted (Task 2.4.2)."""
        # Create a complex meal to test all field types
        complex_meal = create_complex_api_meal()
        api_update_meal = ApiUpdateMeal.from_api_meal(complex_meal)
        domain_command = api_update_meal.to_domain()
        updates = domain_command.updates
        
        # Test string field types
        string_fields = ["name", "description", "notes", "image_url"]
        for field in string_fields:
            if field in updates:
                assert isinstance(updates[field], (str, type(None))), f"String field {field} has wrong type: {type(updates[field])}"
                if updates[field] is not None:
                    assert len(updates[field]) >= 0, f"String field {field} has invalid length"
        
        # Test UUID field types
        uuid_fields = ["menu_id"]
        for field in uuid_fields:
            if field in updates and updates[field] is not None:
                assert isinstance(updates[field], str), f"UUID field {field} is not string: {type(updates[field])}"
                assert len(updates[field].replace('-', '')) == 32, f"UUID field {field} has invalid format: {updates[field]}"
        
        # Test boolean field types
        boolean_fields = ["like"]
        for field in boolean_fields:
            if field in updates:
                assert isinstance(updates[field], (bool, type(None))), f"Boolean field {field} has wrong type: {type(updates[field])}"
        
        # Test collection field types
        if "recipes" in updates:
            assert isinstance(updates["recipes"], list), f"recipes field is not list: {type(updates['recipes'])}"
            for recipe in updates["recipes"]:
                # Each recipe should be a domain recipe object with proper attributes
                assert hasattr(recipe, 'id'), "Recipe missing id attribute"
                assert hasattr(recipe, 'name'), "Recipe missing name attribute"
                assert hasattr(recipe, 'meal_id'), "Recipe missing meal_id attribute"
                assert isinstance(recipe.id, str), f"Recipe id wrong type: {type(recipe.id)}"
                assert isinstance(recipe.name, str), f"Recipe name wrong type: {type(recipe.name)}"
                assert isinstance(recipe.meal_id, str), f"Recipe meal_id wrong type: {type(recipe.meal_id)}"
        
        if "tags" in updates:
            assert isinstance(updates["tags"], set), f"tags field is not set: {type(updates['tags'])}"
            for tag in updates["tags"]:
                # Each tag should be a domain tag object with proper attributes
                assert hasattr(tag, 'key'), "Tag missing key attribute"
                assert hasattr(tag, 'value'), "Tag missing value attribute"
                assert hasattr(tag, 'author_id'), "Tag missing author_id attribute"
                assert isinstance(tag.key, str), f"Tag key wrong type: {type(tag.key)}"
                assert isinstance(tag.value, str), f"Tag value wrong type: {type(tag.value)}"
                assert isinstance(tag.author_id, str), f"Tag author_id wrong type: {type(tag.author_id)}"

    @pytest.mark.parametrize("scenario_name,scenario_data", 
                            [(name, data) for name, data in create_type_conversion_test_scenarios().get("collection_conversions", {}).items()])
    def test_command_field_types_with_type_scenarios(self, scenario_name, scenario_data):
        """Test command field types using type conversion scenarios (Task 2.4.2)."""
        api_meal = scenario_data["meal"]
        api_update_meal = ApiUpdateMeal.from_api_meal(api_meal)
        domain_command = api_update_meal.to_domain()
        updates = domain_command.updates
        
        # Verify collection field types are handled correctly
        collection_fields = scenario_data.get("collection_fields", [])
        
        for field_name in collection_fields:
            if field_name in updates:
                if field_name == "recipes":
                    assert isinstance(updates[field_name], list), f"recipes should be list, got {type(updates[field_name])}"
                elif field_name == "tags":
                    assert isinstance(updates[field_name], set), f"tags should be set, got {type(updates[field_name])}"
                    
                    # Verify frozenset to set conversion worked correctly
                    api_tags = getattr(api_meal, field_name, frozenset())
                    domain_tags = updates[field_name]
                    assert len(domain_tags) == len(api_tags), f"Tag count mismatch after conversion"

    def test_frozen_set_handling_comprehensive(self):
        """Test frozen set handling for all collection fields (Task 2.4.3)."""
        # Test with meal that has various collection types
        meal_with_collections = create_api_meal_with_max_recipes()
        api_update_meal = ApiUpdateMeal.from_api_meal(meal_with_collections)
        domain_command = api_update_meal.to_domain()
        updates = domain_command.updates
        
        # Test frozenset to list conversion for recipes
        if "recipes" in updates:
            api_recipes = meal_with_collections.recipes
            domain_recipes = updates["recipes"]
            
            # Verify frozenset/list conversion
            assert isinstance(api_recipes, list), f"API recipes should be list, got {type(api_recipes)}"
            assert isinstance(domain_recipes, list), f"Domain recipes should be list, got {type(domain_recipes)}"
            assert len(domain_recipes) == len(api_recipes), "Recipe count should be preserved"
            
            # Verify no duplicates (frozenset property maintained)
            recipe_ids = [recipe.id for recipe in domain_recipes]
            assert len(set(recipe_ids)) == len(recipe_ids), "Recipe IDs should be unique (frozenset property)"
        
        # Test frozenset to set conversion for tags
        if "tags" in updates:
            api_tags = meal_with_collections.tags
            domain_tags = updates["tags"]
            
            # Verify frozenset to set conversion
            assert isinstance(api_tags, frozenset), f"API tags should be frozenset, got {type(api_tags)}"
            assert isinstance(domain_tags, set), f"Domain tags should be set, got {type(domain_tags)}"
            assert len(domain_tags) == len(api_tags), "Tag count should be preserved"
            
            # Verify unique elements (frozenset property maintained)
            tag_keys = [tag.key for tag in domain_tags]
            assert len(set(tag_keys)) == len(tag_keys), "Tag keys should be unique (frozenset property)"

    def test_frozen_set_handling_edge_cases(self):
        """Test frozen set handling edge cases (Task 2.4.3)."""
        # Test with empty collections
        minimal_meal = create_minimal_api_meal()
        api_update_meal = ApiUpdateMeal.from_api_meal(minimal_meal)
        domain_command = api_update_meal.to_domain()
        updates = domain_command.updates
        
        # Verify empty collection handling
        if "recipes" in updates:
            assert isinstance(updates["recipes"], list), "Empty recipes should still be list"
            assert len(updates["recipes"]) == 0, "Empty recipes should have length 0"
        
        if "tags" in updates:
            assert isinstance(updates["tags"], set), "Empty tags should still be set"
            assert len(updates["tags"]) == 0, "Empty tags should have length 0"
        
        # Test with single-item collections
        simple_meal = create_simple_api_meal()
        if simple_meal.recipes or simple_meal.tags:
            api_update_simple = ApiUpdateMeal.from_api_meal(simple_meal)
            domain_simple = api_update_simple.to_domain()
            simple_updates = domain_simple.updates
            
            # Verify single-item collection handling
            if "recipes" in simple_updates and simple_updates["recipes"]:
                assert isinstance(simple_updates["recipes"], list), "Single-item recipes should be list"
                assert len(simple_updates["recipes"]) >= 1, "Should have at least one recipe"
            
            if "tags" in simple_updates and simple_updates["tags"]:
                assert isinstance(simple_updates["tags"], set), "Single-item tags should be set"
                assert len(simple_updates["tags"]) >= 1, "Should have at least one tag"

    def test_frozen_set_recipe_id_uniqueness(self):
        """Test that recipe IDs maintain uniqueness through frozenset conversion (Task 2.4.3)."""
        # Create meal with maximum recipes to test large frozenset handling
        max_meal = create_api_meal_with_max_recipes()
        
        # Verify starting conditions - API should have unique recipe IDs
        assert max_meal.recipes is not None
        api_recipe_ids = [recipe.id for recipe in max_meal.recipes]
        assert len(set(api_recipe_ids)) == len(api_recipe_ids), "API recipe IDs should be unique"
        
        # Convert to domain
        api_update_meal = ApiUpdateMeal.from_api_meal(max_meal)
        domain_command = api_update_meal.to_domain()
        updates = domain_command.updates
        
        if "recipes" in updates:
            domain_recipes = updates["recipes"]
            domain_recipe_ids = [recipe.id for recipe in domain_recipes]
            
            # Verify uniqueness is maintained through conversion
            assert len(set(domain_recipe_ids)) == len(domain_recipe_ids), "Domain recipe IDs should remain unique"
            assert len(domain_recipe_ids) == len(api_recipe_ids), "Recipe count should be preserved"
            
            # Verify same IDs are preserved
            assert set(domain_recipe_ids) == set(api_recipe_ids), "Recipe IDs should be exactly preserved"
        
        # Test tag uniqueness as well
        if max_meal.tags and "tags" in updates:
            api_tag_keys = [tag.key for tag in max_meal.tags]
            domain_tag_keys = [tag.key for tag in updates["tags"]]
            
            # Verify tag uniqueness through conversion
            assert len(set(domain_tag_keys)) == len(domain_tag_keys), "Domain tag keys should be unique"
            assert set(domain_tag_keys) == set(api_tag_keys), "Tag keys should be exactly preserved" 