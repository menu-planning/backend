"""
Integration behavior tests for ApiUser schema validation.

Following Phase 1 patterns: behavior-focused approach, comprehensive integration testing,
and cross-context compatibility validation.

Focus: Test integration behavior and cross-context compatibility.
"""

import json
from uuid import uuid4

import pytest
from src.contexts.recipes_catalog.core.adapters.shared.api_schemas.value_objects.api_user import (
    ApiUser,
)
from src.contexts.recipes_catalog.core.domain.shared.value_objects.user import User

# Import data factories
from tests.contexts.recipes_catalog.core.adapters.shared.api_schemas.value_objects.data_factories.api_role_data_factories import (
    create_admin_role,
    create_premium_user_role,
    create_user_role,
)
from tests.contexts.recipes_catalog.core.adapters.shared.api_schemas.value_objects.data_factories.api_user_data_factories import (
    check_json_serialization_roundtrip,
    create_admin_user,
    create_api_integration_user,
    create_api_role,
    create_api_user,
    create_basic_user,
    create_content_manager_user,
    create_guest_user,
    create_multi_role_user,
    create_premium_user,
    create_professional_user,
    create_user_hierarchy,
    create_user_with_max_roles,
    create_user_with_single_role,
    create_user_without_roles,
)

# =============================================================================
# INTEGRATION BEHAVIOR TESTS
# =============================================================================


class TestApiUserIntegrationBehavior:
    """Test comprehensive integration behavior for ApiUser schema."""

    def test_immutability_behavior(self):
        """Test that ApiUser instances are immutable."""
        user_role = create_user_role()
        user = create_api_user(id=str(uuid4()), roles=frozenset([user_role]))

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
            id=str(uuid4()), roles=frozenset([admin_role, user_role])
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
        chef_role = create_api_role(
            name="chef_role",
            permissions=frozenset(["manage_recipes", "access_basic_features"]),
        )

        original_user = create_api_user(
            id=str(uuid4()), roles=frozenset([premium_role, chef_role])
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
        user_1 = create_api_user(id=str(uuid4()), roles=frozenset([user_role]))

        user_2 = create_api_user(id=user_1.id, roles=user_1.roles)

        admin_role = create_admin_role()
        user_3 = create_api_user(id=str(uuid4()), roles=frozenset([admin_role]))

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

    @pytest.mark.parametrize(
        "user",
        [
            create_admin_user(),
            create_basic_user(),
            create_premium_user(),
            create_professional_user(),
        ],
    )
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

    @pytest.mark.parametrize(
        "factory_func",
        [
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
        ],
    )
    def test_data_factory_integration_consistency(self, factory_func):
        """Test consistency when using various data factory functions."""
        user = factory_func()

        # Verify all factory functions produce valid users
        assert isinstance(user, ApiUser)
        assert user.id is not None
        assert isinstance(user.roles, frozenset)

        # Test JSON serialization roundtrip
        assert check_json_serialization_roundtrip(user)
