from src.contexts.recipes_catalog.core.adapters.client.api_schemas.entities.api_menu_fields import (
    MenuDescriptionOptional,
    MenuTagsOptional,
)
from src.contexts.recipes_catalog.core.domain.client.commands.create_menu import (
    CreateMenu,
)
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import (
    UUIDIdRequired,
)
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import (
    BaseApiCommand,
)
from src.db.base import SaBase


class ApiCreateMenu(BaseApiCommand[CreateMenu]):
    """
    A Pydantic model representing and validating the data required
    to add a new menu via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        client_id (str): ID of the client the menu belongs to.
        description (str, optional): Description of the menu.
        tags (frozenset[ApiTag], optional): Tags associated with the menu.

    Methods:
        to_domain() -> CreateMenu:
            Converts the instance to a domain model object for creating a menu.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    client_id: UUIDIdRequired
    description: MenuDescriptionOptional
    tags: MenuTagsOptional

    def to_domain(self) -> CreateMenu:
        """Converts the instance to a domain model object for creating a menu."""
        try:
            return CreateMenu(
                client_id=self.client_id,
                description=self.description,
                tags=frozenset([tag.to_domain() for tag in self.tags]) if self.tags else None,
            )
        except Exception as e:
            raise ValueError(f"Failed to convert ApiCreateMenu to domain model: {e}")
