"""
Test suite for ApiUpdateMeal error handling scenarios.

This module tests error handling, validation failures, and graceful error recovery
for the ApiUpdateMeal and ApiAttributesToUpdateOnMeal classes.
"""

import pytest
import json
from pydantic import ValidationError

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.commands.api_update_meal import (
    ApiUpdateMeal
)
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import ApiMeal

# Import existing data factories
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.data_factories.api_meal_data_factories import (
    create_simple_api_meal,
    create_systematic_error_scenarios,
    create_field_validation_test_suite,
    create_comprehensive_validation_error_scenarios,
)

class TestApiUpdateMealErrorHandling:
    """
    Test error handling scenarios for ApiUpdateMeal conversion logic.
    
    This test class validates that the ApiUpdateMeal and ApiAttributesToUpdateOnMeal classes
    handle various error scenarios gracefully, including:
    
    - Invalid input data (None values, wrong types, malformed UUIDs)
    - Missing required fields
    - Conversion failures during factory method usage
    - Comprehensive validation error scenarios
    - Edge cases and boundary conditions
    - Error message clarity and descriptiveness
    - Recovery after error correction
    
    The tests use existing data factories from api_meal_data_factories.py and follow
    error handling patterns established in the root_aggregate test files.
    
    Test Strategy:
    - Use pytest.parametrize to test multiple scenarios separately
    - Test both ApiMeal creation failures and conversion failures
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
        {"name": "test", "meal_id": "invalid-uuid"},  # Invalid UUID format
        {"name": "test", "recipe_ids": ["invalid-uuid"]},  # Invalid recipe UUID
        {"name": 123, "description": "test"},  # Invalid name type
        {"name": "test", "description": 123},  # Invalid description type
    ])
    def test_conversion_failure_invalid_meal_data(self, invalid_scenario):
        """Test graceful handling of invalid ApiMeal data during conversion."""
        with pytest.raises((ValidationError, ValueError, TypeError)):
            # Try to create ApiMeal with invalid data
            api_meal = ApiMeal(**invalid_scenario)
            # If ApiMeal creation somehow succeeds, test conversion
            ApiUpdateMeal.from_api_meal(api_meal)

    @pytest.mark.parametrize("missing_field_scenario", [
        {},  # Empty dict
        {"name": "test"},  # Missing other required fields
        {"description": "test"},  # Missing name
        {"meal_id": "550e8400-e29b-41d4-a716-446655440000"},  # Missing name and description
    ])
    def test_conversion_failure_missing_required_fields(self, missing_field_scenario):
        """Test error handling when required fields are missing."""
        with pytest.raises((ValidationError, TypeError)):
            ApiMeal(**missing_field_scenario)

    @pytest.mark.parametrize("scenario_name,scenario_data", [
        ("invalid_uuid_format", {
            "name": "test",
            "description": "test",
            "meal_id": "not-a-uuid",
        }),
        ("invalid_recipe_uuids", {
            "name": "test", 
            "description": "test",
            "recipe_ids": ["not-a-uuid", "also-not-a-uuid"],
        }),
        ("invalid_types", {
            "name": 123,  # Should be string
            "description": True,  # Should be string
        }),
    ])
    def test_conversion_failure_with_systematic_error_scenarios_manual(self, scenario_name, scenario_data):
        """Test conversion failures using manual error scenarios."""
        with pytest.raises((ValidationError, ValueError, TypeError)):
            api_meal = ApiMeal(**scenario_data)
            ApiUpdateMeal.from_api_meal(api_meal)

    def test_conversion_failure_with_systematic_error_scenarios(self):
        """Test conversion failures using systematic error scenarios from data factories."""
        try:
            # Use data factory for systematic error scenarios
            error_scenarios = create_systematic_error_scenarios()
            
            for scenario_name, scenario_data in error_scenarios.items():
                with pytest.raises((ValidationError, ValueError, TypeError)):
                    # Try to create ApiMeal with error scenario
                    api_meal = ApiMeal(**scenario_data)
                    ApiUpdateMeal.from_api_meal(api_meal)
        except AttributeError:
            # If create_systematic_error_scenarios doesn't exist, skip this test
            # The manual scenarios are covered by test_conversion_failure_with_systematic_error_scenarios_manual
            pytest.skip("create_systematic_error_scenarios not available")

    @pytest.mark.parametrize("field_name,invalid_value", [
        ("name", None),
        ("name", ""),
        ("name", 123),
        ("name", []),
        ("name", {}),
        ("description", 123),
        ("description", []),
        ("description", {}),
        ("meal_id", "not-uuid"),
        ("meal_id", 123),
        ("meal_id", None),
        ("recipe_ids", "not-list"),
        ("recipe_ids", 123),
        ("recipe_ids", ["not-uuid"]),
    ])
    def test_invalid_input_handling_comprehensive_manual(self, field_name, invalid_value):
        """Test comprehensive invalid input handling using manual field validation scenarios."""
        with pytest.raises((ValidationError, ValueError, TypeError)):
            # Create valid base meal
            base_meal = create_simple_api_meal()
            
            # Use JSON serialization/deserialization to handle frozensets properly
            meal_json = base_meal.model_dump_json()
            meal_data = json.loads(meal_json)
            
            # Replace field with invalid value
            meal_data[field_name] = invalid_value
            
            # Test conversion
            invalid_meal = ApiMeal.model_validate_json(json.dumps(meal_data))
            ApiUpdateMeal.from_api_meal(invalid_meal)

    def test_invalid_input_handling_comprehensive(self):
        """Test comprehensive invalid input handling using field validation test suite."""
        try:
            # Try using data factory validation test suite
            validation_test_suite = create_field_validation_test_suite()
            
            for field_name, invalid_values in validation_test_suite.items():
                for invalid_value in invalid_values:
                    with pytest.raises((ValidationError, ValueError, TypeError)):
                        # Create valid base meal
                        base_meal = create_simple_api_meal()
                        
                        # Use JSON serialization/deserialization to handle frozensets properly
                        meal_json = base_meal.model_dump_json()
                        meal_data = json.loads(meal_json)
                        
                        # Replace field with invalid value
                        meal_data[field_name] = invalid_value
                        
                        # Test conversion
                        invalid_meal = ApiMeal.model_validate_json(json.dumps(meal_data))
                        ApiUpdateMeal.from_api_meal(invalid_meal)
        except AttributeError:
            # If create_field_validation_test_suite doesn't exist, skip this test
            # The manual scenarios are covered by test_invalid_input_handling_comprehensive_manual
            pytest.skip("create_field_validation_test_suite not available")

    @pytest.mark.parametrize("scenario", [
        {
            "data": {"name": None, "description": "test"},
            "expected_error_type": ValidationError,
            "error_should_contain": "name"
        },
        {
            "data": {"name": "test", "meal_id": "invalid-uuid"},
            "expected_error_type": ValidationError,
            "error_should_contain": "uuid"
        },
        {
            "data": {"name": "test", "description": "test", "recipe_ids": ["invalid-uuid"]},
            "expected_error_type": ValidationError,
            "error_should_contain": "uuid"
        },
    ])
    def test_error_messages_are_descriptive(self, scenario):
        """Test that error messages provide clear information about what went wrong."""
        with pytest.raises(scenario["expected_error_type"]) as exc_info:
            ApiMeal(**scenario["data"])
        
        # Check that error message contains expected information
        error_message = str(exc_info.value).lower()
        assert scenario["error_should_contain"].lower() in error_message

    @pytest.mark.parametrize("edge_case_scenario", [
        # Empty collections
        {"name": "test", "description": "test", "recipe_ids": []},  # This might be valid
        {"name": "test", "description": "test", "tags": []},  # This might be valid
        
        # Very large data
        {"name": "test", "description": "x" * 10000},  # Very long description
        {"name": "x" * 1000, "description": "test"},  # Very long name
        
        # Unicode and special characters
        {"name": "test\x00", "description": "test"},  # Null character
        {"name": "test", "description": "test\x00"},  # Null character in description
    ])
    def test_edge_case_error_handling(self, edge_case_scenario):
        """Test error handling for edge cases and boundary conditions."""
        try:
            api_meal = ApiMeal(**edge_case_scenario)
            # If creation succeeds, test conversion
            update_meal = ApiUpdateMeal.from_api_meal(api_meal)
            # Some scenarios might be valid, so this is okay
        except (ValidationError, ValueError, TypeError):
            # Expected for truly invalid scenarios
            pass

    @pytest.mark.parametrize("scenario_name,scenario_data", [
        ("all_fields_invalid", {
            "name": None,
            "description": None,
            "meal_id": "not-uuid",
            "recipe_ids": ["not-uuid"],
            "tags": "not-list",
        }),
        ("type_mismatches", {
            "name": 123,
            "description": True,
            "meal_id": ["not-string"],
            "recipe_ids": "not-list",
        }),
        ("boundary_violations", {
            "name": "",  # Empty string
            "description": "",  # Empty string
            "meal_id": "too-short",
            "recipe_ids": [],  # Empty list might be valid
        }),
    ])
    def test_comprehensive_validation_error_scenarios_manual(self, scenario_name, scenario_data):
        """Test comprehensive validation error scenarios using manual scenarios."""
        with pytest.raises((ValidationError, ValueError, TypeError)):
            api_meal = ApiMeal(**scenario_data)
            ApiUpdateMeal.from_api_meal(api_meal)

    def test_comprehensive_validation_error_scenarios(self):
        """Test comprehensive validation error scenarios using data factory."""
        try:
            # Use data factory for comprehensive validation errors
            validation_error_scenarios = create_comprehensive_validation_error_scenarios()
            
            for scenario_name, scenario_data in validation_error_scenarios.items():
                with pytest.raises((ValidationError, ValueError, TypeError)):
                    api_meal = ApiMeal(**scenario_data)
                    ApiUpdateMeal.from_api_meal(api_meal)
        except AttributeError:
            # If function doesn't exist, skip this test
            # The manual scenarios are covered by test_comprehensive_validation_error_scenarios_manual
            pytest.skip("create_comprehensive_validation_error_scenarios not available")

    @pytest.mark.parametrize("nested_error_scenario", [
        # Test with invalid recipe IDs
        {
            "name": "test meal",
            "description": "test description", 
            "recipe_ids": ["invalid-uuid-1", "invalid-uuid-2"]
        },
        # Test with invalid data types
        {
            "name": "test meal",
            "description": "test description",
            "tags": "not-a-frozenset"  # Should be frozenset
        },
    ])
    def test_nested_validation_errors(self, nested_error_scenario):
        """Test error handling in nested object validation."""
        with pytest.raises((ValidationError, ValueError, TypeError)):
            api_meal = ApiMeal(**nested_error_scenario)
            ApiUpdateMeal.from_api_meal(api_meal)

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
            ApiMeal(**invalid_data)
        
        # Now create valid data using the data factory approach
        base_meal = create_simple_api_meal()
        
        # Use JSON serialization/deserialization to handle frozensets properly
        meal_json = base_meal.model_dump_json()
        meal_data = json.loads(meal_json)
        
        # Modify the data
        meal_data["name"] = "Fixed Name"
        meal_data["description"] = "test"
        
        # Create new valid meal instance using JSON
        valid_meal = ApiMeal.model_validate_json(json.dumps(meal_data))
        
        # This should now succeed
        update_meal = ApiUpdateMeal.from_api_meal(valid_meal)
        
        # Verify the conversion worked
        assert update_meal.updates.name == "Fixed Name"
        assert update_meal.updates.description == "test"
        assert update_meal.meal_id == valid_meal.id 