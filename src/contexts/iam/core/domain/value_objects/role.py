from __future__ import annotations

from attrs import field, frozen
from src.contexts.iam.core.domain.enums import Permission as EnumPermissions
from src.contexts.iam.core.domain.enums import Role as EnumRoles
from src.contexts.seedwork.domain.value_objects.value_object import ValueObject


@frozen(hash=True)
class Role(ValueObject):
    """Value object representing an IAM role with permissions.
    
    Encapsulates role identity, context, and associated permissions.
    Provides factory methods for creating predefined role instances.
    
    Invariants:
        - Role name must be non-empty
        - Context must be non-empty
        - Permissions list cannot be None
    
    Attributes:
        name: Role identifier (e.g., 'administrator', 'user').
        context: Domain context where role applies (default: 'IAM').
        permissions: List of permission strings granted by this role.
    
    Notes:
        Immutable. Equality by value (name, context, permissions).
    """
    name: str
    context: str = field(default="IAM")
    permissions: list[str] = field(factory=list, hash=False)

    def has_permission(self, permission: str | EnumPermissions) -> bool:
        """Check if this role grants a specific permission.
        
        Args:
            permission: Permission to check (string or enum).
        
        Returns:
            True if the role grants the specified permission.
        """
        if isinstance(permission, EnumPermissions):
            permission = permission.value
        return permission in self.permissions

    @classmethod
    def administrator(cls) -> Role:
        """Create Administrator role with full IAM permissions.
        
        Returns:
            Role with manage_users, manage_roles, and view_audit_log permissions.
        """
        return cls(
            EnumRoles.ADMINISTRATOR.name.lower(),
            "IAM",
            EnumRoles.ADMINISTRATOR.permissions,
        )

    @classmethod
    def user_manager(cls) -> Role:
        """Create User Manager role with user management permissions.
        
        Returns:
            Role with manage_users permission.
        """
        return cls(
            EnumRoles.USER_MANAGER.name.lower(),
            "IAM",
            EnumRoles.USER_MANAGER.permissions,
        )

    @classmethod
    def role_manager(cls) -> Role:
        """Create Role Manager role with role management permissions.
        
        Returns:
            Role with manage_roles permission.
        """
        return cls(
            EnumRoles.ROLE_MANAGER.name.lower(),
            "IAM",
            EnumRoles.ROLE_MANAGER.permissions,
        )

    @classmethod
    def auditor(cls) -> Role:
        """Create Auditor role with audit log access permissions.
        
        Returns:
            Role with view_audit_log permission.
        """
        return cls(
            EnumRoles.AUDITOR.name.lower(),
            "IAM",
            EnumRoles.AUDITOR.permissions,
        )

    @classmethod
    def user(cls) -> Role:
        """Create basic User role with minimal permissions.
        
        Returns:
            Role with access_basic_features permission.
        """
        return cls(
            EnumRoles.USER.name.lower(),
            "IAM",
            EnumRoles.USER.permissions,
        )

    @classmethod
    def developer(cls) -> Role:
        """Create Developer role with developer tool access.
        
        Returns:
            Role with access_developer_tools permission.
        """
        return cls(
            EnumRoles.DEVELOPER.name.lower(),
            "IAM",
            EnumRoles.DEVELOPER.permissions,
        )

    @classmethod
    def support_staff(cls) -> Role:
        """Create Support Staff role with support and basic permissions.
        
        Returns:
            Role with access_support and access_basic_features permissions.
        """
        return cls(
            EnumRoles.SUPPORT_STAFF.name.lower(),
            "IAM",
            EnumRoles.SUPPORT_STAFF.permissions,
        )

    def __str__(self):
        return f"<Role {self.name}>"

    def __repr__(self):
        return f"<Role {self.name}>"
