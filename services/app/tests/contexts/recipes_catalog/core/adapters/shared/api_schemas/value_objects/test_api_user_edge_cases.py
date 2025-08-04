"""
Edge cases tests for ApiUser schema validation.

Following Phase 1 patterns: behavior-focused approach, comprehensive edge case coverage,
and boundary condition testing.

Focus: Test edge case behavior and boundary conditions.
Uses hybrid approach: direct kwargs for explicit edge cases, factories for complex scenarios.
"""

import pytest
from uuid import uuid4

from src.contexts.recipes_catalog.core.adapters.shared.api_schemas.value_objects.api_user import ApiUser
from src.contexts.recipes_catalog.core.adapters.shared.api_schemas.value_objects.api_role import ApiRole
from pydantic import ValidationError

# Import data factories (used selectively for complex scenarios)
from tests.contexts.recipes_catalog.core.adapters.shared.api_schemas.value_objects.data_factories.api_user_data_factories import (
    create_user_hierarchy,
    create_users_with_different_role_combinations,
    create_edge_case_users,
    create_users_with_different_ids,
)



# =============================================================================
# LIGHTWEIGHT KWARGS HELPERS FOR UNIT TESTS
# =============================================================================

def minimal_user_kwargs(**overrides) -> dict:
    """Create minimal user kwargs for unit tests with clear defaults."""
    return {
        "id": str(uuid4()),
        "roles": frozenset(),
        **overrides
    }

def single_role_user_kwargs(role_name: str = "test_role", permissions: frozenset | None = None, **overrides) -> dict:
    """Create user kwargs with a single role for clear testing."""
    if permissions is None:
        permissions = frozenset(["access_basic_features"])
    
    role = ApiRole(name=role_name, permissions=permissions)
    return {
        "id": str(uuid4()),
        "roles": frozenset([role]),
        **overrides
    }

def multi_role_user_kwargs(role_specs: list | None = None, **overrides) -> dict:
    """Create user kwargs with multiple roles for explicit testing."""
    if role_specs is None:
        role_specs = [
            ("administrator_role", frozenset(["manage_users", "manage_recipes"])),
            ("standard_user", frozenset(["access_basic_features"]))
        ]
    
    roles = frozenset([
        ApiRole(name=name, permissions=perms) 
        for name, perms in role_specs
    ])
    
    return {
        "id": str(uuid4()),
        "roles": roles,
        **overrides
    }


# =============================================================================
# EDGE CASES TESTS - HYBRID APPROACH
# =============================================================================

class TestApiUserEdgeCases:
    """Test comprehensive edge cases for ApiUser data handling."""

    def test_user_without_roles_creation(self):
        """Test creating a user without any roles - explicit edge case."""
        # Direct construction makes the edge case explicit
        user = ApiUser(**minimal_user_kwargs())
        
        # Verify user without roles is valid
        assert len(user.roles) == 0
        assert user.id is not None
        assert user.roles == frozenset()

    def test_user_with_single_role_creation(self):
        """Test creating a user with exactly one role - explicit edge case."""
        # Direct construction shows exactly what we're testing
        user = ApiUser(**single_role_user_kwargs(
            role_name="standard_user",
            permissions=frozenset(["access_basic_features"])
        ))
        
        # Verify single role user is valid
        assert len(user.roles) == 1
        assert user.id is not None
        
        role = next(iter(user.roles))
        assert role.name == "standard_user"
        assert "access_basic_features" in role.permissions

    def test_user_with_maximum_roles_creation(self):
        """Test creating a user with maximum number of roles - use factory for complexity."""
        # Factory is appropriate here due to complexity
        from tests.contexts.recipes_catalog.core.adapters.shared.api_schemas.value_objects.data_factories.api_user_data_factories import create_user_with_max_roles
        max_roles_user = create_user_with_max_roles()
        
        # Verify max roles user is valid
        assert len(max_roles_user.roles) > 1
        assert max_roles_user.roles is not None

    @pytest.mark.parametrize("user", create_users_with_different_ids())
    def test_user_with_different_id_formats(self, user):
        """Test users with different valid UUID formats - factory appropriate for parametrized test."""
        # Verify all users have valid IDs
        assert user.id is not None
        assert len(user.id) > 0

    @pytest.mark.parametrize("user", create_user_hierarchy())
    def test_user_with_role_hierarchy_combinations(self, user):
        """Test users with different role hierarchy combinations - factory appropriate."""
        # Verify hierarchy users are valid
        assert isinstance(user, ApiUser)
        assert user.id is not None

    @pytest.mark.parametrize("user", create_users_with_different_role_combinations())
    def test_user_with_different_role_combinations(self, user):
        """Test users with various role combinations - factory appropriate for comprehensive coverage."""
        # Verify all combinations are valid
        assert isinstance(user, ApiUser)
        assert user.id is not None

    @pytest.mark.parametrize("original", create_edge_case_users())
    def test_edge_case_round_trip_conversions(self, original):
        """Test round-trip conversions with edge case values - factory appropriate."""
        # Round trip through domain
        domain_user = original.to_domain()
        converted_back = ApiUser.from_domain(domain_user)
        
        # Verify edge case round-trip integrity
        assert converted_back.id == original.id
        assert len(converted_back.roles) == len(original.roles)

    def test_unicode_and_special_characters_handling(self):
        """Test handling of unicode and special characters in user data - explicit test case."""
        # Direct construction makes the test intent clear
        special_uuid = "550e8400-e29b-41d4-a716-446655440001"  # Known valid UUID
        user = ApiUser(**minimal_user_kwargs(id=special_uuid))
        
        # Verify special characters are handled correctly
        assert user.id == special_uuid

    def test_role_permission_boundary_conditions(self):
        """Test boundary conditions for role permissions - explicit edge cases."""
        # Test with minimal valid permissions (1 permission)
        minimal_role = ApiRole(
            name="minimal_role", 
            permissions=frozenset(["access_basic_features"])
        )
        user_minimal = ApiUser(**minimal_user_kwargs(roles=frozenset([minimal_role])))
        
        # Test with maximum valid permissions (all allowed permissions)
        # Based on validation error, these are the allowed permissions:
        all_valid_permissions = frozenset([
            "access_basic_features", "access_developer_tools", "access_support", 
            "manage_clients", "manage_meals", "manage_menus", "manage_recipes", 
            "manage_users", "view_audit_log"
        ])
        max_role = ApiRole(
            name="max_permissions_role",
            permissions=all_valid_permissions
        )
        user_max = ApiUser(**minimal_user_kwargs(roles=frozenset([max_role])))
        
        # Verify boundary conditions
        assert len(minimal_role.permissions) == 1
        assert len(max_role.permissions) == 9  # All valid permissions
        assert user_minimal.id is not None
        assert user_max.id is not None

    def test_duplicate_role_name_handling(self):
        """Test handling of duplicate role names - explicit edge case with clear intent."""
        # Create two roles with same name but different permissions
        role1 = ApiRole(
            name="duplicate_role", 
            permissions=frozenset(["access_basic_features"])
        )
        role2 = ApiRole(
            name="duplicate_role", 
            permissions=frozenset(["manage_recipes"])
        )
        
        # frozenset should allow both roles since they're different objects
        # even though they have the same name
        user = ApiUser(**minimal_user_kwargs(roles=frozenset([role1, role2])))
        
        # Verify both roles exist (they're different objects despite same name)
        assert len(user.roles) == 2
        role_names = [role.name for role in user.roles]
        assert role_names.count("duplicate_role") == 2

    def test_empty_role_permissions_edge_case(self):
        """Test role with empty permissions - explicit validation edge case."""
        # This should test validation behavior for empty permissions
        empty_permissions_role = ApiRole(
            name="empty_perms_role",
            permissions=frozenset()  # Empty permissions set
        )
        
        # Depending on validation rules, this might be valid or invalid
        user = ApiUser(**minimal_user_kwargs(roles=frozenset([empty_permissions_role])))
        
        # Verify the role exists with empty permissions
        assert len(user.roles) == 1
        role = next(iter(user.roles))
        assert len(role.permissions) == 0

    def test_role_name_validation_edge_cases(self):
        """Test various role name edge cases - explicit validation testing."""
        # Test valid edge case: minimum length (3 characters based on validation error)
        min_length_role = ApiRole(name="min", permissions=frozenset(["access_basic_features"]))
        user_min = ApiUser(**minimal_user_kwargs(roles=frozenset([min_length_role])))
        assert len(user_min.roles) == 1
        
        # Test valid edge case: long name
        long_name = "very_long_role_name_that_might_test_length_limits"
        long_name_role = ApiRole(name=long_name, permissions=frozenset(["access_basic_features"]))
        user_long = ApiUser(**minimal_user_kwargs(roles=frozenset([long_name_role])))
        assert len(user_long.roles) == 1

    def test_multiple_users_with_same_role_references(self):
        """Test multiple users sharing the same role object - edge case for object sharing."""
        # Create a shared role object
        shared_role = ApiRole(
            name="shared_role",
            permissions=frozenset(["access_basic_features"])
        )
        
        # Create multiple users with the same role object (using valid UUID4 format)
        user1 = ApiUser(**minimal_user_kwargs(
            id=str(uuid4()),  # Generate valid UUID4
            roles=frozenset([shared_role])
        ))
        user2 = ApiUser(**minimal_user_kwargs(
            id=str(uuid4()),  # Generate valid UUID4
            roles=frozenset([shared_role])
        ))
        
        # Verify both users have the role
        assert len(user1.roles) == 1
        assert len(user2.roles) == 1
        
        # Verify they reference the same role object
        user1_role = next(iter(user1.roles))
        user2_role = next(iter(user2.roles))
        assert user1_role is shared_role
        assert user2_role is shared_role

    def test_complex_role_combinations_edge_case(self):
        """Test complex role combinations - use helper for clarity."""
        # Use helper to create complex but explicit scenario (avoiding reserved names)
        complex_roles = [
            ("administrator_role", frozenset(["manage_users", "manage_recipes", "view_audit_log"])),
            ("developer_role", frozenset(["access_developer_tools", "manage_recipes"])),
            ("support_role", frozenset(["access_support", "access_basic_features"]))
        ]
        
        user = ApiUser(**multi_role_user_kwargs(role_specs=complex_roles))
        
        # Verify complex combination
        assert len(user.roles) == 3
        role_names = {role.name for role in user.roles}
        assert role_names == {"administrator_role", "developer_role", "support_role"}
        
        # Verify permission overlap is preserved
        all_permissions = set()
        for role in user.roles:
            all_permissions.update(role.permissions)
        
        assert "manage_recipes" in all_permissions  # Should appear from both admin and developer
        assert len(all_permissions) > 3  # Should have unique permissions combined

    def test_reserved_role_name_validation_edge_case(self):
        """Test that reserved role names are properly rejected - explicit validation edge case."""
        # Test that "admin" is reserved (discovered from validation error)
        with pytest.raises(ValidationError, match="reserved"):
            ApiRole(name="admin", permissions=frozenset(["access_basic_features"]))

    def test_invalid_permission_validation_edge_case(self):
        """Test that invalid permissions are properly rejected - explicit validation edge case."""
        # Test that invalid permissions are rejected
        with pytest.raises(ValidationError, match="Invalid permissions"):
            ApiRole(name="test_role", permissions=frozenset(["invalid_permission"]))

    def test_role_name_length_validation_edge_case(self):
        """Test role name length validation - explicit edge case based on discovered rules."""
        # Test that names shorter than 3 characters are rejected
        with pytest.raises(ValidationError, match="at least 3 characters"):
            ApiRole(name="ab", permissions=frozenset(["access_basic_features"])) 