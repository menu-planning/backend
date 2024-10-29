from __future__ import annotations

import uuid
from datetime import datetime

from src.contexts.recipes_catalog.shared.domain.value_objects.ingredient import (
    Ingredient,
)
from src.contexts.recipes_catalog.shared.domain.value_objects.rating import Rating
from src.contexts.seedwork.shared.domain.entitie import Entity
from src.contexts.seedwork.shared.domain.event import Event
from src.contexts.shared_kernel.domain.enums import Month, Privacy
from src.contexts.shared_kernel.domain.value_objects.name_tag.allergen import Allergen
from src.contexts.shared_kernel.domain.value_objects.name_tag.cuisine import Cuisine
from src.contexts.shared_kernel.domain.value_objects.name_tag.flavor import Flavor
from src.contexts.shared_kernel.domain.value_objects.name_tag.texture import Texture
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts


class Menu(Entity):
    def __init__(
        self,
        *,
        id: str,
        client: Client,
        name: str,
        ingredients: list[Ingredient],
        instructions: str,
        author_id: str,
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
        ratings: list[Rating] | None = None,
        nutri_facts: NutriFacts | None = None,
        weight_in_grams: int | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        discarded: bool = False,
        version: int = 1,
    ) -> None:
        """Do not call directly to create a new Recipe."""
        super().__init__(id=id, discarded=discarded, version=version)
        self._name = name
        self._description = description
        self._ingredients = ingredients
        self._instructions = instructions
        self._author_id = author_id
        self._utensils = utensils
        self._total_time = total_time
        self._servings = servings
        self._notes = notes
        self._diet_types_ids = diet_types_ids or set()
        self._categories_ids = categories_ids or set()
        self._cuisine = cuisine
        self._flavor = flavor
        self._texture = texture
        self._allergens = allergens or set()
        self._meal_planning_ids = meal_planning_ids or set()
        self._privacy = privacy
        self._ratings = ratings or []
        self._nutri_facts = nutri_facts
        self._weight_in_g = weight_in_grams
        self._season = season or set()
        self._image_url = image_url
        self._created_at = created_at
        self._updated_at = updated_at
        self.events: list[Event] = []

    @classmethod
    def create_recipe(
        cls,
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
    ) -> "Recipe":
        id = uuid.uuid4().hex
        recipe = cls(
            id=id,
            name=name,
            description=description,
            ingredients=ingredients,
            instructions=instructions,
            author_id=author_id,
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
        recipe.events.append(event)
        return recipe

    @property
    def id(self) -> str:
        self._check_not_discarded()
        return self._id

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
    def description(self) -> str:
        self._check_not_discarded()
        return self._description

    @description.setter
    def description(self, value: str) -> None:
        self._check_not_discarded()
        if self._description != value:
            self._description = value
            self._increment_version()
