"""
ApiMeal Validation Test Suite

Test classes for ApiMeal validation logic including field validation,
custom validators, serialization scenarios, and error handling.

Following the same pattern as test_api_meal_core.py but focused on validation behavior.
"""

import json
import pytest
from uuid import uuid4
from datetime import datetime
from pydantic import ValidationError

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import ApiMeal

# Import test data factories
from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.data_factories.api_meal_data_factories import (
    create_simple_api_meal,
    create_complex_api_meal,
    create_valid_json_test_cases,
    create_invalid_json_test_cases,
)


class TestApiMealFieldValidation:
    """
    Test suite for ApiMeal field validation behavior (>95% coverage target).
    
    Tests individual field validation including type checking, format validation,
    and range validation for all ApiMeal fields.
    """

    def test_required_field_validation(self):
        """Test that required fields are properly validated."""
        # Test missing required fields
        with pytest.raises(ValidationError) as exc_info:
            ApiMeal.model_validate_json('{}')
        
        errors = exc_info.value.errors()
        required_fields = {'id', 'name', 'author_id', 'created_at', 'updated_at'}
        error_fields = {str(error['loc'][0]) if error['loc'] else '' for error in errors}
        
        # Should have errors for all required fields
        assert required_fields.issubset(error_fields), f"Missing required field validation for: {required_fields - error_fields}"

    @pytest.mark.parametrize("invalid_uuid", [
        "invalid-uuid",
        "123",
        "not-a-uuid-at-all",
        "12345678-1234-1234-1234-123456789abcd",  # Invalid length
        ""
    ])
    def test_uuid_field_validation(self, invalid_uuid):
        """Test UUID field validation for id, author_id, and menu_id."""
        base_data = {
            "name": "Test Meal",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "recipes": [],
            "tags": []
        }
        
        # Test invalid id
        with pytest.raises(ValidationError) as exc_info:
            ApiMeal.model_validate_json(json.dumps({
                **base_data,
                "id": invalid_uuid,
                "author_id": str(uuid4())
            }))
        assert "Invalid UUID4 format" in str(exc_info.value)
        
        # Test invalid author_id
        with pytest.raises(ValidationError) as exc_info:
            ApiMeal.model_validate_json(json.dumps({
                **base_data,
                "id": str(uuid4()),
                "author_id": invalid_uuid
            }))
        assert "Invalid UUID4 format" in str(exc_info.value)
        
        # Test invalid menu_id (optional)
        with pytest.raises(ValidationError) as exc_info:
            ApiMeal.model_validate_json(json.dumps({
                **base_data,
                "id": str(uuid4()),
                "author_id": str(uuid4()),
                "menu_id": invalid_uuid
            }))
        assert "Invalid UUID4 format" in str(exc_info.value)

    @pytest.mark.parametrize("invalid_name", [
        "",  # Empty string
        "   ",  # Only whitespace
        "x" * 256,  # Too long
        None  # None value
    ])
    def test_name_field_validation(self, invalid_name):
        """Test name field validation including length and content."""
        base_data = {
            "id": str(uuid4()),
            "author_id": str(uuid4()),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "recipes": [],
            "tags": []
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ApiMeal.model_validate_json(json.dumps({
                **base_data,
                "name": invalid_name
            }))
        errors = exc_info.value.errors()
        assert any("name" in str(error) for error in errors)

    @pytest.mark.parametrize("invalid_url", [
        "not-a-url",
        "ftp://invalid-protocol.com",
        "http://",
        "just-text",
        "http://[invalid-ipv6"
    ])
    def test_url_field_validation(self, invalid_url):
        """Test image_url field validation."""
        base_data = {
            "id": str(uuid4()),
            "name": "Test Meal",
            "author_id": str(uuid4()),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "recipes": [],
            "tags": []
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ApiMeal.model_validate_json(json.dumps({
                **base_data,
                "image_url": invalid_url
            }))
        errors = exc_info.value.errors()
        assert any("image_url" in str(error) for error in errors)

    @pytest.mark.parametrize("field,invalid_percentage", [
        ("carbo_percentage", -1),
        ("carbo_percentage", 101),
        ("carbo_percentage", 150.5),
        ("carbo_percentage", -50.0),
        ("protein_percentage", -1),
        ("protein_percentage", 101),
        ("protein_percentage", 150.5),
        ("protein_percentage", -50.0),
        ("total_fat_percentage", -1),
        ("total_fat_percentage", 101),
        ("total_fat_percentage", 150.5),
        ("total_fat_percentage", -50.0),
    ])
    def test_percentage_field_validation(self, field, invalid_percentage):
        """Test percentage field validation (0-100 range)."""
        base_data = {
            "id": str(uuid4()),
            "name": "Test Meal",
            "author_id": str(uuid4()),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "recipes": [],
            "tags": []
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ApiMeal.model_validate_json(json.dumps({
                **base_data,
                field: invalid_percentage
            }))
        assert "Percentage must be between 0 and 100" in str(exc_info.value)

    @pytest.mark.parametrize("field,invalid_value", [
        ("weight_in_grams", -1),
        ("weight_in_grams", -50),
        ("weight_in_grams", -999999),
        ("calorie_density", -1),
        ("calorie_density", -50.5),
        ("calorie_density", float('-inf')),
    ])
    def test_non_negative_field_validation(self, field, invalid_value):
        """Test non-negative field validation."""
        base_data = {
            "id": str(uuid4()),
            "name": "Test Meal",
            "author_id": str(uuid4()),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "recipes": [],
            "tags": []
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ApiMeal.model_validate_json(json.dumps({
                **base_data,
                field: invalid_value
            }))
        assert "Value must be non-negative" in str(exc_info.value)

    @pytest.mark.parametrize("invalid_datetime", [
        "not-a-datetime",
        "2023-13-01T10:30:00Z",  # Invalid month
        "2023-01-32T10:30:00Z",  # Invalid day
        "2023-01-01T25:30:00Z",  # Invalid hour
        "invalid-format",
    ])
    def test_datetime_field_validation(self, invalid_datetime):
        """Test datetime field validation."""
        base_data = {
            "id": str(uuid4()),
            "name": "Test Meal",
            "author_id": str(uuid4()),
            "recipes": [],
            "tags": []
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ApiMeal.model_validate_json(json.dumps({
                **base_data,
                "created_at": invalid_datetime,
                "updated_at": datetime.now().isoformat()
            }))
        errors = exc_info.value.errors()
        assert any("created_at" in str(error) for error in errors)

    @pytest.mark.parametrize("invalid_version", [0, -1, -10, 0.5])
    def test_version_field_validation(self, invalid_version):
        """Test version field validation (must be >= 1)."""
        base_data = {
            "id": str(uuid4()),
            "name": "Test Meal",
            "author_id": str(uuid4()),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "recipes": [],
            "tags": []
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ApiMeal.model_validate_json(json.dumps({
                **base_data,
                "version": invalid_version
            }))
        errors = exc_info.value.errors()
        assert any("version" in str(error) for error in errors)


class TestApiMealCustomValidators:
    """
    Test suite for ApiMeal custom validator methods behavior.
    
    Tests the two custom validators:
    - validate_recipes_have_correct_meal_and_author_id
    - validate_tags_have_correct_author_id_and_type
    """

    def test_recipe_meal_id_validation(self):
        """Test that recipes must have correct meal_id."""
        meal_id = str(uuid4())
        author_id = str(uuid4())
        wrong_meal_id = str(uuid4())
        
        # Create recipe with wrong meal_id
        recipe_data = {
            "id": str(uuid4()),
            "name": "Test Recipe",
            "author_id": author_id,
            "meal_id": wrong_meal_id,  # Wrong meal_id
            "instructions": "Test instructions",
            "ingredients": [],
            "tags": [],
            "ratings": [],
            "privacy": "public",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "version": 1,
            "discarded": False
        }
        
        meal_data = {
            "id": meal_id,
            "name": "Test Meal",
            "author_id": author_id,
            "recipes": [recipe_data],
            "tags": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "version": 1,
            "discarded": False
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ApiMeal.model_validate_json(json.dumps(meal_data))
        
        error_message = str(exc_info.value)
        assert "incorrect meal_id" in error_message
        assert wrong_meal_id in error_message
        assert meal_id in error_message

    def test_recipe_author_id_validation(self):
        """Test that recipes must have correct author_id."""
        meal_id = str(uuid4())
        author_id = str(uuid4())
        wrong_author_id = str(uuid4())
        
        # Create recipe with wrong author_id
        recipe_data = {
            "id": str(uuid4()),
            "name": "Test Recipe",
            "author_id": wrong_author_id,  # Wrong author_id
            "meal_id": meal_id,
            "instructions": "Test instructions",
            "ingredients": [],
            "tags": [],
            "ratings": [],
            "privacy": "public",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "version": 1,
            "discarded": False
        }
        
        meal_data = {
            "id": meal_id,
            "name": "Test Meal",
            "author_id": author_id,
            "recipes": [recipe_data],
            "tags": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "version": 1,
            "discarded": False
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ApiMeal.model_validate_json(json.dumps(meal_data))
        
        error_message = str(exc_info.value)
        assert "incorrect author_id" in error_message
        assert wrong_author_id in error_message
        assert author_id in error_message

    def test_tag_author_id_auto_assignment(self):
        """Test that tags without author_id get meal's author_id."""
        meal_id = str(uuid4())
        author_id = str(uuid4())
        
        # Create tag without author_id
        tag_data = {
            "key": "meal_type",
            "value": "dinner"
            # No author_id or type
        }
        
        meal_data = {
            "id": meal_id,
            "name": "Test Meal",
            "author_id": author_id,
            "recipes": [],
            "tags": [tag_data],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "version": 1,
            "discarded": False
        }
        
        # Should successfully create meal with auto-assigned author_id
        meal = ApiMeal.model_validate_json(json.dumps(meal_data))

        assert meal.recipes is not None
        assert meal.tags is not None
        assert len(meal.tags) == 1
        tag = list(meal.tags)[0]
        assert tag.author_id == author_id
        assert tag.type == "meal"  # Default type

    def test_tag_type_auto_assignment(self):
        """Test that tags without type get 'meal' as default."""
        meal_id = str(uuid4())
        author_id = str(uuid4())
        
        # Create tag without type
        tag_data = {
            "key": "cuisine",
            "value": "italian",
            "author_id": author_id
            # No type
        }
        
        meal_data = {
            "id": meal_id,
            "name": "Test Meal",
            "author_id": author_id,
            "recipes": [],
            "tags": [tag_data],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "version": 1,
            "discarded": False
        }
        
        # Should successfully create meal with auto-assigned type
        meal = ApiMeal.model_validate_json(json.dumps(meal_data))
        
        assert meal.tags is not None
        assert len(meal.tags) == 1
        tag = list(meal.tags)[0]
        assert tag.type == "meal"

    def test_tag_author_id_mismatch_validation(self):
        """Test that tags with wrong author_id are rejected."""
        meal_id = str(uuid4())
        author_id = str(uuid4())
        wrong_author_id = str(uuid4())
        
        # Create tag with wrong author_id
        tag_data = {
            "key": "difficulty",
            "value": "hard",
            "author_id": wrong_author_id,  # Wrong author_id
            "type": "meal"
        }
        
        meal_data = {
            "id": meal_id,
            "name": "Test Meal",
            "author_id": author_id,
            "recipes": [],
            "tags": [tag_data],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "version": 1,
            "discarded": False
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ApiMeal.model_validate_json(json.dumps(meal_data))
        
        error_message = str(exc_info.value)
        assert "does not match meal author_id" in error_message

    def test_tag_validation_with_failed_author_id(self):
        """Test tag validation when meal author_id validation fails."""
        meal_id = str(uuid4())
        
        # Create meal with invalid author_id
        meal_data = {
            "id": meal_id,
            "name": "Test Meal",
            "author_id": "invalid-uuid",  # Invalid UUID
            "recipes": [],
            "tags": [{"key": "test", "value": "value"}],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "version": 1,
            "discarded": False
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ApiMeal.model_validate_json(json.dumps(meal_data))
        
        # Should get author_id validation error, not tag validation error
        error_message = str(exc_info.value)
        assert "Invalid UUID4 format" in error_message

    def test_recipe_validation_with_failed_ids(self):
        """Test recipe validation when meal id or author_id validation fails."""
        # Create meal with invalid id
        meal_data = {
            "id": "invalid-uuid",  # Invalid UUID
            "name": "Test Meal",
            "author_id": str(uuid4()),
            "recipes": [{
                "id": str(uuid4()),
                "name": "Test Recipe",
                "author_id": str(uuid4()),
                "meal_id": str(uuid4()),
                "ingredients": [],
                "tags": [],
                "ratings": [],
                "privacy": "public",
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat(),
                "version": 1,
                "discarded": False
            }],
            "tags": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "version": 1,
            "discarded": False
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ApiMeal.model_validate_json(json.dumps(meal_data))
        
        # Should get id validation error, not recipe validation error
        error_message = str(exc_info.value)
        assert "Invalid UUID4 format" in error_message


class TestApiMealSerialization:
    """
    Test suite for ApiMeal JSON serialization and deserialization scenarios.
    
    Tests both model_validate_json (deserialization) and model_dump_json (serialization)
    with various valid and invalid scenarios.
    """

    @pytest.mark.parametrize("case_data", create_valid_json_test_cases())
    def test_valid_json_deserialization(self, case_data):
        """Test successful JSON deserialization with valid data."""
        # Convert to JSON serializable format
        original_api_meal = ApiMeal(**case_data)
        json_str = original_api_meal.model_dump_json()
        
        # Should successfully deserialize
        new_api_meal = ApiMeal.model_validate_json(json_str)
        
        # Verify key fields
        assert new_api_meal.id == case_data["id"]
        assert new_api_meal.name == case_data["name"]
        assert new_api_meal.author_id == case_data["author_id"]
        assert new_api_meal.recipes is not None
        assert new_api_meal.tags is not None
        assert len(new_api_meal.recipes) == len(case_data["recipes"])
        assert len(new_api_meal.tags) == len(case_data["tags"])

    @pytest.mark.parametrize("case_data", create_invalid_json_test_cases())
    def test_invalid_json_deserialization(self, case_data):
        """Test JSON deserialization with invalid data."""
        json_str = json.dumps(case_data["data"])
        
        with pytest.raises(ValidationError) as exc_info:
            ApiMeal.model_validate_json(json_str)
        
        # Verify expected error fields are present
        errors = exc_info.value.errors()
        error_fields = {str(error['loc'][0]) if error['loc'] else '' for error in errors}
        
        # Check that at least one expected error field is present
        expected_error_fields = set(case_data["expected_errors"])
        assert error_fields.intersection(expected_error_fields), \
            f"Expected error fields {expected_error_fields} not found in actual errors {error_fields}"

    @pytest.mark.parametrize("required_field", [
        "id", "name", "author_id", "recipes", "tags",
        "created_at", "updated_at", "version", "discarded"
    ])
    def test_json_serialization_completeness(self, required_field):
        """Test that JSON serialization includes all required fields."""
        meal = create_complex_api_meal()
        json_str = meal.model_dump_json()
        
        # Parse back to verify completeness
        data = json.loads(json_str)
        
        # Required field should be present
        assert required_field in data, f"Field '{required_field}' missing from JSON serialization"

    def test_json_round_trip_consistency(self):
        """Test that JSON round-trip preserves data integrity."""
        original_meal = create_complex_api_meal()
        
        # Serialize to JSON
        json_str = original_meal.model_dump_json()
        
        # Deserialize back
        recovered_meal = ApiMeal.model_validate_json(json_str)
        
        # Should be identical
        assert recovered_meal == original_meal

    @pytest.mark.parametrize("malformed_json", [
        "",  # Empty string
        "{",  # Incomplete JSON
        "null",  # Null value
        "[]",  # Wrong type (array)
        "not-json",  # Invalid JSON
        '{"id": }',  # Syntax error
    ])
    def test_malformed_json_handling(self, malformed_json):
        """Test handling of malformed JSON."""
        with pytest.raises((ValidationError, json.JSONDecodeError)):
            ApiMeal.model_validate_json(malformed_json)

    def test_extra_fields_rejection(self):
        """Test that extra fields are rejected due to 'forbid' config."""
        meal_data = {
            "id": str(uuid4()),
            "name": "Test Meal",
            "author_id": str(uuid4()),
            "recipes": [],
            "tags": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "version": 1,
            "discarded": False,
            "extra_field": "should_be_rejected"  # Extra field
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ApiMeal.model_validate_json(json.dumps(meal_data))
        
        error_message = str(exc_info.value)
        assert "Extra inputs are not permitted" in error_message

    def test_null_handling_in_optional_fields(self):
        """Test that null values are handled correctly in optional fields."""
        meal_data = {
            "id": str(uuid4()),
            "name": "Test Meal",
            "author_id": str(uuid4()),
            "recipes": [],
            "tags": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "version": 1,
            "discarded": False,
            # Optional fields as null
            "menu_id": None,
            "description": None,
            "notes": None,
            "like": None,
            "image_url": None,
            "nutri_facts": None,
            "weight_in_grams": None,
            "calorie_density": None,
            "carbo_percentage": None,
            "protein_percentage": None,
            "total_fat_percentage": None
        }
        
        # Should successfully handle null values
        meal = ApiMeal.model_validate_json(json.dumps(meal_data))
        
        assert meal.menu_id is None
        assert meal.description is None
        assert meal.notes is None
        assert meal.like is None
        assert meal.image_url is None
        assert meal.nutri_facts is None
        assert meal.calorie_density is None


class TestApiMealValidationBehavior:
    """
    Test suite for overall ApiMeal validation behavior patterns.
    
    Tests integration of all validation rules and edge cases.
    """

    def test_strict_validation_no_coercion(self):
        """Test that strict validation prevents type coercion."""
        meal_data = {
            "id": str(uuid4()),
            "name": "Test Meal",
            "author_id": str(uuid4()),
            "recipes": [],
            "tags": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "version": "1",  # String instead of int
            "discarded": "false"  # String instead of bool
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ApiMeal.model_validate_json(json.dumps(meal_data))
        
        errors = exc_info.value.errors()
        error_fields = {str(error['loc'][0]) if error['loc'] else '' for error in errors}
        
        # Should have validation errors for type mismatches
        assert "version" in error_fields or "discarded" in error_fields

    def test_frozen_model_immutability(self):
        """Test that ApiMeal instances are immutable."""
        meal = create_simple_api_meal()
        
        # Should not be able to modify fields
        with pytest.raises(ValidationError):
            meal.name = "Modified Name"
        
        with pytest.raises(ValidationError):
            meal.author_id = str(uuid4())

    def test_validation_error_quality(self):
        """Test that validation errors provide clear, actionable information."""
        # Create meal with multiple validation errors
        meal_data = {
            "id": "invalid-uuid",
            "name": "",
            "author_id": "invalid-uuid",
            "recipes": [],
            "tags": [],
            "created_at": "invalid-date",
            "updated_at": "invalid-date",
            "version": 0,
            "discarded": "not-boolean"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            ApiMeal.model_validate_json(json.dumps(meal_data))
        
        errors = exc_info.value.errors()
        
        # Should have clear error messages
        error_messages = [error['msg'] for error in errors]
        assert any("Invalid UUID4 format" in msg for msg in error_messages)
        assert any("ensure this value is greater than or equal to 1" in msg or "greater than or equal to 1" in msg for msg in error_messages)

    def test_performance_with_complex_data(self):
        """Test validation performance with complex nested data."""
        import time
        
        # Create complex meal with many nested objects
        complex_meal = create_complex_api_meal()
        json_str = complex_meal.model_dump_json()
        
        # Measure validation time
        start_time = time.time()
        for _ in range(100):
            ApiMeal.model_validate_json(json_str)
        end_time = time.time()
        
        # Should complete validation in reasonable time
        avg_time = (end_time - start_time) / 100
        assert avg_time < 0.1, f"Validation took {avg_time:.4f}s, should be < 0.1s"

    def test_validation_with_real_world_data(self):
        """Test validation with realistic production-like data."""
        # Create meal with realistic data
        meal = create_complex_api_meal()
        
        # Should validate successfully
        assert meal.name
        assert meal.author_id
        assert meal.recipes is not None
        assert meal.tags is not None
        assert len(meal.recipes) > 0
        assert len(meal.tags) > 0
        
        # Should have computed properties
        if meal.nutri_facts:
            assert meal.nutri_facts.calories.value > 0
            assert meal.nutri_facts.protein.value >= 0
            assert meal.nutri_facts.carbohydrate.value >= 0
        
        # Should maintain data integrity
        for recipe in meal.recipes:
            assert recipe.meal_id == meal.id
            assert recipe.author_id == meal.author_id
        
        for tag in meal.tags:
            assert tag.author_id == meal.author_id
            assert tag.type == "meal"

    def test_empty_collections_validation(self):
        """Test validation with empty collections."""
        meal_data = {
            "id": str(uuid4()),
            "name": "Empty Meal",
            "author_id": str(uuid4()),
            "recipes": [],  # Empty recipes
            "tags": [],     # Empty tags
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "version": 1,
            "discarded": False
        }
        
        # Should successfully validate empty collections
        meal = ApiMeal.model_validate_json(json.dumps(meal_data))
        
        assert meal.recipes == []
        assert meal.tags == frozenset()

    def test_boundary_value_validation(self):
        """Test validation with boundary values."""
        meal_data = {
            "id": str(uuid4()),
            "name": "x",  # Minimum length
            "author_id": str(uuid4()),
            "recipes": [],
            "tags": [],
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "version": 1,  # Minimum version
            "discarded": False,
            "carbo_percentage": 0.0,  # Minimum percentage
            "protein_percentage": 100.0,  # Maximum percentage
            "total_fat_percentage": 50.0,  # Mid-range percentage
            "weight_in_grams": 0,  # Minimum weight
            "calorie_density": 0.0  # Minimum calorie density
        }
        
        # Should successfully validate boundary values
        meal = ApiMeal.model_validate_json(json.dumps(meal_data))
        
        assert meal.name == "x"
        assert meal.version == 1
        assert meal.carbo_percentage == 0.0
        assert meal.protein_percentage == 100.0
        assert meal.weight_in_grams == 0
        assert meal.calorie_density == 0.0
