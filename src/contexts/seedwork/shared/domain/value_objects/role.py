from attrs import field, frozen
from src.contexts.seedwork.shared.domain.enums import Permission
from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject


@frozen(hash=True)
class SeedRole(ValueObject):
    name: str
    permissions: frozenset[str] = field(factory=frozenset)

    def has_permission(self, permission: str | Permission) -> bool:
        if isinstance(permission, Permission):
            permission = permission.value
        return permission in self.permissions
