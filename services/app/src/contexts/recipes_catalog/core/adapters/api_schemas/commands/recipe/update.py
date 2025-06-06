from typing import Any
from pydantic import field_validator

from src.contexts.seedwork.shared.adapters.api_schemas.base import BaseCommand
from src.contexts.recipes_catalog.core.adapters.api_schemas.entities.recipe.recipe import (
    ApiRecipe,
)
from src.contexts.recipes_catalog.core.adapters.api_schemas.value_objects.ingredient import (
    ApiIngredient,
    IngredientListAdapter,
)
from src.contexts.recipes_catalog.core.domain.commands import UpdateRecipe
from src.contexts.seedwork.shared.adapters.api_schemas.fields import UUIDId
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag import ApiTag, TagSetAdapter
from src.db.base import SaBase
from src.contexts.recipes_catalog.core.adapters.api_schemas.entities.recipe.fields import (
    RecipeName,
    RecipeInstructions,
    RecipeDescription,
    RecipeUtensils,
    RecipeTotalTime,
    RecipeNotes,
    OptionalRecipeTags,
    RecipePrivacy,
    RecipeNutriFacts,
    RecipeWeightInGrams,
    RecipeImageUrl,
    RecipeIngredients,
)


class ApiAttributesToUpdateOnRecipe(BaseCommand[UpdateRecipe, SaBase]):
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

    name: RecipeName | None = None
    description: RecipeDescription
    ingredients: RecipeIngredients
    instructions: RecipeInstructions | None = None
    weight_in_grams: RecipeWeightInGrams
    utensils: RecipeUtensils
    total_time: RecipeTotalTime
    notes: RecipeNotes
    tags: OptionalRecipeTags
    privacy: RecipePrivacy | None = None
    nutri_facts: RecipeNutriFacts
    image_url: RecipeImageUrl

    @field_validator('ingredients')
    @classmethod
    def validate_ingredients(cls, v: list[ApiIngredient]) -> list[ApiIngredient]:
        """Validate that ingredients are unique by name."""
        if not v:
            return v
        return IngredientListAdapter.validate_python(v)

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: set[ApiTag]) -> set[ApiTag]:
        """Validate tags using TypeAdapter."""
        return TagSetAdapter.validate_python(v)

    def to_domain(self) -> dict[str, Any]:
        """Converts the instance to a dictionary of attributes to update."""
        try:
            return self.model_dump(exclude_unset=True)
        except Exception as e:
            raise ValueError(
                f"Failed to convert ApiAttributesToUpdateOnRecipe to domain model: {e}"
            )


class ApiUpdateRecipe(BaseCommand[UpdateRecipe, SaBase]):
    """
    A Pydantic model representing and validating the data required
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

    recipe_id: UUIDId
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
