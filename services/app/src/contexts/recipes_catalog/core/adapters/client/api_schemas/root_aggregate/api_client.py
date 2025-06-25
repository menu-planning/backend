from datetime import datetime
from typing import Any, Dict
from pydantic import field_validator

from src.contexts.recipes_catalog.core.adapters.client.ORM.sa_models.client_sa_model import ClientSaModel
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.entities.api_menu import ApiMenu
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.root_aggregate.api_client_fields import ClientAddress, ClientContactInfo, ClientMenus, ClientNotes, ClientProfile, ClientTags
from src.contexts.recipes_catalog.core.domain.client.root_aggregate.client import Client
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseEntity
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import UUIDId
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.address import ApiAddress
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.contact_info import ApiContactInfo
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.profile import ApiProfile
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag import ApiTag, TagFrozensetAdapter


class ApiClient(BaseEntity[Client, ClientSaModel]):
    """
    A Pydantic model representing and validating a client encompassing
    details about the client, their profile, contact information, and
    additional metadata.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        id (str): Unique identifier of the client.
        author_id (str): ID of the user who created the client.
        profile (ApiProfile): Profile information of the client.
        contact_info (ApiContactInfo, optional): Contact information of the client.
        address (ApiAddress, optional): Address of the client.
        tags (frozenset[ApiTag]): Frozenset of tags associated with the client.
        menus (list[ApiMenu]): List of menus associated with the client.
        notes (str, optional): Additional notes about the client.
        created_at (datetime): Timestamp of client creation.
        updated_at (datetime): Timestamp of last update.
        discarded (bool): Indicates if the client is discarded.
        version (int): Version of the client.

    Raises:
        ValueError: If the instance cannot be converted to a domain model or
            if it this class cannot be instantiated from a domain model.
        ValidationError: If the instance is invalid.
    """

    id: UUIDId
    author_id: UUIDId
    profile: ClientProfile
    contact_info: ClientContactInfo
    address: ClientAddress
    tags: ClientTags
    menus: ClientMenus
    notes: ClientNotes

    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: frozenset[ApiTag]) -> frozenset[ApiTag]:
        """Validate tags using TypeAdapter."""
        return TagFrozensetAdapter.validate_python(v)

    @classmethod
    def from_domain(cls, domain_obj: Client) -> "ApiClient":
        """Convert a domain object to an API schema instance."""
        return cls(
            id=domain_obj.id,
            author_id=domain_obj.author_id,
            profile=ApiProfile.from_domain(domain_obj.profile),
            contact_info=ApiContactInfo.from_domain(domain_obj.contact_info) if domain_obj.contact_info else None,
            address=ApiAddress.from_domain(domain_obj.address) if domain_obj.address else None,
            tags=TagFrozensetAdapter.validate_python(frozenset(ApiTag.from_domain(t) for t in domain_obj.tags)),
            menus=[ApiMenu.from_domain(m) for m in domain_obj.menus],
            notes=domain_obj.notes,
            created_at=domain_obj.created_at or datetime.now(),
            updated_at=domain_obj.updated_at or datetime.now(),
            discarded=domain_obj.discarded,
            version=domain_obj.version,
        )

    def to_domain(self) -> Client:
        """Convert the API schema instance to a domain object."""
        return Client(
            id=self.id,
            author_id=self.author_id,
            profile=self.profile.to_domain(),
            contact_info=self.contact_info.to_domain() if self.contact_info else None,
            address=self.address.to_domain() if self.address else None,
            tags=set(t.to_domain() for t in self.tags),
            menus=[m.to_domain() for m in self.menus],
            notes=self.notes,
            created_at=self.created_at,
            updated_at=self.updated_at,
            discarded=self.discarded,
            version=self.version,
        )

    @classmethod
    def from_orm_model(cls, orm_model: ClientSaModel) -> "ApiClient":
        """Convert an ORM model to an API schema instance."""
        return cls(
            id=orm_model.id,
            author_id=orm_model.author_id,
            profile=ApiProfile.from_orm_model(orm_model.profile),
            contact_info=ApiContactInfo.from_orm_model(orm_model.contact_info) if orm_model.contact_info else None,
            address=ApiAddress.from_orm_model(orm_model.address) if orm_model.address else None,
            tags=TagFrozensetAdapter.validate_python(frozenset(ApiTag.from_orm_model(t) for t in orm_model.tags)),
            menus=[ApiMenu.from_orm_model(m) for m in orm_model.menus],
            notes=orm_model.notes,
            created_at=orm_model.created_at or datetime.now(),
            updated_at=orm_model.updated_at or datetime.now(),
            discarded=orm_model.discarded,
            version=orm_model.version,
        )

    def to_orm_kwargs(self) -> Dict[str, Any]:
        """Convert the API schema instance to ORM model kwargs."""
        return {
            "id": self.id,
            "author_id": self.author_id,
            "profile": self.profile.to_orm_kwargs(),
            "contact_info": self.contact_info.to_orm_kwargs() if self.contact_info else None,
            "address": self.address.to_orm_kwargs() if self.address else None,
            "tags": [t.to_orm_kwargs() for t in self.tags],
            "menus": [m.to_orm_kwargs() for m in self.menus],
            "notes": self.notes,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "discarded": self.discarded,
            "version": self.version,
        }
