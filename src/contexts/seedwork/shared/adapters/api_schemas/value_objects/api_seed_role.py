from abc import ABC, abstractmethod
from typing import Annotated, Any, Generic, TypeVar

from pydantic import AfterValidator, Field

from src.contexts.iam.core.adapters.ORM.sa_models.role_sa_model import RoleSaModel
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import (
    SanitizedText,
)
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import (
    BaseApiValueObject,
)
from src.contexts.seedwork.shared.adapters.api_schemas.validators import (
    validate_role_name_format,
)
from src.contexts.seedwork.shared.domain.value_objects.role import SeedRole

D_ROLE = TypeVar("D_ROLE", bound=SeedRole)
S_ROLE = TypeVar("S_ROLE", bound=RoleSaModel)
API_SEED_ROLE = TypeVar("API_SEED_ROLE", bound="ApiSeedRole")


class ApiSeedRole(
    BaseApiValueObject[D_ROLE, S_ROLE],
    Generic[API_SEED_ROLE, D_ROLE, S_ROLE],
    ABC,
):
    """Abstract base schema for the SeedRole value object.

    This class defines the interface for role schemas that can convert between
    domain objects, ORM models, and API representations. It enforces that all
    subclasses implement the required conversion methods.

    The class uses generic type parameters to ensure type safety across the
    conversion chain:
    - API_SEED_ROLE: The concrete API role class type
    - D_ROLE: The domain role type
    - S_ROLE: The ORM role model type

    Fields:
        name: The name of the IAM role (sanitized and validated)
        permissions: Immutable set of permissions associated with the role

    Validation Strategy:
        - BeforeValidator(validate_optional_text): Input sanitization
                                                   (trim, handle None/empty)
        - AfterValidator(validate_role_name_format): Business logic validation
                                                     (type-safe)
        - BeforeValidator(validate_permissions_collection): Complex type conversion
                                                            with clear errors

    Note:
        This class cannot be instantiated directly. Subclasses must implement
        the abstract conversion methods to provide concrete functionality.
    """

    name: Annotated[
        SanitizedText,
        AfterValidator(validate_role_name_format),
        Field(..., min_length=3, max_length=50, description="The name of the IAM role"),
    ]
    permissions: Annotated[
        frozenset[str],
        Field(
            default_factory=frozenset,
            description="Immutable set of permissions associated with the role",
        ),
    ]

    @classmethod
    @abstractmethod
    def from_domain(cls, domain_obj: D_ROLE) -> API_SEED_ROLE:
        """Convert a SeedRole domain object to an ApiSeedRole instance.

        This method handles the conversion from domain model to API schema,
        including all necessary type transformations and data mapping.

        Type Conversions:
            - Domain set[str] → API frozenset[str] (ensures immutability)
            - Domain role name → API sanitized and validated name
            - Domain permission collections → API frozenset format

        Args:
            domain_obj: The SeedRole domain object to convert from

        Returns:
            An instance of the concrete ApiSeedRole subclass

        Raises:
            ValueError: If the domain object contains invalid data
            TypeError: If type conversion fails

        Example:
            >>> domain_role = SeedRole(name="admin", permissions={"read", "write"})
            >>> api_role = ApiRole.from_domain(domain_role)
            >>> assert isinstance(api_role, ApiRole)
            >>> assert api_role.permissions == frozenset(["read", "write"])
        """

    @abstractmethod
    def to_domain(self) -> D_ROLE:
        """Convert the ApiSeedRole instance to a SeedRole domain object.

        This method handles the conversion from API schema back to domain model,
        including all necessary type transformations and validation.

        Type Conversions:
            - API frozenset[str] → Domain set[str] (maintains permission set)
            - API sanitized name → Domain role name
            - API string types → Domain-compatible types

        Returns:
            A SeedRole domain object instance

        Raises:
            ValueError: If the API data cannot be converted to valid domain types
            TypeError: If type conversion fails

        Example:
            >>> domain_role = api_role.to_domain()
            >>> assert isinstance(domain_role, SeedRole)
            >>> assert isinstance(domain_role.permissions, set)
        """

    @classmethod
    @abstractmethod
    def from_orm_model(cls, orm_model: S_ROLE) -> API_SEED_ROLE:
        """Convert an ORM model to an ApiSeedRole instance.

        This method handles the conversion from SQLAlchemy ORM model to API schema,
        including relationship handling and data extraction.

        ORM Conversions:
            - ORM comma-separated string → API frozenset[str]
            - ORM nullable fields → API optional fields
            - ORM string data → API validated and sanitized data

        Args:
            orm_model: The SQLAlchemy ORM model to convert from

        Returns:
            An instance of the concrete ApiSeedRole subclass

        Raises:
            ValueError: If the ORM model contains invalid data
            AttributeError: If required ORM attributes are missing

        Example:
            >>> orm_role = RoleSaModel.query.get(role_id)
            >>> api_role = ApiRole.from_orm_model(orm_role)
            >>> assert isinstance(api_role, ApiRole)
            >>> assert isinstance(api_role.permissions, frozenset)
        """

    def to_orm_kwargs(self) -> dict[str, Any]:
        """Convert the ApiSeedRole instance to ORM model kwargs.

        This method prepares the API schema data for ORM model creation or updates.
        It handles the conversion from API types to ORM-compatible types and
        structures the data appropriately for database operations.

        API → ORM Conversions:
            - API frozenset[str] → ORM comma-separated string
            - API validated name → ORM string field
            - API permission sets → ORM storage format

        Note:
            The permissions are stored as a comma-separated string in the ORM
            for simplicity, but this can be optimized for complex permission
            hierarchies in the future.

        Returns:
            Dictionary of keyword arguments suitable for ORM model creation
            or update operations

        Example:
            >>> kwargs = api_role.to_orm_kwargs()
            >>> orm_role = RoleSaModel(**kwargs)
            >>> assert orm_role.name == api_role.name
            >>> assert orm_role.permissions == "read, write"

        Structure:
            {
                "name": "admin",
                "permissions": "read, write"
            }
        """
        return {
            "name": self.name,
            "permissions": (
                ", ".join(sorted(self.permissions)) if self.permissions else ""
            ),
        }
