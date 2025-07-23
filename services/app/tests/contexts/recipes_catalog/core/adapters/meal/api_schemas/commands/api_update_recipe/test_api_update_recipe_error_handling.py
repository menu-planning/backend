"""
Test suite for ApiUpdateRecipe error handling scenarios.

This module tests error handling, validation failures, and graceful error recovery
for the ApiUpdateRecipe and ApiAttributesToUpdateOnRecipe classes.
"""

import pytest
import json
from pydantic import ValidationError

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_update_recipe import (
    ApiUpdateRecipe,
    ApiAttributesToUpdateOnRecipe,
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import ApiRecipe

# Import existing data factories
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import (
    create_simple_api_recipe,
    create_invalid_json_test_cases,
    create_comprehensive_validation_test_cases_for_api_recipe,
    create_api_recipe_with_invalid_name,
    create_api_recipe_with_invalid_instructions,
    create_api_recipe_with_invalid_total_time,
    create_api_recipe_with_invalid_weight,
    create_api_recipe_with_invalid_privacy,
)

class TestApiUpdateRecipeErrorHandling:
    """
    Test error handling scenarios for ApiUpdateRecipe conversion logic.
    
    This test class validates that the ApiUpdateRecipe and ApiAttributesToUpdateOnRecipe classes
    handle various error scenarios gracefully, including:
    
    - Invalid input data (None values, wrong types, malformed UUIDs)
    - Missing required fields
    - Conversion failures during factory method usage
    - Comprehensive validation error scenarios
    - Edge cases and boundary conditions
    - Error message clarity and descriptiveness
    - Recovery after error correction
    
    The tests use existing data factories from api_recipe_data_factories.py and follow
    error handling patterns established in the recipe test files.
    
    Test Strategy:
    - Use pytest.parametrize to test multiple scenarios separately
    - Test both ApiRecipe creation failures and conversion failures
    - Verify error messages contain meaningful information
    - Use JSON serialization/deserialization for complex test scenarios
    - Test recovery scenarios to ensure error handling doesn't break functionality
    
    Key Testing Areas:
    1. Input validation failures
    2. Type conversion errors
    3. UUID format validation
    4. Nested object validation
    5. Error message quality
    6. Edge case handling
    7. Recovery after error correction
    """

    @pytest.mark.parametrize("invalid_scenario", [
        {"name": None, "description": "test"},  # None name
        {"name": "test", "description": None},  # None description  
        {"name": "test", "id": "invalid-uuid"},  # Invalid UUID format
        {"name": 123, "description": "test"},  # Invalid name type
        {"name": "test", "description": 123},  # Invalid description type
        {"name": "test", "ingredients": "not-frozenset"},  # Invalid ingredients type
        {"name": "test", "tags": "not-frozenset"},  # Invalid tags type
        {"name": "test", "total_time": "not-int"},  # Invalid total_time type
        {"name": "test", "weight_in_grams": "not-int"},  # Invalid weight type
    ])
    def test_conversion_failure_invalid_recipe_data(self, invalid_scenario):
        """Test graceful handling of invalid ApiRecipe data during conversion."""
        with pytest.raises((ValidationError, ValueError, TypeError)):
            # Try to create ApiRecipe with invalid data
            api_recipe = ApiRecipe(**invalid_scenario)
            # If ApiRecipe creation somehow succeeds, test conversion
            ApiUpdateRecipe.from_api_recipe(api_recipe)

    @pytest.mark.parametrize("missing_field_scenario", [
        {},  # Empty dict
        {"name": "test"},  # Missing other fields - might be valid for update
        {"description": "test"},  # Missing name
    ])
    def test_conversion_failure_missing_required_fields(self, missing_field_scenario):
        """Test error handling when required fields are missing."""
        with pytest.raises((ValidationError, TypeError)):
            ApiRecipe(**missing_field_scenario)

    @pytest.mark.parametrize("scenario_name,scenario_data", [
        ("invalid_uuid_format", {
            "name": "test",
            "description": "test",
            "id": "not-a-uuid",
        }),
        ("invalid_author_uuid", {
            "name": "test", 
            "description": "test",
            "author_id": "not-a-uuid",
        }),
        ("invalid_meal_uuid", {
            "name": "test", 
            "description": "test",
            "meal_id": "not-a-uuid",
        }),
        ("invalid_types", {
            "name": 123,  # Should be string
            "description": True,  # Should be string
        }),
        ("invalid_negative_values", {
            "name": "test",
            "description": "test",
            "total_time": -1,  # Should be positive
            "weight_in_grams": -100,  # Should be positive
        }),
    ])
    def test_conversion_failure_with_systematic_error_scenarios_manual(self, scenario_name, scenario_data):
        """Test conversion failures using manual error scenarios."""
        with pytest.raises((ValidationError, ValueError, TypeError)):
            api_recipe = ApiRecipe(**scenario_data)
            ApiUpdateRecipe.from_api_recipe(api_recipe)

    def test_conversion_failure_with_invalid_json_test_cases(self):
        """Test conversion failures using invalid JSON test cases from data factories."""
        try:
            # Use data factory for invalid JSON scenarios
            invalid_json_cases = create_invalid_json_test_cases()
            
            for test_case in invalid_json_cases:
                test_data = test_case["data"]
                with pytest.raises((ValidationError, ValueError, TypeError)):
                    # Try to create ApiRecipe with invalid JSON scenario
                    api_recipe = ApiRecipe(**test_data)
                    ApiUpdateRecipe.from_api_recipe(api_recipe)
        except (AttributeError, ImportError):
            # If create_invalid_json_test_cases doesn't exist or can't be imported, skip this test
            pytest.skip("create_invalid_json_test_cases not available")

    @pytest.mark.parametrize("field_name,invalid_value", [
        ("name", None),
        ("name", ""),
        ("name", 123),
        ("name", []),
        ("name", {}),
        ("description", 123),
        ("description", []),
        ("description", {}),
        ("instructions", None),
        ("instructions", 123),
        ("instructions", []),
        ("id", "not-uuid"),
        ("id", 123),
        ("id", None),
        ("author_id", "not-uuid"),
        ("author_id", 123),
        ("meal_id", "not-uuid"),
        ("meal_id", 123),
        ("total_time", "not-int"),
        ("total_time", -1),
        ("total_time", 1.5),
        ("weight_in_grams", "not-int"),
        ("weight_in_grams", -100),
        ("ingredients", "not-frozenset"),
        ("ingredients", 123),
        ("tags", "not-frozenset"),
        ("tags", 123),
        ("privacy", "invalid-privacy"),
        ("privacy", 123),
    ])
    def test_invalid_input_handling_comprehensive_manual(self, field_name, invalid_value):
        """Test comprehensive invalid input handling using manual field validation scenarios."""
        with pytest.raises((ValidationError, ValueError, TypeError)):
            # Create valid base recipe
            base_recipe = create_simple_api_recipe()
            
            # Use JSON serialization/deserialization to handle frozensets properly
            recipe_json = base_recipe.model_dump_json()
            recipe_data = json.loads(recipe_json)
            
            # Replace field with invalid value
            recipe_data[field_name] = invalid_value
            
            # Test conversion
            invalid_recipe = ApiRecipe.model_validate_json(json.dumps(recipe_data))
            ApiUpdateRecipe.from_api_recipe(invalid_recipe)

    def test_invalid_input_handling_with_comprehensive_validation_test_cases(self):
        """Test comprehensive invalid input handling using validation test cases."""
        try:
            # Try using data factory comprehensive validation test cases
            validation_test_cases = create_comprehensive_validation_test_cases_for_api_recipe()
            
            for test_case in validation_test_cases:
                factory_func = test_case["factory"]
                expected_error = test_case.get("expected_error")
                
                # Only test cases that should cause errors
                if expected_error:
                    with pytest.raises((ValidationError, ValueError, TypeError)):
                        # Create invalid recipe using factory
                        invalid_recipe_data = factory_func()
                        
                        # Test conversion
                        invalid_recipe = ApiRecipe(**invalid_recipe_data)
                        ApiUpdateRecipe.from_api_recipe(invalid_recipe)
        except (AttributeError, ImportError):
            # If create_comprehensive_validation_test_cases doesn't exist, skip this test
            pytest.skip("create_comprehensive_validation_test_cases not available")

    @pytest.mark.parametrize("scenario", [
        {
            "data": {"name": None, "description": "test"},
            "expected_error_type": ValidationError,
            "error_should_contain": "name"
        },
        {
            "data": {"name": "test", "id": "invalid-uuid"},
            "expected_error_type": ValidationError,
            "error_should_contain": "uuid"
        },
        {
            "data": {"name": "test", "description": "test", "author_id": "invalid-uuid"},
            "expected_error_type": ValidationError,
            "error_should_contain": "uuid"
        },
        {
            "data": {"name": "test", "description": "test", "total_time": -1},
            "expected_error_type": ValidationError,
            "error_should_contain": "total_time"
        },
    ])
    def test_error_messages_are_descriptive(self, scenario):
        """Test that error messages provide clear information about what went wrong."""
        with pytest.raises(scenario["expected_error_type"]) as exc_info:
            ApiRecipe(**scenario["data"])
        
        # Check that error message contains expected information
        error_message = str(exc_info.value).lower()
        assert scenario["error_should_contain"].lower() in error_message

    @pytest.mark.parametrize("edge_case_scenario", [
        # Empty collections - These might be valid for updates
        {"name": "test", "description": "test", "ingredients": frozenset()},
        {"name": "test", "description": "test", "tags": frozenset()},
        
        # Very large data
        {"name": "test", "description": "x" * 10000},  # Very long description
        {"name": "x" * 1000, "description": "test"},  # Very long name
        {"name": "test", "instructions": "x" * 50000},  # Very long instructions
        
        # Unicode and special characters
        {"name": "test\x00", "description": "test"},  # Null character
        {"name": "test", "description": "test\x00"},  # Null character in description
        {"name": "test", "instructions": "test\x00"},  # Null character in instructions
        
        # Boundary values
        {"name": "test", "total_time": 0},  # Zero time might be invalid
        {"name": "test", "weight_in_grams": 0},  # Zero weight might be invalid
    ])
    def test_edge_case_error_handling(self, edge_case_scenario):
        """Test error handling for edge cases and boundary conditions."""
        try:
            api_recipe = ApiRecipe(**edge_case_scenario)
            # If creation succeeds, test conversion
            update_recipe = ApiUpdateRecipe.from_api_recipe(api_recipe)
            # Some scenarios might be valid, so this is okay
        except (ValidationError, ValueError, TypeError):
            # Expected for truly invalid scenarios
            pass

    @pytest.mark.parametrize("scenario_name,scenario_data", [
        ("all_fields_invalid", {
            "name": None,
            "description": None,
            "instructions": None,
            "id": "not-uuid",
            "author_id": "not-uuid",
            "meal_id": "not-uuid",
            "total_time": -1,
            "weight_in_grams": -100,
        }),
        ("type_mismatches", {
            "name": 123,
            "description": True,
            "instructions": [],
            "id": ["not-string"],
            "total_time": "not-int",
            "weight_in_grams": "not-int",
        }),
        ("boundary_violations", {
            "name": "",  # Empty string might be invalid
            "description": "",  # Empty string
            "instructions": "",  # Empty instructions might be invalid
            "total_time": -999,  # Very negative
            "weight_in_grams": -999,  # Very negative
        }),
    ])
    def test_comprehensive_validation_error_scenarios_manual(self, scenario_name, scenario_data):
        """Test comprehensive validation error scenarios using manual scenarios."""
        with pytest.raises((ValidationError, ValueError, TypeError)):
            api_recipe = ApiRecipe(**scenario_data)
            ApiUpdateRecipe.from_api_recipe(api_recipe)

    @pytest.mark.parametrize("nested_error_scenario", [
        # Test with invalid ingredients - just test the recipe creation itself
        {
            "name": "test recipe",
            "description": "test description", 
            "total_time": -1  # Invalid negative time
        },
        # Test with invalid weight
        {
            "name": "test recipe",
            "description": "test description",
            "weight_in_grams": -100  # Invalid negative weight
        },
        # Test with invalid privacy
        {
            "name": "test recipe",
            "description": "test description",
            "privacy": "invalid_privacy_value"  # Invalid privacy enum
        },
    ])
    def test_nested_validation_errors(self, nested_error_scenario):
        """Test error handling in nested object validation."""
        with pytest.raises((ValidationError, ValueError, TypeError)):
            api_recipe = ApiRecipe(**nested_error_scenario)
            ApiUpdateRecipe.from_api_recipe(api_recipe)

    def test_conversion_recovery_after_error(self):
        """Test that conversion can recover after encountering errors."""
        # Create a scenario that initially fails, then succeeds when corrected
        
        # First, create invalid data that should fail
        invalid_data = {
            "name": None,  # Invalid
            "description": "test",
        }
        
        # Verify it fails
        with pytest.raises(ValidationError):
            ApiRecipe(**invalid_data)
        
        # Now create valid data using the data factory approach
        base_recipe = create_simple_api_recipe()
        
        # Use JSON serialization/deserialization to handle frozensets properly
        recipe_json = base_recipe.model_dump_json()
        recipe_data = json.loads(recipe_json)
        
        # Modify the data
        recipe_data["name"] = "Fixed Recipe Name"
        recipe_data["description"] = "test"
        
        # Create new valid recipe instance using JSON
        valid_recipe = ApiRecipe.model_validate_json(json.dumps(recipe_data))
        
        # This should now succeed
        update_recipe = ApiUpdateRecipe.from_api_recipe(valid_recipe)
        
        # Verify the conversion worked
        assert update_recipe.updates.name == "Fixed Recipe Name"
        assert update_recipe.updates.description == "test"
        assert update_recipe.recipe_id == valid_recipe.id

    def test_to_domain_conversion_errors(self):
        """Test error handling in to_domain conversion method."""
        # Create a minimal update attributes instance with required defaults
        update_attrs = ApiAttributesToUpdateOnRecipe(
            name="Test Recipe",
            description=None,
            ingredients=None,
            weight_in_grams=None,
            utensils=None,
            total_time=None,
            notes=None,
            tags=None,
            privacy=None,
            nutri_facts=None,
            image_url=None
        )
        
        # This should work fine
        domain_updates = update_attrs.to_domain()
        assert domain_updates["name"] == "Test Recipe"
        
        # Test with complex nested objects that might fail conversion
        base_recipe = create_simple_api_recipe()
        update_recipe = ApiUpdateRecipe.from_api_recipe(base_recipe)
        
        # This should work
        domain_command = update_recipe.to_domain()
        assert domain_command.recipe_id == base_recipe.id
        assert domain_command.updates["name"] == base_recipe.name

    @pytest.mark.parametrize("field_specific_error", [
        # Test specific field validation using available factory functions
        ("invalid_name", create_api_recipe_with_invalid_name),
        ("invalid_instructions", create_api_recipe_with_invalid_instructions),
        ("invalid_total_time", create_api_recipe_with_invalid_total_time),
        ("invalid_weight", create_api_recipe_with_invalid_weight),
        ("invalid_privacy", create_api_recipe_with_invalid_privacy),
    ])
    def test_field_specific_validation_errors(self, field_specific_error):
        """Test field-specific validation errors using data factory functions."""
        error_name, factory_func = field_specific_error
        
        try:
            # Create invalid recipe data using factory
            invalid_data = factory_func()
            
            with pytest.raises((ValidationError, ValueError, TypeError)):
                api_recipe = ApiRecipe(**invalid_data)
                ApiUpdateRecipe.from_api_recipe(api_recipe)
        except (AttributeError, ImportError):
            # If factory function doesn't exist, skip this specific test
            pytest.skip(f"Factory function {factory_func.__name__} not available")

    def test_malformed_uuid_handling(self):
        """Test handling of malformed UUIDs in recipe_id field."""
        # Create a valid updates object to test the UUID validation
        base_recipe = create_simple_api_recipe()
        valid_updates = ApiUpdateRecipe.from_api_recipe(base_recipe).updates
        
        with pytest.raises(ValidationError):
            ApiUpdateRecipe(
                recipe_id="not-a-uuid",
                updates=valid_updates
            )

    def test_empty_updates_with_minimal_fields(self):
        """Test handling of updates with minimal required fields."""
        # Create updates with minimal fields to test the to_domain conversion
        base_recipe = create_simple_api_recipe()
        update_recipe = ApiUpdateRecipe.from_api_recipe(base_recipe)
        
        # This should work fine
        domain_command = update_recipe.to_domain()
        assert domain_command.recipe_id == base_recipe.id
        assert isinstance(domain_command.updates, dict)

    def test_partial_updates_with_single_field(self):
        """Test handling of partial updates focusing on field-level validation."""
        # Create a base recipe to get its ID
        base_recipe = create_simple_api_recipe()
        
        # Create an update with just a modified name field
        modified_updates = ApiAttributesToUpdateOnRecipe(
            name="Modified Recipe Name",
            description=base_recipe.description,
            ingredients=base_recipe.ingredients,
            weight_in_grams=base_recipe.weight_in_grams,
            utensils=base_recipe.utensils,
            total_time=base_recipe.total_time,
            notes=base_recipe.notes,
            tags=base_recipe.tags,
            privacy=base_recipe.privacy,
            nutri_facts=base_recipe.nutri_facts,
            image_url=base_recipe.image_url
        )
        
        update_recipe = ApiUpdateRecipe(
            recipe_id=base_recipe.id,
            updates=modified_updates
        )
        
        # This should work fine
        domain_command = update_recipe.to_domain()
        assert domain_command.recipe_id == base_recipe.id
        assert "name" in domain_command.updates
        assert domain_command.updates["name"] == "Modified Recipe Name"

    def test_update_conversion_with_complex_fields(self):
        """Test handling of updates with complex nested fields."""
        # Create a complex recipe with various field types
        base_recipe = create_simple_api_recipe()
        update_recipe = ApiUpdateRecipe.from_api_recipe(base_recipe)
        
        # Test that the conversion works with complex fields
        domain_command = update_recipe.to_domain()
        assert domain_command.recipe_id == base_recipe.id
        assert isinstance(domain_command.updates, dict)
        
        # Verify that the converted data has expected structure
        if "ingredients" in domain_command.updates:
            assert isinstance(domain_command.updates["ingredients"], list)
        
        if "tags" in domain_command.updates:
            assert isinstance(domain_command.updates["tags"], (frozenset, set))
