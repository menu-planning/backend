from typing import Any

from pydantic import BaseModel, Field, field_serializer

from src.contexts.recipes_catalog.core.adapters.api_schemas.entities.recipe.recipe import (
    ApiRecipe,
)
from src.contexts.recipes_catalog.core.adapters.api_schemas.value_objects.ingredient import (
    ApiIngredient,
)
from src.contexts.recipes_catalog.core.domain.commands import UpdateRecipe
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.nutri_facts import (
    ApiNutriFacts,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag import ApiTag
from src.contexts.shared_kernel.domain.enums import Privacy


class ApiAttributesToUpdateOnRecipe(BaseModel):
    """
    A pydantic model representing and validating the data required to update
    a recipe via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        name (str, optional): Name of the recipe.
        description (str, optional): Detailed description of the recipe.
        ingredients (str): (list[ApiIngredient], optional): Detailed list of
            ingredients.
        instructions (str): Detailed instructions.
        utensils (str, optional): Comma-separated list of utensils.
        total_time (int, optional): Total preparation and cooking time in
            minutes.
        notes (str, optional): Additional notes about the recipe.
        tags (str, optional): for tagging a recipe.
        privacy (Privacy, optional): Privacy setting of the recipe.
        nutri_facts (ApiNutriFacts, optional): Nutritional facts of the
            recipe.
        image_url (str, optional): URL of an image of the recipe.

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
    ingredients: list[ApiIngredient] = Field(default_factory=list)
    instructions: str | None = None
    weight_in_grams: int | None = None
    utensils: str | None = None
    total_time: int | None = None
    notes: str | None = None
    tags: set[ApiTag] | None = Field(default_factory=set)
    privacy: Privacy | None = None
    nutri_facts: ApiNutriFacts | None = None
    image_url: str | None = None

    @field_serializer("ingredients")
    def serialize_ingredients(self, ingredients: list[ApiIngredient] | None, _info):
        """Serializes the ingredient list to a list of domain models."""
        return [i.to_domain() for i in ingredients] if ingredients else []

    @field_serializer("nutri_facts")
    def serialize_nutri_facts(self, nutri_facts: ApiNutriFacts | None, _info):
        """Serializes the nutritional facts to a domain model."""
        return nutri_facts.to_domain() if nutri_facts else None

    @field_serializer("tags")
    def serialize_tags(self, tags: list[ApiTag] | None, _info):
        """Serializes the tags to a list of domain models."""
        return set([t.to_domain() for t in tags]) if tags else set()

    def to_domain(self) -> dict[str, Any]:
        """Converts the instance to a dictionary of attributes to update."""
        try:
            return self.model_dump(exclude_unset=True)
        except Exception as e:
            raise ValueError(
                f"Failed to convert ApiAttributesToUpdateOnRecipe to domain model: {e}"
            )


class ApiUpdateRecipe(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to update a recipe via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        recipe_id (str): Identifier of the recipe to update.
        updates (ApiAttributesToUpdateOnRecipe): Attributes to update.

    Methods:
        to_domain() -> UpdateRecipe:
            Converts the instance to a domain model object for updating a recipe.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    recipe_id: str
    updates: ApiAttributesToUpdateOnRecipe

    def to_domain(self) -> UpdateRecipe:
        """Converts the instance to a domain model object for updating a recipe."""
        try:
            return UpdateRecipe(
                recipe_id=self.recipe_id, updates=self.updates.to_domain()
            )
        except Exception as e:
            raise ValueError(f"Failed to convert ApiUpdateRecipe to domain model: {e}")

    @classmethod
    def from_api_recipe(cls, api_recipe: ApiRecipe) -> "ApiUpdateRecipe":
        """Creates an instance from an existing recipe."""
        attributes_to_update = {
            key: getattr(api_recipe, key) for key in api_recipe.model_fields.keys()
        }
        return cls(
            recipe_id=api_recipe.id,
            updates=ApiAttributesToUpdateOnRecipe(**attributes_to_update),
        )
