from pydantic import BaseModel, Field

from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.menu.menu import ApiMenu
from src.contexts.recipes_catalog.shared.adapters.api_schemas.pydantic_validators import (
    CreatedAtValue,
)
from src.contexts.recipes_catalog.shared.domain.entities.client import Client
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.address import ApiAddress
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.contact_info import ApiContactInfo
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.profile import ApiProfile
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag import ApiTag
from src.logging.logger import logger


class ApiClient(BaseModel):
    """
    A Pydantic model representing and validating a meal encompassing
    details about the meal, its ingredients, preparation, and
    additional metadata.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        id (str): Unique identifier of the meal.
        author_id (str): ID of the user who created the meal.
        profile (ApiProfile): Profile information of the meal.
        contact_info (ApiContactInfo): Contact information of the meal.
        address (ApiAddress, optional): Address of the meal.
        notes (str, optional): Additional notes about the meal.
        created_at (CreatedAtValue, optional): Timestamp of meal creation.
        updated_at (CreatedAtValue, optional): Timestamp of last update.
        discarded (bool): Indicates if the meal is discarded.
        version (int): Version of the meal.

    Raises:
        ValueError: If the instance cannot be converted to a domain model or
            if it this class cannot be instantiated from a domain model.
        ValidationError: If the instance is invalid.

    Methods:
        from_domain(domain_obj: Client) -> "ApiClient":
            Creates an instance from a domain model object.
        to_domain() -> Client:
            Converts the instance to a domain model object.
    """

    id: str
    author_id: str
    profile: ApiProfile
    contact_info: ApiContactInfo | None = None
    address: ApiAddress | None = None
    tags: set[ApiTag] = Field(default_factory=set)
    menus: list[ApiMenu] = Field(default_factory=list)
    notes: str | None = None
    created_at: CreatedAtValue | None = None
    updated_at: CreatedAtValue | None = None
    discarded: bool = False
    version: int = 1

    @classmethod
    def from_domain(cls, domain_obj: Client) -> "ApiClient":
        """
        Creates an instance from a domain model object.

        Returns:
            ApiClient: Converted instance.
        """
        try:
            return cls(
                id=domain_obj.id,
                author_id=domain_obj.author_id,
                profile=ApiProfile.from_domain(domain_obj.profile),
                contact_info=ApiContactInfo.from_domain(domain_obj.contact_info) if domain_obj.contact_info else None,
                address=ApiAddress.from_domain(domain_obj.address)
                if domain_obj.address
                else None,
                tags=set([ApiTag.from_domain(t) for t in domain_obj.tags]),
                menus=[ApiMenu.from_domain(m) for m in domain_obj.menus],
                notes=domain_obj.notes,
                created_at=domain_obj.created_at,
                updated_at=domain_obj.updated_at,
                discarded=domain_obj.discarded,
                version=domain_obj.version,
            )
        except Exception as e:
            logger.error(f"Error converting domain object to API schema: {e}")
            raise ValueError("Error converting domain object to API schema") from e

    def to_domain(self) -> Client:
        """
        Converts the instance to a domain model object.

        Returns:
            Client: Converted domain model object.
        """
        try:
            return Client(
                id=self.id,
                author_id=self.author_id,
                profile=self.profile.to_domain(),
                contact_info=self.contact_info.to_domain() if self.contact_info else None,
                address=self.address.to_domain() if self.address else None,
                tags=set([t.to_domain() for t in self.tags]),
                menus=[m.to_domain() for m in self.menus],
                notes=self.notes,
                created_at=self.created_at,
                updated_at=self.updated_at,
                discarded=self.discarded,
                version=self.version,
            )
        except Exception as e:
            logger.error(f"Error converting API schema to domain object: {e}")
            raise ValueError("Error converting API schema to domain object") from e
