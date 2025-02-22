from pydantic import BaseModel

from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.recipe.recipe import (
    ApiRecipe,
)
from src.contexts.recipes_catalog.shared.domain.commands.meal.add_recipe import (
    AddRecipeToMeal,
)


class ApiAddRecipeToMeal(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to add a recipe to a meal via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        meal_id (str): ID of the meal.
        recipes (ApiRecipe): Recipe to be added.

    Methods:
        to_domain() -> Addmeal:
            Converts the instance to a domain model object for adding a meal.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    meal_id: str
    recipe: ApiRecipe

    def to_domain(self) -> AddRecipeToMeal:
        """Converts the instance to a domain model object for addin a recipe to a meal."""
        try:
            return AddRecipeToMeal(
                meal_id=self.meal_id,
                recipe=self.recipe.to_domain(),
            )
        except Exception as e:
            raise ValueError(
                f"Failed to convert ApiAddRecipeToMeal to domain model: {e}"
            )
