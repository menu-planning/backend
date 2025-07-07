from typing import Any

from src.contexts.recipes_catalog.core.adapters.client.api_schemas.entities.api_menu_fields import MenuDescription, MenuName, MenuNotes, MenuTags
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.entities.api_menu import ApiMenu
from src.contexts.recipes_catalog.core.domain.client.commands.update_menu import UpdateMenu
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiCommand
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import UUIDId


class ApiAttributesToUpdateOnMenu(BaseApiCommand[UpdateMenu]):
    """
    A Pydantic model representing and validating the data required
    to update a menu via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        name (str, optional): Name of the menu.
        description (str, optional): Description of the menu.
        notes (str, optional): Additional notes about the menu.
        tags (frozenset[ApiTag], optional): Tags associated with the menu.

    Methods:
        to_domain() -> dict:
            Converts the instance to a dictionary of attributes to update.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    name: MenuName | None = None
    description: MenuDescription
    notes: MenuNotes
    tags: MenuTags

    def to_domain(self) -> dict[str, Any]:
        """Converts the instance to a dictionary of attributes to update."""
        try:
            return self.model_dump(exclude_unset=True)
        except Exception as e:
            raise ValueError(
                f"Failed to convert ApiAttributesToUpdateOnMenu to domain model: {e}"
            )


class ApiUpdateMenu(BaseApiCommand[UpdateMenu]):
    """
    A Pydantic model representing and validating the data required
    to update a menu via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        menu_id (str): ID of the menu to update.
        updates (ApiAttributesToUpdateOnMenu): Attributes to update.

    Methods:
        to_domain() -> UpdateMenu:
            Converts the instance to a domain model object for updating a menu.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    menu_id: UUIDId
    updates: ApiAttributesToUpdateOnMenu

    def to_domain(self) -> UpdateMenu:
        """Converts the instance to a domain model object for updating a menu."""
        try:
            return UpdateMenu(
                menu_id=self.menu_id,
                updates=self.updates.to_domain(),
            )
        except Exception as e:
            raise ValueError(f"Failed to convert ApiUpdateMenu to domain model: {e}")

    @classmethod
    def from_api_menu(cls, api_menu: ApiMenu) -> "ApiUpdateMenu":
        """Creates an instance from an existing menu."""
        attributes_to_update = {
            key: getattr(api_menu, key) for key in api_menu.__class__.model_fields.keys()
        }
        # attributes_to_update["meals"] = set(api_menu.meals.values()) if api_menu.meals else None
        return cls(
            menu_id=api_menu.id,
            updates=ApiAttributesToUpdateOnMenu(**attributes_to_update),
        )
