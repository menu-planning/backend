"""
Data factories for ApiRole testing following seedwork patterns.
Uses deterministic values (not random) for consistent test behavior.

This module provides:
- Deterministic data creation with static counters
- JSON serialization/deserialization testing with model_validate_json and model_dump_json
- Parametrized test scenarios for role validation
- Performance test scenarios with dataset expectations
- Specialized factory functions for different role types
- Comprehensive attribute validation using check_missing_attributes
- Realistic data sets for production-like testing

All data follows the exact structure of ApiRole API entities and their validation rules.
Includes extensive testing for Pydantic model validation, JSON handling, and edge cases.
"""

import json
from typing import Dict, Any, List, Optional, cast
from uuid import uuid4

from src.contexts.recipes_catalog.core.adapters.shared.api_schemas.value_objects.api_role import ApiRole
from src.contexts.recipes_catalog.core.domain.shared.value_objects.role import Role
from src.contexts.iam.core.adapters.ORM.sa_models.role_sa_model import RoleSaModel

# Import check_missing_attributes for validation
from tests.utils import check_missing_attributes

# =============================================================================
# REALISTIC DATA SETS FOR PRODUCTION-LIKE TESTING
# =============================================================================

REALISTIC_ROLES = [
    {
        "name": "admin",
        "permissions": frozenset(["read", "write", "delete", "manage_users", "manage_roles", "system_config"])
    },
    {
        "name": "editor",
        "permissions": frozenset(["read", "write", "edit_recipes", "publish_recipes", "moderate_content"])
    },
    {
        "name": "contributor",
        "permissions": frozenset(["read", "write", "create_recipes", "edit_own_recipes", "submit_for_review"])
    },
    {
        "name": "moderator",
        "permissions": frozenset(["read", "write", "moderate_content", "approve_recipes", "manage_comments"])
    },
    {
        "name": "user",
        "permissions": frozenset(["read", "write", "create_recipes", "edit_own_recipes", "rate_recipes"])
    },
    {
        "name": "guest",
        "permissions": frozenset(["read", "view_public_recipes", "search_recipes"])
    },
    {
        "name": "chef",
        "permissions": frozenset(["read", "write", "create_recipes", "edit_own_recipes", "share_recipes", "cooking_tips"])
    },
    {
        "name": "nutritionist",
        "permissions": frozenset(["read", "write", "analyze_nutrition", "create_healthy_recipes", "dietary_advice"])
    },
    {
        "name": "reviewer",
        "permissions": frozenset(["read", "write", "review_recipes", "approve_content", "quality_check"])
    },
    {
        "name": "premium_user",
        "permissions": frozenset(["read", "write", "create_recipes", "premium_features", "advanced_search", "recipe_collections"])
    },
    {
        "name": "api_user",
        "permissions": frozenset(["read", "api_access", "bulk_operations", "data_export"])
    },
    {
        "name": "analytics_user",
        "permissions": frozenset(["read", "view_analytics", "generate_reports", "data_insights"])
    },
    {
        "name": "content_manager",
        "permissions": frozenset(["read", "write", "manage_content", "curate_recipes", "featured_content"])
    },
    {
        "name": "social_moderator",
        "permissions": frozenset(["read", "write", "moderate_comments", "manage_social_features", "community_management"])
    },
    {
        "name": "recipe_tester",
        "permissions": frozenset(["read", "write", "test_recipes", "provide_feedback", "quality_assurance"])
    }
]

COMMON_PERMISSIONS = [
    "read",
    "write",
    "delete",
    "create_recipes",
    "edit_recipes",
    "edit_own_recipes",
    "publish_recipes",
    "approve_recipes",
    "moderate_content",
    "manage_users",
    "manage_roles",
    "system_config",
    "view_analytics",
    "api_access",
    "bulk_operations",
    "data_export",
    "premium_features",
    "advanced_search",
    "recipe_collections",
    "rate_recipes",
    "comment_recipes",
    "share_recipes",
    "cooking_tips",
    "dietary_advice",
    "quality_check",
    "community_management",
    "view_public_recipes",
    "search_recipes",
    "submit_for_review",
    "featured_content",
    "curate_recipes",
    "manage_content",
    "moderate_comments",
    "manage_social_features",
    "test_recipes",
    "provide_feedback",
    "quality_assurance",
    "analyze_nutrition",
    "create_healthy_recipes",
    "generate_reports",
    "data_insights"
]

# =============================================================================
# STATIC COUNTERS FOR DETERMINISTIC IDS
# =============================================================================

_ROLE_COUNTER = 1


def reset_api_role_counters() -> None:
    """Reset all counters for test isolation"""
    global _ROLE_COUNTER
    _ROLE_COUNTER = 1


# =============================================================================
# API ROLE DATA FACTORIES
# =============================================================================

def create_api_role_kwargs(**kwargs) -> Dict[str, Any]:
    """
    Create ApiRole kwargs with deterministic values and comprehensive validation.
    
    Uses check_missing_attributes to ensure completeness and generates
    realistic test data for comprehensive API testing.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        Dict with all required ApiRole creation parameters
    """
    global _ROLE_COUNTER
    
    # Get realistic role data for deterministic values
    role_data = REALISTIC_ROLES[(_ROLE_COUNTER - 1) % len(REALISTIC_ROLES)]
    
    final_kwargs = {
        "name": kwargs.get("name", role_data["name"]),
        "permissions": kwargs.get("permissions", role_data["permissions"]),
    }
    
    # Allow override of any attribute
    final_kwargs.update(kwargs)
    
    # Check for missing attributes using comprehensive validation
    missing = check_missing_attributes(ApiRole, final_kwargs)
    missing = set(missing) - {'convert', 'model_computed_fields', 'model_config', 'model_fields'}
    assert not missing, f"Missing attributes for ApiRole: {missing}"
    
    # Increment counter for next call
    _ROLE_COUNTER += 1
    
    return final_kwargs


def create_api_role(**kwargs) -> ApiRole:
    """
    Create an ApiRole instance with deterministic data and validation.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiRole instance with comprehensive validation
    """
    role_kwargs = create_api_role_kwargs(**kwargs)
    return ApiRole(**role_kwargs)


def create_api_role_from_json(json_data: Optional[str] = None, **kwargs) -> ApiRole:
    """
    Create an ApiRole instance from JSON using model_validate_json.
    
    This tests Pydantic's JSON validation and parsing capabilities.
    
    Args:
        json_data: JSON string to parse (if None, generates from kwargs)
        **kwargs: Override any default values
        
    Returns:
        ApiRole instance created from JSON
    """
    if json_data is None:
        role_kwargs = create_api_role_kwargs(**kwargs)
        # Convert frozenset to list for JSON serialization
        if isinstance(role_kwargs.get("permissions"), frozenset):
            role_kwargs["permissions"] = list(role_kwargs["permissions"])
        json_data = json.dumps(role_kwargs)
    
    return ApiRole.model_validate_json(json_data)


def create_api_role_json(**kwargs) -> str:
    """
    Create JSON representation of ApiRole using model_dump_json.
    
    This tests Pydantic's JSON serialization capabilities.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        JSON string representation of ApiRole
    """
    role = create_api_role(**kwargs)
    return role.model_dump_json()


# =============================================================================
# SPECIALIZED FACTORY FUNCTIONS
# =============================================================================

def create_admin_role(**kwargs) -> ApiRole:
    """
    Create an admin role with full permissions.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiRole representing an admin
    """
    final_kwargs = {
        "name": kwargs.get("name", "admin"),
        "permissions": kwargs.get("permissions", frozenset([
            "read", "write", "delete", "manage_users", "manage_roles", 
            "system_config", "view_analytics", "api_access", "bulk_operations"
        ])),
        **{k: v for k, v in kwargs.items() if k not in ["name", "permissions"]}
    }
    return create_api_role(**final_kwargs)


def create_user_role(**kwargs) -> ApiRole:
    """
    Create a basic user role with standard permissions.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiRole representing a standard user
    """
    final_kwargs = {
        "name": kwargs.get("name", "user"),
        "permissions": kwargs.get("permissions", frozenset([
            "read", "write", "create_recipes", "edit_own_recipes", "rate_recipes"
        ])),
        **{k: v for k, v in kwargs.items() if k not in ["name", "permissions"]}
    }
    return create_api_role(**final_kwargs)


def create_guest_role(**kwargs) -> ApiRole:
    """
    Create a guest role with minimal permissions.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiRole representing a guest user
    """
    final_kwargs = {
        "name": kwargs.get("name", "guest"),
        "permissions": kwargs.get("permissions", frozenset([
            "read", "view_public_recipes", "search_recipes"
        ])),
        **{k: v for k, v in kwargs.items() if k not in ["name", "permissions"]}
    }
    return create_api_role(**final_kwargs)


def create_editor_role(**kwargs) -> ApiRole:
    """
    Create an editor role with content management permissions.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiRole representing an editor
    """
    final_kwargs = {
        "name": kwargs.get("name", "editor"),
        "permissions": kwargs.get("permissions", frozenset([
            "read", "write", "edit_recipes", "publish_recipes", "moderate_content", "approve_recipes"
        ])),
        **{k: v for k, v in kwargs.items() if k not in ["name", "permissions"]}
    }
    return create_api_role(**final_kwargs)


def create_moderator_role(**kwargs) -> ApiRole:
    """
    Create a moderator role with content moderation permissions.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiRole representing a moderator
    """
    final_kwargs = {
        "name": kwargs.get("name", "moderator"),
        "permissions": kwargs.get("permissions", frozenset([
            "read", "write", "moderate_content", "approve_recipes", "manage_comments", "moderate_comments"
        ])),
        **{k: v for k, v in kwargs.items() if k not in ["name", "permissions"]}
    }
    return create_api_role(**final_kwargs)


def create_api_user_role(**kwargs) -> ApiRole:
    """
    Create an API user role with API access permissions.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiRole representing an API user
    """
    final_kwargs = {
        "name": kwargs.get("name", "api_user"),
        "permissions": kwargs.get("permissions", frozenset([
            "read", "api_access", "bulk_operations", "data_export"
        ])),
        **{k: v for k, v in kwargs.items() if k not in ["name", "permissions"]}
    }
    return create_api_role(**final_kwargs)


def create_premium_user_role(**kwargs) -> ApiRole:
    """
    Create a premium user role with advanced features.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiRole representing a premium user
    """
    final_kwargs = {
        "name": kwargs.get("name", "premium_user"),
        "permissions": kwargs.get("permissions", frozenset([
            "read", "write", "create_recipes", "premium_features", "advanced_search", "recipe_collections"
        ])),
        **{k: v for k, v in kwargs.items() if k not in ["name", "permissions"]}
    }
    return create_api_role(**final_kwargs)


def create_minimal_role(**kwargs) -> ApiRole:
    """
    Create a role with minimal permissions (read only).
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiRole with minimal permissions
    """
    final_kwargs = {
        "name": kwargs.get("name", "minimal"),
        "permissions": kwargs.get("permissions", frozenset(["read"])),
        **{k: v for k, v in kwargs.items() if k not in ["name", "permissions"]}
    }
    return create_api_role(**final_kwargs)


def create_empty_permissions_role(**kwargs) -> ApiRole:
    """
    Create a role with no permissions.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiRole with empty permissions
    """
    final_kwargs = {
        "name": kwargs.get("name", "empty"),
        "permissions": kwargs.get("permissions", frozenset()),
        **{k: v for k, v in kwargs.items() if k not in ["name", "permissions"]}
    }
    return create_api_role(**final_kwargs)


def create_role_with_max_name(**kwargs) -> ApiRole:
    """
    Create a role with maximum allowed name length.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiRole with maximum length name
    """
    # Create a valid role name that's as long as possible while following validation rules
    max_name = "a" * 50  # Adjust based on actual validation limits
    
    final_kwargs = {
        "name": kwargs.get("name", max_name),
        "permissions": kwargs.get("permissions", frozenset(["read"])),
        **{k: v for k, v in kwargs.items() if k not in ["name", "permissions"]}
    }
    return create_api_role(**final_kwargs)


def create_role_with_max_permissions(**kwargs) -> ApiRole:
    """
    Create a role with maximum number of permissions.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiRole with maximum permissions
    """
    final_kwargs = {
        "name": kwargs.get("name", "max_permissions"),
        "permissions": kwargs.get("permissions", frozenset(COMMON_PERMISSIONS)),
        **{k: v for k, v in kwargs.items() if k not in ["name", "permissions"]}
    }
    return create_api_role(**final_kwargs)


def create_role_with_single_permission(**kwargs) -> ApiRole:
    """
    Create a role with exactly one permission.
    
    Args:
        **kwargs: Override any default values
        
    Returns:
        ApiRole with single permission
    """
    final_kwargs = {
        "name": kwargs.get("name", "single_perm"),
        "permissions": kwargs.get("permissions", frozenset(["read"])),
        **{k: v for k, v in kwargs.items() if k not in ["name", "permissions"]}
    }
    return create_api_role(**final_kwargs)


# =============================================================================
# HELPER FUNCTIONS FOR TEST SETUP
# =============================================================================

def create_role_hierarchy() -> List[ApiRole]:
    """Create a hierarchy of roles with different permission levels"""
    return [
        create_admin_role(),
        create_editor_role(),
        create_moderator_role(),
        create_user_role(),
        create_guest_role()
    ]


def create_roles_with_all_permissions() -> List[ApiRole]:
    """Create roles that collectively cover all available permissions"""
    roles = []
    
    # Create roles with different permission combinations
    for i in range(0, len(COMMON_PERMISSIONS), 5):
        permissions_subset = frozenset(COMMON_PERMISSIONS[i:i+5])
        role_kwargs = create_api_role_kwargs()
        role_kwargs["name"] = f"role_{i//5}"
        role_kwargs["permissions"] = permissions_subset
        role = create_api_role(**role_kwargs)
        roles.append(role)
    
    return roles


def create_roles_with_different_names() -> List[ApiRole]:
    """Create roles with various name formats for testing"""
    name_formats = [
        "admin",
        "user_role",
        "guest123",
        "api_user",
        "content_manager",
        "recipe_tester",
        "social_moderator",
        "premium_user",
        "analytics_user",
        "system_admin"
    ]
    
    roles = []
    for i, name in enumerate(name_formats):
        role_kwargs = create_api_role_kwargs()
        role_kwargs["name"] = name
        role_kwargs["permissions"] = frozenset(COMMON_PERMISSIONS[:i+1])
        role = create_api_role(**role_kwargs)
        roles.append(role)
    
    return roles


def create_roles_with_different_permission_counts() -> List[ApiRole]:
    """Create roles with various permission counts for testing"""
    permission_counts = [0, 1, 2, 5, 10, 20, len(COMMON_PERMISSIONS)]
    roles = []
    
    for i, count in enumerate(permission_counts):
        role_kwargs = create_api_role_kwargs()
        role_kwargs["name"] = f"role_{count}_perms"
        role_kwargs["permissions"] = frozenset(COMMON_PERMISSIONS[:count])
        role = create_api_role(**role_kwargs)
        roles.append(role)
    
    return roles


def create_test_role_dataset(role_count: int = 100) -> Dict[str, Any]:
    """Create a dataset of roles for performance testing"""
    roles = []
    json_strings = []
    
    for i in range(role_count):
        # Create API role
        role_kwargs = create_api_role_kwargs()
        role = create_api_role(**role_kwargs)
        roles.append(role)
        
        # Create JSON representation
        json_string = role.model_dump_json()
        json_strings.append(json_string)
    
    return {
        "roles": roles,
        "json_strings": json_strings,
        "total_roles": len(roles)
    }


# =============================================================================
# DOMAIN AND ORM CONVERSION HELPERS
# =============================================================================

def create_role_domain_from_api(api_role: ApiRole) -> Role:
    """Convert ApiRole to domain Role using to_domain method"""
    # ApiRole.to_domain() returns SeedRole, but Role inherits from SeedRole
    # so we need to create a proper Role instance
    seed_role = api_role.to_domain()
    return Role(name=seed_role.name, permissions=seed_role.permissions)


def create_api_role_from_domain(domain_role: Role) -> ApiRole:
    """Convert domain Role to ApiRole using from_domain method"""
    # Use ApiRole.from_domain() which returns ApiRole, not ApiSeedRole
    return cast(ApiRole, ApiRole.from_domain(domain_role))


def create_role_orm_kwargs_from_api(api_role: ApiRole) -> Dict[str, Any]:
    """Convert ApiRole to ORM kwargs using to_orm_kwargs method"""
    return api_role.to_orm_kwargs()


def create_api_role_from_orm(orm_role: RoleSaModel) -> ApiRole:
    """Convert ORM Role to ApiRole using from_orm_model method"""
    # Use ApiRole.from_orm_model() which returns ApiRole, not ApiSeedRole
    return cast(ApiRole, ApiRole.from_orm_model(orm_role))


# =============================================================================
# JSON VALIDATION AND EDGE CASE TESTING
# =============================================================================

def create_valid_json_test_cases() -> List[Dict[str, Any]]:
    """Create various valid JSON test cases for model_validate_json testing"""
    return [
        # Standard admin role
        {
            "name": "admin",
            "permissions": ["read", "write", "delete", "manage_users"]
        },
        # Basic user role
        {
            "name": "user",
            "permissions": ["read", "write", "create_recipes"]
        },
        # Guest role with minimal permissions
        {
            "name": "guest",
            "permissions": ["read"]
        },
        # Empty permissions
        {
            "name": "empty",
            "permissions": []
        },
        # Single character name
        {
            "name": "a",
            "permissions": ["read"]
        },
        # Role with many permissions
        {
            "name": "superuser",
            "permissions": COMMON_PERMISSIONS[:20]
        },
        # Role with duplicate permissions (should be deduplicated)
        {
            "name": "duplicate_perms",
            "permissions": ["read", "write", "read", "write"]
        },
        # Role with special characters in permissions
        {
            "name": "special",
            "permissions": ["read_write", "manage_users", "api_access"]
        }
    ]


def create_invalid_json_test_cases() -> List[Dict[str, Any]]:
    """Create various invalid JSON test cases for validation error testing"""
    return [
        # Invalid name (uppercase)
        {
            "data": {
                "name": "ADMIN",  # Invalid - uppercase
                "permissions": ["read"]
            },
            "expected_errors": ["name"]
        },
        # Invalid name (special characters)
        {
            "data": {
                "name": "admin@role",  # Invalid - special characters
                "permissions": ["read"]
            },
            "expected_errors": ["name"]
        },
        # Invalid name (empty)
        {
            "data": {
                "name": "",  # Invalid - empty
                "permissions": ["read"]
            },
            "expected_errors": ["name"]
        },
        # Invalid name (whitespace only)
        {
            "data": {
                "name": "   ",  # Invalid - whitespace only
                "permissions": ["read"]
            },
            "expected_errors": ["name"]
        },
        # Invalid permissions (not a list/set)
        {
            "data": {
                "name": "test",
                "permissions": "read"  # Invalid - string instead of list
            },
            "expected_errors": ["permissions"]
        },
        # Invalid permissions (contains non-string)
        {
            "data": {
                "name": "test",
                "permissions": ["read", 123]  # Invalid - number in permissions
            },
            "expected_errors": ["permissions"]
        },
        # Missing required fields
        {
            "data": {
                "name": "test"
                # Missing permissions
            },
            "expected_errors": ["permissions"]
        },
        # Missing name
        {
            "data": {
                "permissions": ["read"]
                # Missing name
            },
            "expected_errors": ["name"]
        },
        # Both fields missing
        {
            "data": {
                # Missing both name and permissions
            },
            "expected_errors": ["name", "permissions"]
        },
        # Invalid name with spaces
        {
            "data": {
                "name": "admin role",  # Invalid - spaces not allowed
                "permissions": ["read"]
            },
            "expected_errors": ["name"]
        }
    ]


def check_json_serialization_roundtrip(api_role: ApiRole) -> bool:
    """Test that JSON serialization and deserialization preserves data integrity"""
    # Serialize to JSON
    json_str = api_role.model_dump_json()
    
    # Deserialize from JSON
    restored_role = ApiRole.model_validate_json(json_str)
    
    # Compare original and restored
    return api_role == restored_role


def create_edge_case_roles() -> List[ApiRole]:
    """Create roles with edge case scenarios"""
    return [
        create_empty_permissions_role(),
        create_role_with_single_permission(),
        create_role_with_max_permissions(),
        create_role_with_max_name(),
        create_minimal_role()
    ]


# =============================================================================
# PERFORMANCE TESTING HELPERS
# =============================================================================

def create_bulk_role_creation_dataset(count: int = 1000) -> List[Dict[str, Any]]:
    """Create a dataset for bulk role creation performance testing"""
    return [create_api_role_kwargs() for _ in range(count)]


def create_bulk_json_serialization_dataset(count: int = 1000) -> List[str]:
    """Create a dataset for bulk JSON serialization performance testing"""
    roles = [create_api_role() for _ in range(count)]
    return [role.model_dump_json() for role in roles]


def create_bulk_json_deserialization_dataset(count: int = 1000) -> List[str]:
    """Create a dataset for bulk JSON deserialization performance testing"""
    json_strings = []
    for _ in range(count):
        role_kwargs = create_api_role_kwargs()
        # Convert frozenset to list for JSON serialization
        role_kwargs["permissions"] = list(role_kwargs["permissions"])
        json_strings.append(json.dumps(role_kwargs))
    return json_strings


def create_conversion_performance_dataset(count: int = 1000) -> Dict[str, Any]:
    """Create a dataset for conversion performance testing"""
    api_roles = [create_api_role() for _ in range(count)]
    domain_roles = [Role(name=f"domain_{i}", permissions=frozenset(["read"])) for i in range(count)]
    orm_roles = [RoleSaModel(name=f"orm_{i}", permissions="read, write") for i in range(count)]
    
    return {
        "api_roles": api_roles,
        "domain_roles": domain_roles,
        "orm_roles": orm_roles,
        "total_count": count
    } 