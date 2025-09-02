"""Role value object for recipes catalog domain."""
from __future__ import annotations

from attrs import frozen
from src.contexts.recipes_catalog.core.domain.enums import Role as EnumRoles
from src.contexts.seedwork.domain.value_objects.role import SeedRole as SeedRole


@frozen(hash=True)
class Role(SeedRole):
    """Role value object with predefined permission sets.

    Provides factory methods for creating common role instances.
    """

    @classmethod
    def administrator(cls) -> Role:
        """Create administrator role with full permissions.

        Returns:
            Role with administrator permissions.
        """
        return Role(
            name=EnumRoles.ADMINISTRATOR.name.lower(),
            permissions=frozenset(EnumRoles.ADMINISTRATOR.permissions),
        )

    @classmethod
    def user_manager(cls) -> Role:
        """Create user manager role with user management permissions.

        Returns:
            Role with user management permissions.
        """
        return Role(
            name=EnumRoles.USER_MANAGER.name.lower(),
            permissions=frozenset(EnumRoles.USER_MANAGER.permissions),
        )

    @classmethod
    def recipe_manager(cls) -> Role:
        """Create recipe manager role with recipe management permissions.

        Returns:
            Role with recipe management permissions.
        """
        return Role(
            name=EnumRoles.RECIPE_MANAGER.name.lower(),
            permissions=frozenset(EnumRoles.RECIPE_MANAGER.permissions),
        )

    @classmethod
    def auditor(cls) -> Role:
        """Create auditor role with audit log access permissions.

        Returns:
            Role with audit log access permissions.
        """
        return Role(
            name=EnumRoles.AUDITOR.name.lower(),
            permissions=frozenset(EnumRoles.AUDITOR.permissions),
        )

    @classmethod
    def user(cls) -> Role:
        """Create basic user role with basic feature access.

        Returns:
            Role with basic feature access permissions.
        """
        return Role(
            name=EnumRoles.USER.name.lower(),
            permissions=frozenset(EnumRoles.USER.permissions),
        )

    @classmethod
    def developer(cls) -> Role:
        """Create developer role with developer tool access.

        Returns:
            Role with developer tool access permissions.
        """
        return Role(
            name=EnumRoles.DEVELOPER.name.lower(),
            permissions=frozenset(EnumRoles.DEVELOPER.permissions),
        )

    @classmethod
    def support_staff(cls) -> Role:
        """Create support staff role with support and basic feature access.

        Returns:
            Role with support and basic feature access permissions.
        """
        return Role(
            name=EnumRoles.SUPPORT_STAFF.name.lower(),
            permissions=frozenset(EnumRoles.SUPPORT_STAFF.permissions),
        )
