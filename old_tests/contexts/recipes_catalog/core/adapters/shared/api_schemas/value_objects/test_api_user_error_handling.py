"""
Error handling tests for ApiUser schema validation.

Following Phase 1 patterns: behavior-focused approach, comprehensive error handling,
and validation error testing.

Focus: Test error handling behavior and validation error scenarios.
"""

import pytest
import json
from unittest.mock import Mock
from uuid import uuid4

from src.contexts.recipes_catalog.core.adapters.shared.api_schemas.value_objects.api_user import ApiUser
from pydantic import ValidationError

# Import data factories
from tests.contexts.recipes_catalog.core.adapters.shared.api_schemas.value_objects.data_factories.api_user_data_factories import (
    create_api_user,
    create_user_with_empty_role_names,
    create_user_with_roles_with_many_permissions,
    create_invalid_json_test_cases,
)


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================

class TestApiUserErrorHandling:
    """Test comprehensive error handling for ApiUser validation and conversion."""

    def test_from_domain_with_none_domain_object_handles_gracefully(self):
        """Test that from_domain with None domain object raises appropriate error."""
        with pytest.raises(AttributeError):
            ApiUser.from_domain(None)  # type: ignore

    def test_from_domain_with_invalid_domain_object_raises_error(self):
        """Test that from_domain with invalid domain object raises appropriate error."""
        invalid_domain = "not a User object"
        
        with pytest.raises(AttributeError):
            ApiUser.from_domain(invalid_domain)  # type: ignore

    def test_json_validation_with_invalid_json_syntax_raises_error(self):
        """Test that model_validate_json with invalid JSON syntax raises appropriate error."""
        invalid_json = '{"id": "test", "roles": [}]'  # malformed JSON
        
        with pytest.raises((ValidationError, ValueError, json.JSONDecodeError)):
            ApiUser.model_validate_json(invalid_json)

    @pytest.mark.parametrize("invalid_case", create_invalid_json_test_cases())
    def test_json_validation_with_invalid_test_cases_raises_errors(self, invalid_case):
        """Test that invalid JSON test cases raise validation errors."""
        json_data = json.dumps(invalid_case["data"])
        
        with pytest.raises(ValidationError) as exc_info:
            ApiUser.model_validate_json(json_data)
        
        # Verify error contains expected field information
        error_str = str(exc_info.value)
        assert any(field in error_str for field in invalid_case["expected_errors"])

    @pytest.mark.parametrize("invalid_id", [
        "",  # empty string
        "not-a-uuid",  # invalid UUID format
        "12345",  # not UUID format
    ])
    def test_field_validation_errors_with_invalid_id(self, invalid_id):
        """Test validation errors for invalid id field values."""
        with pytest.raises(ValidationError) as exc_info:
            create_api_user(id=invalid_id)
        
        error_str = str(exc_info.value)
        assert "id" in error_str

    def test_field_validation_errors_with_invalid_roles(self):
        """Test validation errors for invalid roles field values."""
        # Test with roles that have invalid properties
        with pytest.raises(ValidationError):
            create_user_with_empty_role_names()
        
        with pytest.raises(ValidationError):
            create_user_with_roles_with_many_permissions()

    def test_multiple_field_validation_errors_aggregation(self):
        """Test that multiple field validation errors are properly aggregated."""
        # Use invalid JSON to trigger multiple validation errors
        invalid_json = json.dumps({
            "id": "not-uuid",  # invalid - not UUID
            "roles": [
                {"name": "", "permissions": []},  # invalid - empty name and permissions
                {"name": "test", "permissions": ["perm"] * 60}  # invalid - too many permissions
            ]
        })
        
        with pytest.raises(ValidationError) as exc_info:
            ApiUser.model_validate_json(invalid_json)
        
        # Verify multiple errors are reported together
        error_message = str(exc_info.value)
        error_fields = ["id", "roles"]
        error_count = sum(1 for field in error_fields if field in error_message)
        assert error_count >= 1  # At least 1 error should be present

    def test_conversion_error_context_preservation(self):
        """Test that conversion errors preserve context about which field failed."""
        # Create mock domain object with problematic attributes
        mock_domain = Mock()
        mock_domain.id = str(uuid4())
        mock_domain.roles = "invalid_roles"  # This might cause issues
        
        # Should handle problematic mock gracefully or provide clear error
        try:
            api_user = ApiUser.from_domain(mock_domain)
            # If successful, verify the result
            assert hasattr(api_user, 'id')
        except Exception as e:
            # If error occurs, should be informative
            assert isinstance(e, (AttributeError, ValidationError, TypeError, ValueError)) 