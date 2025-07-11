from typing import Any

from pydantic import field_serializer
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.root_aggregate.api_client import ApiClient
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.root_aggregate.api_client_fields import ClientAddressOptional, ClientContactInfoOptinal, ClientNotesOptional, ClientProfileRequired, ClientTagsOptionalFrozenset
from src.contexts.recipes_catalog.core.domain.client.commands.update_client import UpdateClient
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import UUIDIdRequired
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_address import ApiAddress
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_contact_info import ApiContactInfo
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_profile import ApiProfile
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiCommand


class ApiAttributesToUpdateOnClient(BaseApiCommand[UpdateClient]):
    """
    A Pydantic model representing and validating the data required
    to update a client via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        profile (ApiProfile, optional): Profile information of the client.
        contact_info (ApiContactInfo, optional): Contact information of the client.
        address (ApiAddress, optional): Address of the client.
        tags (set[ApiTag], optional): Tags associated with the client.
        notes (str, optional): Additional notes about the client.

    Methods:
        to_domain() -> dict:
            Converts the instance to a dictionary of attributes to update.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    profile: ClientProfileRequired | None = None
    contact_info: ClientContactInfoOptinal | None = None
    address: ClientAddressOptional | None = None
    tags: ClientTagsOptionalFrozenset | None = None
    notes: ClientNotesOptional | None = None

    @field_serializer("profile")
    def serialize_profile(self, profile: ApiProfile | None, _info):
        """Serializes the profile to a domain model."""
        return profile.to_domain() if profile else None
    
    @field_serializer("contact_info")
    def serialize_contact_info(self, contact_info: ApiContactInfo | None, _info):
        """Serializes the contact info to a domain model."""
        return contact_info.to_domain() if contact_info else None
     
    @field_serializer("address")
    def serialize_address(self, address: ApiAddress | None, _info):
        """Serializes the address to a domain model."""
        return address.to_domain() if address else None

    @field_serializer("tags")
    def serialize_tags(self, tags: list[ApiTag] | None, _info):
        """Serializes the tag list to a list of domain models."""
        return {i.to_domain() for i in tags} if tags else set()

    def to_domain(self) -> dict[str, Any]:
        """Converts the instance to a dictionary of attributes to update."""
        try:
            return self.model_dump(exclude_unset=True)
        except Exception as e:
            raise ValueError(
                f"Failed to convert ApiAttributesToUpdateOnClient to domain model: {e}"
            )


class ApiUpdateClient(BaseApiCommand[UpdateClient]):
    """
    A Pydantic model representing and validating the data required
    to update a client via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        client_id (str): ID of the client to update.
        updates (ApiAttributesToUpdateOnClient): Attributes to update.

    Methods:
        to_domain() -> UpdateClient:
            Converts the instance to a domain model object for updating a client.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    client_id: UUIDIdRequired
    updates: ApiAttributesToUpdateOnClient

    def to_domain(self) -> UpdateClient:
        """Converts the instance to a domain model object for updating a client."""
        try:
            return UpdateClient(
                client_id=self.client_id,
                updates=self.updates.to_domain(),
            )
        except Exception as e:
            raise ValueError(f"Failed to convert ApiUpdateClient to domain model: {e}")

    @classmethod
    def from_api_client(cls, api_client: ApiClient) -> "ApiUpdateClient":
        """Creates an instance from an existing client."""
        attributes_to_update = {
            key: getattr(api_client, key) for key in ApiClient.model_fields.keys()
        }
        return cls(
            client_id=api_client.id,
            updates=ApiAttributesToUpdateOnClient(**attributes_to_update),
        )
