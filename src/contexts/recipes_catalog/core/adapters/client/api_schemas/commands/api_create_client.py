from typing import Any, Optional

from pydantic import ValidationInfo, field_validator
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.root_aggregate.api_client_fields import (
    ClientAddressOptional,
    ClientContactInfoOptinal,
    ClientNotesOptional,
    ClientProfileRequired,
    ClientTagsOptionalFrozenset,
)
from src.contexts.recipes_catalog.core.domain.client.commands.create_client import (
    CreateClient,
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


class ApiCreateClient(BaseApiCommand[CreateClient]):
    """
    A Pydantic model representing and validating the data required
    to add a new client via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Supports two creation modes:
    1. Standard creation: Provide explicit field values
    2. Form response integration: Provide form_response_id for automatic data mapping

    Attributes:
        author_id (str): ID of the user who created the client.
        profile (ApiProfile): Profile information of the client.
        contact_info (ApiContactInfo, optional): Contact information of the client.
        address (ApiAddress, optional): Address of the client.
        tags (set[ApiTag]): Set of tags associated with the client.
        notes (str, optional): Additional notes about the client.
        form_response_id (str, optional): TypeForm response ID to fetch and map data from.
            When provided, automatically maps form data to client fields and stores
            original response in onboarding_data field.

    Precedence Rules:
        - Explicit field values take precedence over form response data
        - If form_response_id is provided, missing fields are populated from form data
        - Original form response is automatically stored in onboarding_data

    Methods:
        to_domain() -> CreateClient:
            Converts the instance to a domain model object for creating a client.

    Raises:
        ValidationConversionError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    author_id: UUIDIdRequired
    profile: ClientProfileRequired
    contact_info: ClientContactInfoOptinal
    address: ClientAddressOptional
    tags: ClientTagsOptionalFrozenset
    notes: ClientNotesOptional
    form_response_id: str | None = None

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
                    type="client",
                )
                for tag in v
            ]
            if v
            else []
        )

    def to_domain(self) -> CreateClient:
        """Converts the instance to a domain model object for creating a client."""
        try:
            return CreateClient(
                author_id=str(self.author_id),
                profile=self.profile.to_domain(),
                contact_info=(
                    self.contact_info.to_domain() if self.contact_info else None
                ),
                address=self.address.to_domain() if self.address else None,
                tags=(
                    frozenset([tag.to_domain() for tag in self.tags])
                    if self.tags
                    else None
                ),
                notes=self.notes,
                form_response_id=self.form_response_id,
            )
        except Exception as e:
            raise ValidationConversionError(
                f"Failed to convert ApiCreateClient to domain model: {e}",
                schema_class=self.__class__,
                conversion_direction="api_to_domain",
                source_data=self.model_dump(),
                validation_errors=[str(e)],
            ) from e
