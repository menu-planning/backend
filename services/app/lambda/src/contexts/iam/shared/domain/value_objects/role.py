from __future__ import annotations

from attrs import field, frozen
from src.contexts.iam.shared.domain.enums import Permission as EnumPermissions
from src.contexts.iam.shared.domain.enums import Role as EnumRoles
from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject


@frozen(hash=True)
class Role(ValueObject):
    name: str
    context: str = field(default="IAM")
    permissions: list[str] = field(factory=list, hash=False)

    def has_permission(self, permission: str | EnumPermissions) -> bool:
        if isinstance(permission, EnumPermissions):
            permission = permission.value
        return permission in self.permissions

    @classmethod
    def administrator(cls) -> Role:
        return Role(
            name=EnumRoles.ADMINISTRATOR.name.lower(),
            permissions=EnumRoles.ADMINISTRATOR.permissions,
        )

    @classmethod
    def user_manager(cls) -> Role:
        return Role(
            name=EnumRoles.USER_MANAGER.name.lower(),
            permissions=EnumRoles.USER_MANAGER.permissions,
        )

    @classmethod
    def role_manager(cls) -> Role:
        return Role(
            name=EnumRoles.ROLE_MANAGER.name.lower(),
            permissions=EnumRoles.ROLE_MANAGER.permissions,
        )

    @classmethod
    def auditor(cls) -> Role:
        return Role(
            name=EnumRoles.AUDITOR.name.lower(),
            permissions=EnumRoles.AUDITOR.permissions,
        )

    @classmethod
    def user(cls) -> Role:
        return Role(
            name=EnumRoles.USER.name.lower(),
            permissions=EnumRoles.USER.permissions,
        )

    @classmethod
    def developer(cls) -> Role:
        return Role(
            name=EnumRoles.DEVELOPER.name.lower(),
            permissions=EnumRoles.DEVELOPER.permissions,
        )

    @classmethod
    def support_staff(cls) -> Role:
        return Role(
            name=EnumRoles.SUPPORT_STAFF.name.lower(),
            permissions=EnumRoles.SUPPORT_STAFF.permissions,
        )

    def __str__(self):
        return f"<Role {self.name}>"

    def __repr__(self):
        return f"<Role {self.name}>"
