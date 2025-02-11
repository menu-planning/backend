from typing import TYPE_CHECKING

from src.contexts.recipes_catalog.shared.domain.enums import Role as EnumRoles
from src.contexts.recipes_catalog.shared.domain.value_objects.ingredient import (
    Ingredient,
)
from src.contexts.recipes_catalog.shared.domain.value_objects.menu_item import MenuItem
from src.contexts.seedwork.shared.domain.rules import BusinessRule
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.shared_kernel.domain.enums import Privacy
from src.logging.logger import logger

if TYPE_CHECKING:
    from src.contexts.recipes_catalog.shared.domain.entities.menu import Menu
#     from src.contexts.shared_kernel.domain.value_objects.name_tag.meal_type import (
#         MealType,
#     )
#     from src.contexts.shared_kernel.domain.enums import Weekday


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

    def __init__(self, menu: "Menu", menu_item: MenuItem):
        self.menu = menu
        self.menu_item = menu_item

    def is_broken(self) -> bool:
        key = (self.menu_item.week, self.menu_item.weekday, self.menu_item.meal_type)
        if key in self.menu.items:
            return True
        else:
            return False

    def get_message(self) -> str:
        return self.__message


class PositionsMustBeConsecutiveStartingFrom1(BusinessRule):
    __message = "Positions must be consecutive and start from 1"

    def __init__(self, ingredients: list[Ingredient]):
        self.ingredients = ingredients

    def is_broken(self) -> bool:
        positions = [ingredient.position for ingredient in self.ingredients]
        if sorted(positions) != list(range(1, len(positions) + 1)):
            logger.error(f"Invalid positions: {positions}")
            return True

    def get_message(self) -> str:
        return self.__message
