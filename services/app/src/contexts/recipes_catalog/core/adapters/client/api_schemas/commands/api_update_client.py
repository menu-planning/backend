from typing import Any

from src.contexts.recipes_catalog.core.adapters.client.api_schemas.root_aggregate.api_client import ApiClient
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.root_aggregate.api_client_fields import ClientAddressOptional, ClientContactInfoOptinal, ClientNotesOptional, ClientProfileRequired, ClientTagsOptionalFrozenset
from src.contexts.recipes_catalog.core.domain.client.commands.update_client import UpdateClient
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import UUIDIdRequired
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiCommand


class ApiAttributesToUpdateOnClient(BaseApiCommand[UpdateClient]):
    """
    A Pydantic model representing and validating the data required
    to update a client via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        profile (ClientProfileRequired, optional): Profile information of the client.
        contact_info (ClientContactInfoOptinal, optional): Contact information of the client.
        address (ClientAddressOptional, optional): Address of the client.
        tags (ClientTagsOptionalFrozenset, optional): Tags associated with the client.
        notes (ClientNotesOptional, optional): Additional notes about the client.

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

    def to_domain(self) -> dict[str, Any]:
        """Converts the instance to a dictionary of attributes to update."""
        try:
            # Manual field conversion to avoid model_dump issues with complex types
            updates = {}
            
            # Get fields that are set (exclude_unset behavior)
            fields_set = self.__pydantic_fields_set__
            
            # Simple fields that can be included directly
            simple_fields = ["notes"]
            
            for field in simple_fields:
                if field in fields_set:
                    value = getattr(self, field)
                    updates[field] = value
            
            # Complex fields that need special handling
            if "profile" in fields_set and self.profile is not None:
                updates["profile"] = self.profile.to_domain()
            
            if "contact_info" in fields_set and self.contact_info is not None:
                updates["contact_info"] = self.contact_info.to_domain()
            
            if "address" in fields_set and self.address is not None:
                updates["address"] = self.address.to_domain()
            
            if "tags" in fields_set and self.tags is not None:
                updates["tags"] = frozenset([tag.to_domain() for tag in self.tags])
            
            return updates
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
    def from_api_client(cls, api_client: ApiClient, old_api_client: ApiClient | None = None) -> "ApiUpdateClient":
        """Creates an instance from an existing client.
        
        Args:
            api_client: The new/updated client data.
            old_api_client: Optional. The original client to compare against.
                           If provided, only changed fields will be included in updates.
                           If not provided, all fields will be included (previous behavior).
        
        Returns:
            ApiUpdateClient instance with only the changed attributes (if old_api_client provided)
            or all attributes (if old_api_client not provided).
        """
        # Only extract fields that ApiAttributesToUpdateOnClient accepts
        allowed_fields = ApiAttributesToUpdateOnClient.model_fields.keys()
        attributes_to_update = {}
        
        for key in allowed_fields:
            new_value = getattr(api_client, key)
            
            # If no old client provided, include all fields (current behavior)
            if old_api_client is None:
                attributes_to_update[key] = new_value
            else:
                # Compare with old value and only include if changed
                old_value = getattr(old_api_client, key)
                if new_value != old_value:
                    attributes_to_update[key] = new_value
        
        return cls(
            client_id=api_client.id,
            updates=ApiAttributesToUpdateOnClient(**attributes_to_update),
        )
