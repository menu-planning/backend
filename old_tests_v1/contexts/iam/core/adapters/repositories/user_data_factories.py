"""
Data factories for UserRepository testing following seedwork patterns.
Uses deterministic values (not random) for consistent test behavior.

This module provides:
- Deterministic data creation with static counters
- Parametrized test scenarios for filtering
- Performance test scenarios with dataset expectations
- Specialized factory functions for different user types
- ORM equivalents for all domain factory methods

All data follows the exact structure of User domain entities and their relationships.
Both domain and ORM variants are provided for comprehensive testing scenarios.
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List

from src.contexts.iam.core.adapters.ORM.sa_models.role_sa_model import RoleSaModel

# ORM model imports
from src.contexts.iam.core.adapters.ORM.sa_models.user_sa_model import UserSaModel
from src.contexts.iam.core.domain.root_aggregate.user import User
from src.contexts.iam.core.domain.value_objects.role import Role
from tests.utils.counter_manager import (
    get_next_role_id,
    get_next_user_id,
    reset_all_counters,
)

# =============================================================================
# USER DATA FACTORIES (DOMAIN)
# =============================================================================


def create_user_kwargs(**kwargs) -> dict[str, Any]:
    """
    Create user kwargs with deterministic values.

    Following seedwork pattern with static counters for consistent test behavior.
    All required entity attributes are guaranteed to be present.

    Args:
        **kwargs: Override any default values

    Returns:
        Dict with all required user creation parameters
    """
    # Base timestamp for deterministic dates
    base_time = datetime(2024, 1, 1, 12, 0, 0)

    # Create basic roles for deterministic testing
    basic_roles = kwargs.get("roles", [Role.user()])  # Default to basic user role

    user_counter = get_next_user_id()
    final_kwargs = {
        "id": kwargs.get("id", f"user_{user_counter:03d}"),
        "roles": basic_roles,
        "discarded": kwargs.get("discarded", False),
        "version": kwargs.get("version", 1),
        "created_at": kwargs.get(
            "created_at", base_time + timedelta(hours=user_counter)
        ),
        "updated_at": kwargs.get(
            "updated_at", base_time + timedelta(hours=user_counter, minutes=30)
        ),
    }

    return final_kwargs


def create_user(**kwargs) -> User:
    """
    Create a User domain entity with deterministic data.

    Args:
        **kwargs: Override any default values

    Returns:
        User domain entity
    """
    user_kwargs = create_user_kwargs(**kwargs)
    return User(**user_kwargs)


# =============================================================================
# USER DATA FACTORIES (ORM)
# =============================================================================


def create_user_orm_kwargs(**kwargs) -> dict[str, Any]:
    """
    Create user ORM kwargs with deterministic values.

    Similar to create_user_kwargs but adapted for ORM model fields.

    Args:
        **kwargs: Override any default values

    Returns:
        Dict with all required ORM user creation parameters
    """
    # Base timestamp for deterministic dates
    base_time = datetime(2024, 1, 1, 12, 0, 0)

    user_counter = get_next_user_id()
    final_kwargs = {
        "id": kwargs.get("id", f"user_{user_counter:03d}"),
        "discarded": kwargs.get("discarded", False),
        "version": kwargs.get("version", 1),
        "created_at": kwargs.get(
            "created_at", base_time + timedelta(hours=user_counter)
        ),
        "updated_at": kwargs.get(
            "updated_at", base_time + timedelta(hours=user_counter, minutes=30)
        ),
        "roles": kwargs.get("roles", []),  # Will be populated separately if needed
    }

    return final_kwargs


def create_user_orm(**kwargs) -> UserSaModel:
    """
    Create a UserSaModel ORM instance with deterministic data.

    Args:
        **kwargs: Override any default values

    Returns:
        UserSaModel ORM instance
    """
    user_kwargs = create_user_orm_kwargs(**kwargs)
    return UserSaModel(**user_kwargs)


# =============================================================================
# ROLE DATA FACTORIES (DOMAIN)
# =============================================================================


def create_role_kwargs(**kwargs) -> dict[str, Any]:
    """
    Create role kwargs with deterministic values.

    Args:
        **kwargs: Override any default values

    Returns:
        Dict with role creation parameters
    """
    # Predefined role data for realistic testing
    role_names = [
        "user",
        "administrator",
        "user_manager",
        "role_manager",
        "auditor",
        "developer",
    ]
    contexts = ["IAM", "recipes_catalog", "products_catalog", "menu_planning"]

    role_counter = get_next_role_id()
    name = kwargs.get("name", role_names[(role_counter - 1) % len(role_names)])
    context = kwargs.get("context", contexts[(role_counter - 1) % len(contexts)])

    # Determine permissions based on role name
    permissions_map = {
        "user": ["read"],
        "administrator": ["read", "write", "delete", "admin"],
        "user_manager": ["read", "write", "manage_users"],
        "role_manager": ["read", "write", "manage_roles"],
        "auditor": ["read", "audit"],
        "developer": ["read", "write", "debug", "deploy"],
    }

    default_permissions = permissions_map.get(name, ["read"])

    final_kwargs = {
        "name": name,
        "context": context,
        "permissions": kwargs.get("permissions", default_permissions),
    }

    return final_kwargs


def create_role(**kwargs) -> Role:
    """
    Create a Role value object with deterministic data.

    Args:
        **kwargs: Override any default values

    Returns:
        Role value object
    """
    role_kwargs = create_role_kwargs(**kwargs)
    return Role(**role_kwargs)


# =============================================================================
# ROLE DATA FACTORIES (ORM)
# =============================================================================


def create_role_orm_kwargs(**kwargs) -> dict[str, Any]:
    """
    Create role ORM kwargs with deterministic values.

    Args:
        **kwargs: Override any default values

    Returns:
        Dict with ORM role creation parameters
    """
    # Predefined role data for realistic testing
    role_names = [
        "user",
        "administrator",
        "user_manager",
        "role_manager",
        "auditor",
        "developer",
    ]
    contexts = ["IAM", "recipes_catalog", "products_catalog", "menu_planning"]

    role_counter = get_next_role_id()
    name = kwargs.get("name", role_names[(role_counter - 1) % len(role_names)])
    context = kwargs.get("context", contexts[(role_counter - 1) % len(contexts)])

    # Determine permissions based on role name
    permissions_map = {
        "user": "read",
        "administrator": "read, write, delete, admin",
        "user_manager": "read, write, manage_users",
        "role_manager": "read, write, manage_roles",
        "auditor": "read, audit",
        "developer": "read, write, debug, deploy",
    }

    default_permissions = permissions_map.get(name, "read")

    # Handle permissions - ORM expects string, but could be passed as list
    permissions = kwargs.get("permissions", default_permissions)
    if isinstance(permissions, list):
        permissions = ", ".join(permissions)

    final_kwargs = {
        "name": name,
        "context": context,
        "permissions": permissions,
    }

    return final_kwargs


def create_role_orm(**kwargs) -> RoleSaModel:
    """
    Create a RoleSaModel ORM instance with deterministic data.

    Args:
        **kwargs: Override any default values

    Returns:
        RoleSaModel ORM instance
    """
    role_kwargs = create_role_orm_kwargs(**kwargs)
    return RoleSaModel(**role_kwargs)


# =============================================================================
# PARAMETRIZED TEST SCENARIOS
# =============================================================================


def get_user_filter_scenarios() -> list[dict[str, Any]]:
    """
    Get predefined scenarios for testing user filtering.

    Returns:
        List of test scenarios with user_kwargs, filter, and expected outcome
    """
    return [
        {
            "scenario_id": "user_id_match",
            "user_kwargs": {"id": "test_user_123"},
            "filter": {"id": "test_user_123"},
            "should_match": True,
            "description": "User should match ID filter",
        },
        {
            "scenario_id": "discarded_false_match",
            "user_kwargs": {"id": "active_user", "discarded": False},
            "filter": {"discarded": False},
            "should_match": True,
            "description": "Active user should match non-discarded filter",
        },
        {
            "scenario_id": "discarded_true_match",
            "user_kwargs": {"id": "deleted_user", "discarded": True},
            "filter": {"discarded": True},
            "should_match": True,
            "description": "Deleted user should match discarded filter",
        },
        {
            "scenario_id": "version_match",
            "user_kwargs": {"id": "versioned_user", "version": 5},
            "filter": {"version": 5},
            "should_match": True,
            "description": "User should match version filter",
        },
        {
            "scenario_id": "role_context_match",
            "user_kwargs": {
                "id": "role_user",
                "roles": [
                    Role(name="administrator", context="IAM", permissions=["admin"])
                ],
            },
            "filter": {"context": "IAM", "name": "administrator"},
            "should_match": True,
            "description": "User with role should match role filter",
        },
    ]


def get_user_filter_scenarios_orm() -> list[dict[str, Any]]:
    """
    Get predefined scenarios for testing user filtering using ORM objects.

    Returns:
        List of test scenarios with user_kwargs, filter, and expected outcome with ORM models
    """
    return [
        {
            "scenario_id": "user_id_match",
            "user_kwargs": {"id": "test_user_123"},
            "filter": {"id": "test_user_123"},
            "should_match": True,
            "description": "User should match ID filter",
        },
        {
            "scenario_id": "discarded_false_match",
            "user_kwargs": {"id": "active_user", "discarded": False},
            "filter": {"discarded": False},
            "should_match": True,
            "description": "Active user should match non-discarded filter",
        },
        {
            "scenario_id": "discarded_true_match",
            "user_kwargs": {"id": "deleted_user", "discarded": True},
            "filter": {"discarded": True},
            "should_match": True,
            "description": "Deleted user should match discarded filter",
        },
        {
            "scenario_id": "version_match",
            "user_kwargs": {"id": "versioned_user", "version": 5},
            "filter": {"version": 5},
            "should_match": True,
            "description": "User should match version filter",
        },
        {
            "scenario_id": "role_context_match",
            "user_kwargs": {
                "id": "role_user",
                "roles": [
                    create_role_orm(
                        name="administrator", context="IAM", permissions="admin"
                    )
                ],
            },
            "filter": {"context": "IAM", "name": "administrator"},
            "should_match": True,
            "description": "User with role should match role filter",
        },
        {
            "scenario_id": "multiple_criteria_match",
            "user_kwargs": {
                "id": "complex_user",
                "discarded": False,
                "version": 2,
                "roles": [
                    create_role_orm(
                        name="user_manager",
                        context="IAM",
                        permissions="read, write, manage_users",
                    )
                ],
            },
            "filter": {"context": "IAM", "discarded": False, "name": "user_manager"},
            "should_match": True,
            "description": "User should match multiple filter criteria",
        },
        {
            "scenario_id": "no_role_match",
            "user_kwargs": {
                "id": "basic_user",
                "roles": [
                    create_role_orm(name="user", context="IAM", permissions="read")
                ],
            },
            "filter": {"name": "administrator"},
            "should_match": False,
            "description": "User should not match when role doesn't exist",
        },
    ]


def get_role_relationship_scenarios() -> list[dict[str, Any]]:
    """
    Get predefined scenarios for testing role relationships.

    Returns:
        List of test scenarios for role filtering and relationships
    """
    return [
        {
            "scenario_id": "single_role_user",
            "user_kwargs": {"id": "single_role_user", "roles": [Role.user()]},
            "filter": {"name": "user"},
            "should_match": True,
            "description": "User should match when filtering by single role",
        },
        {
            "scenario_id": "multiple_roles_user",
            "user_kwargs": {
                "id": "multi_role_user",
                "roles": [Role.user(), Role.administrator()],
            },
            "filter": {"name": "administrator"},
            "should_match": True,
            "description": "User should match when filtering by one of multiple roles",
        },
        {
            "scenario_id": "no_matching_role",
            "user_kwargs": {"id": "basic_user", "roles": [Role.user()]},
            "filter": {"name": "administrator"},
            "should_match": False,
            "description": "User with basic role should not match admin filter",
        },
    ]


def get_role_relationship_scenarios_orm() -> list[dict[str, Any]]:
    """
    Get predefined scenarios for testing role relationships using ORM objects.

    Returns:
        List of test scenarios for role filtering and relationships with ORM models
    """
    return [
        {
            "scenario_id": "single_role_user",
            "user_kwargs": {
                "id": "single_role_user",
                "roles": [
                    create_role_orm(name="user", context="IAM", permissions="read")
                ],
            },
            "filter": {"name": "user"},
            "should_match": True,
            "description": "User should match when filtering by single role",
        },
        {
            "scenario_id": "multiple_roles_user",
            "user_kwargs": {
                "id": "multi_role_user",
                "roles": [
                    create_role_orm(name="user", context="IAM", permissions="read"),
                    create_role_orm(
                        name="administrator",
                        context="IAM",
                        permissions="read, write, delete, admin",
                    ),
                ],
            },
            "filter": {"name": "administrator"},
            "should_match": True,
            "description": "User should match when filtering by one of multiple roles",
        },
        {
            "scenario_id": "no_matching_role",
            "user_kwargs": {
                "id": "basic_user",
                "roles": [
                    create_role_orm(name="user", context="IAM", permissions="read")
                ],
            },
            "filter": {"name": "administrator"},
            "should_match": False,
            "description": "User with basic role should not match admin filter",
        },
        {
            "scenario_id": "context_specific_role",
            "user_kwargs": {
                "id": "recipes_user",
                "roles": [
                    create_role_orm(
                        name="user", context="recipes_catalog", permissions="read"
                    )
                ],
            },
            "filter": {"context": "recipes_catalog"},
            "should_match": True,
            "description": "User should match when filtering by role context",
        },
        {
            "scenario_id": "wrong_context_filter",
            "user_kwargs": {
                "id": "iam_user",
                "roles": [
                    create_role_orm(name="user", context="IAM", permissions="read")
                ],
            },
            "filter": {"context": "recipes_catalog"},
            "should_match": False,
            "description": "User should not match when filtering by wrong context",
        },
    ]


def get_permission_scenarios() -> list[dict[str, Any]]:
    """
    Get predefined scenarios for testing permission validation.

    Returns:
        List of test scenarios for permission filtering and validation
    """
    return [
        {
            "scenario_id": "admin_permissions",
            "user_kwargs": {"id": "admin_user", "roles": [Role.administrator()]},
            "expected_permissions": ["read", "write", "delete", "admin"],
            "description": "Administrator should have full permissions",
        },
        {
            "scenario_id": "user_permissions",
            "user_kwargs": {"id": "basic_user", "roles": [Role.user()]},
            "expected_permissions": ["read"],
            "description": "Basic user should have read-only permissions",
        },
        {
            "scenario_id": "multiple_role_permissions",
            "user_kwargs": {
                "id": "manager_user",
                "roles": [Role.user(), Role.user_manager()],
            },
            "expected_contexts": ["IAM"],
            "description": "User manager should have combined permissions",
        },
    ]


def get_permission_scenarios_orm() -> list[dict[str, Any]]:
    """
    Get predefined scenarios for testing permission validation using ORM objects.

    Returns:
        List of test scenarios for permission filtering and validation with ORM models
    """
    return [
        {
            "scenario_id": "admin_permissions",
            "user_kwargs": {
                "id": "admin_user",
                "roles": [
                    create_role_orm(
                        name="administrator",
                        context="IAM",
                        permissions="read, write, delete, admin",
                    )
                ],
            },
            "expected_permissions": ["read", "write", "delete", "admin"],
            "description": "Administrator should have full permissions",
        },
        {
            "scenario_id": "user_permissions",
            "user_kwargs": {
                "id": "basic_user",
                "roles": [
                    create_role_orm(name="user", context="IAM", permissions="read")
                ],
            },
            "expected_permissions": ["read"],
            "description": "Basic user should have read-only permissions",
        },
        {
            "scenario_id": "multiple_role_permissions",
            "user_kwargs": {
                "id": "manager_user",
                "roles": [
                    create_role_orm(name="user", context="IAM", permissions="read"),
                    create_role_orm(
                        name="user_manager",
                        context="IAM",
                        permissions="read, write, manage_users",
                    ),
                ],
            },
            "expected_permissions": ["read", "write", "manage_users"],
            "description": "User manager should have combined permissions",
        },
        {
            "scenario_id": "auditor_permissions",
            "user_kwargs": {
                "id": "auditor_user",
                "roles": [
                    create_role_orm(
                        name="auditor", context="IAM", permissions="read, audit"
                    )
                ],
            },
            "expected_permissions": ["read", "audit"],
            "description": "Auditor should have read and audit permissions",
        },
    ]


def get_performance_test_scenarios() -> list[dict[str, Any]]:
    """
    Get scenarios for performance testing with dataset expectations.

    Returns:
        List of performance test scenarios
    """
    return [
        {
            "scenario_id": "bulk_user_creation",
            "dataset_size": 100,
            "expected_time_per_entity": 0.003,  # 3ms per user
            "description": "Bulk creation of 100 users should complete within 300ms total",
        },
        {
            "scenario_id": "complex_role_filter_query",
            "dataset_size": 1000,
            "filter": {"context": "IAM", "name": "administrator", "discarded": False},
            "expected_query_time": 0.5,  # 500ms max
            "description": "Complex role filter query on 1000 users should complete within 500ms",
        },
        {
            "scenario_id": "role_permission_performance",
            "dataset_size": 500,
            "filter": {"context": "IAM"},
            "expected_query_time": 0.3,  # 300ms max
            "description": "Role filtering on 500 users should complete within 300ms",
        },
    ]


# =============================================================================
# SPECIALIZED USER FACTORIES (DOMAIN)
# =============================================================================


def create_admin_user(**kwargs) -> User:
    """
    Create an administrator user.

    Args:
        **kwargs: Override any default values

    Returns:
        User domain entity with administrator role
    """
    final_kwargs = {
        "id": kwargs.get("id", "admin_user"),
        "roles": kwargs.get("roles", [Role.administrator()]),
        **{k: v for k, v in kwargs.items() if k not in ["id", "roles"]},
    }
    return create_user(**final_kwargs)


def create_basic_user(**kwargs) -> User:
    """
    Create a basic user with minimal privileges.

    Args:
        **kwargs: Override any default values

    Returns:
        User domain entity with basic user role
    """
    final_kwargs = {
        "id": kwargs.get("id", "basic_user"),
        "roles": kwargs.get("roles", [Role.user()]),
        **{k: v for k, v in kwargs.items() if k not in ["id", "roles"]},
    }
    return create_user(**final_kwargs)


def create_user_manager(**kwargs) -> User:
    """
    Create a user manager.

    Args:
        **kwargs: Override any default values

    Returns:
        User domain entity with user management role
    """
    final_kwargs = {
        "id": kwargs.get("id", "user_manager"),
        "roles": kwargs.get("roles", [Role.user_manager()]),
        **{k: v for k, v in kwargs.items() if k not in ["id", "roles"]},
    }
    return create_user(**final_kwargs)


def create_multi_role_user(**kwargs) -> User:
    """
    Create a user with multiple roles.

    Args:
        **kwargs: Override any default values

    Returns:
        User domain entity with multiple roles
    """
    final_kwargs = {
        "id": kwargs.get("id", "multi_role_user"),
        "roles": kwargs.get(
            "roles", [Role.user(), Role.user_manager(), Role.auditor()]
        ),
        **{k: v for k, v in kwargs.items() if k not in ["id", "roles"]},
    }
    return create_user(**final_kwargs)


def create_discarded_user(**kwargs) -> User:
    """
    Create a discarded (deleted) user for soft delete testing.

    Args:
        **kwargs: Override any default values

    Returns:
        User domain entity marked as discarded
    """
    final_kwargs = {
        "id": kwargs.get("id", "discarded_user"),
        "discarded": kwargs.get("discarded", True),
        "roles": kwargs.get("roles", [Role.user()]),
        **{k: v for k, v in kwargs.items() if k not in ["id", "discarded", "roles"]},
    }
    return create_user(**final_kwargs)


# =============================================================================
# SPECIALIZED USER FACTORIES (ORM)
# =============================================================================


def create_admin_user_orm(**kwargs) -> UserSaModel:
    """
    Create an administrator user ORM instance.

    Args:
        **kwargs: Override any default values

    Returns:
        UserSaModel ORM instance with administrator role
    """
    admin_role = create_role_orm(
        name="administrator", context="IAM", permissions="read, write, delete, admin"
    )
    final_kwargs = {
        "id": kwargs.get("id", "admin_user"),
        "roles": kwargs.get("roles", [admin_role]),
        **{k: v for k, v in kwargs.items() if k not in ["id", "roles"]},
    }
    return create_user_orm(**final_kwargs)


def create_basic_user_orm(**kwargs) -> UserSaModel:
    """
    Create a basic user ORM instance with minimal privileges.

    Args:
        **kwargs: Override any default values

    Returns:
        UserSaModel ORM instance with basic user role
    """
    user_role = create_role_orm(name="user", context="IAM", permissions="read")
    final_kwargs = {
        "id": kwargs.get("id", "basic_user"),
        "roles": kwargs.get("roles", [user_role]),
        **{k: v for k, v in kwargs.items() if k not in ["id", "roles"]},
    }
    return create_user_orm(**final_kwargs)


def create_user_manager_orm(**kwargs) -> UserSaModel:
    """
    Create a user manager ORM instance.

    Args:
        **kwargs: Override any default values

    Returns:
        UserSaModel ORM instance with user management role
    """
    manager_role = create_role_orm(
        name="user_manager", context="IAM", permissions="read, write, manage_users"
    )
    final_kwargs = {
        "id": kwargs.get("id", "user_manager"),
        "roles": kwargs.get("roles", [manager_role]),
        **{k: v for k, v in kwargs.items() if k not in ["id", "roles"]},
    }
    return create_user_orm(**final_kwargs)


def create_multi_role_user_orm(**kwargs) -> UserSaModel:
    """
    Create a user ORM instance with multiple roles.

    Args:
        **kwargs: Override any default values

    Returns:
        UserSaModel ORM instance with multiple roles
    """
    user_role = create_role_orm(name="user", context="IAM", permissions="read")
    manager_role = create_role_orm(
        name="user_manager", context="IAM", permissions="read, write, manage_users"
    )
    auditor_role = create_role_orm(
        name="auditor", context="IAM", permissions="read, audit"
    )

    final_kwargs = {
        "id": kwargs.get("id", "multi_role_user"),
        "roles": kwargs.get("roles", [user_role, manager_role, auditor_role]),
        **{k: v for k, v in kwargs.items() if k not in ["id", "roles"]},
    }
    return create_user_orm(**final_kwargs)


def create_discarded_user_orm(**kwargs) -> UserSaModel:
    """
    Create a discarded (deleted) user ORM instance for soft delete testing.

    Args:
        **kwargs: Override any default values

    Returns:
        UserSaModel ORM instance marked as discarded
    """
    final_kwargs = {
        "id": kwargs.get("id", "discarded_user"),
        "discarded": kwargs.get("discarded", True),
        "roles": kwargs.get("roles", []),
        **{k: v for k, v in kwargs.items() if k not in ["id", "discarded", "roles"]},
    }
    return create_user_orm(**final_kwargs)


# =============================================================================
# DATASET CREATION UTILITIES (DOMAIN & ORM)
# =============================================================================


def create_users_with_roles(count: int = 3, roles_per_user: int = 2) -> list[User]:
    """
    Create a list of users with roles for relationship testing.

    Args:
        count: Number of users to create
        roles_per_user: Number of roles per user

    Returns:
        List of User entities with roles
    """
    users = []
    for i in range(count):
        roles = []
        for j in range(roles_per_user):
            role = create_role(
                name=f"role_{j+1}",
                context=f"context_{i+1}",
                permissions=[f"permission_{j+1}"],
            )
            roles.append(role)

        user = create_user(id=f"user_{i+1:03d}", roles=roles)
        users.append(user)

    return users


def create_users_with_roles_orm(
    count: int = 3, roles_per_user: int = 2
) -> list[UserSaModel]:
    """
    Create a list of user ORM instances with roles for relationship testing.

    Args:
        count: Number of users to create
        roles_per_user: Number of roles per user

    Returns:
        List of UserSaModel instances with roles
    """
    users = []
    for i in range(count):
        roles = []
        for j in range(roles_per_user):
            role = create_role_orm(
                name=f"role_{j+1}",
                context=f"context_{i+1}",
                permissions=f"permission_{j+1}",
            )
            roles.append(role)

        user = create_user_orm(id=f"user_{i+1:03d}", roles=roles)
        users.append(user)

    return users


def create_test_dataset(
    user_count: int = 100, roles_per_user: int = 1
) -> dict[str, Any]:
    """
    Create a comprehensive test dataset for performance and integration testing.

    Args:
        user_count: Number of users to create
        roles_per_user: Number of roles per user

    Returns:
        Dict containing users, roles, and metadata
    """
    reset_all_counters()

    users = []
    all_roles = []

    for i in range(user_count):
        # Create varied users
        if i % 4 == 0:
            user = create_admin_user()
        elif i % 4 == 1:
            user = create_user_manager()
        elif i % 4 == 2:
            user = create_multi_role_user()
        else:
            user = create_basic_user()

        # Collect roles
        all_roles.extend(user.roles)
        users.append(user)

    return {
        "users": users,
        "roles": all_roles,
        "metadata": {
            "user_count": len(users),
            "role_count": len(all_roles),
            "roles_per_user": roles_per_user,
        },
    }


def create_test_dataset_orm(
    user_count: int = 100, roles_per_user: int = 1
) -> dict[str, Any]:
    """
    Create a comprehensive test dataset with ORM instances for performance and integration testing.

    Args:
        user_count: Number of users to create
        roles_per_user: Number of roles per user

    Returns:
        Dict containing ORM users, roles, and metadata
    """
    reset_all_counters()

    users = []
    all_roles = []

    for i in range(user_count):
        # Create varied users
        if i % 4 == 0:
            user = create_admin_user_orm()
        elif i % 4 == 1:
            user = create_user_manager_orm()
        elif i % 4 == 2:
            user = create_multi_role_user_orm()
        else:
            user = create_basic_user_orm()

        # Collect roles
        all_roles.extend(user.roles if user.roles else [])
        users.append(user)

    return {
        "users": users,
        "roles": all_roles,
        "metadata": {
            "user_count": len(users),
            "role_count": len(all_roles),
            "roles_per_user": roles_per_user,
        },
    }
