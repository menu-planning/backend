from attrs import field, frozen
from src.contexts.seedwork.domain.enums import Permission
from src.contexts.seedwork.domain.value_objects.value_object import ValueObject


@frozen(hash=True)
class SeedRole(ValueObject):
    """Role value object with permissions.

    Invariants:
        - Role name must be non-empty.
        - Permissions set can be empty (role with no permissions).

    Attributes:
        name: Role identifier.
        permissions: Set of permission strings.

    Notes:
        Immutable. Equality by value (name, permissions).
    """
    name: str
    permissions: frozenset[str] = field(factory=frozenset)

    def has_permission(self, permission: str | Permission) -> bool:
        """Check if role has the specified permission.

        Args:
            permission: Permission to check (string or enum).

        Returns:
            True if role has permission, False otherwise.
        """
        if isinstance(permission, Permission):
            permission = permission.value
        return permission in self.permissions
