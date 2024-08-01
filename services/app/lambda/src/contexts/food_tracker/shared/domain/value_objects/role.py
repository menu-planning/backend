from __future__ import annotations

from attrs import frozen
from src.contexts.food_tracker.shared.domain.enums import Role as EnumRoles
from src.contexts.seedwork.shared.domain.value_objects.role import SeedRole as SeedRole


@frozen(hash=True)
class Role(SeedRole):
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
    def house_manager(cls) -> Role:
        return Role(
            name=EnumRoles.HOUSE_MANAGER.name.lower(),
            permissions=EnumRoles.HOUSE_MANAGER.permissions,
        )

    @classmethod
    def item_manager(cls) -> Role:
        return Role(
            name=EnumRoles.ITEM_MANAGER.name.lower(),
            permissions=EnumRoles.ITEM_MANAGER.permissions,
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
