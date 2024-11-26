from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.contexts.recipes_catalog.shared.domain.value_objects.menu_item import (
        MenuItem,
    )
    from src.contexts.recipes_catalog.shared.domain.entities.menu import Menu
    from src.contexts.shared_kernel.domain.value_objects.name_tag.meal_type import (
        MealType,
    )
    from src.contexts.shared_kernel.domain.enums import Weekday

from src.contexts.recipes_catalog.shared.domain.enums import Role as EnumRoles
from src.contexts.seedwork.shared.domain.rules import BusinessRule
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.shared_kernel.domain.enums import Privacy


class OnlyAdminUserCanCreatePublicTag(BusinessRule):
    __message = "Only administrators can create public tags"

    def __init__(self, user: SeedUser, privacy: Privacy):
        self.user = user
        self.privacy = privacy

    def is_broken(self) -> bool:
        return self.privacy == Privacy.PUBLIC and not self.user.has_role(
            EnumRoles.ADMINISTRATOR
        )

    def get_message(self) -> str:
        return self.__message


class CannotHaveSameMealTypeInSameDay(BusinessRule):
    __message = "This day already has a meal of the same type"

    def __init__(
        self, menu: "Menu", key: dict[tuple[int, Weekday, MealType], MenuItem]
    ):
        self.menu = menu
        self.key = key

    def is_broken(self) -> bool:
        if self.key in self.menu.items:
            return True
        else:
            return False

    def get_message(self) -> str:
        return self.__message
