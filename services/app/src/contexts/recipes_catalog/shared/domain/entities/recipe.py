from __future__ import annotations

import uuid
from copy import deepcopy
from datetime import datetime
from functools import lru_cache, reduce
from operator import add

from src.contexts.recipes_catalog.shared.domain.rules import (
    AuthorIdOnTagMustMachRootAggregateAuthor,
    PositionsMustBeConsecutiveStartingFrom0,
)
from src.contexts.recipes_catalog.shared.domain.value_objects.ingredient import (
    Ingredient,
)
from src.contexts.recipes_catalog.shared.domain.value_objects.macro_division import (
    MacroDivision,
)
from src.contexts.recipes_catalog.shared.domain.value_objects.rating import Rating
from src.contexts.recipes_catalog.shared.domain.value_objects.product_shopping_data import ProductShoppingData
from src.contexts.seedwork.shared.domain.entitie import Entity
from src.contexts.seedwork.shared.domain.event import Event
from src.contexts.shared_kernel.domain.enums import Privacy
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.value_objects.tag import Tag


class _Recipe(Entity):
    def __init__(
        self,
        *,
        id: str,
        name: str,
        ingredients: list[Ingredient],
        instructions: str,
        author_id: str,
        meal_id: str,
        nutri_facts: NutriFacts | None = None,
        description: str | None = None,
        utensils: str | None = None,
        total_time: int | None = None,
        notes: str | None = None,
        tags: set[Tag] | None = None,
        privacy: Privacy = Privacy.PRIVATE,
        ratings: list[Rating] | None = None,
        weight_in_grams: int | None = None,
        image_url: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        discarded: bool = False,
        version: int = 1,
    ) -> None:
        """Do not call directly to create a new Recipe."""
        _Recipe.check_rule(
            PositionsMustBeConsecutiveStartingFrom0(ingredients=ingredients),
        )
        super().__init__(id=id, discarded=discarded, version=version)
        self._name = name
        self._description = description
        self._ingredients = ingredients
        self._instructions = instructions
        self._author_id = author_id
        self._meal_id = meal_id
        self._utensils = utensils
        self._total_time = total_time
        self._notes = notes
        self._tags = tags or set()
        self._privacy = privacy
        self._ratings = ratings or []
        self._nutri_facts = nutri_facts
        self._weight_in_grams = weight_in_grams
        self._image_url = image_url
        self._created_at = created_at
        self._updated_at = updated_at
        self.events: list[Event] = []

    @classmethod
    def copy_recipe(cls, *, recipe: _Recipe, user_id: str, meal_id: str) -> _Recipe:
        copy = deepcopy(recipe)
        copy._id = uuid.uuid4().hex
        copy._author_id = user_id
        copy._meal_id = meal_id
        copy._privacy = Privacy.PRIVATE
        copy._created_at = None
        copy._updated_at = None
        copy._version = 1
        copy._ratings = []
        copy.events = []
        tags = set()
        for t in recipe.tags:
            tags.add(Tag(key=t.key, value=t.value, author_id=user_id, type=t.type))
        copy._tags = tags
        return copy

    @classmethod
    def create_recipe(
        cls,
        *,
        name: str,
        ingredients: list[Ingredient],
        instructions: str,
        author_id: str,
        nutri_facts: NutriFacts,
        meal_id: str,
        description: str | None = None,
        utensils: str | None = None,
        total_time: int | None = None,
        notes: str | None = None,
        tags: set[Tag] | None = None,
        privacy: Privacy = Privacy.PRIVATE,
        weight_in_grams: int | None = None,
        image_url: str | None = None,
    ) -> "_Recipe":
        recipe_id = uuid.uuid4().hex
        recipe = cls(
            id=recipe_id,
            name=name,
            description=description,
            ingredients=ingredients,
            instructions=instructions,
            author_id=author_id,
            meal_id=meal_id,
            utensils=utensils,
            total_time=total_time,
            notes=notes,
            tags=tags,
            privacy=privacy,
            nutri_facts=nutri_facts,
            weight_in_grams=weight_in_grams,
            image_url=image_url,
        )
        return recipe
    
    @property
    def meal_id(self) -> str:
        self._check_not_discarded()
        return self._meal_id

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
    def ingredients(self) -> list[Ingredient]:
        self._check_not_discarded()
        return self._ingredients

    @ingredients.setter
    def ingredients(self, value: list[Ingredient]) -> None:
        self._check_not_discarded()
        if value is None:
            value = []
        self.check_rule(PositionsMustBeConsecutiveStartingFrom0(ingredients=value))
        self._ingredients = value
        self._increment_version()

    # def shopping_list(self, data: list[ProductShoppingData]) -> ShoppingList:
    #     self._check_not_discarded()
    #     items: list[ProductShoppingData] = []
    #     for i in self._ingredients:
    #         item = ProductShoppingData(
    #             shopping_name=i.shopping_name or i.name,
    #             store_department=i.store_department,
    #             quantity=i.quantity,
    #             unit=i.unit,
    #             recommended_brands_and_products=i.recommended_brands_and_products)
    #         if item not in items:
    #             items.append(item)
    #         else:
    #             existing_item = items.pop(items.index(item))
    #             new_item = existing_item + item
    #             items.append(new_item)
    #     return items

    @property
    def instructions(self) -> str:
        self._check_not_discarded()
        return self._instructions

    @instructions.setter
    def instructions(self, value: str) -> None:
        self._check_not_discarded()
        self._instructions = value
        self._increment_version()

    @property
    def author_id(self) -> str:
        self._check_not_discarded()
        return self._author_id

    @property
    def utensils(self) -> str | None:
        self._check_not_discarded()
        return self._utensils

    @utensils.setter
    def utensils(self, value: str | None) -> None:
        self._check_not_discarded()
        if self._utensils != value:
            self._utensils = value
            self._increment_version()

    @property
    def total_time(self) -> int | None:
        self._check_not_discarded()
        return self._total_time

    @total_time.setter
    def total_time(self, value: int | None) -> None:
        self._check_not_discarded()
        if self._total_time != value:
            self._total_time = value
            self._increment_version()

    @property
    def notes(self) -> str | None:
        self._check_not_discarded()
        return self._notes

    @notes.setter
    def notes(self, value: str | None) -> None:
        self._check_not_discarded()
        if self._notes != value:
            self._notes = value
            self._increment_version()

    @property
    def tags(self) -> set[Tag]:
        self._check_not_discarded()
        return self._tags

    @tags.setter
    def tags(self, value: set[Tag]) -> None:
        self._check_not_discarded()
        if value is None:
            value = set()
        for tag in value:
            _Recipe.check_rule(
                AuthorIdOnTagMustMachRootAggregateAuthor(tag, self),
            )
        self._tags = value
        self._increment_version()

    @property
    def privacy(self) -> Privacy:
        self._check_not_discarded()
        return self._privacy

    @privacy.setter
    def privacy(self, value: Privacy) -> None:
        self._check_not_discarded()
        self._privacy = value
        self._increment_version()

    @property
    def ratings(self) -> list[Rating] | None:
        self._check_not_discarded()
        return self._ratings

    def rate(
        self,
        user_id: str,
        taste: int,
        convenience: int,
        comment: str | None = None,
    ) -> None:
        self._check_not_discarded()
        for i in range(len(self._ratings)):
            if self._ratings[i].user_id == user_id:
                self._ratings[i] = self._ratings[i].replace(
                    taste=taste,
                    convenience=convenience,
                    comment=comment,
                )
                self._increment_version()
                return
        self._ratings.append(
            Rating(
                user_id=user_id,
                taste=taste,
                convenience=convenience,
                comment=comment,
                recipe_id=self.id,
            )
        )
        self._increment_version()

    def delete_rate(self, user_id: str) -> None:
        self._check_not_discarded()
        for i in range(len(self._ratings)):
            if self._ratings[i].user_id == user_id:
                self._ratings.pop(i)
                self._increment_version()
                return

    @property
    @lru_cache()
    def average_taste_rating(self) -> float | None:
        self._check_not_discarded()
        if self._ratings:
            taste = reduce(add, [i.taste for i in self._ratings])
            n = len(self._ratings)
            return taste / n
        return None

    @property
    @lru_cache()
    def average_convenience_rating(self) -> float | None:
        self._check_not_discarded()
        if self._ratings:
            convenience = reduce(add, [i.convenience for i in self._ratings])
            n = len(self._ratings)
            return convenience / n
        return None

    @property
    def nutri_facts(self) -> NutriFacts | None:
        self._check_not_discarded()
        return self._nutri_facts

    @nutri_facts.setter
    def nutri_facts(self, value: NutriFacts) -> None:
        self._check_not_discarded()
        if self._nutri_facts != value:
            self._nutri_facts = value
            self._increment_version()

    @property
    def weight_in_grams(self) -> int | None:
        self._check_not_discarded()
        return self._weight_in_grams

    @weight_in_grams.setter
    def weight_in_grams(self, value: int | None) -> None:
        self._check_not_discarded()
        if self._weight_in_grams != value:
            self._weight_in_grams = value
            self._increment_version()

    @property
    def calorie_density(self) -> float | None:
        self._check_not_discarded()
        if self._nutri_facts and self.weight_in_grams:
            return self._nutri_facts.calories.value / self.weight_in_grams

    @property
    def macro_division(self) -> MacroDivision | None:
        self._check_not_discarded()
        if self._nutri_facts:
            denominator = (
                self._nutri_facts.carbohydrate.value
                + self._nutri_facts.protein.value
                + self._nutri_facts.total_fat.value
            )
            return MacroDivision(
                carbohydrate=self._nutri_facts.carbohydrate.value / denominator,
                protein=self._nutri_facts.protein.value / denominator,
                fat=self._nutri_facts.total_fat.value / denominator,
            )

    @property
    def carbo_percentage(self) -> float | None:
        self._check_not_discarded()
        if self.macro_division:
            return self.macro_division.carbohydrate

    @property
    def protein_percentage(self) -> float | None:
        self._check_not_discarded()
        if self.macro_division:
            return self.macro_division.protein

    @property
    def total_fat_percentage(self) -> float | None:
        self._check_not_discarded()
        if self.macro_division:
            return self.macro_division.fat

    @property
    def image_url(self) -> str | None:
        self._check_not_discarded()
        return self._image_url

    @image_url.setter
    def image_url(self, value: str | None) -> None:
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
            f"(meal_id={self.meal_id}, id={self.id!r}, name={self.name!r}, author={self.author_id!r})"
        )

    def __hash__(self) -> int:
        return hash(self._id)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, _Recipe):
            return NotImplemented
        return self.id == other.id

    def _update_properties(self, **kwargs) -> None:
        self._check_not_discarded()
        super()._update_properties(**kwargs)

    def update_properties(self, **kwargs) -> None:
        self._check_not_discarded()
        self._update_properties(**kwargs)
