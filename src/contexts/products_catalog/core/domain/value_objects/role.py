"""Role value object for Products Catalog domain.

Provides factory methods for creating role instances with
catalog-specific permissions and access controls.
"""
from __future__ import annotations

from attrs import frozen
from src.contexts.products_catalog.core.domain.enums import Role as EnumRoles
from src.contexts.seedwork.domain.value_objects.role import SeedRole as SeedRole


@frozen(hash=True)
class Role(SeedRole):
    """Role value object for Products Catalog domain.
    
    Invariants:
        - name must be non-empty
        - permissions must be a valid frozenset of permission strings
    
    Attributes:
        name: Role name (e.g., "administrator", "user").
        permissions: Set of permissions granted to this role.
    
    Notes:
        Immutable. Equality by value (name, permissions).
        Provides factory methods for common catalog roles.
    """
    @classmethod
    def administrator(cls) -> Role:
        """Create administrator role with full system permissions.
        
        Returns:
            Role with manage_users, manage_products, and view_audit_log permissions.
        """
        return Role(
            name=EnumRoles.ADMINISTRATOR.name.lower(),
            permissions=frozenset(EnumRoles.ADMINISTRATOR.permissions),
        )

    @classmethod
    def user_manager(cls) -> Role:
        """Create user manager role with user management permissions.
        
        Returns:
            Role with manage_users permission.
        """
        return Role(
            name=EnumRoles.USER_MANAGER.name.lower(),
            permissions=frozenset(EnumRoles.USER_MANAGER.permissions),
        )

    @classmethod
    def product_manager(cls) -> Role:
        """Create product manager role with product management permissions.
        
        Returns:
            Role with manage_products permission.
        """
        return Role(
            name=EnumRoles.PRODUCT_MANAGER.name.lower(),
            permissions=frozenset(EnumRoles.PRODUCT_MANAGER.permissions),
        )

    @classmethod
    def auditor(cls) -> Role:
        """Create auditor role with audit log access permissions.
        
        Returns:
            Role with view_audit_log permission.
        """
        return Role(
            name=EnumRoles.AUDITOR.name.lower(),
            permissions=frozenset(EnumRoles.AUDITOR.permissions),
        )

    @classmethod
    def user(cls) -> Role:
        """Create basic user role with basic feature access.
        
        Returns:
            Role with access_basic_features permission.
        """
        return Role(
            name=EnumRoles.USER.name.lower(),
            permissions=frozenset(EnumRoles.USER.permissions),
        )

    @classmethod
    def developer(cls) -> Role:
        """Create developer role with developer tools access.
        
        Returns:
            Role with access_developer_tools permission.
        """
        return Role(
            name=EnumRoles.DEVELOPER.name.lower(),
            permissions=frozenset(EnumRoles.DEVELOPER.permissions),
        )

    @classmethod
    def support_staff(cls) -> Role:
        """Create support staff role with support and basic feature access.
        
        Returns:
            Role with access_support and access_basic_features permissions.
        """
        return Role(
            name=EnumRoles.SUPPORT_STAFF.name.lower(),
            permissions=frozenset(EnumRoles.SUPPORT_STAFF.permissions),
        )
