from src.contexts.recipes_catalog.core.domain.meal.commands.delete_meal import (
    DeleteMeal,
)
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import (
    UUIDIdRequired,
)
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import (
    BaseApiCommand,
)


class ApiDeleteMeal(BaseApiCommand[DeleteMeal]):
    """
    A Pydantic model representing and validating the data required
    to delete a meal via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        meal_id (str): ID of the meal to delete.

    Methods:
        to_domain() -> DeleteMeal:
            Converts the instance to a domain model object for deleting a meal.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    meal_id: UUIDIdRequired

    def to_domain(self) -> DeleteMeal:
        """Converts the instance to a domain model object for deleting a meal."""
        try:
            return DeleteMeal(
                meal_id=self.meal_id,
            )
        except Exception as e:
            raise ValueError(f"Failed to convert ApiDeleteMeal to domain model: {e}")
