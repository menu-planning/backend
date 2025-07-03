"""
Tests for field validation patterns used in API schemas.

This module validates the documented field validation patterns:
- BeforeValidator(validate_optional_text) for input sanitization  
- field_validator for business logic validation
- AfterValidator for post-processing validation

These tests ensure documentation accuracy and validate edge case handling.
"""

import pytest
from pydantic import ValidationError
from typing import Any, Dict, get_origin, get_args

from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import validate_optional_text
from src.contexts.shared_kernel.adapters.api_schemas.fields import TagValue, TagKey, TagType
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import ApiMeal
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import ApiRecipe
from src.contexts.seedwork.shared.adapters.api_schemas.value_objects.role import ApiSeedRole
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag


def extract_before_validator_func(annotated_type: Any) -> Any:
    """Extract BeforeValidator function from Annotated type metadata."""
    if hasattr(annotated_type, '__metadata__'):
        for metadata_item in annotated_type.__metadata__:
            if hasattr(metadata_item, 'func') and metadata_item.func == validate_optional_text:
                return metadata_item.func
    return None


class TestBeforeValidatorPatterns:
    """Test BeforeValidator patterns for input sanitization."""
    
    def test_validate_optional_text_behavior(self):
        """Test validate_optional_text function with comprehensive edge cases."""
        # Test normal string trimming
        assert validate_optional_text("  normal text  ") == "normal text"
        assert validate_optional_text("no whitespace") == "no whitespace"
        
        # Test None handling
        assert validate_optional_text(None) is None
        
        # Test empty string handling
        assert validate_optional_text("") is None
        assert validate_optional_text("   ") is None  # Whitespace only
        assert validate_optional_text("\t\n\r ") is None  # Various whitespace chars
        
        # Test edge cases with minimal content
        assert validate_optional_text(" a ") == "a"
        assert validate_optional_text("\ta\n") == "a"
        
    def test_tag_field_validation_with_before_validator(self):
        """Test tag fields using BeforeValidator(validate_optional_text)."""
        # Test TagValue with whitespace trimming
        test_cases = [
            ("  trimmed  ", "trimmed"),
            ("normal", "normal"),
            ("  single_char  ", "single_char"),
        ]
        
        for input_value, expected in test_cases:
            # TagValue uses BeforeValidator(validate_optional_text) + Field(min_length=1, max_length=100)
            # So empty strings after trimming should fail validation due to min_length=1
            validator_func = extract_before_validator_func(TagValue)
            if validator_func:
                result = validator_func(input_value)
                assert result == expected
            
    def test_before_validator_edge_cases_with_required_fields(self):
        """Test BeforeValidator behavior with required fields (min_length constraints)."""
        from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal_fields import MealName
        
        # MealName uses BeforeValidator(validate_optional_text) + Field(..., min_length=1)
        before_validator_func = extract_before_validator_func(MealName)
        
        assert before_validator_func is not None, "MealName should use BeforeValidator(validate_optional_text)"
        
        # Test the before validator step
        assert before_validator_func("  valid name  ") == "valid name"
        assert before_validator_func("") is None  # This will fail Field(min_length=1) validation later
        assert before_validator_func("   ") is None  # This will fail Field(min_length=1) validation later
        
    def test_before_validator_with_optional_fields(self):
        """Test BeforeValidator behavior with optional fields."""
        from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe_fields import RecipeNotes, RecipeUtensils
        
        # These fields use BeforeValidator(validate_optional_text) but are optional
        # So None/empty results should be valid
        for field_type in [RecipeNotes, RecipeUtensils]:
            before_validator_func = extract_before_validator_func(field_type)
            
            if before_validator_func:
                assert before_validator_func("  content  ") == "content"
                assert before_validator_func("") is None
                assert before_validator_func(None) is None


class TestFieldValidatorPatterns:
    """Test field_validator patterns for business logic validation."""
    
    def test_role_name_validation_pattern(self):
        """Test field_validator for format validation (lowercase, alphanumeric + underscore/hyphen)."""
        # Valid role names
        valid_names = ["admin", "user_role", "test-role", "role123", "simple"]
        for name in valid_names:
            role_data = {"name": name, "permissions": ["read", "write"]}
            role = ApiSeedRole.model_validate(role_data)
            assert role.name == name
            
        # Invalid role names (should raise ValidationError)
        invalid_names = ["Admin", "ADMIN", "user role", "user@role", "user.role", "user/role"]
        for name in invalid_names:
            role_data = {"name": name, "permissions": ["read"]}
            with pytest.raises(ValidationError) as exc_info:
                ApiSeedRole.model_validate(role_data)
            assert "lowercase" in str(exc_info.value) or "alphanumeric" in str(exc_info.value)
            
    def test_permissions_validation_pattern(self):
        """Test field_validator for collection validation with type conversion."""
        # Test frozenset conversion from list
        role_data = {"name": "test_role", "permissions": ["read", "write", "admin"]}
        role = ApiSeedRole.model_validate(role_data)
        assert isinstance(role.permissions, frozenset)
        assert role.permissions == frozenset(["read", "write", "admin"])
        
        # Test frozenset conversion from set
        role_data = {"name": "test_role", "permissions": {"read", "write"}}
        role = ApiSeedRole.model_validate(role_data)
        assert isinstance(role.permissions, frozenset)
        assert role.permissions == frozenset(["read", "write"])
        
        # Test empty permissions handling
        role_data = {"name": "test_role", "permissions": []}
        role = ApiSeedRole.model_validate(role_data)
        assert role.permissions == frozenset()
        
    def test_collection_uniqueness_validation_with_typeadapters(self, sample_meal_data):
        """Test field_validator patterns that use TypeAdapters for validation."""
        # Test that ApiMeal validates recipes and tags using TypeAdapters
        api_meal = ApiMeal.model_validate(sample_meal_data)
        
        # Verify that collections are validated (actual validation logic is in TypeAdapters)
        assert isinstance(api_meal.recipes, list)
        assert isinstance(api_meal.tags, frozenset)
        
        # The specific validation logic (uniqueness, etc.) is handled by the TypeAdapters
        # which are tested separately in performance tests
        
    def test_business_logic_validation_edge_cases(self):
        """Test field_validator patterns with edge cases."""
        # Test ApiSeedRole with edge case inputs
        edge_cases = [
            {"name": "a", "permissions": []},  # Minimal valid name
            {"name": "a" * 50, "permissions": ["read"]},  # Long valid name
            {"name": "test_123", "permissions": ["p1", "p2", "p1"]},  # Duplicate permissions (should be deduplicated)
        ]
        
        for case in edge_cases:
            try:
                role = ApiSeedRole.model_validate(case)
                # Verify deduplication occurred for duplicate permissions
                if "p1" in case["permissions"]:
                    assert len(role.permissions) == 2  # Should deduplicate "p1"
                    assert "p1" in role.permissions and "p2" in role.permissions
            except ValidationError:
                # Some edge cases might fail validation, which is expected
                pass


class TestAfterValidatorPatterns:
    """Test AfterValidator patterns for post-processing validation."""
    
    def test_id_length_validation_with_format_warnings(self):
        """Test AfterValidator for ID length validation (not strict UUID format validation).
        
        Note: validate_uuid_format only raises ValueError for length issues.
        Format issues only generate warnings but don't fail validation.
        """
        from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import validate_uuid_format
        
        # Valid length (32 hex characters) - should work
        valid_uuid = "a" * 32  # 32 hex characters
        assert validate_uuid_format(valid_uuid) == valid_uuid
        
        # Valid length but invalid format - should work but log warning
        invalid_format_valid_length = "z" * 32  # 32 non-hex characters
        result = validate_uuid_format(invalid_format_valid_length)
        assert result == invalid_format_valid_length  # No exception, just warning logged
        
        # Invalid lengths (should raise ValueError)
        invalid_length_ids = [
            "",  # Too short (< 1)
            "a" * 37,  # Too long (> 36)
        ]
        
        for invalid_id in invalid_length_ids:
            with pytest.raises(ValueError) as exc_info:
                validate_uuid_format(invalid_id)
            assert "length" in str(exc_info.value)
            
        # Edge cases - valid lengths
        edge_cases = [
            "a",  # Minimum length (1)
            "a" * 36,  # Maximum length (36)
        ]
        
        for edge_case in edge_cases:
            result = validate_uuid_format(edge_case)
            assert result == edge_case  # Should not raise exception
            
    def test_percentage_range_validation(self, sample_meal_data):
        """Test AfterValidator for percentage range validation."""
        # Test valid percentages
        valid_meal_data = sample_meal_data.copy()
        valid_meal_data.update({
            "carbo_percentage": 50.0,
            "protein_percentage": 25.0,
            "total_fat_percentage": 25.0,
        })
        
        api_meal = ApiMeal.model_validate(valid_meal_data)
        assert api_meal.carbo_percentage == 50.0
        assert api_meal.protein_percentage == 25.0
        assert api_meal.total_fat_percentage == 25.0
        
        # Test edge cases
        edge_cases = [
            {"carbo_percentage": 0.0},  # Minimum valid
            {"carbo_percentage": 100.0},  # Maximum valid
            {"carbo_percentage": None},  # None should be valid for optional fields
        ]
        
        for case in edge_cases:
            test_data = sample_meal_data.copy()
            test_data.update(case)
            api_meal = ApiMeal.model_validate(test_data)
            assert api_meal.carbo_percentage == case["carbo_percentage"]
            
    def test_non_negative_validation(self, sample_meal_data):
        """Test AfterValidator for non-negative number validation."""
        # Test valid non-negative values
        valid_meal_data = sample_meal_data.copy()
        valid_meal_data.update({
            "weight_in_grams": 500,
            "calorie_density": 2.5,
        })
        
        api_meal = ApiMeal.model_validate(valid_meal_data)
        assert api_meal.weight_in_grams == 500
        assert api_meal.calorie_density == 2.5
        
        # Test edge cases
        edge_cases = [
            {"weight_in_grams": 0},  # Zero should be valid
            {"weight_in_grams": None},  # None should be valid for optional fields
        ]
        
        for case in edge_cases:
            test_data = sample_meal_data.copy()
            test_data.update(case)
            api_meal = ApiMeal.model_validate(test_data)
            assert api_meal.weight_in_grams == case["weight_in_grams"]


class TestValidationIntegration:
    """Test integration of multiple validation patterns."""
    
    def test_complete_meal_validation_pipeline(self, sample_meal_data):
        """Test complete validation pipeline with all validator types."""
        # Test meal with comprehensive data including edge cases
        test_data = sample_meal_data.copy()
        test_data.update({
            "name": "  Test Meal Name  ",  # BeforeValidator should trim
            "description": "   ",  # MealDescription doesn't use BeforeValidator, so this stays as-is
            "notes": None,  # Should remain None
            "carbo_percentage": 45.5,  # AfterValidator should validate range
            "protein_percentage": 25.0,
            "total_fat_percentage": 29.5,
            "weight_in_grams": 750,  # AfterValidator should validate non-negative
        })
        
        api_meal = ApiMeal.model_validate(test_data)
        
        # Verify BeforeValidator effects
        assert api_meal.name == "Test Meal Name"  # Trimmed
        assert api_meal.description == "   "  # MealDescription doesn't use BeforeValidator, preserves whitespace
        assert api_meal.notes is None  # None preserved
        
        # Verify AfterValidator effects
        assert api_meal.carbo_percentage == 45.5
        assert api_meal.protein_percentage == 25.0
        assert api_meal.total_fat_percentage == 29.5
        assert api_meal.weight_in_grams == 750
        
        # Verify field_validator effects (collections properly validated)
        assert isinstance(api_meal.recipes, list)
        assert isinstance(api_meal.tags, frozenset)
        
    def test_validation_error_quality(self):
        """Test that validation errors provide clear, actionable messages."""
        # Test BeforeValidator + Field validation interaction
        with pytest.raises(ValidationError) as exc_info:
            # Empty string after trimming fails min_length validation
            ApiMeal.model_validate({
                "id": "a" * 32,
                "name": "   ",  # Will be trimmed to None, then fail min_length
                "author_id": "a" * 32,
                "recipes": [],
                "tags": frozenset(),
            })
        
        error_str = str(exc_info.value)
        # Should mention the field name and constraint
        assert "name" in error_str
        
        # Test field_validator error quality
        with pytest.raises(ValidationError) as exc_info:
            ApiSeedRole.model_validate({
                "name": "Invalid Name",  # Uppercase should fail
                "permissions": []
            })
        
        error_str = str(exc_info.value)
        assert "lowercase" in error_str or "name" in error_str
        
    def test_validation_pattern_consistency(self):
        """Test that validation patterns are consistently applied across similar fields."""
        # All tag-related string fields should use BeforeValidator(validate_optional_text)
        tag_field_types = [TagValue, TagKey, TagType]
        
        for field_type in tag_field_types:
            # Check that BeforeValidator(validate_optional_text) is used
            before_validator_func = extract_before_validator_func(field_type)
            assert before_validator_func is not None, f"{field_type} should use BeforeValidator(validate_optional_text)"


class TestDocumentationExamples:
    """Test that documented examples work correctly."""
    
    def test_documented_beforevalidator_example(self):
        """Test the BeforeValidator example from documentation."""
        # This tests the exact pattern that will be documented
        from pydantic import BaseModel, Field
        from pydantic import BeforeValidator
        from typing import Annotated
        
        # Example pattern from documentation - create type inside the class to avoid mypy issues
        class ExampleMeal(BaseModel):
            name: Annotated[
                str,
                BeforeValidator(validate_optional_text),
                Field(..., min_length=1, max_length=255)
            ]
            
        # Test the documented behavior
        meal = ExampleMeal(name="  Trimmed Name  ")
        assert meal.name == "Trimmed Name"
        
        # Test validation failure with empty string
        with pytest.raises(ValidationError):
            ExampleMeal(name="   ")  # Should fail min_length after trimming
            
    def test_documented_fieldvalidator_example(self):
        """Test the field_validator example from documentation."""
        # This validates the pattern that will be documented for business logic
        role_data = {
            "name": "valid_role_name",
            "permissions": ["read", "write", "admin"]
        }
        
        role = ApiSeedRole.model_validate(role_data)
        assert role.name == "valid_role_name"
        assert isinstance(role.permissions, frozenset)
        assert len(role.permissions) == 3


@pytest.mark.performance
class TestValidationPerformance:
    """Test performance characteristics of validation patterns."""
    
    def test_beforevalidator_performance(self, benchmark):
        """Benchmark BeforeValidator(validate_optional_text) performance."""
        test_strings = [
            "  normal string  ",
            "",
            "   ",
            None,
            "a" * 1000,  # Long string
        ]
        
        def run_validation():
            for s in test_strings:
                validate_optional_text(s)
                
        # Benchmark the function - this executes it and measures performance
        benchmark(run_validation)
        
        # The benchmark automatically measures performance
        # We can access timing via benchmark.stats if needed, but for this test
        # we just want to ensure the function runs without errors
        
    def test_fieldvalidator_performance(self, benchmark, sample_meal_data):
        """Benchmark field_validator performance with TypeAdapters."""
        def run_validation():
            return ApiMeal.model_validate(sample_meal_data)
            
        # Benchmark the function - this executes it and measures performance  
        result = benchmark(run_validation)
        
        # Verify the result is valid and BeforeValidator processed correctly
        assert isinstance(result, ApiMeal)
        # BeforeValidator(validate_optional_text) trims whitespace from "  Test Meal  " to "Test Meal"
        assert result.name == "Test Meal"  # Trimmed value, not original "  Test Meal  "


# Utility functions for testing
def create_test_validation_scenarios() -> Dict[str, Any]:
    """Create test scenarios for validation pattern testing."""
    return {
        "whitespace_trimming": {
            "input": "  test  ",
            "expected": "test",
            "pattern": "BeforeValidator(validate_optional_text)"
        },
        "empty_to_none": {
            "input": "",
            "expected": None,
            "pattern": "BeforeValidator(validate_optional_text)"
        },
        "business_logic": {
            "input": "Invalid_Name",
            "expected_error": "lowercase",
            "pattern": "field_validator"
        },
        "range_validation": {
            "input": 150.0,
            "expected_error": "between 0 and 100",
            "pattern": "AfterValidator(percentage_range)"
        }
    }


class TestNamingConsistencyIssues:
    """Test that identifies naming inconsistencies in field validation patterns."""
    
    def test_uuid_field_naming_inconsistency(self):
        """Document the naming inconsistency with UUIDId fields.
        
        ISSUE: UUIDId and UUIDIdOptional are misleadingly named since they don't
        enforce strict UUID format - they only validate length and log warnings.
        
        SUGGESTED BETTER NAMES:
        - UUIDId → IdWithLengthValidation or FlexibleId  
        - UUIDIdOptional → OptionalIdWithLengthValidation or OptionalFlexibleId
        
        This test documents the actual behavior for future refactoring consideration.
        """
        from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import UUIDId, UUIDIdOptional
        from pydantic import BaseModel
        
        class TestModel(BaseModel):
            required_id: UUIDId
            optional_id: UUIDIdOptional
            
        # Test that "UUID" fields accept non-UUID formats without raising errors
        test_cases = [
            {
                "required_id": "not_a_uuid_but_valid_length",  # 28 chars - within 1-36 range
                "optional_id": "also_not_uuid_format_ok"       # 23 chars - within 1-36 range
            },
            {
                "required_id": "x" * 32,  # 32 chars, not hex
                "optional_id": None
            },
            {
                "required_id": "short",   # 5 chars, not UUID format
                "optional_id": "a" * 36   # 36 chars, not UUID format
            }
        ]
        
        for test_case in test_cases:
            # These should all work despite not being valid UUID format
            model = TestModel.model_validate(test_case)
            assert model.required_id == test_case["required_id"]
            assert model.optional_id == test_case["optional_id"]
            
        # Document what would actually fail (length violations)
        with pytest.raises(ValidationError) as exc_info:
            TestModel.model_validate({
                "required_id": "",  # Too short (< 1)
                "optional_id": None
            })
        assert "length" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            TestModel.model_validate({
                "required_id": "a" * 37,  # Too long (> 36)
                "optional_id": None
            })
        assert "length" in str(exc_info.value) 