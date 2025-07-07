from typing import Any
from pydantic import field_validator

from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe_fields import RecipeTagsOptional, RecipeDescriptionOptional, RecipeImageUrlOptional, RecipeIngredientsRequiredFrozenset, RecipeInstructionsRequired, RecipeNameRequired, RecipeNotesOptional, RecipeNutriFactsOptional, RecipePrivacyOptional, RecipeTotalTimeOptional, RecipeUtensilsOptional, RecipeWeightInGramsOptional
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import ApiRecipe
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.value_objetcs.api_ingredient import ApiIngredient
from src.contexts.recipes_catalog.core.domain.meal.commands.update_recipe import UpdateRecipe
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiCommand
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import UUIDId
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag


class ApiAttributesToUpdateOnRecipe(BaseApiCommand[UpdateRecipe]):
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

    name: RecipeNameRequired | None = None
    description: RecipeDescriptionOptional
    ingredients: RecipeIngredientsRequiredFrozenset
    instructions: RecipeInstructionsRequired | None = None
    weight_in_grams: RecipeWeightInGramsOptional
    utensils: RecipeUtensilsOptional
    total_time: RecipeTotalTimeOptional
    notes: RecipeNotesOptional
    tags: RecipeTagsOptional
    privacy: RecipePrivacyOptional | None = None
    nutri_facts: RecipeNutriFactsOptional
    image_url: RecipeImageUrlOptional

    def to_domain(self) -> dict[str, Any]:
        """Converts the instance to a dictionary of attributes to update."""
        try:
            return self.model_dump(exclude_unset=True)
        except Exception as e:
            raise ValueError(
                f"Failed to convert ApiAttributesToUpdateOnRecipe to domain model: {e}"
            )


class ApiUpdateRecipe(BaseApiCommand[UpdateRecipe]):
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
            key: getattr(api_recipe, key) for key in api_recipe.__class__.model_fields.keys()
        }
        return cls(
            recipe_id=api_recipe.id,
            updates=ApiAttributesToUpdateOnRecipe(**attributes_to_update),
        )
