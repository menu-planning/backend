from __future__ import annotations

from typing import TYPE_CHECKING

from src.contexts.recipes_catalog.core.domain.enums import Role as EnumRoles
from src.contexts.seedwork.shared.domain.rules import BusinessRule
from src.contexts.shared_kernel.domain.enums import Privacy
from src.logging.logger import structlog_logger

if TYPE_CHECKING:
    from src.contexts.recipes_catalog.core.domain.client.entities.menu import Menu
    from src.contexts.recipes_catalog.core.domain.client.value_objects.menu_meal import (
        MenuMeal,
    )
    from src.contexts.recipes_catalog.core.domain.meal.entities.recipe import _Recipe
    from src.contexts.recipes_catalog.core.domain.meal.root_aggregate.meal import Meal
    from src.contexts.recipes_catalog.core.domain.meal.value_objects.ingredient import (
        Ingredient,
    )
    from src.contexts.recipes_catalog.core.domain.shared.value_objects.user import User
    from src.contexts.shared_kernel.domain.value_objects.tag import Tag


class OnlyAdminUserCanCreatePublicTag(BusinessRule):
    __message = "Only administrators can create public tags"

    def __init__(self, user: User, privacy: Privacy):
        self.user = user
        self.privacy = privacy

    def is_broken(self) -> bool:
        return self.privacy.value == Privacy.PUBLIC and not self.user.has_role(
            EnumRoles.ADMINISTRATOR
        )

    def get_message(self) -> str:
        return self.__message


# class CannotHaveSameMealTypeInSameDay(BusinessRule):
#     __message = "This day already has a meal of the same type"

#     def __init__(self, menu: "Menu", menu_meal: "MenuMeal"):
#         self.menu = menu
#         self.menu_meal = menu_meal

#     def is_broken(self) -> bool:
#         key = (self.menu_meal.week, self.menu_meal.weekday, self.menu_meal.meal_type)
#         if key in self.menu.get_meals_dict():
#             return True
#         else:
#             return False

#     def get_message(self) -> str:
#         return self.__message


class PositionsMustBeConsecutiveStartingFromZero(BusinessRule):
    __message = "Positions must be consecutive and start from 0"

    def __init__(self, ingredients: list[Ingredient]):
        self.ingredients = ingredients

    def is_broken(self) -> bool:
        positions = [ingredient.position for ingredient in self.ingredients]
        expected_positions = list(range(len(positions)))
        if sorted(positions) != expected_positions:
            log = structlog_logger("recipes_catalog.domain.rules")
            log.warning(
                "Ingredient positions validation failed",
                rule="PositionsMustBeConsecutiveStartingFromZero",
                actual_positions=positions,
                expected_positions=expected_positions,
                ingredient_count=len(self.ingredients)
            )
            return True
        return False

    def get_message(self) -> str:
        return self.__message


class RecipeMustHaveCorrectMealIdAndAuthorId(BusinessRule):
    __message = "Recipe must have the correct meal id and author id"

    def __init__(self, meal: Meal, recipe: _Recipe):
        self.meal = meal
        self.recipe = recipe

    def is_broken(self) -> bool:
        log = structlog_logger("recipes_catalog.domain.rules")
        
        if self.recipe.meal_id != self.meal.id:
            log.warning(
                "Recipe meal ID mismatch",
                rule="RecipeMustHaveCorrectMealIdAndAuthorId",
                recipe_meal_id=self.recipe.meal_id,
                expected_meal_id=self.meal.id,
                recipe_id=getattr(self.recipe, 'id', None)
            )
            return True
            
        if self.recipe.author_id != self.meal.author_id:
            log.warning(
                "Recipe author ID mismatch",
                rule="RecipeMustHaveCorrectMealIdAndAuthorId",
                recipe_author_id=self.recipe.author_id,
                expected_author_id=self.meal.author_id,
                recipe_id=getattr(self.recipe, 'id', None),
                meal_id=self.meal.id
            )
            return True
            
        return False

    def get_message(self) -> str:
        return self.__message


class AuthorIdOnTagMustMachRootAggregateAuthor(BusinessRule):
    __message = "Author id on tag must match root aggregate author"

    def __init__(self, tag: Tag, root_aggregate):
        self.tag = tag
        self.root_aggregate = root_aggregate

    def is_broken(self) -> bool:
        if self.tag.author_id != self.root_aggregate.author_id:
            log = structlog_logger("recipes_catalog.domain.rules")
            log.warning(
                "Tag author ID mismatch with root aggregate",
                rule="AuthorIdOnTagMustMachRootAggregateAuthor",
                tag_author_id=self.tag.author_id,
                root_aggregate_author_id=self.root_aggregate.author_id,
                tag_name=getattr(self.tag, 'name', None),
                root_aggregate_type=type(self.root_aggregate).__name__
            )
            return True
        return False

    def get_message(self) -> str:
        return self.__message


class MealMustAlreadyExistInTheMenu(BusinessRule):
    __message = "Meal must already exist in the menu"

    def __init__(self, menu_meal: MenuMeal, menu: Menu):
        self.menu_meal = menu_meal
        self.menu = menu

    def is_broken(self) -> bool:
        log = structlog_logger("recipes_catalog.domain.rules")
        
        current_meal = self.menu.filter_meals(
            week=self.menu_meal.week,
            weekday=self.menu_meal.weekday,
            meal_type=self.menu_meal.meal_type,
        )
        
        if not current_meal:
            log.warning(
                "Meal not found in menu",
                rule="MealMustAlreadyExistInTheMenu",
                week=self.menu_meal.week,
                weekday=self.menu_meal.weekday,
                meal_type=self.menu_meal.meal_type,
                expected_meal_id=self.menu_meal.meal_id,
                menu_id=getattr(self.menu, 'id', None)
            )
            return True
            
        if current_meal[0].meal_id != self.menu_meal.meal_id:
            log.warning(
                "Meal ID mismatch in menu",
                rule="MealMustAlreadyExistInTheMenu",
                found_meal_id=current_meal[0].meal_id,
                expected_meal_id=self.menu_meal.meal_id,
                week=self.menu_meal.week,
                weekday=self.menu_meal.weekday,
                meal_type=self.menu_meal.meal_type
            )
            return True
            
        return False

    def get_message(self) -> str:
        return self.__message
