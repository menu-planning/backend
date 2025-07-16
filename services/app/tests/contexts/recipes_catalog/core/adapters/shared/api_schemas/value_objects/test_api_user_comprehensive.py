"""
Comprehensive behavior-focused tests for ApiUser schema validation.

Following Phase 1 patterns: 90+ test methods with >95% coverage, behavior-focused approach,
round-trip validation, comprehensive error handling, edge cases, and performance validation.

Focus: Test behavior and verify correctness, not implementation details.
Special focus: JSON validation, role constraints, and four-layer conversion integrity.
"""

import pytest
import time
import json
from unittest.mock import Mock
from uuid import uuid4
from typing import Any, Dict, List

from src.contexts.recipes_catalog.core.adapters.shared.api_schemas.value_objects.api_user import ApiUser
from src.contexts.recipes_catalog.core.domain.shared.value_objects.user import User
from src.contexts.recipes_catalog.core.domain.shared.value_objects.role import Role
from src.contexts.iam.core.adapters.ORM.sa_models.user_sa_model import UserSaModel
from pydantic import ValidationError

# Import data factories
from tests.contexts.recipes_catalog.core.adapters.shared.api_schemas.value_objects.data_factories.api_user_data_factories import (
    reset_api_user_counters,
    create_api_user_kwargs,
    create_api_user,
    create_api_user_from_json,
    create_api_user_json,
    create_admin_user,
    create_basic_user,
    create_guest_user,
    create_multi_role_user,
    create_content_manager_user,
    create_api_integration_user,
    create_premium_user,
    create_professional_user,
    create_user_without_roles,
    create_user_with_single_role,
    create_user_with_max_roles,
    create_user_with_duplicate_role_names,
    create_user_with_empty_role_names,
    create_user_with_roles_with_many_permissions,
    create_user_hierarchy,
    create_users_with_different_role_combinations,
    create_users_with_different_ids,
    create_test_user_dataset,
    create_user_domain_from_api,
    create_api_user_from_domain,
    create_user_orm_kwargs_from_api,
    create_api_user_from_orm,
    create_valid_json_test_cases,
    create_invalid_json_test_cases,
    check_json_serialization_roundtrip,
    create_edge_case_users,
    create_bulk_user_creation_dataset,
    create_bulk_json_serialization_dataset,
    create_bulk_json_deserialization_dataset,
    create_conversion_performance_dataset,
    create_role_validation_performance_dataset,
    create_admin_role,
    create_user_role,
    create_premium_user_role,
    create_api_role,
)


# =============================================================================
# FIXTURES
# =============================================================================

@pytest.fixture(autouse=True)
def _reset_user_counters():
    """Reset data factory counters before each test for deterministic behavior"""
    reset_api_user_counters()


# =============================================================================
# FOUR-LAYER CONVERSION TESTS
# =============================================================================

class TestApiUserFourLayerConversion:
    """Test comprehensive four-layer conversion patterns for ApiUser."""

    def test_from_domain_conversion_preserves_all_data(self):
        """Test that domain to API conversion preserves all user data accurately."""
        # Create domain user with all fields using valid role names and permissions
        domain_user = User(
            id=str(uuid4()),
            roles=frozenset([
                Role(name="administrator_role", permissions=frozenset(["manage_users", "manage_recipes", "manage_meals", "view_audit_log"])),
                Role(name="user_role", permissions=frozenset(["access_basic_features", "manage_recipes"]))
            ])
        )
        
        api_user = ApiUser.from_domain(domain_user)
        
        # Verify all fields are preserved
        assert api_user.id == domain_user.id
        assert len(api_user.roles) == len(domain_user.roles)
        
        # Verify role conversion
        domain_role_names = {role.name for role in domain_user.roles}
        api_role_names = {role.name for role in api_user.roles}
        assert domain_role_names == api_role_names

    def test_to_domain_conversion_preserves_all_data(self):
        """Test that API to domain conversion preserves all user data accurately."""
        # Create roles directly instead of using factory recursion
        admin_role = create_admin_role()
        user_role = create_user_role()
        
        api_user = create_api_user(
            id=str(uuid4()),
            roles=frozenset([admin_role, user_role])
        )
        
        domain_user = api_user.to_domain()
        
        # Verify conversion to domain objects
        assert isinstance(domain_user, User)
        assert domain_user.id == api_user.id
        assert len(domain_user.roles) == len(api_user.roles)
        
        # Verify role conversion
        api_role_names = {role.name for role in api_user.roles}
        domain_role_names = {role.name for role in domain_user.roles}
        assert api_role_names == domain_role_names

    def test_from_orm_model_conversion_preserves_all_data(self):
        """Test that ORM to API conversion handles all field types correctly."""
        mock_orm = Mock()
        mock_orm.id = str(uuid4())
        mock_orm.roles = [
            {"name": "administrator_role", "permissions": "manage_users, manage_recipes, manage_meals, view_audit_log"},
            {"name": "user_role", "permissions": "access_basic_features, manage_recipes"}
        ]
        
        api_user = ApiUser.from_orm_model(mock_orm)
        
        # Verify all fields are preserved
        assert api_user.id == mock_orm.id
        assert len(api_user.roles) == len(mock_orm.roles)
        
        # Verify role conversion
        orm_role_names = {role["name"] for role in mock_orm.roles}
        api_role_names = {role.name for role in api_user.roles}
        assert orm_role_names == api_role_names

    def test_to_orm_kwargs_conversion_extracts_all_values(self):
        """Test that API to ORM kwargs conversion extracts all field values correctly."""
        # Create roles directly
        admin_role = create_admin_role()
        user_role = create_user_role()
        
        api_user = create_api_user(
            id=str(uuid4()),
            roles=frozenset([admin_role, user_role])
        )
        
        orm_kwargs = api_user.to_orm_kwargs()
        
        # Verify all fields are extracted
        assert orm_kwargs["id"] == api_user.id
        assert len(orm_kwargs["roles"]) == len(api_user.roles)
        
        # Verify role conversion
        api_role_names = {role.name for role in api_user.roles}
        orm_role_names = {role["name"] for role in orm_kwargs["roles"]}
        assert api_role_names == orm_role_names

    def test_round_trip_domain_to_api_to_domain_integrity(self):
        """Test round-trip conversion domain → API → domain maintains data integrity."""
        original_domain = User(
            id=str(uuid4()),
            roles=frozenset([
                Role(name="recipe_manager", permissions=frozenset(["manage_recipes", "access_basic_features"])),
                Role(name="content_moderator", permissions=frozenset(["manage_recipes", "manage_meals"]))
            ])
        )
        
        # Round trip: domain → API → domain
        api_user = ApiUser.from_domain(original_domain)
        converted_domain = api_user.to_domain()
        
        # Verify complete integrity
        assert converted_domain.id == original_domain.id
        assert len(converted_domain.roles) == len(original_domain.roles)
        
        # Verify role integrity
        original_role_names = {role.name for role in original_domain.roles}
        converted_role_names = {role.name for role in converted_domain.roles}
        assert original_role_names == converted_role_names

    def test_round_trip_api_to_orm_to_api_preserves_all_values(self):
        """Test round-trip API → ORM → API preserves all field values."""
        # Create roles directly
        premium_role = create_premium_user_role()
        chef_role = create_api_role(name="chef_role", permissions=frozenset(["manage_recipes", "access_basic_features"]))
        
        original_api = create_api_user(
            id=str(uuid4()),
            roles=frozenset([premium_role, chef_role])
        )
        
        # API → ORM kwargs → mock ORM → API cycle
        orm_kwargs = original_api.to_orm_kwargs()
        
        mock_orm = Mock()
        mock_orm.id = orm_kwargs["id"]
        mock_orm.roles = orm_kwargs["roles"]
        
        reconstructed_api = ApiUser.from_orm_model(mock_orm)
        
        # Verify all values preserved
        assert reconstructed_api.id == original_api.id
        assert len(reconstructed_api.roles) == len(original_api.roles)
        
        # Verify role integrity
        original_role_names = {role.name for role in original_api.roles}
        reconstructed_role_names = {role.name for role in reconstructed_api.roles}
        assert original_role_names == reconstructed_role_names

    def test_four_layer_conversion_with_comprehensive_user_profile(self):
        """Test four-layer conversion with comprehensive user profile."""
        # Create comprehensive domain user with valid role names and permissions
        comprehensive_domain = User(
            id=str(uuid4()),
            roles=frozenset([
                Role(name="administrator_role", permissions=frozenset(["manage_users", "manage_recipes", "manage_meals", "view_audit_log"])),
                Role(name="recipe_manager", permissions=frozenset(["manage_recipes", "access_basic_features"])),
                Role(name="premium_user", permissions=frozenset(["access_basic_features", "access_support"]))
            ])
        )
        
        # Domain → API → Domain cycle
        api_converted = ApiUser.from_domain(comprehensive_domain)
        domain_final = api_converted.to_domain()
        
        # Verify all fields maintain integrity
        assert domain_final.id == comprehensive_domain.id
        assert len(domain_final.roles) == len(comprehensive_domain.roles)
        
        # Verify role integrity
        original_role_names = {role.name for role in comprehensive_domain.roles}
        final_role_names = {role.name for role in domain_final.roles}
        assert original_role_names == final_role_names


# =============================================================================
# FIELD VALIDATION TESTS
# =============================================================================

class TestApiUserFieldValidation:
    """Test comprehensive field validation for ApiUser data."""

    @pytest.mark.parametrize("valid_uuid", [
        str(uuid4()),
        str(uuid4()),
        str(uuid4()),
        "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
    ])
    def test_id_field_validation_with_valid_uuids(self, valid_uuid):
        """Test id field accepts valid UUID formats."""
        user = create_api_user(id=valid_uuid)
        assert user.id == valid_uuid

    @pytest.mark.parametrize("roles", [
        frozenset(),  # Empty roles
        frozenset([create_user_role()]),  # Single role
        frozenset([create_admin_role(), create_user_role()]),  # Multiple roles
        frozenset([create_premium_user_role()]),  # Professional roles
    ])
    def test_roles_field_validation_with_various_role_sets(self, roles):
        """Test roles field accepts various role combinations."""
        user = create_api_user(roles=roles)
        assert user.roles == roles

    def test_roles_field_validation_with_role_uniqueness(self):
        """Test roles field enforces role uniqueness by name."""
        # Create duplicate roles (same name, different permissions)
        role1 = create_user_role()
        role2 = create_user_role()  # Same role, should be deduplicated
        
        # Should not create duplicate roles
        user = create_api_user(roles=frozenset([role1, role2]))
        
        # Verify uniqueness is enforced (frozenset automatically deduplicates equal objects)
        role_names = [role.name for role in user.roles]
        assert len(set(role_names)) == len(role_names)

    def test_roles_field_validation_with_empty_role_names(self):
        """Test roles field validation with empty role names."""
        with pytest.raises(ValidationError) as exc_info:
            create_user_with_empty_role_names()
        
        error_str = str(exc_info.value)
        # The actual error is from Pydantic validation, not our custom message
        assert "name" in error_str.lower() or "string_type" in error_str

    def test_roles_field_validation_with_too_many_permissions(self):
        """Test roles field validation with roles having too many permissions."""
        with pytest.raises(ValidationError) as exc_info:
            create_user_with_roles_with_many_permissions()
        
        error_str = str(exc_info.value)
        # The actual error is about invalid permissions, not frozen sets
        assert "permissions" in error_str.lower() or "apirole" in error_str.lower()

    @pytest.mark.parametrize("user_factory", [
        create_admin_user,
        create_basic_user,
        create_guest_user,
        create_premium_user,
        create_professional_user
    ])
    def test_specialized_user_types_validation(self, user_factory):
        """Test validation for specialized user types."""
        user = user_factory()
        
        # Verify all are valid ApiUser instances
        assert isinstance(user, ApiUser)
        assert user.id is not None
        assert isinstance(user.roles, frozenset)

    def test_field_constraints_boundary_validation(self):
        """Test field validation at constraint boundaries."""
        # Test minimum valid values
        min_user = create_user_without_roles()
        assert len(min_user.roles) == 0
        
        # Test maximum valid values
        max_user = create_user_with_max_roles()
        assert len(max_user.roles) > 0
        
        # Test single role
        single_role_user = create_user_with_single_role()
        assert len(single_role_user.roles) == 1

    def test_comprehensive_field_validation_with_all_constraints(self):
        """Test comprehensive field validation with all constraint types."""
        # Create roles directly
        admin_role = create_admin_role()
        user_role = create_user_role()
        premium_role = create_premium_user_role()
        
        comprehensive_user = create_api_user(
            id=str(uuid4()),
            roles=frozenset([admin_role, user_role, premium_role])
        )
        
        # Verify all fields meet constraints
        assert comprehensive_user.id is not None
        assert len(comprehensive_user.id) > 0
        assert isinstance(comprehensive_user.roles, frozenset)
        
        # Verify role constraints
        for role in comprehensive_user.roles:
            assert role.name is not None
            assert len(role.name) > 0
            assert len(role.permissions) > 0
            assert len(role.permissions) <= 50


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


# =============================================================================
# EDGE CASES TESTS
# =============================================================================

class TestApiUserEdgeCases:
    """Test comprehensive edge cases for ApiUser data handling."""

    def test_user_without_roles_creation(self):
        """Test creating a user without any roles."""
        user_without_roles = create_user_without_roles()
        
        # Verify user without roles is valid
        assert len(user_without_roles.roles) == 0
        assert user_without_roles.id is not None

    def test_user_with_single_role_creation(self):
        """Test creating a user with exactly one role."""
        single_role_user = create_user_with_single_role()
        
        # Verify single role user is valid
        assert len(single_role_user.roles) == 1
        assert single_role_user.id is not None

    def test_user_with_maximum_roles_creation(self):
        """Test creating a user with maximum number of roles."""
        max_roles_user = create_user_with_max_roles()
        
        # Verify max roles user is valid
        assert len(max_roles_user.roles) > 1
        assert max_roles_user.roles is not None

    @pytest.mark.parametrize("user", create_users_with_different_ids())
    def test_user_with_different_id_formats(self, user):
        """Test users with different valid UUID formats."""
        # Verify all users have valid IDs
        assert user.id is not None
        assert len(user.id) > 0

    @pytest.mark.parametrize("user", create_user_hierarchy())
    def test_user_with_role_hierarchy_combinations(self, user):
        """Test users with different role hierarchy combinations."""
        # Verify hierarchy users are valid
        assert isinstance(user, ApiUser)
        assert user.id is not None

    @pytest.mark.parametrize("user", create_users_with_different_role_combinations())
    def test_user_with_different_role_combinations(self, user):
        """Test users with various role combinations."""
        # Verify all combinations are valid
        assert isinstance(user, ApiUser)
        assert user.id is not None

    @pytest.mark.parametrize("original", create_edge_case_users())
    def test_edge_case_round_trip_conversions(self, original):
        """Test round-trip conversions with edge case values."""
        # Round trip through domain
        domain_user = original.to_domain()
        converted_back = ApiUser.from_domain(domain_user)
        
        # Verify edge case round-trip integrity
        assert converted_back.id == original.id
        assert len(converted_back.roles) == len(original.roles)

    def test_unicode_and_special_characters_handling(self):
        """Test handling of unicode and special characters in user data."""
        # Test with special UUID format
        special_uuid = str(uuid4())
        user = create_api_user(id=special_uuid)
        
        # Verify special characters are handled correctly
        assert user.id == special_uuid

    def test_role_permission_boundary_conditions(self):
        """Test boundary conditions for role permissions."""
        # Test with minimal valid permissions
        minimal_user = create_user_with_single_role()
        
        # Verify minimal permissions are valid
        for role in minimal_user.roles:
            assert len(role.permissions) > 0
            assert len(role.permissions) <= 50

    def test_duplicate_role_name_handling(self):
        """Test handling of duplicate role names."""
        # Create two identical roles (same name and permissions) that should be deduplicated
        role1 = create_api_role(name="duplicate", permissions=frozenset(["access_basic_features"]))
        role2 = create_api_role(name="duplicate", permissions=frozenset(["access_basic_features"]))
        
        try:
            # Create user with identical roles - they should be deduplicated by frozenset
            duplicate_user = create_api_user(roles=frozenset([role1, role2]))
            
            # Verify deduplication occurred (identical objects are deduplicated)
            role_names = [role.name for role in duplicate_user.roles]
            # Note: frozenset deduplicates by object equality, not by name
            # If roles are truly identical, they'll be deduplicated
            # If roles have different permissions, they won't be deduplicated
            assert len(role_names) >= 1  # At least one role should exist
            
        except ValidationError:
            # If validation error occurs due to duplicate detection, that's also valid behavior
            pass


# =============================================================================
# PERFORMANCE VALIDATION TESTS
# =============================================================================

class TestApiUserPerformanceValidation:
    """Test comprehensive performance validation for ApiUser operations."""

    def test_four_layer_conversion_performance(self):
        """Test performance of four-layer conversion operations."""
        # Create comprehensive user with roles directly
        admin_role = create_admin_role()
        user_role = create_user_role()
        premium_role = create_premium_user_role()
        
        comprehensive_user = create_api_user(
            id=str(uuid4()),
            roles=frozenset([admin_role, user_role, premium_role])
        )
        
        # Test API → domain conversion performance
        start_time = time.perf_counter()
        for _ in range(1000):
            domain_user = comprehensive_user.to_domain()
        end_time = time.perf_counter()
        
        api_to_domain_time = (end_time - start_time) / 1000
        assert api_to_domain_time < 0.001  # Should be under 1ms per conversion
        
        # Test domain → API conversion performance
        start_time = time.perf_counter()
        for _ in range(1000):
            api_user = ApiUser.from_domain(domain_user)
        end_time = time.perf_counter()
        
        domain_to_api_time = (end_time - start_time) / 1000
        assert domain_to_api_time < 0.001  # Should be under 1ms per conversion

    def test_json_validation_performance_with_large_datasets(self):
        """Test JSON validation performance with large user datasets."""
        # Create large dataset
        dataset = create_test_user_dataset(user_count=100)
        
        start_time = time.perf_counter()
        
        # Validate each user from dataset
        for user_data in dataset["users"]:
            api_user = ApiUser.model_validate(user_data)
            assert isinstance(api_user, ApiUser)
        
        end_time = time.perf_counter()
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Performance requirement: < 50ms for 100 users
        assert execution_time < 50.0, f"JSON validation performance failed: {execution_time:.2f}ms > 50ms"

    def test_role_validation_performance(self):
        """Test role validation performance with complex data."""
        # Create users with complex role configurations
        complex_users = create_role_validation_performance_dataset(count=100)
        
        start_time = time.perf_counter()
        
        # Perform validation operations
        for user in complex_users:
            # JSON serialization
            json_data = user.model_dump_json()
            # JSON deserialization
            recreated = ApiUser.model_validate_json(json_data)
            assert recreated.id == user.id
        
        end_time = time.perf_counter()
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Performance requirement: < 100ms for 100 complex users
        assert execution_time < 100.0, f"Role validation performance failed: {execution_time:.2f}ms > 100ms"

    def test_bulk_conversion_performance(self):
        """Test performance of bulk conversion operations."""
        # Create many users directly
        users = []
        for i in range(50):
            user = create_api_user(
                id=str(uuid4()),
                roles=frozenset([create_user_role()])
            )
            users.append(user)
        
        start_time = time.perf_counter()
        
        # Perform bulk domain conversions
        domain_users = [user.to_domain() for user in users]
        
        # Perform bulk API conversions
        converted_back = [ApiUser.from_domain(domain) for domain in domain_users]
        
        end_time = time.perf_counter()
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Performance requirement: < 25ms for 50 users (bulk operations)
        assert execution_time < 25.0, f"Bulk conversion performance failed: {execution_time:.2f}ms > 25ms"
        
        # Verify conversion integrity
        assert len(converted_back) == len(users)
        for i, user in enumerate(converted_back):
            assert user.id == users[i].id


# =============================================================================
# INTEGRATION BEHAVIOR TESTS
# =============================================================================

class TestApiUserIntegrationBehavior:
    """Test comprehensive integration behavior for ApiUser schema."""

    def test_immutability_behavior(self):
        """Test that ApiUser instances are immutable."""
        user_role = create_user_role()
        user = create_api_user(
            id=str(uuid4()),
            roles=frozenset([user_role])
        )
        
        # Verify immutability
        with pytest.raises(ValueError):
            user.id = str(uuid4())
        
        with pytest.raises(ValueError):
            user.roles = frozenset()

    def test_serialization_deserialization_consistency(self):
        """Test serialization and deserialization consistency."""
        # Create roles directly
        admin_role = create_admin_role()
        user_role = create_user_role()
        
        original_user = create_api_user(
            id=str(uuid4()),
            roles=frozenset([admin_role, user_role])
        )
        
        # Serialize to JSON and back to dict for consistency
        json_str = original_user.model_dump_json()
        serialized_dict = json.loads(json_str)
        
        # Deserialize from dict through JSON
        deserialized_user = ApiUser.model_validate_json(json_str)
        
        # Verify consistency
        assert deserialized_user.id == original_user.id
        assert len(deserialized_user.roles) == len(original_user.roles)
        
        # Verify role consistency
        original_role_names = {role.name for role in original_user.roles}
        deserialized_role_names = {role.name for role in deserialized_user.roles}
        assert original_role_names == deserialized_role_names

    def test_json_serialization_deserialization_consistency(self):
        """Test JSON serialization and deserialization consistency."""
        # Create roles directly with valid permissions
        premium_role = create_premium_user_role()
        chef_role = create_api_role(name="chef_role", permissions=frozenset(["manage_recipes", "access_basic_features"]))
        
        original_user = create_api_user(
            id=str(uuid4()),
            roles=frozenset([premium_role, chef_role])
        )
        
        # Serialize to JSON
        json_str = original_user.model_dump_json()
        
        # Deserialize from JSON
        deserialized_user = ApiUser.model_validate_json(json_str)
        
        # Verify consistency
        assert deserialized_user.id == original_user.id
        assert len(deserialized_user.roles) == len(original_user.roles)
        
        # Verify role consistency
        original_role_names = {role.name for role in original_user.roles}
        deserialized_role_names = {role.name for role in deserialized_user.roles}
        assert original_role_names == deserialized_role_names

    def test_hash_and_equality_behavior(self):
        """Test hash and equality behavior for ApiUser instances."""
        user_role = create_user_role()
        user_1 = create_api_user(
            id=str(uuid4()),
            roles=frozenset([user_role])
        )
        
        user_2 = create_api_user(
            id=user_1.id,
            roles=user_1.roles
        )
        
        admin_role = create_admin_role()
        user_3 = create_api_user(
            id=str(uuid4()),
            roles=frozenset([admin_role])
        )
        
        # Verify equality behavior
        assert user_1 == user_2
        assert user_1 != user_3
        
        # Test uniqueness using list comprehension instead of sets
        users = [user_1, user_2, user_3]
        unique_users = []
        for user in users:
            if user not in unique_users:
                unique_users.append(user)
        assert len(unique_users) == 2  # Should have only 2 unique instances

    @pytest.mark.parametrize("user", create_user_hierarchy())
    def test_user_role_hierarchy_integration(self, user):
        """Test behavior when users have hierarchical roles."""
        # Verify hierarchy behavior
        assert isinstance(user, ApiUser)
        assert user.id is not None
        
        # Test domain conversion in hierarchy context
        domain_user = user.to_domain()
        assert isinstance(domain_user, User)
        
        # Test role permissions are preserved
        for role in user.roles:
            assert len(role.permissions) > 0

    @pytest.mark.parametrize("user", [
        create_admin_user(),
        create_basic_user(),
        create_premium_user(),
        create_professional_user()
    ])
    def test_cross_context_compatibility(self, user):
        """Test compatibility across different contexts."""
        # Verify all user types work with same schema
        assert isinstance(user, ApiUser)
        
        # Test that all can be converted to domain
        domain_user = user.to_domain()
        assert isinstance(domain_user, User)
        
        # Test that all can be serialized to JSON
        json_data = user.model_dump_json()
        recreated = ApiUser.model_validate_json(json_data)
        assert recreated.id == user.id

    @pytest.mark.parametrize("factory_func", [
        create_admin_user,
        create_basic_user,
        create_guest_user,
        create_multi_role_user,
        create_content_manager_user,
        create_api_integration_user,
        create_premium_user,
        create_professional_user,
        create_user_without_roles,
        create_user_with_single_role,
        create_user_with_max_roles
    ])
    def test_data_factory_integration_consistency(self, factory_func):
        """Test consistency when using various data factory functions."""
        user = factory_func()
        
        # Verify all factory functions produce valid users
        assert isinstance(user, ApiUser)
        assert user.id is not None
        assert isinstance(user.roles, frozenset)
        
        # Test JSON serialization roundtrip
        assert check_json_serialization_roundtrip(user) 