from __future__ import annotations

import uuid
from copy import deepcopy
from datetime import datetime
from functools import lru_cache, reduce, cached_property
from operator import add
from typing import Any

from src.contexts.recipes_catalog.core.domain.rules import (
    AuthorIdOnTagMustMachRootAggregateAuthor,
    PositionsMustBeConsecutiveStartingFromZero,
    RecipeMustHaveCorrectMealIdAndAuthorId,
)
from src.contexts.recipes_catalog.core.domain.meal.value_objects.ingredient import Ingredient
from src.contexts.recipes_catalog.core.domain.meal.value_objects.rating import Rating
from src.contexts.recipes_catalog.core.domain.meal.value_objects.macro_division import MacroDivision
from src.contexts.recipes_catalog.core.domain.shared.product_shopping_data import ProductShoppingData
from src.contexts.seedwork.shared.domain.entity import Entity
from src.contexts.seedwork.shared.domain.event import Event
from src.contexts.shared_kernel.domain.enums import Privacy
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.value_objects.tag import Tag
from src.logging.logger import logger


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
            PositionsMustBeConsecutiveStartingFromZero(ingredients=ingredients),
        )
        super().__init__(id=id, discarded=discarded, version=version, created_at=created_at, updated_at=updated_at)
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
        recipe_id: str | None = None,
        description: str | None = None,
        utensils: str | None = None,
        total_time: int | None = None,
        notes: str | None = None,
        tags: set[Tag] | None = None,
        privacy: Privacy = Privacy.PRIVATE,
        weight_in_grams: int | None = None,
        image_url: str | None = None,
    ) -> "_Recipe":
        recipe = cls(
            id=recipe_id if recipe_id else uuid.uuid4().hex,
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

    def _set_name(self, value: str) -> None:
        """Protected setter for name. Can only be called through Meal aggregate."""
        self._check_not_discarded()
        if self._name != value:
            self._name = value
            self._increment_version()

    @property
    def description(self) -> str | None:
        self._check_not_discarded()
        return self._description

    def _set_description(self, value: str) -> None:
        """Protected setter for description. Can only be called through Meal aggregate."""
        self._check_not_discarded()
        if self._description != value:
            self._description = value
            self._increment_version()

    @property
    def ingredients(self) -> list[Ingredient]:
        self._check_not_discarded()
        return self._ingredients

    def _set_ingredients(self, value: list[Ingredient]) -> None:
        """Protected setter for ingredients. Can only be called through Meal aggregate."""
        self._check_not_discarded()
        if value is None:
            value = []
        self.check_rule(PositionsMustBeConsecutiveStartingFromZero(ingredients=value))
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

    def _set_instructions(self, value: str) -> None:
        """Protected setter for instructions. Can only be called through Meal aggregate."""
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

    def _set_utensils(self, value: str | None) -> None:
        """Protected setter for utensils. Can only be called through Meal aggregate."""
        self._check_not_discarded()
        if self._utensils != value:
            self._utensils = value
            self._increment_version()

    @property
    def total_time(self) -> int | None:
        self._check_not_discarded()
        return self._total_time

    def _set_total_time(self, value: int | None) -> None:
        """Protected setter for total_time. Can only be called through Meal aggregate."""
        self._check_not_discarded()
        if self._total_time != value:
            self._total_time = value
            self._increment_version()

    @property
    def notes(self) -> str | None:
        self._check_not_discarded()
        return self._notes

    def _set_notes(self, value: str | None) -> None:
        """Protected setter for notes. Can only be called through Meal aggregate."""
        self._check_not_discarded()
        if self._notes != value:
            self._notes = value
            self._increment_version()

    @property
    def tags(self) -> set[Tag]:
        self._check_not_discarded()
        return self._tags

    def _set_tags(self, value: set[Tag]) -> None:
        """Protected setter for tags. Can only be called through Meal aggregate."""
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

    def _set_privacy(self, value: Privacy) -> None:
        """Protected setter for privacy. Can only be called through Meal aggregate."""
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
        """Add or update a rating. Can only be called through Meal aggregate."""
        self._check_not_discarded()
        for i in range(len(self._ratings)):
            if self._ratings[i].user_id == user_id:
                self._ratings[i] = self._ratings[i].replace(
                    taste=taste,
                    convenience=convenience,
                    comment=comment,
                )
                self._increment_version()
                # Invalidate rating-related caches
                self._invalidate_caches('average_taste_rating', 'average_convenience_rating')
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
        # Invalidate rating-related caches
        self._invalidate_caches('average_taste_rating', 'average_convenience_rating')

    def delete_rate(self, user_id: str) -> None:
        """Delete a rating. Can only be called through Meal aggregate."""
        self._check_not_discarded()
        for i in range(len(self._ratings)):
            if self._ratings[i].user_id == user_id:
                self._ratings.pop(i)
                self._increment_version()
                # Invalidate rating-related caches
                self._invalidate_caches('average_taste_rating', 'average_convenience_rating')
                return

    @cached_property
    def average_taste_rating(self) -> float | None:
        """Calculate the average taste rating across all ratings for this recipe.
        
        This property uses instance-level caching to avoid repeated computation
        when accessed multiple times. The cache is automatically invalidated
        when ratings are modified through rate() or delete_rate() methods.
        
        Returns:
            float | None: Average taste rating (1.0-5.0), or None if no ratings exist
            
        Cache invalidation triggers:
            - rate(): When new rating is added or existing rating is updated
            - delete_rate(): When a rating is removed
            
        Performance: O(n) computation on first access, O(1) on subsequent accesses
        until cache invalidation.
        """
        self._check_not_discarded()
        if not self._ratings or len(self._ratings) == 0:
            return None
        total_taste = sum(rating.taste for rating in self._ratings)
        return total_taste / len(self._ratings)

    @cached_property
    def average_convenience_rating(self) -> float | None:
        """Calculate the average convenience rating across all ratings for this recipe.
        
        This property uses instance-level caching to avoid repeated computation
        when accessed multiple times. The cache is automatically invalidated
        when ratings are modified through rate() or delete_rate() methods.
        
        Returns:
            float | None: Average convenience rating (1.0-5.0), or None if no ratings exist
            
        Cache invalidation triggers:
            - rate(): When new rating is added or existing rating is updated
            - delete_rate(): When a rating is removed
            
        Performance: O(n) computation on first access, O(1) on subsequent accesses
        until cache invalidation.
        """
        self._check_not_discarded()
        if not self._ratings or len(self._ratings) == 0:
            return None
        total_convenience = sum(rating.convenience for rating in self._ratings)
        return total_convenience / len(self._ratings)

    @property
    def nutri_facts(self) -> NutriFacts | None:
        self._check_not_discarded()
        return self._nutri_facts

    def _set_nutri_facts(self, value: NutriFacts) -> None:
        """Protected setter for nutri_facts. Can only be called through Meal aggregate."""
        self._check_not_discarded()
        if self._nutri_facts != value:
            self._nutri_facts = value
            self._increment_version()
            # Invalidate nutrition-related caches
            self._invalidate_caches('macro_division')

    @property
    def weight_in_grams(self) -> int | None:
        self._check_not_discarded()
        return self._weight_in_grams

    def _set_weight_in_grams(self, value: int | None) -> None:
        """Protected setter for weight_in_grams. Can only be called through Meal aggregate."""
        self._check_not_discarded()
        if self._weight_in_grams != value:
            self._weight_in_grams = value
            self._increment_version()

    @property
    def calorie_density(self) -> float | None:
        self._check_not_discarded()
        if self.nutri_facts and self.nutri_facts.calories.value is not None and self.weight_in_grams:
            return (self.nutri_facts.calories.value / self.weight_in_grams) * 100
        return None

    @cached_property
    def macro_division(self) -> MacroDivision | None:
        """Calculate the macronutrient distribution as percentages.
        
        This property computes the percentage breakdown of carbohydrates, proteins,
        and fats based on the recipe's nutritional facts. Uses instance-level caching
        to avoid repeated computation when accessed multiple times.
        
        Returns:
            MacroDivision | None: Object containing carbohydrate, protein, and fat
            percentages (totaling 100%), or None if insufficient nutritional data
            
        Cache invalidation triggers:
            - nutri_facts setter: When nutritional facts are updated
            
        Performance: O(1) computation on first access, O(1) on subsequent accesses
        until cache invalidation.
        
        Notes:
            - Returns None if nutri_facts is None
            - Returns None if any macro values (carbs, protein, fat) are None
            - Returns None if total macros sum to zero (division by zero protection)
        """
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

    def _set_image_url(self, value: str | None) -> None:
        """Protected setter for image_url. Can only be called through Meal aggregate."""
        self._check_not_discarded()
        if self._image_url != value:
            self._image_url = value
            self._increment_version()

    def delete(self) -> None:
        """Delete (discard) the recipe. Can only be called through Meal aggregate."""
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
        """Override to route property updates to protected setter methods."""
        self._check_not_discarded()
        if not kwargs:
            return
        
        # Store original version for single increment (like base Entity class)
        original_version = self.version
        
        # Validate all properties first (similar to Entity base class)
        for key, value in kwargs.items():
            if key[0] == "_":
                raise AttributeError(f"{key} is private.")
            
            # Check if there's a corresponding protected setter method
            setter_method_name = f"_set_{key}"
            if not hasattr(self, setter_method_name):
                raise AttributeError(f"Recipe has no property '{key}' or it cannot be updated.")
        
        # Apply all property updates using reflection
        for key, value in kwargs.items():
            setter_method = getattr(self, f"_set_{key}")
            setter_method(value)
        
        # Set version manually to avoid multiple increments (like base Entity class)
        self._version = original_version + 1
        # Invalidate all caches after successful property updates
        self._invalidate_caches()

    def update_properties(self, **kwargs) -> None:
        """Update multiple properties. Can only be called through Meal aggregate."""
        self._check_not_discarded()
        self._update_properties(**kwargs)
