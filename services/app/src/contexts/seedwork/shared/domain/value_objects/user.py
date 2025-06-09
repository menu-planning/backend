from typing import Generic, TypeVar
from attrs import frozen
from src.contexts.seedwork.shared.domain.enums import Permission
from src.contexts.seedwork.shared.domain.enums import Role as EnumRoles
from src.contexts.seedwork.shared.domain.value_objects.role import SeedRole
from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject

R = TypeVar("R", bound=SeedRole)

@frozen(kw_only=True)
class SeedUser(ValueObject, Generic[R]):
    id: str
    roles: set[R]

    def has_permission(self, permission: str | Permission) -> bool:
        if isinstance(permission, Permission):
            permission = permission.value
        return any(role.has_permission(permission) for role in self.roles)

    def has_role(self, role: str | EnumRoles) -> bool:
        if isinstance(role, EnumRoles):
            role = role.name.lower()
        return any(role.name.lower() == role for role in self.roles)
