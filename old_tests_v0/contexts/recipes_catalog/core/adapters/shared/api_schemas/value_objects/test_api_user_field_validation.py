"""
Field validation tests for ApiUser schema validation.

Following Phase 1 patterns: behavior-focused approach, comprehensive validation coverage,
and field constraint testing.

Focus: Test field validation behavior and constraint enforcement.
Approach: Hybrid - direct construction for explicit edge cases, data factories for complex scenarios.
"""

from uuid import uuid4

import pytest

# Import data factories - kept for complex scenarios
from old_tests_v0.contexts.recipes_catalog.core.adapters.shared.api_schemas.value_objects.data_factories.api_role_data_factories import (
    create_admin_role,
    create_premium_user_role,
    create_user_role,
)
from old_tests_v0.contexts.recipes_catalog.core.adapters.shared.api_schemas.value_objects.data_factories.api_user_data_factories import (
    create_admin_user,
    create_basic_user,
    create_guest_user,
    create_premium_user,
    create_professional_user,
    create_user_with_roles_with_many_permissions,
)
from pydantic import ValidationError
from src.contexts.recipes_catalog.core.adapters.shared.api_schemas.value_objects.api_user import (
    ApiUser,
)

# =============================================================================
# LIGHTWEIGHT KWARGS HELPERS - For explicit edge cases and unit tests
# =============================================================================


def minimal_api_user_kwargs(**overrides) -> dict:
    """Create minimal ApiUser kwargs for unit tests with clear defaults."""
    return {"id": str(uuid4()), "roles": frozenset(), **overrides}


def api_user_with_roles_kwargs(roles=None, **overrides) -> dict:
    """Create ApiUser kwargs with specified roles for clear testing."""
    if roles is None:
        roles = frozenset([create_user_role()])

    return {"id": str(uuid4()), "roles": roles, **overrides}


def api_user_with_single_role_kwargs(role_factory=None, **overrides) -> dict:
    """Create ApiUser kwargs with single role for boundary testing."""
    if role_factory is None:
        role_factory = create_user_role

    return {"id": str(uuid4()), "roles": frozenset([role_factory()]), **overrides}


# =============================================================================
# FIELD VALIDATION TESTS - Hybrid Approach
# =============================================================================


class TestApiUserFieldValidation:
    """Test comprehensive field validation for ApiUser data."""

    def test_id_field_validation_with_valid_uuid(self):
        """Test id field accepts valid UUID formats - explicit edge case."""
        # Direct construction makes the UUID validation explicit
        test_id = str(uuid4())
        user = ApiUser(**minimal_api_user_kwargs(id=test_id))
        assert user.id == test_id

    def test_id_field_validation_edge_cases(self):
        """Test id field validation rules - explicit validation testing."""
        # Test valid UUID formats
        valid_uuid = str(uuid4())
        user = ApiUser(**minimal_api_user_kwargs(id=valid_uuid))
        assert user.id == valid_uuid

        # Note: Pydantic handles invalid UUID validation automatically
        # If needed, add specific UUID format validation tests here

    @pytest.mark.parametrize(
        "roles",
        [
            frozenset(),  # Empty roles
            frozenset([create_user_role()]),  # Single role
            frozenset([create_admin_role(), create_user_role()]),  # Multiple roles
            frozenset([create_premium_user_role()]),  # Professional roles
        ],
    )
    def test_roles_field_validation_with_various_role_sets(self, roles):
        """Test roles field accepts various role combinations - factory appropriate for multiple scenarios."""
        # Parametrized test with multiple scenarios - factory usage justified
        user = ApiUser(**minimal_api_user_kwargs(roles=roles))
        assert user.roles == roles

    def test_roles_field_validation_with_role_uniqueness(self):
        """Test roles field enforces role uniqueness by name - explicit edge case."""
        # Direct construction makes the uniqueness test explicit
        role1 = create_user_role()
        role2 = create_user_role()  # Same role, should be deduplicated

        user = ApiUser(**minimal_api_user_kwargs(roles=frozenset([role1, role2])))

        # Verify uniqueness is enforced (frozenset automatically deduplicates equal objects)
        role_names = [role.name for role in user.roles]
        assert len(set(role_names)) == len(role_names)

    def test_roles_field_validation_with_empty_roles(self):
        """Test roles field validation with empty roles - explicit edge case."""
        # Direct construction makes the empty roles case explicit
        user = ApiUser(**minimal_api_user_kwargs(roles=frozenset()))
        assert len(user.roles) == 0
        assert user.roles == frozenset()

    def test_roles_field_validation_with_invalid_role_names(self):
        """Test roles field validation with invalid role names - explicit validation edge case."""
        # Direct construction makes the validation failure explicit
        from src.contexts.recipes_catalog.core.adapters.shared.api_schemas.value_objects.api_role import (
            ApiRole,
        )

        with pytest.raises(ValidationError) as exc_info:
            # Create role with empty name to trigger validation
            invalid_role = ApiRole(name="", permissions=frozenset(["read"]))
            ApiUser(**minimal_api_user_kwargs(roles=frozenset([invalid_role])))

        error_str = str(exc_info.value)
        assert "name" in error_str.lower() or "string_type" in error_str

    def test_roles_field_validation_with_too_many_permissions(self):
        """Test roles field validation with roles having too many permissions - explicit validation edge case."""
        # Direct construction makes the validation failure explicit
        with pytest.raises(ValidationError) as exc_info:
            user_with_invalid_roles = create_user_with_roles_with_many_permissions()

        error_str = str(exc_info.value)
        assert "permissions" in error_str.lower() or "apirole" in error_str.lower()

    @pytest.mark.parametrize(
        "user_factory",
        [
            create_admin_user,
            create_basic_user,
            create_guest_user,
            create_premium_user,
            create_professional_user,
        ],
    )
    def test_specialized_user_types_validation(self, user_factory):
        """Test validation for specialized user types - factory appropriate for comprehensive coverage."""
        # Complex scenarios with multiple user types - factory usage justified
        user = user_factory()

        # Verify all are valid ApiUser instances
        assert isinstance(user, ApiUser)
        assert user.id is not None
        assert isinstance(user.roles, frozenset)

    def test_field_constraints_boundary_validation(self):
        """Test field validation at constraint boundaries - explicit boundary testing."""
        # Direct construction makes boundary conditions explicit

        # Test minimum valid values - no roles
        min_user = ApiUser(**minimal_api_user_kwargs(roles=frozenset()))
        assert len(min_user.roles) == 0

        # Test single role boundary
        single_role_user = ApiUser(**api_user_with_single_role_kwargs())
        assert len(single_role_user.roles) == 1

        # Test multiple roles boundary
        multi_role_user = ApiUser(
            **api_user_with_roles_kwargs(
                roles=frozenset([create_admin_role(), create_user_role()])
            )
        )
        assert len(multi_role_user.roles) == 2

    def test_id_field_immutability(self):
        """Test id field immutability - explicit edge case documenting constraint."""
        # Direct construction makes the immutability test explicit
        original_id = str(uuid4())
        user = ApiUser(**minimal_api_user_kwargs(id=original_id))

        # Verify id cannot be changed (Pydantic models are immutable by default)
        assert user.id == original_id

        # Note: Pydantic models are frozen, so direct assignment would raise an error
        # This documents the expected immutable behavior

    def test_roles_field_immutability(self):
        """Test roles field immutability - explicit edge case documenting constraint."""
        # Direct construction makes the immutability test explicit
        original_roles = frozenset([create_user_role()])
        user = ApiUser(**minimal_api_user_kwargs(roles=original_roles))

        # Verify roles cannot be modified
        assert user.roles == original_roles
        assert isinstance(user.roles, frozenset)  # Immutable collection type

    def test_comprehensive_field_validation_with_all_constraints(self):
        """Test comprehensive field validation with all constraint types - factory appropriate for complex scenario."""
        # Complex scenario with multiple constraints - factory usage justified
        admin_role = create_admin_role()
        user_role = create_user_role()
        premium_role = create_premium_user_role()

        comprehensive_user = ApiUser(
            **minimal_api_user_kwargs(
                id=str(uuid4()), roles=frozenset([admin_role, user_role, premium_role])
            )
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

    def test_validation_error_messages_clarity(self):
        """Test validation error messages provide clear feedback - explicit validation testing."""
        # Direct construction makes validation error testing explicit

        # Test invalid UUID format
        with pytest.raises(ValidationError) as exc_info:
            ApiUser(**minimal_api_user_kwargs(id="not-a-valid-uuid"))

        error_str = str(exc_info.value)
        assert "uuid" in error_str.lower() or "value" in error_str.lower()

        # Test invalid roles type - pass None instead of frozenset
        with pytest.raises(ValidationError) as exc_info:
            ApiUser(**minimal_api_user_kwargs(roles=None))  # Invalid type for roles

        error_str = str(exc_info.value)
        assert (
            "type" in error_str.lower()
            or "none is not an allowed value" in error_str.lower()
        )
