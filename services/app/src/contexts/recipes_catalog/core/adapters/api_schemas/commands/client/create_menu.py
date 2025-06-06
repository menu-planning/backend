from src.contexts.seedwork.shared.adapters.api_schemas.base import BaseCommand
from src.contexts.recipes_catalog.core.domain.commands.client.create_menu import CreateMenu
from src.contexts.seedwork.shared.adapters.api_schemas.fields import UUIDId
from src.db.base import SaBase
from src.contexts.recipes_catalog.core.adapters.api_schemas.entities.menu.fields import (
    MenuDescription,
    MenuTags,
)


class ApiCreateMenu(BaseCommand[CreateMenu, SaBase]):
    """
    A Pydantic model representing and validating the data required
    to add a new menu via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        client_id (str): ID of the client the menu belongs to.
        description (str, optional): Description of the menu.
        tags (set[ApiTag], optional): Tags associated with the menu.

    Methods:
        to_domain() -> CreateMenu:
            Converts the instance to a domain model object for creating a menu.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    client_id: UUIDId
    description: MenuDescription
    tags: MenuTags

    def to_domain(self) -> CreateMenu:
        """Converts the instance to a domain model object for creating a menu."""
        try:
            return CreateMenu(
                client_id=self.client_id,
                description=self.description,
                tags={tag.to_domain() for tag in self.tags} if self.tags else None,
            )
        except Exception as e:
            raise ValueError(f"Failed to convert ApiCreateMenu to domain model: {e}")
