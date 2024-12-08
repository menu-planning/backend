from pydantic import BaseModel, Field
from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.recipes.recipe import (
    ApiRecipe,
)
from src.contexts.recipes_catalog.shared.domain.commands.meals.create import CreateMeal


class ApiCreateMeal(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to add a new meal via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        name (str): Name of the meal.
        author_id (str, optional): ID of the user who created the meal.
        recipes (list[ApiRecipe], optional): Recipes that make up the meal.
        description (str, optional): Description of the meal.
        notes (str, optional): Additional notes about the meal.
        image_url (str, optional): URL of an image of the meal.

    Methods:
        to_domain() -> Addmeal:
            Converts the instance to a domain model object for adding a meal.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    name: str
    author_id: str | None = None
    recipes: list[ApiRecipe] = Field(default_factory=list)
    description: str | None = None
    notes: str | None = None
    image_url: str | None = None

    def to_domain(self) -> CreateMeal:
        """Converts the instance to a domain model object for creating a meal."""
        try:
            return CreateMeal(
                name=self.name,
                author_id=self.author_id,
                recipes=[recipe.to_domain() for recipe in self.recipes],
                description=self.description,
                notes=self.notes,
                image_url=self.image_url,
            )
        except Exception as e:
            raise ValueError(f"Failed to convert ApiCreateMeal to domain model: {e}")
