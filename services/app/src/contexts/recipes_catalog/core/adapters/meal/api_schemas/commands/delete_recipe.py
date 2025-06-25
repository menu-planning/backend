from src.contexts.recipes_catalog.core.domain.meal.commands.delete_recipe import DeleteRecipe
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseCommand
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import UUIDId
from src.db.base import SaBase


class ApiDeleteRecipe(BaseCommand[DeleteRecipe, SaBase]):
    """
    A Pydantic model representing and validating the data required
    to delete a recipe via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        recipe_id (str): ID of the recipe to delete.

    Methods:
        to_domain() -> DeleteRecipe:
            Converts the instance to a domain model object for deleting a recipe.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    recipe_id: UUIDId

    def to_domain(self) -> DeleteRecipe:
        """Converts the instance to a domain model object for deleting a recipe."""
        try:
            return DeleteRecipe(
                recipe_id=self.recipe_id,
            )
        except Exception as e:
            raise ValueError(f"Failed to convert ApiDeleteRecipe to domain model: {e}")
