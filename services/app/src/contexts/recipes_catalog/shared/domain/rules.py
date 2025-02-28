from __future__ import annotations
from typing import TYPE_CHECKING

from src.contexts.seedwork.shared.domain.rules import BusinessRule
from src.contexts.recipes_catalog.shared.domain.enums import Role as EnumRoles
from src.contexts.shared_kernel.domain.enums import Privacy
from src.logging.logger import logger

if TYPE_CHECKING:
    from src.contexts.recipes_catalog.shared.domain.entities.menu import Menu
    from src.contexts.shared_kernel.domain.value_objects.tag import Tag
    from src.contexts.recipes_catalog.shared.domain.value_objects.menu_meal import MenuMeal
    from src.contexts.recipes_catalog.shared.domain.value_objects.ingredient import (
    Ingredient,
)
    from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
    from src.contexts.recipes_catalog.shared.domain.entities.meal import Meal
    from src.contexts.recipes_catalog.shared.domain.entities.recipe import Recipe



class OnlyAdminUserCanCreatePublicTag(BusinessRule):
    __message = "Only administrators can create public tags"

    def __init__(self, user: "SeedUser", privacy: Privacy):
        self.user = user
        self.privacy = privacy

    def is_broken(self) -> bool:
        return self.privacy.value == Privacy.PUBLIC and not self.user.has_role(
            EnumRoles.ADMINISTRATOR
        )

    def get_message(self) -> str:
        return self.__message


class CannotHaveSameMealTypeInSameDay(BusinessRule):
    __message = "This day already has a meal of the same type"

    def __init__(self, menu: "Menu", menu_meal: "MenuMeal"):
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

    def __init__(self, ingredients: list["Ingredient"]):
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

    def __init__(self, meal: "Meal", recipe: "Recipe"):
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

    def __init__(self, tag: "Tag", root_aggregate):
        self.tag = tag
        self.root_aggregate = root_aggregate

    def is_broken(self) -> bool:
        if self.tag.author_id != self.root_aggregate.author_id:
            logger.error(f"Invalid author id: {self.tag.author_id}")
            return True

    def get_message(self) -> str:
        return self.__message


class MealMustAlreadyExistInTheMenu(BusinessRule):
    __message = "Meal must already exist in the menu"

    def __init__(self, menu_meal: "MenuMeal", menu: "Menu"):
        self.menu_meal = menu_meal
        self.menu = menu

    def is_broken(self) -> bool:
        current_meal = self.menu.filter_meals(
            week=self.menu_meal.week,
            weekday=self.menu_meal.weekday,
            meal_type=self.menu_meal.meal_type,
        )
        if not current_meal:
            logger.error(f"Meal not found on menu: {self.menu_meal}")
            return True
        if current_meal[0].meal_id != self.menu_meal.meal_id:
            logger.error(f"Invalid meal id: {current_meal[0].meal_id}")
            return True
        return False

    def get_message(self) -> str:
        return self.__message
