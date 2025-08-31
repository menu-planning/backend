from src.contexts.recipes_catalog.core.domain.client.commands.delete_menu import (
    DeleteMenu,
)
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import (
    UUIDIdRequired,
)
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import (
    BaseApiCommand,
)
from src.db.base import SaBase


class ApiDeleteMenu(BaseApiCommand[DeleteMenu]):
    """
    A Pydantic model representing and validating the data required
    to delete a menu via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        menu_id (str): ID of the menu to delete.

    Methods:
        to_domain() -> DeleteMenu:
            Converts the instance to a domain model object for deleting a menu.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    menu_id: UUIDIdRequired

    def to_domain(self) -> DeleteMenu:
        """Converts the instance to a domain model object for deleting a menu."""
        try:
            return DeleteMenu(menu_id=self.menu_id)
        except Exception as e:
            raise ValueError(f"Failed to convert ApiDeleteMenu to domain model: {e}")
