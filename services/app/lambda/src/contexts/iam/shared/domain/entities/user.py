from __future__ import annotations

from src.contexts.iam.shared.domain.enums import Permission as EnumPermissions
from src.contexts.iam.shared.domain.enums import Role as EnumRoles
from src.contexts.iam.shared.domain.events import UserCreated
from src.contexts.iam.shared.domain.value_objects.role import Role
from src.contexts.seedwork.shared.domain.entitie import Entity
from src.contexts.seedwork.shared.domain.event import Event


class User(Entity):
    def __init__(
        self,
        id: str,
        roles: list[Role] | None = None,
        discarded: bool = False,
        version: int = 1,
    ) -> None:
        """Do not call directly to create a new User."""
        super().__init__(id=id, discarded=discarded, version=version)
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
        event = UserCreated(
            user_id=id,
        )
        user = cls(
            id=id,
        )
        user.events.append(event)
        return user

    @property
    def id(self) -> str:
        self._check_not_discarded()
        return self._id

    @property
    def roles(
        self,
    ) -> list[Role]:
        self._check_not_discarded()
        return self._roles

    def assign_role(self, role: Role) -> None:
        self._check_not_discarded()
        if role not in self._roles:
            self._roles.append(role)
            self._increment_version()

    def remove_role(self, role: Role) -> None:
        self._check_not_discarded()
        if role in self._roles:
            self._roles.remove(role)
            self._increment_version()

    def has_permission(self, context: str, permission: str | EnumPermissions) -> bool:
        self._check_not_discarded()
        if isinstance(permission, EnumPermissions):
            permission = permission.value
        for i in self._roles:
            if i.context == context and i.has_permission(permission):
                return True
        return False

    def has_role(self, context: str, role: str | EnumRoles | Role) -> bool:
        self._check_not_discarded()
        if isinstance(role, Role):
            return role in self._roles
        if isinstance(role, EnumRoles):
            role = role.name.lower()
        for i in self._roles:
            if i.context == context and i.name == role:
                return True
        return False

    def context_roles(self, context: str) -> list[Role]:
        self._check_not_discarded()
        return [role for role in self._roles if role.context == context]

    @property
    def version(self) -> int:
        self._check_not_discarded()
        return self._version

    def delete(self) -> None:
        self._check_not_discarded()
        self._discard()
        self._increment_version()

    def _update_properties(self, **kwargs) -> None:
        return NotImplemented
