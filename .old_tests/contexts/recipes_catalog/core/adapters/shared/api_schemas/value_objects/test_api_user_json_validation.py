"""
JSON validation tests for ApiUser schema validation.

Following Phase 1 patterns: behavior-focused approach, comprehensive JSON validation,
and serialization round-trip testing.

Focus: Test JSON validation behavior and serialization integrity.
"""

import pytest
import time
import json
from uuid import uuid4

from src.contexts.recipes_catalog.core.adapters.shared.api_schemas.value_objects.api_user import ApiUser

# Import data factories
from tests.contexts.recipes_catalog.core.adapters.shared.api_schemas.value_objects.data_factories.api_role_data_factories import create_admin_role, create_user_role
from tests.contexts.recipes_catalog.core.adapters.shared.api_schemas.value_objects.data_factories.api_user_data_factories import (
    create_api_user,
    create_valid_json_test_cases
)


# =============================================================================
# JSON VALIDATION TESTS
# =============================================================================

class TestApiUserJsonValidation:
    """Test comprehensive JSON validation for ApiUser."""

    def test_json_validation_with_complete_user_data(self):
        """Test model_validate_json with complete user data."""
        json_data = json.dumps({
            "id": str(uuid4()),
            "roles": [
                {"name": "administrator_role", "permissions": ["manage_users", "manage_recipes", "manage_meals", "view_audit_log"]},
                {"name": "user_role", "permissions": ["access_basic_features"]}
            ]
        })
        
        api_user = ApiUser.model_validate_json(json_data)
        
        # Verify all fields are correctly parsed
        assert api_user.id is not None
        assert len(api_user.roles) == 2
        
        # Verify role parsing
        role_names = {role.name for role in api_user.roles}
        assert "administrator_role" in role_names
        assert "user_role" in role_names

    def test_json_validation_with_minimal_required_fields(self):
        """Test model_validate_json with only required fields."""
        json_data = json.dumps({
            "id": str(uuid4())
        })
        
        api_user = ApiUser.model_validate_json(json_data)
        
        # Verify required fields are parsed
        assert api_user.id is not None
        
        # Verify optional fields have defaults
        assert api_user.roles == frozenset()

    def test_json_validation_with_empty_roles_list(self):
        """Test JSON validation with empty roles list."""
        json_data = json.dumps({
            "id": str(uuid4()),
            "roles": []
        })
        
        api_user = ApiUser.model_validate_json(json_data)
        
        # Verify empty roles are handled correctly
        assert api_user.roles == frozenset()

    @pytest.mark.parametrize("test_case", create_valid_json_test_cases())
    def test_json_validation_with_valid_test_cases(self, test_case):
        """Test JSON validation with parametrized valid test cases."""
        json_data = json.dumps(test_case)
        
        # Should validate successfully
        api_user = ApiUser.model_validate_json(json_data)
        
        # Verify basic structure
        assert isinstance(api_user, ApiUser)
        assert api_user.id is not None
        assert isinstance(api_user.roles, frozenset)

    def test_json_serialization_roundtrip_integrity(self):
        """Test JSON serialization and deserialization maintains data integrity."""
        # Create roles directly
        admin_role = create_admin_role()
        user_role = create_user_role()
        
        original_user = create_api_user(
            id=str(uuid4()),
            roles=frozenset([admin_role, user_role])
        )
        
        # Serialize to JSON
        json_string = original_user.model_dump_json()
        
        # Deserialize from JSON
        recreated_user = ApiUser.model_validate_json(json_string)
        
        # Verify complete integrity
        assert recreated_user.id == original_user.id
        assert len(recreated_user.roles) == len(original_user.roles)
        
        # Verify role integrity
        original_role_names = {role.name for role in original_user.roles}
        recreated_role_names = {role.name for role in recreated_user.roles}
        assert original_role_names == recreated_role_names

    def test_json_validation_performance_with_user_datasets(self):
        """Test JSON validation performance with large user datasets."""
        # Create large dataset directly as properly formatted JSON data
        json_data_list = []
        for i in range(100):
            user_data = {
                "id": str(uuid4()),
                "roles": [
                    {"name": "user_role", "permissions": ["access_basic_features"]},
                    {"name": "administrator_role", "permissions": ["manage_users", "manage_recipes", "manage_meals", "view_audit_log"]}
                ]
            }
            json_str = json.dumps(user_data)
            json_data_list.append(json_str)
        
        start_time = time.perf_counter()
        
        # Validate each user from JSON
        for json_str in json_data_list:
            api_user = ApiUser.model_validate_json(json_str)
            assert isinstance(api_user, ApiUser)
        
        end_time = time.perf_counter()
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Performance requirement: < 50ms for 100 users
        assert execution_time < 50.0, f"JSON validation performance failed: {execution_time:.2f}ms > 50ms" 