"""Enumerations for IAM permissions and roles.

Extends seedwork enums with IAM-specific values and helpers.
"""

from enum import unique

from src.contexts.seedwork.domain.enums import Permission as SeedPermission
from src.contexts.seedwork.domain.enums import Role as SeedRole


@unique
class Permission(SeedPermission):
    """IAM-specific permissions for access control.
    
    Defines granular permissions that can be granted to users through roles.
    Each permission represents a specific capability within the IAM system.
    """
    MANAGE_USERS = "manage_users"
    MANAGE_ROLES = "manage_roles"
    VIEW_AUDIT_LOG = "view_audit_log"
    ACCESS_DEVELOPER_TOOLS = "access_developer_tools"
    ACCESS_SUPPORT = "access_support"
    ACCESS_BASIC_FEATURES = "access_basic_features"


@unique
class Role(SeedRole):
    """IAM roles with predefined permission sets.
    
    Each role represents a collection of permissions that define what
    actions a user with that role can perform within the IAM context.
    """
    ADMINISTRATOR = frozenset({
        Permission.MANAGE_USERS,
        Permission.MANAGE_ROLES,
        Permission.VIEW_AUDIT_LOG,
    })
    USER_MANAGER = frozenset({Permission.MANAGE_USERS})
    ROLE_MANAGER = frozenset({Permission.MANAGE_ROLES})
    AUDITOR = frozenset({Permission.VIEW_AUDIT_LOG})
    USER = frozenset({Permission.ACCESS_BASIC_FEATURES})
    DEVELOPER = frozenset({Permission.ACCESS_DEVELOPER_TOOLS})
    SUPPORT_STAFF = frozenset({Permission.ACCESS_SUPPORT, Permission.ACCESS_BASIC_FEATURES})

    @property
    def permissions(self) -> list[str]:
        """Return permission strings associated with this role.
        
        Returns:
            List of permission string values for this role.
        """
        return [i.value for i in list(self.value)]
