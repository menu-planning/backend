from __future__ import annotations

from attrs import frozen
from src.contexts.client_onboarding.core.domain.enums import Role as EnumRoles
from src.contexts.seedwork.domain.value_objects.role import SeedRole


@frozen(hash=True)
class Role(SeedRole):
    """Client onboarding role value object.

    Provides factory methods for creating role instances with predefined
    permission sets for onboarding form management.
    """

    @classmethod
    def form_administrator(cls) -> Role:
        """Create form administrator role with full permissions.

        Returns:
            Role instance with all form management permissions.
        """
        return Role(
            name=EnumRoles.FORM_ADMINISTRATOR.name.lower(),
            permissions=frozenset(EnumRoles.FORM_ADMINISTRATOR.permissions),
        )

    @classmethod
    def form_manager(cls) -> Role:
        """Create form manager role with management permissions.

        Returns:
            Role instance with form management and response viewing permissions.
        """
        return Role(
            name=EnumRoles.FORM_MANAGER.name.lower(),
            permissions=frozenset(EnumRoles.FORM_MANAGER.permissions),
        )

    @classmethod
    def form_viewer(cls) -> Role:
        """Create form viewer role with read-only permissions.

        Returns:
            Role instance with response viewing and client data access permissions.
        """
        return Role(
            name=EnumRoles.FORM_VIEWER.name.lower(),
            permissions=frozenset(EnumRoles.FORM_VIEWER.permissions),
        )

    @classmethod
    def user(cls) -> Role:
        """Create basic user role with minimal permissions.

        Returns:
            Role instance with basic feature access only.
        """
        return Role(
            name=EnumRoles.USER.name.lower(),
            permissions=frozenset(EnumRoles.USER.permissions),
        )

    @classmethod
    def developer(cls) -> Role:
        """Create developer role with development tool access.

        Returns:
            Role instance with developer tool permissions.
        """
        return Role(
            name=EnumRoles.DEVELOPER.name.lower(),
            permissions=frozenset(EnumRoles.DEVELOPER.permissions),
        )

    @classmethod
    def support_staff(cls) -> Role:
        """Create support staff role with support and basic permissions.

        Returns:
            Role instance with support access and basic feature permissions.
        """
        return Role(
            name=EnumRoles.SUPPORT_STAFF.name.lower(),
            permissions=frozenset(EnumRoles.SUPPORT_STAFF.permissions),
        )
