from typing import Any

from pydantic import BaseModel, Field, field_serializer
from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.meals.meal import (
    ApiMeal,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.recipes.recipe import (
    ApiRecipe,
)
from src.contexts.recipes_catalog.shared.domain.commands.meals.update_meal import (
    UpdateMeal,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag import ApiTag


class ApiAttributesToUpdateOnMeal(BaseModel):
    """
    A pydantic model representing and validating the data required to update
    a Meal via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        name (str, optional): Name of the Meal.
        description (str, optional): Detailed description of the Meal.
        recipes (list[ApiRecipe], optional): List of Recipes in the Meal.
        tags (set[ApiTag], optional): Set of Tags associated with the Meal.
        notes (str, optional): Additional notes about the Meal.
        like (bool, optional): Whether the user likes the Meal.
        image_url (str, optional): URL of the image of the Meal.


    Methods:
        to_domain() -> dict:
            Converts the instance to a dictionary of attributes to update.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    # recipe_id: str
    name: str | None = None
    description: str | None = None
    recipes: list[ApiRecipe] | None = None
    tags: set[ApiTag] | None = Field(default_factory=set)
    notes: str | None = None
    like: bool | None = None
    image_url: str | None = None

    @field_serializer("recipes")
    def serialize_recipe(self, recipes: list[ApiRecipe] | None, _info):
        """Serializes the recipe list to a list of domain models."""
        return [i.to_domain() for i in recipes] if recipes else None

    @field_serializer("tags")
    def serialize_tags(self, tags: list[ApiTag] | None, _info):
        """Serializes the tag list to a list of domain models."""
        return set([i.to_domain() for i in tags]) if tags else None

    def to_domain(self) -> dict[str, Any]:
        """Converts the instance to a dictionary of attributes to update."""
        try:
            return self.model_dump(exclude_unset=True)
        except Exception as e:
            raise ValueError(
                f"Failed to convert ApiAttributesToUpdateOnMeal to domain model: {e}"
            )


class ApiUpdateMeal(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to update a Meal via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        meal_id (str): Identifier of the Meal to update.
        updates (ApiAttributesToUpdateOnMeal): Attributes to update.

    Methods:
        to_domain() -> UpdateMeal:
            Converts the instance to a domain model object for updating a Meal.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    meal_id: str
    updates: ApiAttributesToUpdateOnMeal

    def to_domain(self) -> UpdateMeal:
        """Converts the instance to a domain model object for updating a meal."""
        try:
            return UpdateMeal(meal_id=self.meal_id, updates=self.updates.to_domain())
        except Exception as e:
            raise ValueError(f"Failed to convert ApiUpdateMeal to domain model: {e}")

    @classmethod
    def from_api_meal(cls, api_meal: ApiMeal) -> "ApiUpdateMeal":
        """Creates an instance from an existing meal."""
        attributes_to_update = {
            key: getattr(api_meal, key) for key in api_meal.model_fields.keys()
        }
        return cls(
            meal_id=api_meal.id,
            updates=ApiAttributesToUpdateOnMeal(**attributes_to_update),
        )
