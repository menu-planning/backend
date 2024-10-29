from __future__ import annotations

import uuid
from copy import deepcopy
from datetime import datetime

from src.contexts.recipes_catalog.shared.domain.entities.recipe import Recipe
from src.contexts.recipes_catalog.shared.domain.entities.tags.category import Category
from src.contexts.recipes_catalog.shared.domain.value_objects.ingredient import (
    Ingredient,
)
from src.contexts.seedwork.shared.domain.entitie import Entity
from src.contexts.seedwork.shared.domain.event import Event
from src.contexts.shared_kernel.domain.enums import Month, Privacy
from src.contexts.shared_kernel.domain.value_objects.name_tag.allergen import Allergen
from src.contexts.shared_kernel.domain.value_objects.name_tag.cuisine import Cuisine
from src.contexts.shared_kernel.domain.value_objects.name_tag.flavor import Flavor
from src.contexts.shared_kernel.domain.value_objects.name_tag.texture import Texture
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts


class Meal(Entity):
    def __init__(
        self,
        *,
        id: str,
        name: str,
        author_id: str,
        recipe_ids: list[str] | None = None,
        menu_id: str | None = None,
        day: datetime.day | None = None,
        hour: datetime.time | None = None,
        category: Category | None = None,
        target_nutri_facts: NutriFacts | None = None,
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
        super().__init__(id=id, discarded=discarded, version=version)
        self._author_id = author_id
        self._menu = menu_id
        self._name = name
        self._day = day
        self._hour = hour
        self._category = category
        self._recipes = recipe_ids
        self._target_nutri_facts = target_nutri_facts
        self._description = description
        self._notes = notes
        self._like = like
        self._image_url = image_url
        self._created_at = created_at
        self._updated_at = updated_at
        self.events: list[Event] = []

    @classmethod
    def create_meal(
        cls,
        *,
        name: str,
        author_id: str,
        recipe_ids: list[Recipe],
        menu_id: str | None = None,
        day: datetime.day | None = None,
        hour: datetime.time | None = None,
        category: Category | None = None,
        target_nutri_facts: NutriFacts | None = None,
        description: str | None = None,
        notes: str | None = None,
        like: bool | None = None,
        image_url: str | None = None,
    ) -> "Meal":
        meal_id = uuid.uuid4().hex
        copies = []
        for meal in recipe_ids:
            copy = deepcopy(meal)
            copy._meal_id = meal_id
            copy._id = uuid.uuid4().hex
            copies.append(copy)
        meal = cls(
            id=meal_id,
            author_id=author_id,
            menu_id=menu_id,
            name=name,
            day=day,
            hour=hour,
            category=category,
            recipe_ids=copies,
            target_nutri_facts=target_nutri_facts,
            description=description,
            notes=notes,
            like=like,
            image_url=image_url,
        )
        # recipe.events.append(event)
        return meal

    @property
    def id(self) -> str:
        self._check_not_discarded()
        return self._id

    @property
    def author_id(self) -> str:
        self._check_not_discarded()
        return self._author_id

    @property
    def menu_id(self) -> str | None:
        self._check_not_discarded()
        return self._menu

    @property
    def name(self) -> str:
        self._check_not_discarded()
        return self._name

    @name.setter
    def name(self, value: str) -> None:
        self._check_not_discarded()
        if self._name != value:
            self._name = value
            self._increment_version()

    @property
    def day(self) -> datetime.day:
        self._check_not_discarded()
        return self._day

    @day.setter
    def day(self, value: datetime.day) -> None:
        self._check_not_discarded()
        if self._day != value:
            self._day = value
            self._increment_version()

    @property
    def hour(self) -> datetime.time:
        self._check_not_discarded()
        return self._hour

    @hour.setter
    def hour(self, value: datetime.time) -> None:
        self._check_not_discarded()
        if self._hour != value:
            self._hour = value
            self._increment_version()

    @property
    def category(self) -> Category:
        self._check_not_discarded()
        return self._category

    @category.setter
    def category(self, value: Category) -> None:
        self._check_not_discarded()
        if self._category != value:
            self._category = value
            self._increment_version()

    @property
    def recipe_ids(self) -> list[Recipe]:
        self._check_not_discarded()
        return [recipe for recipe in self._recipes if recipe.discarded is False]

    def create_recipe(
        self,
        *,
        name: str,
        ingredients: list[Ingredient],
        instructions: str,
        author_id: str,
        description: str | None = None,
        utensils: str | None = None,
        total_time: int | None = None,
        servings: int | None = None,
        notes: str | None = None,
        diet_types_ids: set[str] | None = None,
        categories_ids: set[str] | None = None,
        cuisine: Cuisine | None = None,
        flavor: Flavor | None = None,
        texture: Texture | None = None,
        allergens: set[Allergen] | None = None,
        meal_planning_ids: set[str] | None = None,
        privacy: Privacy = Privacy.PRIVATE,
        nutri_facts: NutriFacts | None = None,
        weight_in_grams: int | None = None,
        season: set[Month] | None = None,
        image_url: str | None = None,
    ) -> Recipe:
        self._check_not_discarded()
        recipe = Recipe.create_recipe(
            name=name,
            ingredients=ingredients,
            instructions=instructions,
            author_id=author_id,
            meal_id=self.id,
            description=description,
            utensils=utensils,
            total_time=total_time,
            servings=servings,
            notes=notes,
            diet_types_ids=diet_types_ids,
            categories_ids=categories_ids,
            cuisine=cuisine,
            flavor=flavor,
            texture=texture,
            allergens=allergens,
            meal_planning_ids=meal_planning_ids,
            privacy=privacy,
            nutri_facts=nutri_facts,
            weight_in_grams=weight_in_grams,
            season=season,
            image_url=image_url,
        )
        self._recipes.append(recipe)
        self._increment_version()
        return recipe

    def remove_recipe(self, recipe_id: str):
        self._check_not_discarded()
        for recipe in self._recipes:
            if recipe.discarded == False and recipe.id == recipe_id:
                recipe.delete()
                break
        self._increment_version()

    @property
    def target_nutri_facts(self) -> NutriFacts | None:
        self._check_not_discarded()
        return self._target_nutri_facts

    @target_nutri_facts.setter
    def target_nutri_facts(self, value: NutriFacts | None) -> None:
        self._check_not_discarded()
        self._target_nutri_facts = value
        self._increment_version()

    @property
    def nutri_facts(self) -> NutriFacts:
        self._check_not_discarded()
        return sum([recipe.nutri_facts for recipe in self._recipes])

    @property
    def description(self) -> str:
        self._check_not_discarded()
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        self._check_not_discarded()
        if self._description != value:
            self._description = value
            self._increment_version()

    @property
    def notes(self) -> str:
        self._check_not_discarded()
        return self._notes

    @notes.setter
    def notes(self, value: str) -> None:
        self._check_not_discarded()
        if self._notes != value:
            self._notes = value
            self._increment_version()

    @property
    def like(self) -> bool:
        self._check_not_discarded()
        return self._like

    def like_meal(self):
        self._check_not_discarded()
        self._like = True
        self._increment_version()

    def dislike_meal(self):
        self._check_not_discarded()
        self._like = False
        self._increment_version()

    @property
    def image_url(self) -> str:
        self._check_not_discarded()
        return self._image_url

    @image_url.setter
    def image_url(self, value: str) -> None:
        self._check_not_discarded()
        if self._image_url != value:
            self._image_url = value
            self._increment_version()

    @property
    def created_at(self) -> datetime | None:
        self._check_not_discarded()
        return self._created_at

    @property
    def updated_at(self) -> datetime | None:
        self._check_not_discarded()
        return self._updated_at

    def delete(self) -> None:
        self._check_not_discarded()
        self._discard()
        self._increment_version()

    def __repr__(self) -> str:
        self._check_not_discarded()
        return (
            f"{self.__class__.__name__}"
            f"(id={self.id!r}, name={self.name!r}, day={self.day!r}, category={self.category!r})"
        )

    def __hash__(self) -> int:
        return hash(self._id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Recipe):
            return NotImplemented
        return self.id == other.id

    def _update_properties(self, **kwargs) -> None:
        self._check_not_discarded()
        super()._update_properties(**kwargs)

    def update_properties(self, **kwargs) -> None:
        self._check_not_discarded()
        self._update_properties(**kwargs)
