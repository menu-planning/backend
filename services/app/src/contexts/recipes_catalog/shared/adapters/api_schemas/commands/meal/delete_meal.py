from pydantic import BaseModel

from src.contexts.recipes_catalog.shared.domain.commands.meal.delete_meal import (
    DeleteMeal,
)


class ApiDeleteMeal(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to delete a meal via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        meal_id (str): ID of the meal.

    Methods:
        to_domain() -> DeleteMeal:
            Converts the instance to a domain model object for deleting a meal.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    meal_id: str

    def to_domain(self) -> DeleteMeal:
        """Converts the instance to a domain model object for coping a meal."""
        try:
            return DeleteMeal(
                meal_id=self.meal_id,
            )
        except Exception as e:
            raise ValueError(f"Failed to convert ApiCopyMeal to domain model: {e}")
