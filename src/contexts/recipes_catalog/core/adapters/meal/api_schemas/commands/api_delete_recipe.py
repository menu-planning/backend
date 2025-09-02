from src.contexts.recipes_catalog.core.domain.meal.commands.delete_recipe import (
    DeleteRecipe,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import (
    UUIDIdRequired,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_model import (
    BaseApiCommand,
)
from src.contexts.seedwork.adapters.exceptions.api_schema_errors import (
    ValidationConversionError,
)


class ApiDeleteRecipe(BaseApiCommand[DeleteRecipe]):
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
        ValidationConversionError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    recipe_id: UUIDIdRequired

    def to_domain(self) -> DeleteRecipe:
        """Converts the instance to a domain model object for deleting a recipe."""
        try:
            return DeleteRecipe(
                recipe_id=self.recipe_id,
            )
        except Exception as e:
            raise ValidationConversionError(
                f"Failed to convert ApiDeleteRecipe to domain model: {e}",
                schema_class=self.__class__,
                conversion_direction="api_to_domain",
                source_data=self.model_dump(),
                validation_errors=[str(e)],
            ) from e
