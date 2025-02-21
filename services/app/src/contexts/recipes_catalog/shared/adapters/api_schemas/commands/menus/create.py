from pydantic import BaseModel, Field, field_serializer

from src.contexts.recipes_catalog.shared.adapters.api_schemas.value_objects.menu_meal import (
    ApiMenuMeal,
)
from src.contexts.recipes_catalog.shared.domain.commands.menus.create import CreateMenu
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag import ApiTag


class ApiCreateMenu(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to add a new menu via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        author_id (str, optional): ID of the user who created the menu.
        client_id (str, optional): ID of the client for whom the menu is created.
        item (set[ApiMenuItem], optional): items that make up the menu.
        tags (list[ApiTag], optional): Tags associated with the menu.
        description (str, optional): Description of the menu.

    Methods:
        to_domain() -> Addmeal:
            Converts the instance to a domain model object for adding a menu.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    name: str
    author_id: str
    items: set[ApiMenuMeal] = Field(default_factory=set)
    tags: set[ApiTag] = Field(default_factory=set)
    description: str | None = None
    notes: str | None = None
    image_url: str | None = None

    def to_domain(self) -> CreateMenu:
        """Converts the instance to a domain model object for creating a meal."""
        try:
            return CreateMenu(
                name=self.name,
                author_id=self.author_id,
                recipes=[recipe.to_domain() for recipe in self.recipes],
                tags=[tag.to_domain() for tag in self.tags],
                description=self.description,
                notes=self.notes,
                image_url=self.image_url,
            )
        except Exception as e:
            raise ValueError(f"Failed to convert ApiCreateMeal to domain model: {e}")
