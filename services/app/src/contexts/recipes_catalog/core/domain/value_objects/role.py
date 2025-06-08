from __future__ import annotations

from attrs import frozen
from src.contexts.recipes_catalog.core.domain.enums import Role as EnumRoles
from src.contexts.seedwork.shared.domain.value_objects.role import SeedRole as SeedRole


@frozen(hash=True)
class Role(SeedRole):
    @classmethod
    def administrator(cls) -> Role:
        return Role(
            name=EnumRoles.ADMINISTRATOR.name.lower(),
            permissions=frozenset(EnumRoles.ADMINISTRATOR.permissions),
        )

    @classmethod
    def user_manager(cls) -> Role:
        return Role(
            name=EnumRoles.USER_MANAGER.name.lower(),
            permissions=frozenset(EnumRoles.USER_MANAGER.permissions),
        )

    @classmethod
    def recipe_manager(cls) -> Role:
        return Role(
            name=EnumRoles.RECIPE_MANAGER.name.lower(),
            permissions=frozenset(EnumRoles.RECIPE_MANAGER.permissions),
        )

    @classmethod
    def auditor(cls) -> Role:
        return Role(
            name=EnumRoles.AUDITOR.name.lower(),
            permissions=frozenset(EnumRoles.AUDITOR.permissions),
        )

    @classmethod
    def user(cls) -> Role:
        return Role(
            name=EnumRoles.USER.name.lower(),
            permissions=frozenset(EnumRoles.USER.permissions),
        )

    @classmethod
    def developer(cls) -> Role:
        return Role(
            name=EnumRoles.DEVELOPER.name.lower(),
            permissions=frozenset(EnumRoles.DEVELOPER.permissions),
        )

    @classmethod
    def support_staff(cls) -> Role:
        return Role(
            name=EnumRoles.SUPPORT_STAFF.name.lower(),
            permissions=frozenset(EnumRoles.SUPPORT_STAFF.permissions),
        )
