from pydantic import BaseModel, Field, field_serializer

from src.contexts.recipes_catalog.core.domain.commands.client.create_client import CreateClient
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.address import ApiAddress
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.contact_info import ApiContactInfo
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.profile import ApiProfile
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag import ApiTag


class ApiCreateClient(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to add a new client via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        author_id (str, optional): ID of the user who created the client.
        profile (ApiProfile): Profile information of the client.
        contact_info (ApiContactInfo): Contact information of the client.
        address (ApiAddress, optional): Address of the client.
        notes (str, optional): Additional notes about the client.

    Methods:
        to_domain() -> CreateClient:
            Converts the instance to a domain model object for adding a client.

    Raises:
        ValueError: If the instance cannot be converted to a domain model.
        ValidationError: If the instance is invalid.

    """

    author_id: str
    profile: ApiProfile
    contact_info: ApiContactInfo | None = None
    address: ApiAddress | None = None
    tags: set[ApiTag] = Field(default_factory=set)
    notes: str | None = None

    @field_serializer('tags')
    def serialize_tags(self, tags: set[ApiTag], _info):
        return list(tags)

    def to_domain(self) -> CreateClient:
        """Converts the instance to a domain model object for creating a client."""
        try:
            return CreateClient(
                author_id=self.author_id,
                profile=self.profile.to_domain(),
                contact_info=self.contact_info.to_domain() if self.contact_info else None,
                address=self.address.to_domain() if self.address else None,
                tags={tag.to_domain() for tag in self.tags},
                notes=self.notes,
            )
        except Exception as e:
            raise ValueError(f"Failed to convert ApiCreateClient to domain model: {e}")
