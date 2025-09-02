from src.contexts.recipes_catalog.core.domain.meal.commands.copy_recipe import (
    CopyRecipe,
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


class ApiCopyRecipe(BaseApiCommand[CopyRecipe]):
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
        ValidationConversionError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    user_id: UUIDIdRequired
    recipe_id: UUIDIdRequired
    meal_id: UUIDIdRequired

    def to_domain(self) -> CopyRecipe:
        """Converts the instance to a domain model object for copying a recipe."""
        try:
            return CopyRecipe(
                user_id=self.user_id,
                recipe_id=self.recipe_id,
                meal_id=self.meal_id,
            )
        except Exception as e:
            raise ValidationConversionError(
                f"Failed to convert ApiCopyRecipe to domain model: {e}",
                schema_class=self.__class__,
                conversion_direction="api_to_domain",
                source_data=self.model_dump(),
                validation_errors=[str(e)],
            ) from e
