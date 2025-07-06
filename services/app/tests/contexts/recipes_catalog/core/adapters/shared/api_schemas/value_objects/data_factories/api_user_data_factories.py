"""
Data factories for ApiUser testing following seedwork patterns.
Uses deterministic values (not random) for consistent test behavior.

This module provides:
- Deterministic data creation with static counters
- JSON serialization/deserialization testing with model_validate_json and model_dump_json
- Parametrized test scenarios for user validation
- Performance test scenarios with dataset expectations
- Specialized factory functions for different user types
- Comprehensive attribute validation using check_missing_attributes
- Realistic data sets for production-like testing

All data follows the exact structure of ApiUser API entities and their validation rules.
Includes extensive testing for Pydantic model validation, JSON handling, and edge cases.
"""

import json
from typing import Dict, Any, List, Optional, Set
from uuid import uuid4

from src.contexts.recipes_catalog.core.adapters.shared.api_schemas.value_objects.api_user import ApiUser
from src.contexts.recipes_catalog.core.domain.shared.value_objects.user import User
from src.contexts.recipes_catalog.core.domain.shared.value_objects.role import Role
from src.contexts.iam.core.adapters.ORM.sa_models.user_sa_model import UserSaModel

# Import check_missing_attributes for validation
from tests.utils import check_missing_attributes

# Import ApiRole and its data factory for role creation
from src.contexts.recipes_catalog.core.adapters.shared.api_schemas.value_objects.api_role import ApiRole
from tests.contexts.recipes_catalog.core.adapters.shared.api_schemas.value_objects.data_factories.api_role_data_factories import (
    create_api_role, create_admin_role, create_user_role, create_guest_role,
    create_editor_role, create_moderator_role, create_api_user_role,
    create_premium_user_role, create_minimal_role
)

# =============================================================================
# REALISTIC DATA SETS FOR PRODUCTION-LIKE TESTING
# =============================================================================

REALISTIC_USER_SCENARIOS = [
    {
        "description": "System Administrator",
        "roles": ["admin"],
        "expected_permissions": ["read", "write", "delete", "manage_users", "manage_roles", "system_config"]
    },
    {
        "description": "Content Editor", 
        "roles": ["editor"],
        "expected_permissions": ["read", "write", "edit_recipes", "publish_recipes", "moderate_content"]
    },
    {
        "description": "Premium User",
        "roles": ["premium_user"],
        "expected_permissions": ["read", "write", "create_recipes", "premium_features", "advanced_search"]
    },
    {
        "description": "Community Moderator",
        "roles": ["moderator"],
        "expected_permissions": ["read", "write", "moderate_content", "manage_comments", "community_management"]
    },
    {
        "description": "Standard User",
        "roles": ["user"],
        "expected_permissions": ["read", "write", "create_recipes", "edit_own_recipes", "rate_recipes"]
    },
    {
        "description": "Guest User",
        "roles": ["guest"],
        "expected_permissions": ["read", "view_public_recipes", "search_recipes"]
    },
    {
        "description": "Multi-Role Power User",
        "roles": ["editor", "moderator"],
        "expected_permissions": ["read", "write", "edit_recipes", "moderate_content"]
    }
]

# Common user role combinations for testing
COMMON_ROLE_COMBINATIONS = [
    [],  # No roles
    ["user"],  # Single role
    ["admin"],  # Admin role
    ["editor", "moderator"],  # Content management roles
    ["premium_user"],  # Premium features
    ["api_user"],  # API access roles
    ["guest"],  # Guest role
    ["user", "moderator"],  # User with moderation
]

# =============================================================================
# STATIC COUNTERS FOR DETERMINISTIC IDS
# =============================================================================

_USER_COUNTER = 1


def reset_api_user_counters() -> None:
    """Reset all counters for test isolation"""
    global _USER_COUNTER
    _USER_COUNTER = 1


# =============================================================================
# API USER DATA FACTORIES
# =============================================================================

def create_api_user_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create ApiUser kwargs with deterministic values and comprehensive validation.
    
    Uses check_missing_attributes to ensure completeness and generates
    realistic test data for comprehensive API testing.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with all required ApiUser creation parameters
    """
    global _USER_COUNTER
    
    # Get realistic user scenario for deterministic values
    role_names = COMMON_ROLE_COMBINATIONS[(_USER_COUNTER - 1) % len(COMMON_ROLE_COMBINATIONS)]
    
    # Create roles frozenset
    roles = []
    for role_name in role_names:
        if role_name == "admin":
            roles.append(create_admin_role())
        elif role_name == "user":
            roles.append(create_user_role())
        elif role_name == "guest":
            roles.append(create_guest_role())
        elif role_name == "editor":
            roles.append(create_editor_role())
        elif role_name == "moderator":
            roles.append(create_moderator_role())
        elif role_name == "api_user":
            roles.append(create_api_user_role())
        elif role_name == "premium_user":
            roles.append(create_premium_user_role())
        else:
            # Create a generic role for other names
            roles.append(create_api_role(name=role_name))
    
    final_kwargs = {
        "id": kwargs.get("id", str(uuid4())),
        "roles": kwargs.get("roles", frozenset(roles)),
    }
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    # Check for missing attributes using comprehensive validation
    missing = check_missing_attributes(ApiUser, final_kwargs)
    missing = set(missing) - {'convert', 'model_computed_fields', 'model_config', 'model_fields'}
    assert not missing, f"Missing attributes for ApiUser: {missing}"
    
    # Increment counter for next call
    _USER_COUNTER += 1
    
    return final_kwargs


def create_api_user(**kwargs) -> ApiUser:
    """
    Create an ApiUser instance with deterministic data and validation.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiUser instance with comprehensive validation
    """
    user_kwargs = create_api_user_kwargs(**kwargs)
    return ApiUser(**user_kwargs)


def create_api_user_from_json(json_data: Optional[str] = None, **kwargs) -> ApiUser:
    """
    Create an ApiUser instance from JSON using model_validate_json.
    
    This tests Pydantic's JSON validation and parsing capabilities.
    
    Args:
        json_data: JSON string to parse (if None, generates from kwargs)
        **kwargs: Override any default values
        
    Returns:
        ApiUser instance created from JSON
    """
    if json_data is None:
        user_kwargs = create_api_user_kwargs(**kwargs)
        # Convert roles frozenset to list of dicts for JSON serialization
        if isinstance(user_kwargs.get("roles"), (set, frozenset)):
            roles_list = []
            for role in user_kwargs["roles"]:
                role_dict = {
                    "name": role.name,
                    "permissions": list(role.permissions)
                }
                roles_list.append(role_dict)
            user_kwargs["roles"] = roles_list
        json_data = json.dumps(user_kwargs)
    
    return ApiUser.model_validate_json(json_data)


def create_api_user_json(**kwargs) -> str:
    """
    Create JSON representation of ApiUser using model_dump_json.
    
    This tests Pydantic's JSON serialization capabilities.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        JSON string representation of ApiUser
    """
    user = create_api_user(**kwargs)
    return user.model_dump_json()


# =============================================================================
# SPECIALIZED FACTORY FUNCTIONS
# =============================================================================

def create_admin_user(**kwargs) -> ApiUser:
    """
    Create an admin user with full administrative roles.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiUser with admin roles
    """
    final_kwargs = {
        "roles": kwargs.get("roles", frozenset([create_admin_role()])),
        **{k: v for k, v in kwargs.items() if k != "roles"}
    }
    return create_api_user(**final_kwargs)


def create_basic_user(**kwargs) -> ApiUser:
    """
    Create a basic user with standard user role.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiUser with basic user role
    """
    final_kwargs = {
        "roles": kwargs.get("roles", frozenset([create_user_role()])),
        **{k: v for k, v in kwargs.items() if k != "roles"}
    }
    return create_api_user(**final_kwargs)


def create_guest_user(**kwargs) -> ApiUser:
    """
    Create a guest user with minimal permissions.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiUser with guest role
    """
    final_kwargs = {
        "roles": kwargs.get("roles", frozenset([create_guest_role()])),
        **{k: v for k, v in kwargs.items() if k != "roles"}
    }
    return create_api_user(**final_kwargs)


def create_multi_role_user(**kwargs) -> ApiUser:
    """
    Create a user with multiple roles for testing role combinations.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiUser with multiple roles
    """
    final_kwargs = {
        "roles": kwargs.get("roles", frozenset([
            create_editor_role(),
            create_moderator_role(),
            create_premium_user_role()
        ])),
        **{k: v for k, v in kwargs.items() if k != "roles"}
    }
    return create_api_user(**final_kwargs)


def create_content_manager_user(**kwargs) -> ApiUser:
    """
    Create a user with content management roles.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiUser with content management roles
    """
    final_kwargs = {
        "roles": kwargs.get("roles", frozenset([
            create_editor_role(),
            create_moderator_role()
        ])),
        **{k: v for k, v in kwargs.items() if k != "roles"}
    }
    return create_api_user(**final_kwargs)


def create_api_integration_user(**kwargs) -> ApiUser:
    """
    Create a user with API access roles.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiUser with API access roles
    """
    final_kwargs = {
        "roles": kwargs.get("roles", frozenset([
            create_api_user_role(),
            create_api_role(name="analytics_user", permissions=frozenset(["read", "view_analytics", "generate_reports"]))
        ])),
        **{k: v for k, v in kwargs.items() if k != "roles"}
    }
    return create_api_user(**final_kwargs)


def create_premium_user(**kwargs) -> ApiUser:
    """
    Create a premium user with enhanced features.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiUser with premium features
    """
    final_kwargs = {
        "roles": kwargs.get("roles", frozenset([
            create_premium_user_role(),
            create_user_role()
        ])),
        **{k: v for k, v in kwargs.items() if k != "roles"}
    }
    return create_api_user(**final_kwargs)


def create_professional_user(**kwargs) -> ApiUser:
    """
    Create a professional user (chef, nutritionist) with specialized roles.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiUser with professional roles
    """
    final_kwargs = {
        "roles": kwargs.get("roles", frozenset([
            create_api_role(name="chef", permissions=frozenset(["read", "write", "create_recipes", "cooking_tips"])),
            create_api_role(name="nutritionist", permissions=frozenset(["read", "write", "analyze_nutrition", "dietary_advice"])),
            create_premium_user_role()
        ])),
        **{k: v for k, v in kwargs.items() if k != "roles"}
    }
    return create_api_user(**final_kwargs)


def create_user_without_roles(**kwargs) -> ApiUser:
    """
    Create a user with no roles.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiUser with empty roles set
    """
    final_kwargs = {
        "roles": kwargs.get("roles", frozenset()),
        **{k: v for k, v in kwargs.items() if k != "roles"}
    }
    return create_api_user(**final_kwargs)


def create_user_with_single_role(**kwargs) -> ApiUser:
    """
    Create a user with exactly one role.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiUser with single role
    """
    final_kwargs = {
        "roles": kwargs.get("roles", frozenset([create_user_role()])),
        **{k: v for k, v in kwargs.items() if k != "roles"}
    }
    return create_api_user(**final_kwargs)


def create_user_with_max_roles(**kwargs) -> ApiUser:
    """
    Create a user with maximum number of roles for testing limits.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiUser with many roles
    """
    # Create diverse roles with different permissions
    roles = frozenset([
        create_admin_role(),
        create_editor_role(),
        create_moderator_role(),
        create_premium_user_role(),
        create_api_user_role(),
        create_api_role(name="chef", permissions=frozenset(["read", "write", "cooking_tips"])),
        create_api_role(name="nutritionist", permissions=frozenset(["read", "analyze_nutrition"])),
        create_api_role(name="reviewer", permissions=frozenset(["read", "write", "review_recipes"])),
        create_api_role(name="tester", permissions=frozenset(["read", "test_recipes"])),
        create_api_role(name="social_manager", permissions=frozenset(["read", "community_management"]))
    ])
    
    final_kwargs = {
        "roles": kwargs.get("roles", roles),
        **{k: v for k, v in kwargs.items() if k != "roles"}
    }
    return create_api_user(**final_kwargs)


def create_user_with_duplicate_role_names(**kwargs) -> ApiUser:
    """
    Create a user with roles that have duplicate names (should be validated).
    This is for testing validation behavior.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiUser with duplicate role names (for validation testing)
    """
    # Create roles with same name but different permissions
    role1 = create_api_role(name="duplicate", permissions=frozenset(["read"]))
    role2 = create_api_role(name="duplicate", permissions=frozenset(["write"]))
    
    final_kwargs = {
        "roles": kwargs.get("roles", frozenset([role1, role2])),
        **{k: v for k, v in kwargs.items() if k != "roles"}
    }
    return create_api_user(**final_kwargs)


def create_user_with_empty_role_names(**kwargs) -> ApiUser:
    """
    Create a user with roles that have empty names (should fail validation).
    This is for testing validation behavior.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiUser with empty role names (for validation testing)
    """
    # Use None name to trigger proper validation error
    from src.contexts.recipes_catalog.core.adapters.shared.api_schemas.value_objects.api_role import ApiRole
    try:
        empty_role = ApiRole(name=None, permissions=frozenset(["read"]))  # type: ignore
    except:
        # If that fails, create with empty string
        empty_role = ApiRole(name="", permissions=frozenset(["read"]))
    
    final_kwargs = {
        "roles": kwargs.get("roles", frozenset([empty_role])),
        **{k: v for k, v in kwargs.items() if k != "roles"}
    }
    return create_api_user(**final_kwargs)


def create_user_with_roles_without_permissions(**kwargs) -> ApiUser:
    """
    Create a user with roles that have no permissions (should fail validation).
    This is for testing validation behavior.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiUser with roles without permissions (for validation testing)
    """
    empty_permissions_role = create_api_role(name="no_perms", permissions=frozenset())
    
    final_kwargs = {
        "roles": kwargs.get("roles", frozenset([empty_permissions_role])),
        **{k: v for k, v in kwargs.items() if k != "roles"}
    }
    return create_api_user(**final_kwargs)


def create_user_with_roles_with_many_permissions(**kwargs) -> ApiUser:
    """
    Create a user with roles that have too many permissions (should fail validation).
    This is for testing validation behavior.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiUser with roles with too many permissions (for validation testing)
    """
    # Create a role with 51 permissions (over the limit of 50)
    too_many_permissions = frozenset([f"permission_{i}" for i in range(51)])
    overloaded_role = create_api_role(name="overloaded", permissions=too_many_permissions)
    
    final_kwargs = {
        "roles": kwargs.get("roles", frozenset([overloaded_role])),
        **{k: v for k, v in kwargs.items() if k != "roles"}
    }
    return create_api_user(**final_kwargs)


# =============================================================================
# HELPER FUNCTIONS FOR TEST SETUP
# =============================================================================

def create_user_hierarchy() -> List[ApiUser]:
    """Create a hierarchy of users with different permission levels"""
    return [
        create_admin_user(),
        create_content_manager_user(),
        create_premium_user(),
        create_professional_user(),
        create_basic_user(),
        create_guest_user(),
        create_user_without_roles()
    ]


def create_users_with_different_role_combinations() -> List[ApiUser]:
    """Create users with various role combinations for testing"""
    users = []
    
    for i, role_combo in enumerate(COMMON_ROLE_COMBINATIONS):
        roles = set()  # Build as set first
        for role_name in role_combo:
            if role_name == "admin":
                roles.add(create_admin_role())  # type: ignore
            elif role_name == "user":
                roles.add(create_user_role())  # type: ignore
            elif role_name == "guest":
                roles.add(create_guest_role())  # type: ignore
            elif role_name == "editor":
                roles.add(create_editor_role())  # type: ignore
            elif role_name == "moderator":
                roles.add(create_moderator_role())  # type: ignore
            else:
                roles.add(create_api_role(name=role_name))  # type: ignore
        
        user = create_api_user(roles=frozenset(roles))
        users.append(user)
    
    return users


def create_users_with_different_ids() -> List[ApiUser]:
    """Create users with different UUID formats for testing"""
    users = []
    
    for i in range(10):
        user = create_api_user(id=str(uuid4()))
        users.append(user)
    
    return users


def create_test_user_dataset(user_count: int = 100) -> Dict[str, Any]:
    """Create a dataset of users for performance testing"""
    users = []
    json_strings = []
    
    for i in range(user_count):
        # Create API user
        user_kwargs = create_api_user_kwargs()
        user = create_api_user(**user_kwargs)
        users.append(user)
        
        # Create JSON representation
        json_string = user.model_dump_json()
        json_strings.append(json_string)
    
    return {
        "users": users,
        "json_strings": json_strings,
        "total_users": len(users)
    }


# =============================================================================
# DOMAIN AND ORM CONVERSION HELPERS
# =============================================================================

def create_user_domain_from_api(api_user: ApiUser) -> User:
    """Convert ApiUser to domain User using to_domain method"""
    return api_user.to_domain()


def create_api_user_from_domain(domain_user: User) -> ApiUser:
    """Convert domain User to ApiUser using from_domain method"""
    return ApiUser.from_domain(domain_user)


def create_user_orm_kwargs_from_api(api_user: ApiUser) -> Dict[str, Any]:
    """Convert ApiUser to ORM kwargs using to_orm_kwargs method"""
    return api_user.to_orm_kwargs()


def create_api_user_from_orm(orm_user: UserSaModel) -> ApiUser:
    """Convert ORM User to ApiUser using from_orm_model method"""
    return ApiUser.from_orm_model(orm_user)


def create_orm_user_model_for_testing() -> UserSaModel:
    """Create a mock ORM User model for testing conversions"""
    return UserSaModel(
        id=str(uuid4()),
        roles=[
            {"name": "user", "permissions": "read, write, create_recipes"},
            {"name": "premium", "permissions": "premium_features, advanced_search"}
        ]
    )


# =============================================================================
# JSON VALIDATION AND EDGE CASE TESTING
# =============================================================================

def create_valid_json_test_cases() -> List[Dict[str, Any]]:
    """Create various valid JSON test cases for model_validate_json testing"""
    return [
        # Standard user with single role
        {
            "id": str(uuid4()),
            "roles": [
                {"name": "user", "permissions": ["read", "write", "create_recipes"]}
            ]
        },
        # Admin user with multiple permissions
        {
            "id": str(uuid4()),
            "roles": [
                {"name": "admin", "permissions": ["read", "write", "delete", "manage_users"]}
            ]
        },
        # Multi-role user
        {
            "id": str(uuid4()),
            "roles": [
                {"name": "editor", "permissions": ["read", "write", "edit_recipes"]},
                {"name": "moderator", "permissions": ["moderate_content", "approve_recipes"]}
            ]
        },
        # User with no roles
        {
            "id": str(uuid4()),
            "roles": []
        },
        # User with minimal role
        {
            "id": str(uuid4()),
            "roles": [
                {"name": "guest", "permissions": ["read"]}
            ]
        },
        # User with many roles
        {
            "id": str(uuid4()),
            "roles": [
                {"name": "admin", "permissions": ["read", "write", "manage_users"]},
                {"name": "editor", "permissions": ["edit_recipes", "publish_recipes"]},
                {"name": "moderator", "permissions": ["moderate_content"]},
                {"name": "premium", "permissions": ["premium_features"]},
                {"name": "api_user", "permissions": ["api_access"]}
            ]
        },
        # User with role having many permissions (but under limit)
        {
            "id": str(uuid4()),
            "roles": [
                {"name": "superuser", "permissions": [f"permission_{i}" for i in range(45)]}
            ]
        }
    ]


def create_invalid_json_test_cases() -> List[Dict[str, Any]]:
    """Create various invalid JSON test cases for validation error testing"""
    return [
        # Invalid ID (not UUID format)
        {
            "data": {
                "id": "not-a-uuid",
                "roles": [{"name": "user", "permissions": ["read"]}]
            },
            "expected_errors": ["id"]
        },
        # Duplicate role names
        {
            "data": {
                "id": str(uuid4()),
                "roles": [
                    {"name": "user", "permissions": ["read"]},
                    {"name": "user", "permissions": ["write"]}  # Duplicate name
                ]
            },
            "expected_errors": ["roles"]
        },
        # Role with empty name
        {
            "data": {
                "id": str(uuid4()),
                "roles": [
                    {"name": "", "permissions": ["read"]}  # Empty name
                ]
            },
            "expected_errors": ["roles"]
        },
        # Role with whitespace-only name
        {
            "data": {
                "id": str(uuid4()),
                "roles": [
                    {"name": "   ", "permissions": ["read"]}  # Whitespace only
                ]
            },
            "expected_errors": ["roles"]
        },
        # Role with no permissions
        {
            "data": {
                "id": str(uuid4()),
                "roles": [
                    {"name": "empty_role", "permissions": []}  # No permissions
                ]
            },
            "expected_errors": ["roles"]
        },
        # Role with too many permissions
        {
            "data": {
                "id": str(uuid4()),
                "roles": [
                    {"name": "overloaded", "permissions": [f"perm_{i}" for i in range(51)]}  # 51 permissions
                ]
            },
            "expected_errors": ["roles"]
        },
        # Missing required fields
        {
            "data": {
                "roles": [{"name": "user", "permissions": ["read"]}]
                # Missing id
            },
            "expected_errors": ["id"]
        },
        # Invalid role structure (missing permissions)
        {
            "data": {
                "id": str(uuid4()),
                "roles": [
                    {"name": "incomplete_role"}  # Missing permissions
                ]
            },
            "expected_errors": ["roles"]
        },
        # Invalid role structure (missing name)
        {
            "data": {
                "id": str(uuid4()),
                "roles": [
                    {"permissions": ["read"]}  # Missing name
                ]
            },
            "expected_errors": ["roles"]
        },
        # Invalid roles type (not a list)
        {
            "data": {
                "id": str(uuid4()),
                "roles": "not_a_list"  # Should be a list
            },
            "expected_errors": ["roles"]
        },
        # Invalid permissions type (not a list)
        {
            "data": {
                "id": str(uuid4()),
                "roles": [
                    {"name": "user", "permissions": "not_a_list"}  # Should be a list
                ]
            },
            "expected_errors": ["roles"]
        }
    ]


def check_json_serialization_roundtrip(api_user: ApiUser) -> bool:
    """Test that JSON serialization and deserialization preserves data integrity"""
    # Serialize to JSON
    json_str = api_user.model_dump_json()
    
    # Deserialize from JSON
    restored_user = ApiUser.model_validate_json(json_str)
    
    # Compare original and restored
    return api_user == restored_user


def create_edge_case_users() -> List[ApiUser]:
    """Create users with edge case scenarios"""
    return [
        create_user_without_roles(),
        create_user_with_single_role(),
        create_user_with_max_roles(),
        create_admin_user(),
        create_guest_user()
    ]


# =============================================================================
# PERFORMANCE TESTING HELPERS
# =============================================================================

def create_bulk_user_creation_dataset(count: int = 1000) -> List[Dict[str, Any]]:
    """Create a dataset for bulk user creation performance testing"""
    return [create_api_user_kwargs() for _ in range(count)]


def create_bulk_json_serialization_dataset(count: int = 1000) -> List[str]:
    """Create a dataset for bulk JSON serialization performance testing"""
    users = [create_api_user() for _ in range(count)]
    return [user.model_dump_json() for user in users]


def create_bulk_json_deserialization_dataset(count: int = 1000) -> List[str]:
    """Create a dataset for bulk JSON deserialization performance testing"""
    json_strings = []
    for _ in range(count):
        user_kwargs = create_api_user_kwargs()
        # Convert roles frozenset to list of dicts for JSON serialization
        if isinstance(user_kwargs.get("roles"), (set, frozenset)):
            roles_list = []
            for role in user_kwargs["roles"]:
                role_dict = {
                    "name": role.name,
                    "permissions": list(role.permissions)
                }
                roles_list.append(role_dict)
            user_kwargs["roles"] = roles_list
        json_strings.append(json.dumps(user_kwargs))
    return json_strings


def create_conversion_performance_dataset(count: int = 1000) -> Dict[str, Any]:
    """Create a dataset for conversion performance testing"""
    api_users = [create_api_user() for _ in range(count)]
    domain_users = [User(id=str(uuid4()), roles=set()) for _ in range(count)]
    orm_users = [create_orm_user_model_for_testing() for _ in range(count)]
    
    return {
        "api_users": api_users,
        "domain_users": domain_users,
        "orm_users": orm_users,
        "total_count": count
    }


def create_role_validation_performance_dataset(count: int = 1000) -> List[ApiUser]:
    """Create a dataset for role validation performance testing"""
    users = []
    
    for i in range(count):
        # Create users with varying numbers of roles
        role_count = (i % 10) + 1  # 1 to 10 roles
        roles = set()  # Build as set first
        
        for j in range(role_count):
            role_name = f"role_{j}"
            permissions = frozenset([f"permission_{j}_{k}" for k in range((j % 5) + 1)])
            role = create_api_role(name=role_name, permissions=permissions)
            roles.add(role)  # type: ignore
        
        user = create_api_user(roles=frozenset(roles))
        users.append(user)
    
    return users 