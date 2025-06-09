from typing import Annotated
from pydantic import Field

from src.contexts.recipes_catalog.core.domain.meal.commands.copy_recipe import CopyRecipe
from src.contexts.seedwork.shared.adapters.api_schemas.base import BaseCommand
from src.contexts.seedwork.shared.adapters.api_schemas.fields import UUIDId
from src.db.base import SaBase


class ApiCopyRecipe(BaseCommand[CopyRecipe, SaBase]):
    """
    A Pydantic model representing and validating the data required
    to copy a recipe via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        user_id (str): ID of the user copying the recipe.
        recipe_id (str): ID of the recipe to copy.
        meal_id (str): ID of the meal to copy the recipe to.

    Methods:
        to_domain() -> CopyRecipe:
            Converts the instance to a domain model object for copying a recipe.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    user_id: UUIDId
    recipe_id: UUIDId
    meal_id: UUIDId

    def to_domain(self) -> CopyRecipe:
        """Converts the instance to a domain model object for copying a recipe."""
        try:
            return CopyRecipe(
                user_id=self.user_id,
                recipe_id=self.recipe_id,
                meal_id=self.meal_id,
            )
        except Exception as e:
            raise ValueError(f"Failed to convert ApiCopyRecipe to domain model: {e}")
