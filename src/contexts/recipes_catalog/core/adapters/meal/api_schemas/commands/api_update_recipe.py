from typing import Any

import src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe_fields as fields
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import (
    ApiRecipe,
)
from src.contexts.recipes_catalog.core.domain.meal.commands.update_recipe import (
    UpdateRecipe,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import (
    UrlOptional,
    UUIDIdRequired,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_model import (
    BaseApiCommand,
)
from src.contexts.seedwork.adapters.exceptions.api_schema_errors import (
    ValidationConversionError,
)


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
        ValidationConversionError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    name: fields.RecipeNameRequired | None = None
    description: fields.RecipeDescriptionOptional
    ingredients: fields.RecipeIngredientsOptionalFrozenset
    instructions: fields.RecipeInstructionsRequired | None = None
    weight_in_grams: fields.RecipeWeightInGramsOptional
    utensils: fields.RecipeUtensilsOptional
    total_time: fields.RecipeTotalTimeOptional
    notes: fields.RecipeNotesOptional
    tags: fields.RecipeTagsOptionalFrozenset
    privacy: fields.RecipePrivacyOptional
    nutri_facts: fields.RecipeNutriFactsOptional
    image_url: UrlOptional

    def to_domain(self) -> dict[str, Any]:
        """Converts the instance to a dictionary of attributes to update."""
        try:
            # Manual field conversion to avoid model_dump issues with frozensets
            updates = {}

            # Get fields that are frozenset (exclude_unset behavior)
            fields_set = self.__pydantic_fields_set__

            # Simple fields that can be included directly
            simple_fields = [
                "name",
                "description",
                "instructions",
                "weight_in_grams",
                "utensils",
                "total_time",
                "notes",
                "privacy",
                "image_url",
            ]

            for field in simple_fields:
                if field in fields_set:
                    value = getattr(self, field)
                    updates[field] = value

            # Complex fields that need special handling
            if "ingredients" in fields_set and self.ingredients is not None:
                updates["ingredients"] = [
                    ingredient.to_domain() for ingredient in self.ingredients
                ]

            if "tags" in fields_set and self.tags is not None:
                updates["tags"] = frozenset([tag.to_domain() for tag in self.tags])

            if "nutri_facts" in fields_set and self.nutri_facts is not None:
                updates["nutri_facts"] = self.nutri_facts.to_domain()
        except Exception as e:
            error_msg = (
                f"Failed to convert ApiAttributesToUpdateOnRecipe to domain model: {e}"
            )
            raise ValidationConversionError(
                error_msg,
                schema_class=self.__class__,
                conversion_direction="api_to_domain",
                source_data=self.model_dump(),
                validation_errors=[str(e)],
            ) from e
        else:
            return updates


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
        ValidationConversionError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    recipe_id: UUIDIdRequired
    updates: ApiAttributesToUpdateOnRecipe

    def to_domain(self) -> UpdateRecipe:
        """Converts the instance to a domain model object for updating a recipe."""
        try:
            return UpdateRecipe(
                recipe_id=self.recipe_id, updates=self.updates.to_domain()
            )
        except Exception as e:
            error_msg = f"Failed to convert ApiUpdateRecipe to domain model: {e}"
            raise ValidationConversionError(
                error_msg,
                schema_class=self.__class__,
                conversion_direction="api_to_domain",
                source_data=self.model_dump(),
                validation_errors=[str(e)],
            ) from e

    @classmethod
    def from_api_recipe(
        cls, api_recipe: ApiRecipe, old_api_recipe: ApiRecipe | None = None
    ) -> "ApiUpdateRecipe":
        """Creates an instance from an existing recipe.

        Args:
            api_recipe: The new/updated recipe data.
            old_api_recipe: Optional. The original recipe to compare against.
                           If provided, only changed fields will be included in updates.
                           If not provided, all fields will be included
                           (previous behavior).

        Returns:
            ApiUpdateRecipe instance with only the changed attributes
            (if old_api_recipe provided) or all attributes
            (if old_api_recipe not provided).
        """
        # Only extract fields that ApiAttributesToUpdateOnRecipe accepts
        allowed_fields = ApiAttributesToUpdateOnRecipe.model_fields.keys()
        attributes_to_update = {}

        for key in allowed_fields:
            new_value = getattr(api_recipe, key)

            # If no old recipe provided, include all fields (current behavior)
            if old_api_recipe is None:
                attributes_to_update[key] = new_value
            else:
                # Compare with old value and only include if changed
                old_value = getattr(old_api_recipe, key)
                if new_value != old_value:
                    attributes_to_update[key] = new_value

        return cls(
            recipe_id=api_recipe.id,
            updates=ApiAttributesToUpdateOnRecipe(**attributes_to_update),
        )
