from src.contexts.recipes_catalog.core.adapters.client.api_schemas.root_aggregate.api_client_fields import ClientAddressOptional, ClientContactInfoOptinal, ClientNotesOptional, ClientProfileRequired, ClientTagsOptionalFrozenset
from src.contexts.recipes_catalog.core.domain.client.commands.create_client import CreateClient
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiCommand
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import UUIDIdRequired


class ApiCreateClient(BaseApiCommand[CreateClient]):
    """
    A Pydantic model representing and validating the data required
    to add a new client via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        author_id (str): ID of the user who created the client.
        profile (ApiProfile): Profile information of the client.
        contact_info (ApiContactInfo, optional): Contact information of the client.
        address (ApiAddress, optional): Address of the client.
        tags (set[ApiTag]): Set of tags associated with the client.
        notes (str, optional): Additional notes about the client.

    Methods:
        to_domain() -> CreateClient:
            Converts the instance to a domain model object for creating a client.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.
    """

    author_id: UUIDIdRequired
    profile: ClientProfileRequired
    contact_info: ClientContactInfoOptinal
    address: ClientAddressOptional
    tags: ClientTagsOptionalFrozenset
    notes: ClientNotesOptional

    def to_domain(self) -> CreateClient:
        """Converts the instance to a domain model object for creating a client."""
        try:
            return CreateClient(
                author_id=self.author_id,
                profile=self.profile.to_domain(),
                contact_info=self.contact_info.to_domain() if self.contact_info else None,
                address=self.address.to_domain() if self.address else None,
                tags=frozenset([tag.to_domain() for tag in self.tags]) if self.tags else None,
                notes=self.notes,
            )
        except Exception as e:
            raise ValueError(f"Failed to convert ApiCreateClient to domain model: {e}")
