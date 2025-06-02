from pydantic import BaseModel, Field, field_serializer
import uuid

from src.contexts.recipes_catalog.core.domain.commands.client.create_menu import CreateMenu
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
        tags (list[ApiTag], optional): Tags associated with the menu.
        description (str, optional): Description of the menu.
        menu_id (str, optional): ID of the menu to create. If not provided, a new UUID will be generated.

    Methods:
        to_domain() -> CreateMenu:
            Converts the instance to a domain model object for adding a menu.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    # author_id: str
    client_id: str
    tags: set[ApiTag] = Field(default_factory=set)
    description: str | None = None

    @field_serializer('tags')
    def serialize_tags(self, tags: set[ApiTag], _info):
        return list(tags)

    def to_domain(self) -> CreateMenu:
        """Converts the instance to a domain model object for creating a menu."""
        try:
            return CreateMenu(
                # author_id=self.author_id,
                client_id=self.client_id,
                tags={tag.to_domain() for tag in self.tags},
                description=self.description,
            )
        except Exception as e:
            raise ValueError(f"Failed to convert ApiCreateMenu to domain model: {e}")
