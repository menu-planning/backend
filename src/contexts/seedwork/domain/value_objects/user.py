from typing import TYPE_CHECKING

from attrs import frozen
from src.contexts.seedwork.domain.enums import Permission
from src.contexts.seedwork.domain.enums import Role as EnumRoles
from src.contexts.seedwork.domain.value_objects.value_object import ValueObject

if TYPE_CHECKING:
    from src.contexts.seedwork.domain.value_objects.role import SeedRole


@frozen(kw_only=True)
class SeedUser[R: "SeedRole"](ValueObject):
    """User value object with roles and permissions.

    Invariants:
        - User ID must be non-empty.
        - Roles set cannot be empty.

    Attributes:
        id: User identifier.
        roles: Set of user roles.

    Notes:
        Immutable. Equality by value (id, roles).
    """
    id: str
    roles: frozenset[R]

    def has_permission(self, permission: str | Permission) -> bool:
        """Check if user has the specified permission through any role.

        Args:
            permission: Permission to check (string or enum).

        Returns:
            True if user has permission through any role, False otherwise.
        """
        if isinstance(permission, Permission):
            permission = permission.value
        return any(role.has_permission(permission) for role in self.roles)

    def has_role(self, role: str | EnumRoles) -> bool:
        """Check if user has the specified role.

        Args:
            role: Role to check (string or enum).

        Returns:
            True if user has the role, False otherwise.
        """
        if isinstance(role, EnumRoles):
            role = role.name.lower()
        return any(r.name.lower() == role for r in self.roles)
