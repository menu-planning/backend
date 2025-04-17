from typing import Any

from pydantic import BaseModel, Field, field_serializer
from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.client.client import ApiClient
from src.contexts.recipes_catalog.shared.domain.commands.client.update_client import UpdateClient
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.address import ApiAddress
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.contact_info import ApiContactInfo
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.profile import ApiProfile
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag import ApiTag


class ApiAttributesToUpdateOnClient(BaseModel):
    """
    A pydantic model representing and validating the data required to update
    a Clinet via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        profile (ApiProfile): Profile information of the client.
        contact_info (ApiContactInfo): Contact information of the client.
        address (ApiAddress, optional): Address of the client.
        notes (str, optional): Additional notes about the client.

    Methods:
        to_domain() -> dict:
            Converts the instance to a dictionary of attributes to update.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    profile: ApiProfile | None = None
    contact_info: ApiContactInfo | None = None
    address: ApiAddress | None = None
    notes: str | None = None
    tags: set[ApiTag] | None = Field(default_factory=set)

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


class ApiUpdateClient(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to update a Client via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        client_id (str): Identifier of the Client to update.
        updates (ApiAttributesToUpdateOnClient): Attributes to update.

    Methods:
        to_domain() -> UpdateClient:
            Converts the instance to a domain model object for updating a Client.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    client_id: str
    updates: ApiAttributesToUpdateOnClient

    def to_domain(self) -> UpdateClient:
        """Converts the instance to a domain model object for updating a client."""
        try:
            return UpdateClient(client_id=self.client_id, updates=self.updates.to_domain())
        except Exception as e:
            raise ValueError(f"Failed to convert ApiUpdateClient to domain model: {e}")

    @classmethod
    def from_api_client(cls, api_client: ApiClient) -> "ApiUpdateClient":
        """Creates an instance from an existing client."""
        attributes_to_update = {
            key: getattr(api_client, key) for key in api_client.model_fields.keys()
        }
        return cls(
            client_id=api_client.id,
            updates=ApiAttributesToUpdateOnClient(**attributes_to_update),
        )
