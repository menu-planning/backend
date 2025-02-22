from pydantic import BaseModel

from src.contexts.recipes_catalog.shared.domain.commands.meal.remove_recipe import (
    RemoveRecipeFromMeal,
)


class ApiCopyExistingRecipeToMeal(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to removing a recipe from a meal via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        meal_id (str): ID of the meal.
        recipe_id (str): ID of the recipe to be removed.

    Methods:
        to_domain() -> RemoveRecipeFromMeal:
            Converts the instance to a domain model object for removing a recipe.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    meal_id: str
    recipe_id: str

    def to_domain(self) -> RemoveRecipeFromMeal:
        """Converts the instance to a domain model object for removing a recipe from a meal."""
        try:
            return RemoveRecipeFromMeal(
                meal_id=self.meal_id,
                recipe=self.recipe_id,
            )
        except Exception as e:
            raise ValueError(
                f"Failed to convert ApiRemoveRecipeFromMeal to domain model: {e}"
            )
