from typing import Any

from pydantic import HttpUrl

import src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe_fields as recipe_annotations
from src.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.api_recipe import ApiRecipe
from src.contexts.recipes_catalog.core.domain.meal.commands.update_recipe import UpdateRecipe
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiCommand
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import UUIDIdRequired, UrlOptional


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

    name: recipe_annotations.RecipeNameRequired | None = None
    description: recipe_annotations.RecipeDescriptionOptional
    ingredients: recipe_annotations.RecipeIngredientsOptionalFrozenset
    instructions: recipe_annotations.RecipeInstructionsRequired | None = None
    weight_in_grams: recipe_annotations.RecipeWeightInGramsOptional
    utensils: recipe_annotations.RecipeUtensilsOptional
    total_time: recipe_annotations.RecipeTotalTimeOptional
    notes: recipe_annotations.RecipeNotesOptional
    tags: recipe_annotations.RecipeTagsOptionalFrozenset
    privacy: recipe_annotations.RecipePrivacyOptional | None = None
    nutri_facts: recipe_annotations.RecipeNutriFactsOptional
    image_url: UrlOptional

    def to_domain(self) -> dict[str, Any]:
        """Converts the instance to a dictionary of attributes to update."""
        try:
            # Manual field conversion to avoid model_dump issues with frozensets
            updates = {}
            
            # Get fields that are frozenset (exclude_unset behavior)
            fields_set = self.__pydantic_fields_set__
            
            # Simple fields that can be included directly
            simple_fields = ["name", "description", "instructions", "weight_in_grams", 
                           "utensils", "total_time", "notes", "privacy", "image_url"]
            
            for field in simple_fields:
                if field in fields_set:
                    value = getattr(self, field)
                    updates[field] = value
            
            # Complex fields that need special handling
            if "ingredients" in fields_set and self.ingredients is not None:
                updates["ingredients"] = [ingredient.to_domain() for ingredient in self.ingredients]
            
            if "tags" in fields_set and self.tags is not None:
                updates["tags"] = frozenset([tag.to_domain() for tag in self.tags])
            
            if "nutri_facts" in fields_set and self.nutri_facts is not None:
                updates["nutri_facts"] = self.nutri_facts.to_domain()
            
            return updates
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

    recipe_id: UUIDIdRequired
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
