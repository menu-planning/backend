from pydantic import BaseModel, Field
import uuid

from src.contexts.recipes_catalog.core.adapters.api_schemas.entities.recipe.recipe import (
    ApiRecipe,
)
from src.contexts.recipes_catalog.core.domain.commands.meal.create_meal import (
    CreateMeal,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag import ApiTag


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
        tags (list[ApiTag], optional): Tags associated with the meal.
        description (str, optional): Description of the meal.
        notes (str, optional): Additional notes about the meal.
        image_url (str, optional): URL of an image of the meal.
        meal_id (str, optional): ID of the meal to create. If not provided, a new UUID will be generated.

    Methods:
        to_domain() -> Addmeal:
            Converts the instance to a domain model object for adding a meal.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    name: str
    author_id: str
    menu_id: str
    recipes: list[ApiRecipe] = Field(default_factory=list)
    tags: set[ApiTag] = Field(default_factory=set)
    description: str | None = None
    notes: str | None = None
    image_url: str | None = None

    def to_domain(self) -> CreateMeal:
        """Converts the instance to a domain model object for creating a meal."""
        try:
            return CreateMeal(
                name=self.name,
                author_id=self.author_id,
                menu_id=self.menu_id,
                recipes=[recipe.to_domain() for recipe in self.recipes],
                tags=set([tag.to_domain() for tag in self.tags]),
                description=self.description,
                notes=self.notes,
                image_url=self.image_url,
            )
        except Exception as e:
            raise ValueError(f"Failed to convert ApiCreateMeal to domain model: {e}")
