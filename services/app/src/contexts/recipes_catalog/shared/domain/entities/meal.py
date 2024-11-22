from __future__ import annotations

import uuid
from datetime import datetime

from src.contexts.recipes_catalog.shared.domain.entities.recipe import Recipe
from src.contexts.recipes_catalog.shared.domain.value_objects.ingredient import (
    Ingredient,
)
from src.contexts.recipes_catalog.shared.domain.value_objects.macro_division import (
    MacroDivision,
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
        recipes: list[Recipe] | None = None,
        # menu_id: str | None = None,
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
        # self._menu = menu_id
        self._name = name
        self._recipes = recipes if recipes else []
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
    ) -> "Meal":
        meal_id = uuid.uuid4().hex
        return cls(
            id=meal_id,
            name=name,
            author_id=author_id,
            # menu_id=menu_id,
        )

    @classmethod
    def copy_meal(
        cls,
        meal: Meal,
        user_id: str,
    ) -> "Meal":
        # Data to copy
        name = meal.name
        description = meal.description
        notes = meal.notes
        image_url = meal.image_url
        # New data
        meal_id = uuid.uuid4().hex
        author_id = user_id
        new_recipes = []
        for r in meal.recipes:
            copy = Recipe.copy_recipe(recipe=r, user_id=user_id, meal_id=meal_id)
            new_recipes.append(copy)
        return cls(
            id=meal_id,
            author_id=author_id,
            # menu_id=menu_id,
            name=name,
            recipes=new_recipes,
            description=description,
            notes=notes,
            image_url=image_url,
        )

    @property
    def id(self) -> str:
        self._check_not_discarded()
        return self._id

    @property
    def author_id(self) -> str:
        self._check_not_discarded()
        return self._author_id

    # @property
    # def menu_id(self) -> str | None:
    #     self._check_not_discarded()
    #     return self._menu

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
    def products_ids(self) -> set[str]:
        self._check_not_discarded()
        products_ids = set()
        for recipe in self.recipes:
            for ingredient in recipe.ingredients:
                if ingredient.product_id:
                    products_ids.add(ingredient.product_id)
        return products_ids

    @property
    def total_time(self) -> int:
        self._check_not_discarded()
        return (
            max([recipe.total_time for recipe in self.recipes])
            if self.recipes
            else None
        )

    @property
    def diet_types_ids(self) -> set[str]:
        self._check_not_discarded()
        return set.intersection(
            *(
                [recipe.diet_types_ids for recipe in self.recipes]
                if self.recipes
                else [set()]
            )
        )

    @property
    def categories_ids(self) -> set[str]:
        self._check_not_discarded()
        ids = set()
        for recipe in self.recipes:
            ids.update(recipe.categories_ids)
        return ids

    @property
    def cuisines(self) -> set[Cuisine]:
        self._check_not_discarded()
        cuisines = set()
        for recipe in self.recipes:
            if recipe.cuisine:
                cuisines.add(recipe.cuisine)
        return cuisines

    @property
    def flavors(self) -> set[Flavor]:
        self._check_not_discarded()
        flavors = set()
        for recipe in self.recipes:
            if recipe.flavor:
                flavors.add(recipe.flavor)
        return flavors

    @property
    def textures(self) -> set[Texture]:
        self._check_not_discarded()
        textures = set()
        for recipe in self.recipes:
            if recipe.texture:
                textures.add(recipe.texture)
        return textures

    @property
    def allergens(self) -> set[Allergen]:
        self._check_not_discarded()
        allergens = set()
        for recipe in self.recipes:
            allergens.update(recipe.allergens)
        return allergens

    @property
    def meal_planning_ids(self) -> set[str]:
        self._check_not_discarded()
        ids = set()
        for recipe in self.recipes:
            ids.update(recipe.meal_planning_ids)
        return ids

    @property
    def recipes(self) -> list[Recipe]:
        self._check_not_discarded()
        return [recipe for recipe in self._recipes if recipe.discarded is False]

    def add_recipe_from_recipe(self, recipe: Recipe):
        self._check_not_discarded()
        copied = Recipe.copy_recipe(
            recipe=recipe, user_id=self.author_id, meal_id=self.id
        )
        self._recipes.append(copied)
        self._increment_version()

    @property
    def nutri_facts(self) -> NutriFacts:
        self._check_not_discarded()
        nutri_facts = NutriFacts()
        for recipe in self.recipes:
            nutri_facts += recipe.nutri_facts
        return nutri_facts

    @property
    def calorie_density(self) -> float | None:
        self._check_not_discarded()
        if self.nutri_facts and self.weight_in_grams:
            return self.nutri_facts.calories.value / self.weight_in_grams / 100

    @property
    def macro_division(self) -> MacroDivision | None:
        self._check_not_discarded()
        if self.nutri_facts:
            denominator = (
                self.nutri_facts.carbohydrate.value
                + self.nutri_facts.protein.value
                + self.nutri_facts.total_fat.value
            )
            if denominator == 0:
                return
            return MacroDivision(
                carbohydrate=self.nutri_facts.carbohydrate.value / denominator,
                protein=self.nutri_facts.protein.value / denominator,
                fat=self.nutri_facts.total_fat.value / denominator,
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
    def season(self) -> set[Month]:
        self._check_not_discarded()
        season = set()
        for recipe in self.recipes:
            season.update(recipe.season)
        return season

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
        return f"{self.__class__.__name__}" f"(id={self.id!r}, name={self.name!r})"

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
        self._update_properties(**kwargs)

    ### This is the part of the code that deals with the children recipes. ###
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
        """
        Create a new Recipe and add it to the Meal.
        """
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

    def update_recipe(self, recipe_id: str, **kwargs):
        self._check_not_discarded()
        for recipe in self._recipes:
            if recipe.discarded == False and recipe.id == recipe_id:
                recipe.update_properties(**kwargs)
                break
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
