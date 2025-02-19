from typing import TYPE_CHECKING

from src.contexts.recipes_catalog.shared.domain.enums import Role as EnumRoles
from src.contexts.recipes_catalog.shared.domain.value_objects.ingredient import (
    Ingredient,
)
from src.contexts.recipes_catalog.shared.domain.value_objects.menu_meal import MenuMeal
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

    def __init__(self, menu: "Menu", menu_meal: MenuMeal):
        self.menu = menu
        self.menu_meal = menu_meal

    def is_broken(self) -> bool:
        key = (self.menu_meal.week, self.menu_meal.weekday, self.menu_meal.meal_type)
        if key in self.menu.meals:
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


class RecipeMustHaveCorrectMealIdAndAuthorId(BusinessRule):
    __message = "Recipe must have the correct meal id and author id"

    def __init__(self, meal, recipe):
        self.meal = meal
        self.recipe = recipe

    def is_broken(self) -> bool:
        if self.recipe.meal_id != self.meal.id:
            logger.error(f"Invalid meal id: {self.recipe.meal_id}")
            return True
        if self.recipe.author_id != self.meal.author_id:
            logger.error(f"Invalid author id: {self.recipe.author_id}")
            return True

    def get_message(self) -> str:
        return self.__message


class AuthorIdOnTagMustMachRootAggregateAuthor(BusinessRule):
    __message = "Author id on tag must match root aggregate author"

    def __init__(self, tag, root_aggregate):
        self.tag = tag
        self.root_aggregate = root_aggregate

    def is_broken(self) -> bool:
        if self.tag.author_id != self.root_aggregate.author_id:
            logger.error(f"Invalid author id: {self.tag.author_id}")
            return True

    def get_message(self) -> str:
        return self.__message
