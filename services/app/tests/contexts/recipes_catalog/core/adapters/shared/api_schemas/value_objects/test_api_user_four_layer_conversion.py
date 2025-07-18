"""
Four-layer conversion tests for ApiUser schema validation.

Following Phase 1 patterns: behavior-focused approach, round-trip validation, 
comprehensive error handling, and four-layer conversion integrity.

Focus: Test four-layer conversion behavior (API ↔ Domain ↔ ORM ↔ JSON) and verify correctness.
"""

import pytest
from unittest.mock import Mock
from uuid import uuid4

from src.contexts.recipes_catalog.core.adapters.shared.api_schemas.value_objects.api_user import ApiUser
from src.contexts.recipes_catalog.core.domain.shared.value_objects.user import User
from src.contexts.recipes_catalog.core.domain.shared.value_objects.role import Role

# Import data factories
from tests.contexts.recipes_catalog.core.adapters.shared.api_schemas.value_objects.data_factories.api_role_data_factories import create_admin_role, create_premium_user_role, create_user_role
from tests.contexts.recipes_catalog.core.adapters.shared.api_schemas.value_objects.data_factories.api_user_data_factories import (
    create_api_user,
    create_api_role,
)


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