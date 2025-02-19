from __future__ import annotations

import uuid
from datetime import datetime

from src.contexts.recipes_catalog.shared.domain.entities.recipe import Recipe
from src.contexts.recipes_catalog.shared.domain.rules import (
    AuthorIdOnTagMustMachRootAggregateAuthor,
    RecipeMustHaveCorrectMealIdAndAuthorId,
)
from src.contexts.recipes_catalog.shared.domain.value_objects.macro_division import (
    MacroDivision,
)
from src.contexts.seedwork.shared.domain.entitie import Entity
from src.contexts.seedwork.shared.domain.event import Event
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.value_objects.tag import Tag


class Meal(Entity):
    def __init__(
        self,
        *,
        id: str,
        name: str,
        author_id: str,
        menu_id: str | None = None,
        recipes: list[Recipe] | None = None,
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
        super().__init__(id=id, discarded=discarded, version=version)
        self._author_id = author_id
        self._name = name
        self._menu_id = menu_id
        self._recipes = recipes if recipes else []
        self._tags = tags if tags else set()
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
        menu_id: str | None = None,
        recipes: list[Recipe] | None = None,
        tags: set[Tag] | None = None,
        description: str | None = None,
        notes: str | None = None,
        image_url: str | None = None,
    ) -> "Meal":
        meal_id = uuid.uuid4().hex
        new_recipes = []
        if recipes:
            # for recipe in recipes:
            #     recipe.meal_id = meal_id
            #     recipe._author_id = author_id
            for recipe in recipes:
                copy = Recipe.copy_recipe(
                    recipe=recipe, user_id=author_id, meal_id=meal_id
                )
                new_recipes.append(copy)
        else:
            recipes = []
        return cls(
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
            copy = Recipe.copy_recipe(
                recipe=r, user_id=id_of_user_coping_meal, meal_id=meal_id
            )
            new_recipes.append(copy)
        for t in meal.tags:
            copy = Tag(
                key=t.key, value=t.value, author_id=id_of_user_coping_meal, type=t.type
            )
            new_tags.append(copy)
        return cls(
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

    @property
    def id(self) -> str:
        self._check_not_discarded()
        return self._id

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
            self._increment_version()

    @property
    def menu_id(self) -> str:
        self._check_not_discarded()
        return self._menu_id

    @menu_id.setter
    def menu_id(self, value: str) -> None:
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
    def total_time(self) -> int:
        self._check_not_discarded()
        return (
            max([recipe.total_time for recipe in self.recipes])
            if self.recipes
            else None
        )

    @property
    def recipes(self) -> list[Recipe]:
        self._check_not_discarded()
        return [recipe for recipe in self._recipes if recipe.discarded is False]

    @recipes.setter
    def recipes(self, value: list[Recipe]) -> None:
        self._check_not_discarded()
        for recipe in value:
            Recipe.check_rule(
                RecipeMustHaveCorrectMealIdAndAuthorId(meal=self, recipe=recipe),
            )
        if self._recipes == []:
            self._recipes = value
            self._increment_version()
            return
        recipes_to_be_added = []
        for r in value:
            if r not in self.recipes:
                recipes_to_be_added.append(r)
        for recipe in self._recipes:
            if recipe.discarded:
                continue
            if recipe not in value:
                recipe._discard()
                continue
            else:
                for r in value:
                    if r == recipe:
                        r._version = recipe.version
                        recipe = r
                        recipe._increment_version()
                        break
        self._recipes += recipes_to_be_added
        self._increment_version()

    def copy_recipes(self, recipes: list[Recipe]) -> None:
        self._check_not_discarded()
        for recipe in recipes:
            copied = Recipe.copy_recipe(
                recipe=recipe, user_id=self.author_id, meal_id=self.id
            )
            self._recipes.append(copied)
        self._increment_version()

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
        for recipe in self._recipes:
            recipe.delete()
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
        if "recipes" in kwargs:
            self.recipes = kwargs.pop("recipes")
        self._update_properties(**kwargs)

    ### This is the part of the code that deals with the children recipes. ###
    def add_recipe(
        self,
        recipe: Recipe,
        # *,
        # name: str,
        # ingredients: list[Ingredient],
        # instructions: str,
        # author_id: str,
        # description: str | None = None,
        # utensils: str | None = None,
        # total_time: int | None = None,
        # notes: str | None = None,
        # tags: set[Tag] | None = None,
        # privacy: Privacy = Privacy.PRIVATE,
        # nutri_facts: NutriFacts | None = None,
        # weight_in_grams: int | None = None,
        # image_url: str | None = None,
    ) -> Recipe:
        """
        Create a new Recipe and add it to the Meal.
        """
        self._check_not_discarded()
        Recipe.check_rule(
            RecipeMustHaveCorrectMealIdAndAuthorId(meal=self, recipe=recipe),
        )
        # recipe = Recipe.create_recipe(
        #     name=name,
        #     ingredients=ingredients,
        #     instructions=instructions,
        #     author_id=author_id,
        #     meal_id=self.id,
        #     description=description,
        #     utensils=utensils,
        #     total_time=total_time,
        #     notes=notes,
        #     tags=tags,
        #     privacy=privacy,
        #     nutri_facts=nutri_facts,
        #     weight_in_grams=weight_in_grams,
        #     image_url=image_url,
        # )
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
