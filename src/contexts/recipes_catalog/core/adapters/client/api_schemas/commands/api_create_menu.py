from typing import Any

from pydantic import ValidationInfo, field_validator
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.entities.api_menu_fields import (
    MenuDescriptionOptional,
    MenuTagsOptional,
)
from src.contexts.recipes_catalog.core.domain.client.commands.create_menu import (
    CreateMenu,
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
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import (
    ApiTag,
)


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
        ValidationConversionError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    client_id: UUIDIdRequired
    description: MenuDescriptionOptional
    tags: MenuTagsOptional

    @field_validator("tags", mode="before")
    @classmethod
    def validate_tags(
        cls, v: list[dict[str, Any]], info: ValidationInfo
    ) -> frozenset[ApiTag]:
        return frozenset(
            [
                ApiTag(
                    key=tag.get("key", ""),
                    value=tag.get("value", ""),
                    author_id=info.data["author_id"],
                    type="menu",
                )
                for tag in v
            ]
            if v
            else []
        )

    def to_domain(self, author_id) -> CreateMenu:
        """Converts the instance to a domain model object for creating a menu."""
        try:
            return CreateMenu(
                author_id=author_id,
                client_id=self.client_id,
                description=self.description,
                tags=(
                    frozenset([tag.to_domain() for tag in self.tags])
                    if self.tags
                    else None
                ),
            )
        except Exception as e:
            raise ValidationConversionError(
                f"Failed to convert ApiCreateMenu to domain model: {e}",
                schema_class=self.__class__,
                conversion_direction="api_to_domain",
                source_data=self.model_dump(),
                validation_errors=[str(e)],
            ) from e
