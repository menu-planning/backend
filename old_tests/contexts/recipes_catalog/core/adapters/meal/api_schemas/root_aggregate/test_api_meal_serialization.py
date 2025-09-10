"""
ApiMeal JSON Serialization Test Suite

Comprehensive test suite for testing JSON serialization and deserialization behavior 
of the ApiMeal class. Tests both successful serialization scenarios and validation 
error scenarios to ensure robust API behavior.

Key Testing Areas:
1. Valid JSON serialization (model_dump_json)
2. Valid JSON deserialization (model_validate_json)
3. Invalid JSON deserialization validation errors
4. Field-specific validation tests
5. Round-trip serialization integrity
6. Complex nested object serialization
7. Edge cases and error handling
8. Pydantic configuration enforcement (strict validation, extra fields forbidden, etc.)

Following the same comprehensive testing patterns as test_api_meal_core.py.
"""

import json
import pytest

from uuid import uuid4
from datetime import datetime
from pydantic import ValidationError

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import ApiMeal
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import ApiRecipe
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_facts import ApiNutriFacts
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag

# Import test data factories
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.data_factories.api_recipe_data_factories import create_complex_api_recipe
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.data_factories.api_meal_data_factories import (
    create_api_meal,
    create_api_tag,
    create_complex_api_meal,
    create_api_meal_json,
    create_valid_json_test_cases,
    create_invalid_json_test_cases,
    create_field_validation_test_suite,
    create_boundary_value_test_cases,

    create_nested_object_validation_test_cases,
    create_pydantic_config_test_cases,

    create_json_edge_cases,
    create_malformed_json_scenarios
)


def _generate_nested_object_validation_test_cases():
    """Helper function to generate flattened test cases for nested object validation."""
    nested_error_scenarios = create_nested_object_validation_test_cases()
    test_cases = []
    
    for scenario_name, test_case_list in nested_error_scenarios.items():
        for test_case in test_case_list:
            test_cases.append((scenario_name, test_case))
    
    return test_cases


class TestApiMealJSONSerialization:
    """
    Test suite for valid JSON serialization scenarios (>95% coverage target).
    """

    # =============================================================================
    # VALID JSON SERIALIZATION TESTS
    # =============================================================================

    def test_basic_json_dump_serialization(self, simple_api_meal):
        """Test basic JSON serialization with model_dump_json."""
        json_str = simple_api_meal.model_dump_json()
        
        # Should produce valid JSON
        assert isinstance(json_str, str)
        parsed_data = json.loads(json_str)
        assert isinstance(parsed_data, dict)
        
        # Should contain all required fields
        required_fields = ["id", "name", "author_id", "recipes", "tags"]
        for field in required_fields:
            assert field in parsed_data, f"Required field '{field}' missing from JSON"
        
        # Should serialize field values correctly
        assert parsed_data["id"] == simple_api_meal.id
        assert parsed_data["name"] == simple_api_meal.name
        assert parsed_data["author_id"] == simple_api_meal.author_id
        assert isinstance(parsed_data["recipes"], list)
        assert isinstance(parsed_data["tags"], list)  # frozenset serializes to list

    def test_complex_json_dump_serialization(self, complex_api_meal):
        """Test JSON serialization with complex nested objects."""
        json_str = complex_api_meal.model_dump_json()
        
        # Should produce valid JSON
        parsed_data = json.loads(json_str)
        
        # Should serialize nested objects correctly
        if complex_api_meal.recipes:
            assert "recipes" in parsed_data
            assert isinstance(parsed_data["recipes"], list)
            assert len(parsed_data["recipes"]) == len(complex_api_meal.recipes)
            
            # Each recipe should be serialized as object
            for recipe_data in parsed_data["recipes"]:
                assert isinstance(recipe_data, dict)
                assert "id" in recipe_data
                assert "name" in recipe_data
        
        if complex_api_meal.tags:
            assert "tags" in parsed_data
            assert isinstance(parsed_data["tags"], list)
            assert len(parsed_data["tags"]) == len(complex_api_meal.tags)
            
            # Each tag should be serialized as object
            for tag_data in parsed_data["tags"]:
                assert isinstance(tag_data, dict)
                assert "key" in tag_data
                assert "value" in tag_data
        
        if complex_api_meal.nutri_facts:
            assert "nutri_facts" in parsed_data
            assert isinstance(parsed_data["nutri_facts"], dict)
            # Nutrition facts should have nutritional components
            nutri_data = parsed_data["nutri_facts"]
            expected_components = ["calories", "protein", "carbohydrate", "total_fat"]
            for component in expected_components:
                if getattr(complex_api_meal.nutri_facts, component, None):
                    assert component in nutri_data

    def test_minimal_json_dump_serialization(self, minimal_api_meal):
        """Test JSON serialization with minimal required fields only."""
        json_str = minimal_api_meal.model_dump_json()
        
        # Should produce valid JSON
        parsed_data = json.loads(json_str)
        
        # Should contain all required fields
        required_fields = ["id", "name", "author_id", "recipes", "tags"]
        for field in required_fields:
            assert field in parsed_data
        
        # Optional fields should be present with default/null values
        optional_fields = ["menu_id", "description", "notes", "like", "image_url", "nutri_facts"]
        for field in optional_fields:
            assert field in parsed_data
            # Optional fields should be null or default values
            assert parsed_data[field] is None or parsed_data[field] == []

    def test_json_dump_includes_computed_properties(self, complex_api_meal):
        """Test that JSON serialization includes computed properties."""
        json_str = complex_api_meal.model_dump_json()
        parsed_data = json.loads(json_str)
        
        # Computed properties should be included in JSON
        computed_properties = [
            "weight_in_grams", "calorie_density", "carbo_percentage", 
            "protein_percentage", "total_fat_percentage"
        ]
        
        for prop in computed_properties:
            assert prop in parsed_data, f"Computed property '{prop}' should be in JSON"
            # Value can be null or numeric
            value = parsed_data[prop]
            assert value is None or isinstance(value, (int, float)), \
                f"Computed property '{prop}' should be null or numeric, got {type(value)}"

    def test_json_dump_includes_entity_lifecycle_fields(self, simple_api_meal):
        """Test that JSON serialization includes entity lifecycle fields."""
        json_str = simple_api_meal.model_dump_json()
        parsed_data = json.loads(json_str)
        
        # Entity lifecycle fields should be included
        lifecycle_fields = ["created_at", "updated_at", "version", "discarded"]
        
        for field in lifecycle_fields:
            assert field in parsed_data, f"Lifecycle field '{field}' should be in JSON"
        
        # Verify field types
        assert isinstance(parsed_data["created_at"], str)  # datetime serializes to ISO string
        assert isinstance(parsed_data["updated_at"], str)  # datetime serializes to ISO string
        assert isinstance(parsed_data["version"], int)
        assert isinstance(parsed_data["discarded"], bool)

    @pytest.mark.parametrize("test_case", create_valid_json_test_cases())
    def test_parametrized_valid_json_serialization(self, test_case):
        """Test JSON serialization with various valid data combinations."""
        # test_case is already the meal data directly (not wrapped in "data" key)
        meal_data = test_case
        
        # Create API meal from test data
        api_meal = ApiMeal(**meal_data)
        
        # Should serialize successfully
        json_str = api_meal.model_dump_json()
        assert isinstance(json_str, str)
        
        # Should parse as valid JSON
        parsed_data = json.loads(json_str)
        assert isinstance(parsed_data, dict)
        
        # Should contain the original data
        assert parsed_data["name"] == meal_data["name"]
        assert parsed_data["author_id"] == meal_data["author_id"]

    def test_json_dump_exclude_none_behavior(self, minimal_api_meal):
        """Test JSON serialization behavior with None values."""
        # Default behavior should include None values
        json_str = minimal_api_meal.model_dump_json()
        parsed_data = json.loads(json_str)
        
        # None fields should be present with null values
        none_fields = ["menu_id", "description", "notes", "like", "image_url", "nutri_facts"]
        for field in none_fields:
            if getattr(minimal_api_meal, field) is None:
                assert field in parsed_data
                assert parsed_data[field] is None

    def test_json_dump_exclude_unset_behavior(self, simple_api_meal):
        """Test JSON serialization with exclude_unset parameter."""
        # Should be able to exclude unset fields
        json_str = simple_api_meal.model_dump_json(exclude_unset=True)
        parsed_data = json.loads(json_str)
        
        # Should still contain required fields and explicitly set fields
        assert "id" in parsed_data
        assert "name" in parsed_data
        assert "author_id" in parsed_data


class TestApiMealJSONDeserialization:
    """
    Test suite for valid JSON deserialization scenarios.
    """

    # =============================================================================
    # VALID JSON DESERIALIZATION TESTS
    # =============================================================================

    def test_basic_json_load_deserialization(self):
        """Test basic JSON deserialization with model_validate_json."""
        # Create valid JSON data
        meal_json = create_api_meal_json(name="Test Meal")
        
        # Should deserialize successfully
        api_meal = ApiMeal.model_validate_json(meal_json)
        
        # Should be proper ApiMeal instance
        assert isinstance(api_meal, ApiMeal)
        assert api_meal.name == "Test Meal"
        assert isinstance(api_meal.recipes, list)
        assert isinstance(api_meal.tags, frozenset)

    def test_complex_json_load_deserialization(self):
        """Test JSON deserialization with complex nested objects."""
        # Create complex meal with nested objects
        complex_meal = create_complex_api_meal()
        json_str = complex_meal.model_dump_json()
        
        # Should deserialize successfully
        restored_meal = ApiMeal.model_validate_json(json_str)
        
        # Should preserve complex nested objects
        assert isinstance(restored_meal, ApiMeal)
        assert restored_meal.recipes is not None
        assert restored_meal.tags is not None
        assert complex_meal.recipes is not None
        assert complex_meal.tags is not None
        assert len(restored_meal.recipes) == len(complex_meal.recipes)
        assert len(restored_meal.tags) == len(complex_meal.tags)
        
        # Nested objects should be properly typed
        assert all(isinstance(recipe, ApiRecipe) for recipe in restored_meal.recipes)
        assert all(isinstance(tag, ApiTag) for tag in restored_meal.tags)
        
        if restored_meal.nutri_facts:
            assert isinstance(restored_meal.nutri_facts, ApiNutriFacts)

    def test_minimal_json_load_deserialization(self):
        """Test JSON deserialization with minimal required fields only."""
        # Create minimal JSON with only required fields
        minimal_data = {
            "id": str(uuid4()),
            "name": "Minimal Meal",
            "author_id": str(uuid4()),
            "recipes": [],
            "tags": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "version": 1,
            "discarded": False
        }
        
        json_str = json.dumps(minimal_data)
        
        # Should deserialize successfully
        api_meal = ApiMeal.model_validate_json(json_str)
        
        # Should have proper types and default values
        assert isinstance(api_meal, ApiMeal)
        assert api_meal.name == "Minimal Meal"
        assert api_meal.recipes == []
        assert api_meal.tags == frozenset()
        assert api_meal.menu_id is None
        assert api_meal.description is None

    def test_json_load_with_type_conversion(self):
        """Test JSON deserialization performs proper type conversions."""
        # Create JSON with string representations that need conversion
        meal_data = {
            "id": str(uuid4()),
            "name": "Type Conversion Test",
            "author_id": str(uuid4()),
            "recipes": [],
            "tags": [],
            "like": True,  # boolean
            "weight_in_grams": 500,  # integer
            "calorie_density": 2.5,  # float
            "carbo_percentage": 45.0,  # float percentage
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "version": 1,
            "discarded": False
        }
        
        json_str = json.dumps(meal_data)
        api_meal = ApiMeal.model_validate_json(json_str)
        
        # Should perform correct type conversions
        assert isinstance(api_meal.like, bool)
        assert isinstance(api_meal.weight_in_grams, int)
        assert isinstance(api_meal.calorie_density, float)
        assert isinstance(api_meal.carbo_percentage, float)
        assert isinstance(api_meal.created_at, datetime)
        assert isinstance(api_meal.updated_at, datetime)

    @pytest.mark.parametrize("test_case", create_valid_json_test_cases())
    def test_parametrized_valid_json_deserialization(self, test_case):
        """Test JSON deserialization with various valid data combinations."""
        # test_case is already the meal data directly (not wrapped in "data" key)
        meal_data = test_case
        api_meal = ApiMeal(**meal_data)
        json_str = api_meal.model_dump_json()
        
        # Should deserialize successfully
        api_meal = ApiMeal.model_validate_json(json_str)
        
        # Should be proper ApiMeal instance
        assert isinstance(api_meal, ApiMeal)
        assert api_meal.name == meal_data["name"]
        assert api_meal.author_id == meal_data["author_id"]

    def test_json_load_handles_nested_collections(self):
        """Test JSON deserialization correctly handles nested collections."""
        # Create meal with various collection types - using plain dicts instead of API classes
        author_id = str(uuid4())
        meal_id = str(uuid4())
        complex_meal = create_complex_api_meal(
            id=meal_id,
            author_id=author_id,
            recipes=[
                create_complex_api_recipe(author_id=author_id, meal_id=meal_id),
                create_complex_api_recipe(author_id=author_id, meal_id=meal_id)
            ],
            tags=frozenset([
                create_api_tag(author_id=author_id, type="meal", key="meal_type", value="dinner"),
                create_api_tag(author_id=author_id, type="meal", key="meal_type", value="lunch")
            ])
        )
        json_str = complex_meal.model_dump_json()
        
        api_meal = ApiMeal.model_validate_json(json_str)
        
        # Collections should be properly typed
        assert isinstance(api_meal.recipes, list)
        assert len(api_meal.recipes) == 2
        assert all(isinstance(recipe, ApiRecipe) for recipe in api_meal.recipes)
        
        assert isinstance(api_meal.tags, frozenset)
        assert len(api_meal.tags) == 2
        assert all(isinstance(tag, ApiTag) for tag in api_meal.tags)


class TestApiMealJSONValidationErrors:
    """
    Test suite for invalid JSON deserialization and validation error scenarios.
    """

    # =============================================================================
    # INVALID JSON DESERIALIZATION TESTS
    # =============================================================================

    @pytest.mark.parametrize("missing_field", ["id", "name", "author_id"])
    def test_missing_required_fields_validation_errors(self, missing_field):
        """Test validation errors when required fields are missing."""
        # Create actual API meal first
        api_meal = create_api_meal()
        
        # Get current JSON representation
        json_str = api_meal.model_dump_json()
        
        # Parse, remove the required field, and serialize back
        import json
        meal_dict = json.loads(json_str)
        del meal_dict[missing_field]
        json_str = json.dumps(meal_dict)
        
        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            ApiMeal.model_validate_json(json_str)
        
        # Error should mention the missing field
        error_details = str(exc_info.value)
        assert missing_field in error_details or "missing" in error_details.lower()

    @pytest.mark.parametrize("field_name,invalid_value", [
        ("id", 123),  # ID should be string
        ("name", None),  # Name is required, can't be None
        ("author_id", "invalid-uuid"),  # Invalid UUID format
        ("recipes", "not-a-list"),  # Recipes should be list
        ("tags", "not-a-list"),  # Tags should be list/set
        ("like", "not-a-boolean"),  # Like should be boolean
        ("weight_in_grams", "not-a-number"),  # Weight should be numeric
        ("calorie_density", "not-a-number"),  # Calorie density should be numeric
        ("carbo_percentage", 150.0),  # Percentage should be 0-100
        ("protein_percentage", -10.0),  # Percentage should be 0-100
    ])
    def test_invalid_field_type_validation_errors(self, field_name, invalid_value):
        """Test validation errors for invalid field types."""
        # Create actual API meal first
        api_meal = create_api_meal()
        
        # Get current JSON representation
        json_str = api_meal.model_dump_json()
        
        # Parse, modify the specific field, and serialize back
        import json
        meal_dict = json.loads(json_str)
        meal_dict[field_name] = invalid_value
        json_str = json.dumps(meal_dict)
        
        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            ApiMeal.model_validate_json(json_str)
        
        # Error should be related to the field
        error_details = str(exc_info.value)
        assert field_name in error_details or "validation" in error_details.lower()

    @pytest.mark.parametrize("test_case", create_invalid_json_test_cases())
    def test_parametrized_invalid_json_validation(self, test_case):
        """Test various invalid JSON scenarios raise appropriate validation errors."""
        invalid_data = test_case["data"]
        expected_error_type = test_case.get("expected_error", ValidationError)
        expected_field = test_case.get("expected_field")
        
        # Check if invalid_data contains API classes that need special handling
        try:
            # Try to serialize directly first
            json_str = json.dumps(invalid_data)
        except (TypeError, ValueError):
            # If direct serialization fails, it likely contains API classes
            # Create a meal, serialize it, then modify with invalid_data values
            api_meal = create_api_meal()
            json_str = api_meal.model_dump_json()
            
            # Parse and update with invalid data
            meal_dict = json.loads(json_str)
            # Update with any scalar values from invalid_data that can be serialized
            for key, value in invalid_data.items():
                try:
                    json.dumps(value)  # Test if value is JSON serializable
                    meal_dict[key] = value
                except (TypeError, ValueError):
                    # Skip non-serializable values (API objects) but log the key
                    # for critical fields, we might want to set to None or invalid value
                    if key in ["id", "name", "author_id"]:
                        meal_dict[key] = None  # Set to invalid value to trigger validation error
            json_str = json.dumps(meal_dict)
        
        # Should raise validation error
        with pytest.raises(expected_error_type) as exc_info:
            ApiMeal.model_validate_json(json_str)
        
        # Error should be related to expected field if specified
        if expected_field:
            error_details = str(exc_info.value)
            assert expected_field in error_details

    def test_extra_fields_forbidden_in_json(self):
        """Test that extra fields are forbidden during JSON deserialization."""
        # Create actual API meal first
        api_meal = create_api_meal()
        
        # Serialize to JSON
        json_str = api_meal.model_dump_json()
        
        # Parse JSON to dict, add extra fields, then convert back to JSON
        meal_dict = json.loads(json_str)
        meal_dict["extra_field"] = "not allowed"
        meal_dict["another_extra"] = 123
        
        json_str = json.dumps(meal_dict)
        
        # Should raise ValidationError due to extra='forbid'
        with pytest.raises(ValidationError) as exc_info:
            ApiMeal.model_validate_json(json_str)
        
        # Error should mention extra fields
        error_details = str(exc_info.value)
        assert "extra" in error_details.lower() or "forbidden" in error_details.lower()

    @pytest.mark.parametrize("field_name,coercion_value", [
        ("weight_in_grams", "500"),  # String to int coercion should fail
        ("like", 1),  # Int to bool coercion should fail
        ("version", "1"),  # String to int coercion should fail
        ("calorie_density", "2.5"),  # String to float coercion should fail
    ])
    def test_strict_validation_prevents_coercion_in_json(self, field_name, coercion_value):
        """Test that strict validation prevents type coercion during JSON loading."""
        # Create actual API meal first
        api_meal = create_api_meal()
        
        # Get the current value of the field
        current_value = getattr(api_meal, field_name)
        
        # Serialize to JSON
        json_str = api_meal.model_dump_json()
        
        # Convert Python values to their JSON representations for proper replacement
        if isinstance(current_value, bool):
            # Python True/False -> JSON true/false
            json_current_value = "true" if current_value else "false"
        elif current_value is None:
            json_current_value = "null"
        else:
            json_current_value = str(current_value)
        
        # Replace the current value with the coercion value
        if isinstance(coercion_value, str):
            # Replace value with string version (wrapped in quotes)
            json_str = json_str.replace(f'"{field_name}":{json_current_value}', f'"{field_name}":"{coercion_value}"')
        else:
            # Replace with different type (like int for bool)
            json_str = json_str.replace(f'"{field_name}":{json_current_value}', f'"{field_name}":{coercion_value}')
      
        # Should raise ValidationError due to strict validation
        with pytest.raises(ValidationError) as exc_info:
            ApiMeal.model_validate_json(json_str)
        
        # Error should be related to type validation
        error_details = str(exc_info.value)
        assert field_name in error_details or "type" in error_details.lower()

    @pytest.mark.parametrize("scenario", create_malformed_json_scenarios())
    def test_malformed_json_parsing_errors(self, scenario):
        """Test various malformed JSON scenarios."""
        malformed_json = scenario["json"]
        
        # Should raise ValidationError (Pydantic wraps JSON parsing errors)
        with pytest.raises(ValidationError):
            ApiMeal.model_validate_json(malformed_json)

    @pytest.mark.parametrize("scenario_name,test_case", _generate_nested_object_validation_test_cases())
    def test_nested_object_validation_errors(self, scenario_name, test_case):
        """Test validation errors in nested objects."""
        # Each test_case is a dict with meal data that has invalid nested objects
        invalid_api_meal = create_api_meal()
        json_str = invalid_api_meal.model_dump_json()
        invalid_data = json.loads(json_str)
        invalid_data.update(test_case)  # Merge the invalid nested object data
        
        json_str = json.dumps(invalid_data)

        # Should raise ValidationError
        with pytest.raises((ValidationError, AttributeError, ValueError)) as exc_info:
            ApiMeal.model_validate_json(json_str)
                
        # Error should relate to nested object validation
        error_details = str(exc_info.value)
        # The error should mention the problematic field (recipes, tags, or nutri_facts)
        problematic_field = list(test_case.keys())[0]  # Get the field being tested
        try:
            assert problematic_field in error_details or "validation" in error_details.lower()
        except AssertionError:
            print(f"AssertionError for {scenario_name} with value {test_case}")
            print(json_str)
            assert False

    def test_boundary_value_validation_errors(self):
        """Test validation errors at boundary values."""
        boundary_scenarios = create_boundary_value_test_cases()
        
        for field_name, test_cases in boundary_scenarios.items():
            for test_case in test_cases:
                if test_case.get("should_fail", False):
                    # Create actual API meal first
                    api_meal = create_api_meal()
                    
                    # Get current JSON representation
                    json_str = api_meal.model_dump_json()
                    
                    # Parse, modify the specific field, and serialize back
                    import json
                    meal_dict = json.loads(json_str)
                    meal_dict[field_name] = test_case["value"]
                    json_str = json.dumps(meal_dict)
                    
                    # Should raise ValidationError
                    with pytest.raises(ValidationError) as exc_info:
                        ApiMeal.model_validate_json(json_str)
                    
                    # Error should be related to the field
                    error_details = str(exc_info.value)
                    assert field_name in error_details or "validation" in error_details.lower()


class TestApiMealJSONRoundTrip:
    """
    Test suite for JSON round-trip conversion integrity.
    """

    # =============================================================================
    # JSON ROUND-TRIP TESTS
    # =============================================================================

    def test_simple_json_round_trip_integrity(self, simple_api_meal):
        """Test JSON round-trip preserves data integrity."""
        # Serialize to JSON
        json_str = simple_api_meal.model_dump_json()
        
        # Deserialize from JSON
        restored_meal = ApiMeal.model_validate_json(json_str)
        
        # Should be equal to original
        assert restored_meal == simple_api_meal

    def test_complex_json_round_trip_integrity(self, complex_api_meal):
        """Test JSON round-trip with complex nested objects."""
        # Serialize to JSON
        json_str = complex_api_meal.model_dump_json()
        
        # Deserialize from JSON
        restored_meal = ApiMeal.model_validate_json(json_str)
        
        # Should preserve all data
        assert restored_meal == complex_api_meal
        
        # Verify nested objects are preserved
        assert restored_meal.recipes is not None
        assert restored_meal.tags is not None
        assert len(restored_meal.recipes) == len(complex_api_meal.recipes)
        assert len(restored_meal.tags) == len(complex_api_meal.tags)
        
        if complex_api_meal.nutri_facts:
            assert restored_meal.nutri_facts == complex_api_meal.nutri_facts

    def test_minimal_json_round_trip_integrity(self, minimal_api_meal):
        """Test JSON round-trip with minimal data."""
        # Serialize to JSON
        json_str = minimal_api_meal.model_dump_json()
        
        # Deserialize from JSON
        restored_meal = ApiMeal.model_validate_json(json_str)
        
        # Should be equal to original
        assert restored_meal == minimal_api_meal

    def test_computed_properties_json_round_trip(self, complex_api_meal):
        """Test that computed properties survive JSON round-trip."""
        original_weight = complex_api_meal.weight_in_grams
        original_calorie_density = complex_api_meal.calorie_density
        original_carbo_percentage = complex_api_meal.carbo_percentage
        
        # Serialize to JSON
        json_str = complex_api_meal.model_dump_json()
        
        # Deserialize from JSON
        restored_meal = ApiMeal.model_validate_json(json_str)
        
        # Computed properties should be preserved
        assert restored_meal.weight_in_grams == original_weight
        assert restored_meal.calorie_density == original_calorie_density
        assert restored_meal.carbo_percentage == original_carbo_percentage

    def test_edge_cases_json_round_trip(self, edge_case_meals):
        """Test JSON round-trip with various edge cases."""
        for case_name, api_meal in edge_case_meals.items():
            # Serialize to JSON
            json_str = api_meal.model_dump_json()
            
            # Deserialize from JSON
            restored_meal = ApiMeal.model_validate_json(json_str)
            
            # Should preserve data integrity
            assert restored_meal == api_meal, f"Round-trip failed for edge case: {case_name}"

    def test_multiple_round_trips_stability(self, simple_api_meal):
        """Test that multiple JSON round-trips maintain stability."""
        current_meal = simple_api_meal
        
        # Perform multiple round-trips
        for i in range(5):
            json_str = current_meal.model_dump_json()
            current_meal = ApiMeal.model_validate_json(json_str)
        
        # Should still equal original after multiple round-trips
        assert current_meal == simple_api_meal

    def test_json_round_trip_preserves_object_types(self, complex_api_meal):
        """Test that JSON round-trip preserves proper object types."""
        # Serialize to JSON
        json_str = complex_api_meal.model_dump_json()
        
        # Deserialize from JSON
        restored_meal = ApiMeal.model_validate_json(json_str)
        
        # Should preserve object types
        assert isinstance(restored_meal.recipes, list)
        assert isinstance(restored_meal.tags, frozenset)
        assert all(isinstance(recipe, ApiRecipe) for recipe in restored_meal.recipes)
        assert all(isinstance(tag, ApiTag) for tag in restored_meal.tags)
        
        if restored_meal.nutri_facts:
            assert isinstance(restored_meal.nutri_facts, ApiNutriFacts)


class TestApiMealJSONFieldValidation:
    """
    Test suite for field-specific JSON validation behavior.
    """

    # =============================================================================
    # FIELD-SPECIFIC VALIDATION TESTS
    # =============================================================================

    @pytest.mark.parametrize("validation,test_scenarios", create_field_validation_test_suite().items())
    def test_field_validation_from_json(self, validation, test_scenarios):
        """Test field-specific validation during JSON deserialization."""
        for scenario in test_scenarios:
            field_name = next(iter(scenario))
            field_value = scenario.get(field_name)
            # Create actual API meal first
            api_meal = create_api_meal()
            
            # Get current JSON representation
            json_str = api_meal.model_dump_json()
            
            # Parse, modify the specific field, and serialize back
            meal_dict = json.loads(json_str)
            meal_dict[field_name] = field_value
            json_str = json.dumps(meal_dict)
            
            # with pytest.raises((ValidationError, AttributeError, ValueError)):
            #     ApiMeal.model_validate_json(json_str)

            try:
                ApiMeal.model_validate_json(json_str)
            except (ValidationError, AttributeError, ValueError) as exc_info:
                pass
            else:
                print(f"No error raised for {field_name} with value {field_value}")
                assert False

    @pytest.mark.parametrize("invalid_uuid", [
        "not-a-uuid",
        "12345",
        "",
        "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",
        123456789,
        None
    ])
    def test_uuid_field_validation_from_json(self, invalid_uuid):
        """Test UUID field validation during JSON deserialization."""
        # Create actual API meal first
        api_meal = create_api_meal()
        
        # Get current JSON representation
        json_str = api_meal.model_dump_json()
        
        # Parse, modify the ID field, and serialize back
        meal_dict = json.loads(json_str)
        meal_dict["id"] = invalid_uuid
        json_str = json.dumps(meal_dict)
        
        # Should raise ValidationError
        with pytest.raises((ValidationError, AttributeError, ValueError)) as exc_info:
            ApiMeal.model_validate_json(json_str)
        
        # Error should mention UUID or ID
        error_details = str(exc_info.value)
        assert "id" in error_details.lower() or "uuid" in error_details.lower()

    @pytest.mark.parametrize("field_name,invalid_value", [
        ("carbo_percentage", -10.0),
        ("carbo_percentage", 150.0),
        ("carbo_percentage", -1),
        ("carbo_percentage", 101),
        ("protein_percentage", -10.0),
        ("protein_percentage", 150.0),
        ("protein_percentage", -1),
        ("protein_percentage", 101),
        ("total_fat_percentage", -10.0),
        ("total_fat_percentage", 150.0),
        ("total_fat_percentage", -1),
        ("total_fat_percentage", 101),
    ])
    def test_percentage_field_validation_from_json(self, field_name, invalid_value):
        """Test percentage field validation during JSON deserialization."""
        # Create actual API meal first
        api_meal = create_api_meal()
        
        # Get current JSON representation
        json_str = api_meal.model_dump_json()
        
        # Parse, modify the specific field, and serialize back
        meal_dict = json.loads(json_str)
        meal_dict[field_name] = invalid_value
        json_str = json.dumps(meal_dict)
        
        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            ApiMeal.model_validate_json(json_str)
        
        # Error should mention percentage or range
        error_details = str(exc_info.value)
        assert "percentage" in error_details.lower() or "100" in error_details

    @pytest.mark.parametrize("field_name,invalid_value", [
        ("weight_in_grams", -1),
        ("weight_in_grams", -10.5),
        ("weight_in_grams", -100),
        ("calorie_density", -1),
        ("calorie_density", -10.5),
        ("calorie_density", -100),
    ])
    def test_non_negative_field_validation_from_json(self, field_name, invalid_value):
        """Test non-negative field validation during JSON deserialization."""
        # Create actual API meal first
        api_meal = create_api_meal()
        
        # Get current JSON representation
        json_str = api_meal.model_dump_json()
        
        # Parse, modify the specific field, and serialize back
        meal_dict = json.loads(json_str)
        meal_dict[field_name] = invalid_value
        json_str = json.dumps(meal_dict)
        
        # Should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            ApiMeal.model_validate_json(json_str)
        
        # Error should mention negative or validation
        error_details = str(exc_info.value)
        assert "negative" in error_details.lower() or field_name in error_details


class TestApiMealJSONPydanticConfiguration:
    """
    Test suite for Pydantic configuration behavior in JSON operations.
    """

    # =============================================================================
    # PYDANTIC CONFIGURATION TESTS
    # =============================================================================

    def test_frozen_model_immutability_after_json_load(self):
        """Test that models remain immutable after JSON deserialization."""
        meal_json = create_api_meal_json()
        api_meal = ApiMeal.model_validate_json(meal_json)
        
        # Should not be able to modify fields (frozen=True)
        with pytest.raises(ValidationError):
            api_meal.name = "Modified Name"

    def test_validate_assignment_after_json_load(self):
        """Test that validate_assignment=True is enforced after JSON loading."""
        meal_json = create_api_meal_json()
        api_meal = ApiMeal.model_validate_json(meal_json)
        
        # Model should be frozen, so assignment should fail regardless
        # This tests that the configuration is properly applied
        with pytest.raises(ValidationError):
            # This should fail due to frozen=True, not validate_assignment
            api_meal.name = "New Name"

    @pytest.mark.parametrize("config_test", create_pydantic_config_test_cases().values())
    def test_pydantic_configuration_enforcement(self, config_test):
        """Test various Pydantic configuration behaviors."""
        
        # Handle different test structures based on the config test type
        if "data" in config_test:
            # Tests that use data field (extra_fields_forbidden, strict_type_validation)
            test_data = config_test["data"]
            
            # Check if test_data contains API classes that need special handling
            try:
                # Try to serialize directly first
                json_str = json.dumps(test_data)
            except (TypeError, ValueError):
                # If direct serialization fails, it likely contains API classes
                # Create a meal, serialize it, then modify with test_data values
                api_meal = create_api_meal()
                json_str = api_meal.model_dump_json()
                
                # Parse and update with test data
                meal_dict = json.loads(json_str)
                # Update with any scalar values from test_data that can be serialized
                for key, value in test_data.items():
                    try:
                        json.dumps(value)  # Test if value is JSON serializable
                        meal_dict[key] = value
                    except (TypeError, ValueError):
                        # Skip non-serializable values (API objects)
                        pass
                json_str = json.dumps(meal_dict)
            
            # Should raise ValidationError for these configuration tests
            with pytest.raises(ValidationError):
                ApiMeal.model_validate_json(json_str)
                
        elif "meal" in config_test:
            # Tests that use pre-created meal (assignment_validation, frozen_immutability)
            api_meal = config_test["meal"]
            
            if "invalid_assignments" in config_test:
                # Test assignment validation
                for field_name, invalid_value in config_test["invalid_assignments"]:
                    with pytest.raises(ValidationError):
                        setattr(api_meal, field_name, invalid_value)
                        
            elif "attempted_mutations" in config_test:
                # Test frozen immutability
                for field_name, new_value in config_test["attempted_mutations"]:
                    with pytest.raises(ValidationError):
                        setattr(api_meal, field_name, new_value)
        else:
            # Fallback for unexpected test structures
            pytest.skip(f"Unhandled config test structure: {list(config_test.keys())}")


class TestApiMealJSONEdgeCases:
    """
    Test suite for JSON edge cases and special scenarios.
    """

    # =============================================================================
    # EDGE CASES AND SPECIAL SCENARIOS
    # =============================================================================

    @pytest.mark.parametrize("unicode_text", [
        "Café au Lait ☕",
        "Spaghetti Carbonara 🍝",
        "Здравствуй мир",  # Russian
        "こんにちは",  # Japanese
        "🍔🍟🥤",  # Emojis only
    ])
    def test_json_with_unicode_characters(self, unicode_text):
        """Test JSON handling with unicode characters in text fields."""
        # Create actual API meal first
        api_meal = create_api_meal(name=unicode_text, description=unicode_text)
        
        # Serialize to JSON with unicode support
        json_str = api_meal.model_dump_json()
        
        # Should handle unicode properly
        restored_meal = ApiMeal.model_validate_json(json_str)
        assert restored_meal.name == unicode_text
        assert restored_meal.description == unicode_text

    @pytest.mark.parametrize("field_name,large_value", [
        ("weight_in_grams", 999999),
        ("calorie_density", 999.99),
        ("version", 2147483647),  # Max 32-bit signed int
    ])
    def test_json_with_very_large_numbers(self, field_name, large_value):
        """Test JSON handling with very large numbers."""
        # Create actual API meal first
        api_meal = create_api_meal()
        
        # Get current JSON representation
        json_str = api_meal.model_dump_json()
        
        # Parse, modify the specific field, and serialize back
        meal_dict = json.loads(json_str)
        meal_dict[field_name] = large_value
        json_str = json.dumps(meal_dict)
        
        # Should handle large numbers properly
        restored_meal = ApiMeal.model_validate_json(json_str)
        assert getattr(restored_meal, field_name) == large_value

    @pytest.mark.parametrize("field_name,precise_value", [
        ("calorie_density", 3.14159265359),
        ("carbo_percentage", 33.333333333),
        ("protein_percentage", 66.666666666),
    ])
    def test_json_with_precision_float_values(self, field_name, precise_value):
        """Test JSON handling with high-precision float values."""
        # Create actual API meal first
        api_meal = create_api_meal()
        
        # Get current JSON representation
        json_str = api_meal.model_dump_json()
        
        # Parse, modify the specific field, and serialize back
        meal_dict = json.loads(json_str)
        meal_dict[field_name] = precise_value
        json_str = json.dumps(meal_dict)
        
        restored_meal = ApiMeal.model_validate_json(json_str)
        
        # Should preserve reasonable precision
        restored_value = getattr(restored_meal, field_name)
        assert abs(restored_value - precise_value) < 0.0001

    @pytest.mark.parametrize("dt_string", [
        datetime.now().isoformat(),
        datetime.now().isoformat() + "Z",
        "2023-12-25T00:00:00",
        "2023-12-25T23:59:59.999999",
    ])
    def test_json_with_datetime_edge_cases(self, dt_string):
        """Test JSON handling with various datetime formats."""
        # Create actual API meal first
        api_meal = create_api_meal()
        
        # Get current JSON representation
        json_str = api_meal.model_dump_json()
        
        # Parse, modify datetime fields, and serialize back
        meal_dict = json.loads(json_str)
        meal_dict["created_at"] = dt_string
        meal_dict["updated_at"] = dt_string
        json_str = json.dumps(meal_dict)
        
        # Should parse datetime properly
        restored_meal = ApiMeal.model_validate_json(json_str)
        assert isinstance(restored_meal.created_at, datetime)
        assert isinstance(restored_meal.updated_at, datetime)

    @pytest.mark.parametrize("edge_case", create_json_edge_cases().values())
    def test_parametrized_json_edge_cases(self, edge_case):
        """Test various JSON edge cases."""
        test_data = edge_case["data"]
        expected_behavior = edge_case["expected_behavior"]
        
        # Check if test_data contains API classes that need special handling
        try:
            # Try to serialize directly first
            json_str = json.dumps(test_data)
        except (TypeError, ValueError):
            # If direct serialization fails, it likely contains API classes
            # Create a meal, serialize it, then modify with test_data values
            api_meal = create_api_meal()
            json_str = api_meal.model_dump_json()
            
            # Parse and update with test data
            meal_dict = json.loads(json_str)
            # Update with any scalar values from test_data that can be serialized
            for key, value in test_data.items():
                try:
                    json.dumps(value)  # Test if value is JSON serializable
                    meal_dict[key] = value
                except (TypeError, ValueError):
                    # Skip non-serializable values (API objects)
                    pass
            json_str = json.dumps(meal_dict)
        
        if expected_behavior == "should_pass":
            # Should handle edge case gracefully
            api_meal = ApiMeal.model_validate_json(json_str)
            assert isinstance(api_meal, ApiMeal)
        elif expected_behavior == "should_fail":
            # Should raise appropriate error
            with pytest.raises((ValidationError, ValueError, json.JSONDecodeError)):
                ApiMeal.model_validate_json(json_str)
        else:
            # Custom expected behavior
            if expected_behavior.get("raises"):
                with pytest.raises(expected_behavior["raises"]):
                    ApiMeal.model_validate_json(json_str)
            else:
                api_meal = ApiMeal.model_validate_json(json_str)
                # Verify specific expectations
                for field, expected_value in expected_behavior.get("field_values", {}).items():
                    assert getattr(api_meal, field) == expected_value

    def test_json_with_empty_collections(self):
        """Test JSON handling with empty collections."""
        # Create actual API meal with empty collections
        api_meal = create_api_meal(recipes=[], tags=frozenset())
        
        # Serialize to JSON
        json_str = api_meal.model_dump_json()
        
        # Deserialize and verify
        restored_meal = ApiMeal.model_validate_json(json_str)
        
        # Should handle empty collections properly
        assert restored_meal.recipes == []
        assert restored_meal.tags == frozenset()
