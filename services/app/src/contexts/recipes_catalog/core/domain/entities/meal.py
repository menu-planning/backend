from __future__ import annotations

from functools import lru_cache
from typing import Any
import uuid
from datetime import datetime

from src.contexts.recipes_catalog.core.domain.entities.recipe import _Recipe
from src.contexts.recipes_catalog.core.domain.events.meal.meal_deleted import (
    MealDeleted,
)
from src.contexts.recipes_catalog.core.domain.events.meal.updated_attr_that_reflect_on_menu import (
    UpdatedAttrOnMealThatReflectOnMenu,
)
from src.contexts.recipes_catalog.core.domain.rules import (
    AuthorIdOnTagMustMachRootAggregateAuthor,
    RecipeMustHaveCorrectMealIdAndAuthorId,
)
from src.contexts.recipes_catalog.core.domain.value_objects.macro_division import (
    MacroDivision,
)
from src.contexts.seedwork.shared.domain.entity import Entity
from src.contexts.seedwork.shared.domain.event import Event
from src.contexts.shared_kernel.domain.enums import Privacy
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.value_objects.tag import Tag
from src.logging.logger import logger

def event_to_updated_menu_on_meal_creation(
    menu_id: str | None,
    meal_id: str,
    message: str,
) -> list[Event]:
    if not menu_id:
        return []
    return [UpdatedAttrOnMealThatReflectOnMenu(menu_id=menu_id, meal_id=meal_id, message=message)]


class Meal(Entity):
    def __init__(
        self,
        *,
        id: str,
        name: str,
        author_id: str,
        menu_id: str | None = None,
        recipes: list[_Recipe] | None = None,
        tags: set[Tag] | None = None,
        description: str | None = None,
        notes: str | None = None,
        like: bool | None = None,
        image_url: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        discarded: bool = False,
        version: int = 1,
    ) -> None:
        """Do not call directly to create a new Meal."""
        super().__init__(id=id, discarded=discarded, version=version, created_at=created_at, updated_at=updated_at)
        self._author_id = author_id
        self._name = name
        self._menu_id = menu_id
        self._recipes = recipes if recipes else []
        self._tags = tags if tags else set()
        self._description = description
        self._notes = notes
        self._like = like
        self._image_url = image_url
        self.events: list[Event] = []

    @classmethod
    def create_meal(
        cls,
        *,
        name: str,
        author_id: str,
        meal_id: str,
        menu_id: str,
        recipes: list[_Recipe] | None = None,
        tags: set[Tag] | None = None,
        description: str | None = None,
        notes: str | None = None,
        image_url: str | None = None,
    ) -> "Meal":
        new_recipes = []
        if recipes:
            for recipe in recipes:
                copy = _Recipe.copy_recipe(
                    recipe=recipe, user_id=author_id, meal_id=meal_id
                )
                new_recipes.append(copy)
        else:
            recipes = []
        meal = cls(
            id=meal_id,
            name=name,
            author_id=author_id,
            menu_id=menu_id,
            recipes=new_recipes,
            tags=tags,
            description=description,
            notes=notes,
            image_url=image_url,
        )
        meal.events = event_to_updated_menu_on_meal_creation(menu_id, meal_id, "Created new meal")
        return meal

    @classmethod
    def copy_meal(
        cls,
        meal: Meal,
        id_of_user_coping_meal: str,
        id_of_target_menu: str | None = None,
    ) -> "Meal":
        name = meal.name
        description = meal.description
        notes = meal.notes
        image_url = meal.image_url
        meal_id = uuid.uuid4().hex
        author_id = id_of_user_coping_meal
        new_recipes = []
        new_tags = []
        for r in meal.recipes:
            copy = _Recipe.copy_recipe(
                recipe=r, user_id=id_of_user_coping_meal, meal_id=meal_id
            )
            new_recipes.append(copy)
        for t in meal.tags:
            copy = Tag(
                key=t.key, value=t.value, author_id=id_of_user_coping_meal, type=t.type
            )
            new_tags.append(copy)
        meal = cls(
            id=meal_id,
            author_id=author_id,
            name=name,
            menu_id=id_of_target_menu,
            recipes=new_recipes,
            description=description,
            tags=set(new_tags),
            notes=notes,
            image_url=image_url,
        )
        meal.events = event_to_updated_menu_on_meal_creation(id_of_target_menu, meal_id, "Copied meal")
        return meal

    def add_event_to_updated_menu(self, message: str = "") -> None:
        if self.menu_id:
            # Find any existing UpdatedAttrOnMealThatReflectOnMenu event
            existing_event = None
            for event in self.events:
                if isinstance(event, UpdatedAttrOnMealThatReflectOnMenu):
                    existing_event = event
                    break

            # Create new message by concatenating old and new if exists
            new_message = message
            if existing_event and existing_event.message:
                new_message = f"{existing_event.message}; {message}" if message else existing_event.message

            # Create new event
            event = UpdatedAttrOnMealThatReflectOnMenu(
                menu_id=self.menu_id,
                meal_id=self.id,
                message=new_message
            )

            # Replace existing event or add new one
            if existing_event:
                self.events[self.events.index(existing_event)] = event
            elif event not in self.events:
                self.events.append(event)

    @property
    def author_id(self) -> str:
        self._check_not_discarded()
        return self._author_id

    @property
    def name(self) -> str:
        self._check_not_discarded()
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._check_not_discarded()
        if self._name != value:
            self._name = value
            self.add_event_to_updated_menu(f"Updated meal name to: {value}")
            self._increment_version()

    @property
    def menu_id(self) -> str | None:
        self._check_not_discarded()
        return self._menu_id

    @menu_id.setter
    def menu_id(self, value: str | None) -> None:
        self._check_not_discarded()
        if self._menu_id != value:
            self._menu_id = value
            self._increment_version()

    @property
    def products_ids(self) -> set[str]:
        self._check_not_discarded()
        products_ids = set()
        for recipe in self.recipes:
            for ingredient in recipe.ingredients:
                if ingredient.product_id:
                    products_ids.add(ingredient.product_id)
        return products_ids

    @property
    def total_time(self) -> int | None:
        self._check_not_discarded()
        times = [recipe.total_time for recipe in self.recipes] if self.recipes else []
        times = [time for time in times if time]
        return max(times) if times else None

    @property
    def recipes(self) -> list[_Recipe]:
        self._check_not_discarded()
        return [recipe for recipe in self._recipes if not recipe.discarded]

    @recipes.setter
    def recipes(self, value: list[_Recipe]) -> None:
        self._check_not_discarded()
        type(self).nutri_facts.fget.cache_clear() # type: ignore
        type(self).macro_division.fget.cache_clear() # type: ignore
        new_recipes = []
        for recipe in value:
            try:
                _Recipe.check_rule(
                    RecipeMustHaveCorrectMealIdAndAuthorId(meal=self, recipe=recipe),
                )
            except Exception:
                new_recipes.append(_Recipe.copy_recipe(recipe=recipe, user_id=self.author_id, meal_id=self.id))
            else:
                new_recipes.append(recipe)
        value = new_recipes
        for recipe in value:
            _Recipe.check_rule(
                RecipeMustHaveCorrectMealIdAndAuthorId(meal=self, recipe=recipe),
            )
        self.add_event_to_updated_menu("Updated meal recipes")
        if self._recipes == []:
            self._recipes = value
            self._increment_version()
            return
        for r in value:
            if r not in self.recipes:
                self._recipes.append(r)
        for i, recipe in enumerate(self._recipes):
            if recipe.discarded:
                continue
            if recipe not in value:
                logger.debug(f"Recipe {recipe.id} not in value and will be discarded.")
                recipe._discard()
            else:
                for r in value:
                    if r == recipe:
                        # Update the list element at index i.
                        self._recipes[i] = r
                        r._version = recipe.version
                        r._increment_version()
                        break
        self._increment_version()

    def get_recipe_by_id(self, recipe_id: str) -> _Recipe | None:
        self._check_not_discarded()
        for recipe in self.recipes:
            if recipe.id == recipe_id:
                return recipe

    def copy_recipes(self, recipes: list[_Recipe]) -> None:
        self._check_not_discarded()
        for recipe in recipes:
            copied = _Recipe.copy_recipe(
                recipe=recipe, user_id=self.author_id, meal_id=self.id
            )
            self._recipes.append(copied)
        self.add_event_to_updated_menu("Copied recipes to meal")
        self._increment_version()

    # @property
    # def shopping_list(self) -> list[ShoppingItem]:
    #     self._check_not_discarded()
    #     items: list[ShoppingItem] = []
    #     for recipe in self.recipes:
    #         for i in recipe.shopping_list:
    #             if i not in items:
    #                 items.append(i)
    #             else:
    #                 existing_item = items.pop(items.index(i))
    #                 new_item = existing_item + i
    #                 items.append(new_item)
    #     return items

    @property
    def recipes_tags(self) -> set[Tag]:
        self._check_not_discarded()
        tags = set()
        for recipe in self.recipes:
            for tag in recipe.tags:
                tags.add(tag)
        return tags

    @property
    def tags(self) -> set[Tag]:
        self._check_not_discarded()
        return self._tags

    @tags.setter
    def tags(self, value: set[Tag]) -> None:
        self._check_not_discarded()
        for tag in value:
            Meal.check_rule(
                AuthorIdOnTagMustMachRootAggregateAuthor(tag, self),
            )
        self._tags = value
        self._increment_version()

    @property
    @lru_cache()
    def nutri_facts(self) -> NutriFacts:
        self._check_not_discarded()
        nutri_facts = NutriFacts()
        for recipe in self.recipes:
            if recipe.nutri_facts:
                nutri_facts += recipe.nutri_facts
        return nutri_facts

    @property
    def calorie_density(self) -> float | None:
        self._check_not_discarded()
        if self.nutri_facts and self.nutri_facts.calories.value is not None and self.weight_in_grams:
            return (self.nutri_facts.calories.value / self.weight_in_grams) * 100
        return None

    @property
    @lru_cache()
    def macro_division(self) -> MacroDivision | None:
        self._check_not_discarded()
        if not self.nutri_facts:
            return None
            
        carb = self.nutri_facts.carbohydrate.value
        protein = self.nutri_facts.protein.value
        fat = self.nutri_facts.total_fat.value
        
        if carb is None or protein is None or fat is None:
            return None
            
        denominator = carb + protein + fat
        if denominator == 0:
            return None
            
        return MacroDivision(
            carbohydrate=(carb / denominator) * 100,
            protein=(protein / denominator) * 100,
            fat=(fat / denominator) * 100,
        )

    @property
    def carbo_percentage(self) -> float | None:
        self._check_not_discarded()
        if self.macro_division:
            return self.macro_division.carbohydrate if self.macro_division else None

    @property
    def protein_percentage(self) -> float | None:
        self._check_not_discarded()
        if self.macro_division:
            return self.macro_division.protein if self.macro_division else None

    @property
    def total_fat_percentage(self) -> float | None:
        self._check_not_discarded()
        if self.macro_division:
            return self.macro_division.fat if self.macro_division else None

    @property
    def weight_in_grams(self) -> int:
        self._check_not_discarded()
        return sum(
            [
                recipe.weight_in_grams
                for recipe in self.recipes
                if recipe.weight_in_grams
            ]
        )

    @property
    def description(self) -> str | None:
        self._check_not_discarded()
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        self._check_not_discarded()
        if self._description != value:
            self._description = value
            self._increment_version()

    @property
    def notes(self) -> str | None:
        self._check_not_discarded()
        return self._notes

    @notes.setter
    def notes(self, value: str) -> None:
        self._check_not_discarded()
        if self._notes != value:
            self._notes = value
            self._increment_version()

    @property
    def like(self) -> bool | None:
        self._check_not_discarded()
        return self._like

    @like.setter
    def like(self, value: bool | None) -> None:
        self._check_not_discarded()
        if self._like != value:
            self._like = value
            self._increment_version()

    @property
    def image_url(self) -> str | None:
        self._check_not_discarded()
        return self._image_url

    @image_url.setter
    def image_url(self, value: str) -> None:
        self._check_not_discarded()
        if self._image_url != value:
            self._image_url = value
            self._increment_version()

    def delete(self) -> None:
        self._check_not_discarded()
        for recipe in self._recipes:
            recipe.delete()
        if self.menu_id:
            self.events.append(
                MealDeleted(
                    meal_id=self.id,
                    menu_id=self.menu_id,
                )
            )
        self._discard()
        self._increment_version()

    def __repr__(self) -> str:
        self._check_not_discarded()
        return f"{self.__class__.__name__}(id={self.id!r}, name={self.name!r})"

    def __hash__(self) -> int:
        return hash(self._id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Meal):
            return NotImplemented
        return self.id == other.id

    def _update_properties(self, **kwargs) -> None:
        self._check_not_discarded()
        super()._update_properties(**kwargs)

    def update_properties(self, **kwargs) -> None:
        self._check_not_discarded()
        initial_nutri_facts = self.nutri_facts
        if "recipes" in kwargs:
            self.recipes = kwargs.pop("recipes")
            self._version -= 1
        if self.menu_id:
            event = UpdatedAttrOnMealThatReflectOnMenu(
                menu_id=self.menu_id,
                meal_id=self.id,
                message="Updated meal properties"
            )
            if (initial_nutri_facts != self.nutri_facts or self.name != kwargs.get(
                "name", self.name) and event not in self.events
            ):
                self.add_event_to_updated_menu("Updated meal properties affecting menu")
        self._update_properties(**kwargs)

    ### This is the part of the code that deals with the children recipes. ###
    def copy_recipe(
        self,
        recipe: _Recipe,
    ) -> None:
        """
        Create a new Recipe and add it to the Meal.
        """
        self._check_not_discarded()
        copied = _Recipe.copy_recipe(recipe=recipe, user_id=self.author_id, meal_id=self.id)
        self._recipes.append(copied)
        self.add_event_to_updated_menu("Added copied recipe to meal")
        self._increment_version()

    def create_recipe(
        self,
        **kwargs: Any,
    ) -> None:
        """
        Create a new Recipe and add it to the Meal.
        """
        self._check_not_discarded()
        recipe = _Recipe.create_recipe(**kwargs)
        self._recipes.append(recipe)
        self.add_event_to_updated_menu("Created new recipe in meal")
        self._increment_version()

    def delete_recipe(self, recipe_id: str):
        self._check_not_discarded()
        for recipe in self._recipes:
            if recipe.discarded == False and recipe.id == recipe_id:
                recipe.delete()
                break
        self.add_event_to_updated_menu(f"Deleted recipe {recipe_id} from meal")
        self._increment_version()

    def update_recipes(self, updates: dict[str: 'recipe_id', dict[str, Any]: 'kwargs']): # type: ignore
        self._check_not_discarded()
        for recipe_id, kwargs in updates.items():
            recipe = self.get_recipe_by_id(recipe_id)
            if recipe:
                recipe.update_properties(**kwargs)
        self.add_event_to_updated_menu("Updated recipes in meal")
        self._increment_version()

    def rate_recipe(
        self,
        recipe_id: str,
        user_id: str,
        taste: int,
        convenience: int,
        comment: str | None = None,
    ):
        self._check_not_discarded()
        for recipe in self._recipes:
            if recipe.discarded == False and recipe.id == recipe_id:
                recipe.rate(
                    user_id=user_id,
                    taste=taste,
                    convenience=convenience,
                    comment=comment,
                )
                break
        self._increment_version()

    def delete_rate(self, recipe_id: str, user_id: str):
        self._check_not_discarded()
        for recipe in self._recipes:
            if recipe.discarded == False and recipe.id == recipe_id:
                recipe.delete_rate(user_id=user_id)
                break
        self._increment_version()

