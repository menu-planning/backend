from typing import Any

from src.contexts.recipes_catalog.core.adapters.client.api_schemas.entities.api_menu import (
    ApiMenu,
)
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.entities.api_menu_fields import (
    MenuDescriptionOptional,
    MenuMealsOptional,
    MenuTagsOptional,
)
from src.contexts.recipes_catalog.core.domain.client.commands.update_menu import (
    UpdateMenu,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import (
    UUIDIdRequired,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_model import (
    BaseApiCommand,
)
from src.contexts.seedwork.adapters.exceptions.api_schema_errors import (
    ValidationConversionError,
)
from src.logging.logger import get_logger

logger =get_logger(__name__)


class ApiAttributesToUpdateOnMenu(BaseApiCommand[UpdateMenu]):
    """
    A Pydantic model representing and validating the data required
    to update a menu via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        description (str, optional): Description of the menu.
        notes (str, optional): Additional notes about the menu.
        tags (frozenset[ApiTag], optional): Tags associated with the menu.

    Methods:
        to_domain() -> dict:
            Converts the instance to a dictionary of attributes to update.

    Raises:
        ValidationConversionError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    meals: MenuMealsOptional
    tags: MenuTagsOptional
    description: MenuDescriptionOptional

    def to_domain(self) -> dict[str, Any]:
        """Converts the instance to a dictionary of attributes to update."""
        try:
            updates = {}

            fields_set = self.__pydantic_fields_set__

            simple_fields = ["description"]

            for field in simple_fields:
                if field in fields_set:
                    value = getattr(self, field)
                    updates[field] = value

            if "meals" in fields_set and self.meals is not None:
                updates["meals"] = [meal.to_domain() for meal in self.meals]

            if "tags" in fields_set and self.tags is not None:
                updates["tags"] = frozenset([tag.to_domain() for tag in self.tags])
        except Exception as e:
            error_msg = (
                f"Failed to convert ApiAttributesToUpdateOnMenu to domain model: {e}"
            )
            raise ValidationConversionError(
                error_msg,
                schema_class=self.__class__,
                conversion_direction="api_to_domain",
                source_data=self.model_dump(),
                validation_errors=[str(e)],
            ) from e
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
        ValidationConversionError: If the instance cannot be converted to a domain model.
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
            raise ValidationConversionError(
                error_msg,
                schema_class=self.__class__,
                conversion_direction="api_to_domain",
                source_data=self.model_dump(),
                validation_errors=[str(e)],
            ) from e

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
        allowed_fields = ApiAttributesToUpdateOnMenu.model_fields.keys()
        attributes_to_update = {}

        for key in allowed_fields:
            new_value = getattr(api_menu, key)

            if old_api_menu is None:
                attributes_to_update[key] = new_value
            else:
                old_value = getattr(old_api_menu, key)
                if new_value != old_value:
                    attributes_to_update[key] = new_value

        return cls(
            menu_id=api_menu.id,
            updates=ApiAttributesToUpdateOnMenu(**attributes_to_update),
        )