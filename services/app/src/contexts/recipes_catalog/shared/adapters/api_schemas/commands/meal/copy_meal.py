from pydantic import BaseModel

from src.contexts.recipes_catalog.shared.domain.commands.meal.copy_meal import CopyMeal


class ApiCopyMeal(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to copy a meal via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        user_id (str): ID of the user.
        meal_id (str): ID of the meal.

    Methods:
        to_domain() -> CopyMeal:
            Converts the instance to a domain model object for copying a meal.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    id_of_user_coping_meal: str
    id_of_meal_to_be_copied: str
    id_of_target_menu: str

    def to_domain(self) -> CopyMeal:
        """Converts the instance to a domain model object for coping a meal."""
        try:
            return CopyMeal(
                id_of_user_coping_meal=self.id_of_user_coping_meal,
                id_of_meal_to_be_copied=self.id_of_meal_to_be_copied,
                id_of_target_menu=self.id_of_target_menu,
            )
        except Exception as e:
            raise ValueError(f"Failed to convert ApiCopyMeal to domain model: {e}")
