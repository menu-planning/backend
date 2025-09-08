from __future__ import annotations

from typing import TYPE_CHECKING

from src.contexts.iam.core.domain.enums import Permission as EnumPermissions
from src.contexts.iam.core.domain.enums import Role as EnumRoles
from src.contexts.iam.core.domain.events import UserCreated
from src.contexts.iam.core.domain.value_objects.role import Role
from src.contexts.seedwork.domain.entity import Entity

if TYPE_CHECKING:
    from datetime import datetime

    from src.contexts.seedwork.domain.event import Event


class User(Entity):
    """IAM user aggregate root.

    Manages user identity, roles, and permissions within the IAM context.
    Provides methods for role assignment, permission checking, and user lifecycle.

    Invariants:
        - User must have at least one role (defaults to basic USER role)
        - Discarded users cannot be modified
        - Version increments on each mutation

    Attributes:
        id: Unique identifier for the user
        roles: List of Role value objects assigned to the user
        discarded: Soft delete flag
        version: Optimistic concurrency control version
        events: List of domain events raised by this aggregate

    Notes:
        Allowed transitions: ACTIVE -> DISCARDED (via delete())
    """

    def __init__(
        self,
        *,
        id: str,
        roles: list[Role] | None = None,
        discarded: bool = False,
        version: int = 1,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ) -> None:
        """Initialize user aggregate.

        Args:
            id: Unique identifier for the user (UUID v4).
            roles: List of roles to assign (defaults to basic USER role).
            discarded: Soft delete flag.
            version: Optimistic concurrency control version.
            created_at: Creation timestamp.
            updated_at: Last update timestamp.

        Notes:
            Prefer using create_user() factory method for new users.
        """
        super().__init__(
            id=id,
            discarded=discarded,
            version=version,
            created_at=created_at,
            updated_at=updated_at,
        )
        self._id = id
        self._roles: list[Role] = roles if roles else [Role.user()]
        self._discarded = discarded
        self._version = version
        self.events: list[Event] = []

    @classmethod
    def create_user(
        cls,
        id: str,
    ) -> User:
        """Create a new user and emit UserCreated event.

        Args:
            id: Unique identifier for the new user (UUID v4).

        Returns:
            New User instance with basic USER role assigned.

        Events:
            UserCreated: Emitted with the provided user_id.
        """
        event = UserCreated(
            user_id=id,
        )
        return cls(
            id=event.user_id,
        )

    @property
    def roles(
        self,
    ) -> list[Role]:
        """Return all roles assigned to this user.

        Returns:
            List of Role value objects assigned to the user.
        """
        self._check_not_discarded()
        return self._roles

    def assign_role(self, role: Role) -> None:
        """Assign a role to the user if not already present.

        Args:
            role: Role value object to assign.

        Notes:
            Increments version if role is added. No-op if role already assigned.
        """
        self._check_not_discarded()
        if role not in self._roles:
            self._roles.append(role)
            self._increment_version()

    def remove_role(self, role: Role) -> None:
        """Remove a role from the user if present.

        Args:
            role: Role value object to remove.

        Notes:
            Increments version if role is removed. No-op if role not assigned.
        """
        self._check_not_discarded()
        if role in self._roles:
            self._roles.remove(role)
            self._increment_version()

    def has_permission(self, context: str, permission: str | EnumPermissions) -> bool:
        """Check if user has a specific permission in a given context.

        Args:
            context: Domain context to check permissions in.
            permission: Permission to check (string or enum).

        Returns:
            True if any role in the context grants the permission.
        """
        self._check_not_discarded()
        if isinstance(permission, EnumPermissions):
            permission = permission.value
        for i in self._roles:
            if i.context == context and i.has_permission(permission):
                return True
        return False

    def has_role(self, context: str, role: str | EnumRoles | Role) -> bool:
        """Check if user has a specific role in a given context.

        Args:
            context: Domain context to check roles in.
            role: Role to check (string, enum, or Role value object).

        Returns:
            True if user has the specified role in the context.
        """
        self._check_not_discarded()
        if isinstance(role, Role):
            return role in self._roles
        if isinstance(role, EnumRoles):
            role = role.name.lower()
        return any(i.context == context and i.name == role for i in self._roles)

    def context_roles(self, context: str) -> list[Role]:
        """Return all roles assigned to the user in a specific context.

        Args:
            context: Domain context to filter roles by.

        Returns:
            List of Role value objects for the specified context.
        """
        self._check_not_discarded()
        return [role for role in self._roles if role.context == context]

    @property
    def version(self) -> int:
        """Return the current version number for optimistic concurrency control.

        Returns:
            Current version number (incremented on each mutation).
        """
        self._check_not_discarded()
        return self._version

    def delete(self) -> None:
        """Soft delete the user by marking as discarded.

        Notes:
            Increments version and marks user as discarded. User cannot be
            modified after deletion.
        """
        self._check_not_discarded()
        self._discard()
        self._increment_version()

    def _update_properties(self, **kwargs) -> None:
        pass
