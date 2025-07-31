from __future__ import annotations

from attrs import frozen
from src.contexts.client_onboarding.core.domain.enums import Role as EnumRoles
from src.contexts.seedwork.shared.domain.value_objects.role import SeedRole


@frozen(hash=True)
class Role(SeedRole):
    @classmethod
    def form_administrator(cls) -> Role:
        return Role(
            name=EnumRoles.FORM_ADMINISTRATOR.name.lower(),
            permissions=frozenset(EnumRoles.FORM_ADMINISTRATOR.permissions),
        )

    @classmethod
    def form_manager(cls) -> Role:
        return Role(
            name=EnumRoles.FORM_MANAGER.name.lower(),
            permissions=frozenset(EnumRoles.FORM_MANAGER.permissions),
        )

    @classmethod
    def form_viewer(cls) -> Role:
        return Role(
            name=EnumRoles.FORM_VIEWER.name.lower(),
            permissions=frozenset(EnumRoles.FORM_VIEWER.permissions),
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