from typing import Any

from pydantic import BaseModel, Field, field_serializer
from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.recipes.recipe import (
    ApiRecipe,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.pydantic_validators import (
    MonthValue,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.value_objects.ingredient import (
    ApiIngredient,
)
from src.contexts.recipes_catalog.shared.domain.commands import UpdateRecipe
from src.contexts.recipes_catalog.shared.domain.entities.recipe import Recipe
from src.contexts.shared_kernel.domain.enums import Month, Privacy
from src.contexts.shared_kernel.domain.value_objects.name_tag.cuisine import Cuisine
from src.contexts.shared_kernel.domain.value_objects.name_tag.flavor import Flavor
from src.contexts.shared_kernel.domain.value_objects.name_tag.texture import Texture
from src.contexts.shared_kernel.endpoints.api_schemas.value_objects.nutri_facts import (
    ApiNutriFacts,
)


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
        servings (int, optional): Number of servings the recipe yields.
        notes (str, optional): Additional notes about the recipe.
        diet_types_ids (set[str], optional): Set of applicable diet types ids
        categoryies_ids (set[str], optional): Set of recipe categories ids
        cuisine (str, optional): The cuisine of the recipe
        flavor (str, optional): Description of the recipe's
            flavor profile.
        texture (str, optional): Description of the recipe's
            texture profile.
        meal_planning_ids (str, optional): Suitable for meal planning purposes.
        privacy (Privacy, optional): Privacy setting of the recipe.
        nutri_facts (ApiNutriFacts, optional): Nutritional facts of the
            recipe.
        season (set[MonthValue], optional): Applicable seasons for the
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
    utensils: str | None = None
    total_time: int | None = None
    servings: int | None = None
    notes: str | None = None
    diet_types_ids: set[str] | None = None
    categories_ids: set[str] | None = None
    cuisine: str | None = None
    flavor: str | None = None
    texture: str | None = None
    meal_planning_ids: set[str] | None = None
    privacy: Privacy | None = None
    nutri_facts: ApiNutriFacts | None = None
    season: set[MonthValue] | None = Field(default_factory=set)
    image_url: str | None = None

    @field_serializer("ingredients")
    def serialize_ingredients(self, ingredients: list[ApiIngredient] | None, _info):
        """Serializes the ingredient list to a list of domain models."""
        return [i.to_domain() for i in ingredients] if ingredients else None

    @field_serializer("nutri_facts")
    def serialize_nutri_facts(self, nutri_facts: ApiNutriFacts | None, _info):
        """Serializes the nutritional facts to a domain model."""
        return nutri_facts.to_domain() if nutri_facts else None

    @field_serializer("season")
    def serialize_season(self, season: set[MonthValue] | None, _info):
        """Serializes the season to a list of values."""
        return set([Month(v) for v in season]) if season else set()

    @field_serializer("cuisine")
    def serialize_cuisine(self, cuisine: str | None, _info):
        """Serializes the cuisine to a domain model."""
        return Cuisine(name=cuisine) if cuisine else None

    @field_serializer("flavor")
    def serialize_flavor(self, flavor: str | None, _info):
        """Serializes the flavor to a domain model."""
        return Flavor(name=flavor) if flavor else None

    @field_serializer("texture")
    def serialize_texture(self, texture: str | None, _info):
        """Serializes the texture to a domain model."""
        return Texture(name=texture) if texture else None

    def to_domain(self) -> dict[str, Any]:
        """Converts the instance to a dictionary of attributes to update."""
        try:
            return self.model_dump()
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
            return UpdateRecipe(id=self.recipe_id, updates=self.updates.to_domain())
        except Exception as e:
            raise ValueError(f"Failed to convert ApiUpdateRecipe to domain model: {e}")

    @classmethod
    def from_api_recipe(cls, api_recipe: ApiRecipe) -> "ApiUpdateRecipe":
        """Creates an instance from an existing recipe."""
        attributes_to_update = {
            key: getattr(api_recipe, key) for key in api_recipe.model_fields.keys()
        }
        attributes_to_update["season"] = set([i.value for i in api_recipe.season])
        return cls(
            recipe_id=api_recipe.id,
            updates=ApiAttributesToUpdateOnRecipe(**attributes_to_update),
        )
