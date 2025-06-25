from typing import Any
from pydantic import field_validator

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import ApiRecipe, RecipeListAdapter
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal_fields import MealDescription, MealImageUrl, MealLike, MealName, MealNotes, MealRecipes, MealTags
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.root_aggregate.api_meal import ApiMeal
from src.contexts.recipes_catalog.core.domain.meal.commands.update_meal import UpdateMeal
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseCommand
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import UUIDId, UUIDIdOptional
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag import ApiTag, TagFrozensetAdapter
from src.db.base import SaBase

class ApiAttributesToUpdateOnMeal(BaseCommand[UpdateMeal, SaBase]):
    """
    A pydantic model representing and validating the data required to update
    a meal via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        name (str, optional): Name of the meal.
        menu_id (str, optional): ID of the menu to move the meal to.
        description (str, optional): Description of the meal.
        recipes (list[ApiRecipe], optional): Recipes in the meal.
        tags (frozenset[ApiTag], optional): Tags associated with the meal.
        notes (str, optional): Additional notes about the meal.
        like (bool, optional): Whether the meal is liked.
        image_url (str, optional): URL of an image of the meal.

    Methods:
        to_domain() -> dict:
            Converts the instance to a dictionary of attributes to update.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    name: MealName | None = None
    menu_id: UUIDIdOptional
    description: MealDescription
    recipes: MealRecipes
    tags: MealTags
    notes: MealNotes
    like: MealLike
    image_url: MealImageUrl

    @field_validator('recipes')
    @classmethod
    def validate_recipes(cls, v: list[ApiRecipe]) -> list[ApiRecipe]:
        """Validate that recipes are unique by id."""
        if not v:
            return v
        return RecipeListAdapter.validate_python(v)

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: frozenset[ApiTag]) -> frozenset[ApiTag]:
        """Validate tags using TypeAdapter."""
        return TagFrozensetAdapter.validate_python(v)

    def to_domain(self) -> dict[str, Any]:
        """Converts the instance to a dictionary of attributes to update."""
        try:
            return self.model_dump(exclude_unset=True)
        except Exception as e:
            raise ValueError(
                f"Failed to convert ApiAttributesToUpdateOnMeal to domain model: {e}"
            )


class ApiUpdateMeal(BaseCommand[UpdateMeal, SaBase]):
    """
    A Pydantic model representing and validating the data required
    to update a meal via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        meal_id (str): ID of the meal to update.
        updates (ApiAttributesToUpdateOnMeal): Attributes to update.

    Methods:
        to_domain() -> UpdateMeal:
            Converts the instance to a domain model object for updating a meal.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    meal_id: UUIDId
    updates: ApiAttributesToUpdateOnMeal

    def to_domain(self) -> UpdateMeal:
        """Converts the instance to a domain model object for updating a meal."""
        try:
            return UpdateMeal(
                meal_id=self.meal_id,
                updates=self.updates.to_domain(),
            )
        except Exception as e:
            raise ValueError(f"Failed to convert ApiUpdateMeal to domain model: {e}")

    @classmethod
    def from_api_meal(cls, api_meal: ApiMeal) -> "ApiUpdateMeal":
        """Creates an instance from an existing meal."""
        attributes_to_update = {
            key: getattr(api_meal, key) for key in ApiMeal.model_fields.keys()
        }
        return cls(
            meal_id=api_meal.id,
            updates=ApiAttributesToUpdateOnMeal(**attributes_to_update),
        )
