from pydantic import BaseModel

from src.contexts.recipes_catalog.shared.domain.commands.meal.copy_recipe_to_meal import \
    CopyRecipeToMeal


class ApiCopyRecipeToMeal(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to copy a recipe to a meal via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        meal_id (str): ID of the meal.
        recipe_id (str): ID of the recipe to be copied.

    Methods:
        to_domain() -> CopyExistingRecipeToMeal:
            Converts the instance to a domain model object for copying a meal.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    meal_id: str
    recipe_id: str

    def to_domain(self) -> CopyRecipeToMeal:
        """Converts the instance to a domain model object for coping a recipe to a meal."""
        try:
            return CopyRecipeToMeal(
                meal_id=self.meal_id,
                recipe_id=self.recipe_id,
            )
        except Exception as e:
            raise ValueError(
                f"Failed to convert ApiCopyExistingRecipeToMeal to domain model: {e}"
            )
