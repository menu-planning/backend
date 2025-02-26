from pydantic import BaseModel

from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.recipe.update import (
    ApiAttributesToUpdateOnRecipe,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.recipe.recipe import (
    ApiRecipe,
)
from src.contexts.recipes_catalog.shared.domain.commands.meal.update_meal import (
    UpdateMeal,
)
from src.contexts.recipes_catalog.shared.domain.commands.meal.update_recipe_on_meal import (
    UpdateRecipeOnMeal,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag import ApiTag


class ApiUpdateRecipeOnMeal(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to update a Meal via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        meal_id (str): Identifier of the Meal to update.
        recipe_id (str): Identifier of the Recipe to update.
        updates (ApiAttributesToUpdateOnMeal): Attributes to update.

    Methods:
        to_domain() -> UpdateMeal:
            Converts the instance to a domain model object for updating a Meal.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    meal_id: str
    recipe_id: str
    updates: ApiAttributesToUpdateOnRecipe

    def to_domain(self) -> UpdateMeal:
        """Converts the instance to a domain model object for updating a meal."""
        try:
            return UpdateRecipeOnMeal(
                meal_id=self.meal_id,
                recipe_id=self.recipe_id,
                updates=self.updates.to_domain(),
            )
        except Exception as e:
            raise ValueError(f"Failed to convert ApiUpdateMeal to domain model: {e}")

    @classmethod
    def from_api_recipe(cls, api_recipe: ApiRecipe) -> "ApiUpdateRecipeOnMeal":
        """Creates an instance from an existing recipe."""
        attributes_to_update = {
            key: getattr(api_recipe, key) for key in api_recipe.model_fields.keys()
        }
        return cls(
            meal_id=api_recipe.meal_id,
            recipe_id=api_recipe.id,
            updates=ApiAttributesToUpdateOnRecipe(**attributes_to_update),
        )
