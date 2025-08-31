from typing import Any

from src.contexts.recipes_catalog.core.adapters.client.api_schemas.entities.api_menu import (
    ApiMenu,
)
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.entities.api_menu_fields import (
    MenuDescriptionOptional,
    MenuNameRequired,
    MenuNotesOptional,
    MenuTagsOptional,
)
from src.contexts.recipes_catalog.core.domain.client.commands.update_menu import (
    UpdateMenu,
)
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import (
    UUIDIdRequired,
)
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import (
    BaseApiCommand,
)


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

    name: MenuNameRequired | None = None
    description: MenuDescriptionOptional
    notes: MenuNotesOptional
    tags: MenuTagsOptional

    def to_domain(self) -> dict[str, Any]:
        """Converts the instance to a dictionary of attributes to update."""
        try:
            # Manual field conversion to avoid model_dump issues with frozensets
            updates = {}

            # Get fields that are frozenset (exclude_unset behavior)
            fields_set = self.__pydantic_fields_set__

            # Simple fields that can be included directly
            simple_fields = ["name", "description", "notes"]

            for field in simple_fields:
                if field in fields_set:
                    value = getattr(self, field)
                    updates[field] = value

            # Complex fields that need special handling
            if "tags" in fields_set and self.tags is not None:
                updates["tags"] = frozenset([tag.to_domain() for tag in self.tags])
        except Exception as e:
            error_msg = (
                f"Failed to convert ApiAttributesToUpdateOnMenu to domain model: {e}"
            )
            raise ValueError(error_msg) from e
        else:
            return updates


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

    menu_id: UUIDIdRequired
    updates: ApiAttributesToUpdateOnMenu

    def to_domain(self) -> UpdateMenu:
        """Converts the instance to a domain model object for updating a menu."""
        try:
            return UpdateMenu(
                menu_id=self.menu_id,
                updates=self.updates.to_domain(),
            )
        except Exception as e:
            error_msg = f"Failed to convert ApiUpdateMenu to domain model: {e}"
            raise ValueError(error_msg) from e

    @classmethod
    def from_api_menu(
        cls, api_menu: ApiMenu, old_api_menu: ApiMenu | None = None
    ) -> "ApiUpdateMenu":
        """Creates an instance from an existing menu.

        Args:
            api_menu: The new/updated menu data.
            old_api_menu: Optional. The original menu to compare against.
                         If provided, only changed fields will be included in updates.
                         If not provided, all fields will be included
                         (previous behavior).

        Returns:
            ApiUpdateMenu instance with only the changed attributes
            (if old_api_menu provided) or all attributes
            (if old_api_menu not provided).
        """
        # Only extract fields that ApiAttributesToUpdateOnMenu accepts
        allowed_fields = ApiAttributesToUpdateOnMenu.model_fields.keys()
        attributes_to_update = {}

        for key in allowed_fields:
            new_value = getattr(api_menu, key)

            # If no old menu provided, include all fields (current behavior)
            if old_api_menu is None:
                attributes_to_update[key] = new_value
            else:
                # Compare with old value and only include if changed
                old_value = getattr(old_api_menu, key)
                if new_value != old_value:
                    attributes_to_update[key] = new_value

        return cls(
            menu_id=api_menu.id,
            updates=ApiAttributesToUpdateOnMenu(**attributes_to_update),
        )
