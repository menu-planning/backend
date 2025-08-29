from abc import ABC, abstractmethod
from typing import Annotated, Any, Generic, TypeVar

from pydantic import Field

from src.contexts.iam.core.adapters.ORM.sa_models.user_sa_model import UserSaModel
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import (
    UUIDIdRequired,
)
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import (
    BaseApiValueObject,
)
from src.contexts.seedwork.shared.adapters.api_schemas.value_objects import (
    ApiSeedRole,
)
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser

D_USER = TypeVar("D_USER", bound=SeedUser)
S_USER = TypeVar("S_USER", bound=UserSaModel)
API_SEED_USER = TypeVar("API_SEED_USER", bound="ApiSeedUser")
API_SEED_ROLE = TypeVar("API_SEED_ROLE", bound=ApiSeedRole)


class ApiSeedUser(
    BaseApiValueObject[D_USER, S_USER],
    Generic[API_SEED_USER, API_SEED_ROLE, D_USER, S_USER],
    ABC,
):
    """Abstract base schema for the SeedUser value object.

    This class defines the interface for user schemas that can convert between
    domain objects, ORM models, and API representations. It enforces that all
    subclasses implement the required conversion methods.

    The class uses generic type parameters to ensure type safety across the
    conversion chain:
    - API_SEED_USER: The concrete API user class type
    - API_SEED_ROLE: The concrete API role class type
    - D_USER: The domain user type
    - S_USER: The ORM user model type

    Fields:
        id: Unique identifier for the user (UUID string)
        roles: Immutable set of roles assigned to the user

    Note:
        This class cannot be instantiated directly. Subclasses must implement
        the abstract conversion methods to provide concrete functionality.
    """

    id: UUIDIdRequired
    roles: Annotated[
        frozenset[API_SEED_ROLE],
        Field(
            default_factory=frozenset,
            description="Immutable set of roles assigned to the user",
        ),
    ]

    @classmethod
    @abstractmethod
    def from_domain(cls, domain_obj: D_USER) -> API_SEED_USER:
        """Convert a SeedUser domain object to an ApiSeedUser instance.

        This method handles the conversion from domain model to API schema,
        including all necessary type transformations and data mapping.

        Type Conversions:
            - Domain set[SeedRole] → API frozenset[ApiSeedRole]
            - Domain UUID → API string representation
            - Any domain-specific types → API-compatible types

        Args:
            domain_obj: The SeedUser domain object to convert from

        Returns:
            An instance of the concrete ApiSeedUser subclass

        Raises:
            ValueError: If the domain object contains invalid data
            TypeError: If type conversion fails

        Example:
            >>> domain_user = SeedUser(id=uuid4(), roles={admin_role})
            >>> api_user = ApiUser.from_domain(domain_user)
            >>> assert isinstance(api_user, ApiUser)
        """

    @abstractmethod
    def to_domain(self) -> D_USER:
        """Convert the ApiSeedUser instance to a SeedUser domain object.

        This method handles the conversion from API schema back to domain model,
        including all necessary type transformations and validation.

        Type Conversions:
            - API string ID → Domain UUID object
            - API frozenset[ApiSeedRole] → Domain set[SeedRole]
            - API string types → Domain enum/object types

        Returns:
            A SeedUser domain object instance

        Raises:
            ValueError: If the API data cannot be converted to valid domain types
            TypeError: If type conversion fails

        Example:
            >>> domain_user = api_user.to_domain()
            >>> assert isinstance(domain_user, SeedUser)
            >>> assert isinstance(domain_user.id, UUID)
        """

    @classmethod
    @abstractmethod
    def from_orm_model(cls, orm_model: S_USER) -> API_SEED_USER:
        """Convert an ORM model to an ApiSeedUser instance.

        This method handles the conversion from SQLAlchemy ORM model to API schema,
        including relationship handling and data extraction.

        ORM Conversions:
            - ORM list[RoleSaModel] → API frozenset[ApiSeedRole]
            - ORM relationship objects → API value objects
            - ORM nullable fields → API optional fields

        Args:
            orm_model: The SQLAlchemy ORM model to convert from

        Returns:
            An instance of the concrete ApiSeedUser subclass

        Raises:
            ValueError: If the ORM model contains invalid data
            AttributeError: If required ORM attributes are missing

        Example:
            >>> orm_user = UserSaModel.query.get(user_id)
            >>> api_user = ApiUser.from_orm_model(orm_user)
            >>> assert isinstance(api_user, ApiUser)
        """

    def to_orm_kwargs(self) -> dict[str, Any]:
        """Convert the ApiSeedUser instance to ORM model kwargs.

        This method prepares the API schema data for ORM model creation or updates.
        It handles the conversion from API types to ORM-compatible types and
        structures the data appropriately for database operations.

        API → ORM Conversions:
            - API frozenset[ApiSeedRole] → ORM role data list
            - API string ID → ORM-compatible ID format
            - API value objects → ORM attribute values

        Note:
            In complex scenarios with many-to-many relationships, role data
            may be handled separately by the repository layer for proper
            transaction management and relationship persistence.

        Returns:
            Dictionary of keyword arguments suitable for ORM model creation
            or update operations

        Example:
            >>> kwargs = api_user.to_orm_kwargs()
            >>> orm_user = UserSaModel(**kwargs)
            >>> assert orm_user.id == api_user.id

        Structure:
            {
                "id": "uuid-string",
                "roles": [
                    {"name": "admin", "permissions": ["read", "write"]},
                    {"name": "user", "permissions": ["read"]}
                ]
            }
        """
        return {
            "id": self.id,
            "roles": (
                [role.to_orm_kwargs() for role in self.roles] if self.roles else []
            ),
        }
