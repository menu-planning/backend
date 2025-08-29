from datetime import datetime
from typing import Annotated, Any, ClassVar, Generic, Self, TypeVar

from pydantic import BaseModel, BeforeValidator, ConfigDict, Field

from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import (
    UUIDIdRequired,
)
from src.contexts.seedwork.shared.adapters.api_schemas.type_convertion_util import (
    TypeConversionUtility,
)
from src.contexts.seedwork.shared.domain.commands.command import Command
from src.contexts.seedwork.shared.domain.entity import Entity
from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject
from src.db.base import SaBase

MODEL_CONFIG = ConfigDict(
    # SECURITY & INTEGRITY SETTINGS
    frozen=True,  # Prevents accidental mutation
    strict=True,  # NO automatic conversions
    extra="forbid",  # Prevents injection attacks
    validate_assignment=True,  # Ensures consistency after creation
    # CONVERSION & COMPATIBILITY SETTINGS
    from_attributes=True,  # Enables ORM integration
    populate_by_name=True,  # Supports multiple naming
    # VALIDATION BEHAVIOR SETTINGS
    validate_default=True,  # Ensures defaults are correct
    str_strip_whitespace=True,  # Data cleansing
    # SERIALIZATION SETTINGS
    alias_generator=None,  # Can be overridden in subclasses for custom naming
    # PERFORMANCE SETTINGS
    arbitrary_types_allowed=False,  # Forces explicit validation
    revalidate_instances="never",  # Performance optimization for immutable objects
)

CONVERT = TypeConversionUtility()

D = TypeVar("D", bound=Entity | ValueObject)
E = TypeVar("E", bound=Entity)
V = TypeVar("V", bound=ValueObject)
C = TypeVar("C", bound=Command)
S = TypeVar("S", bound=SaBase)


def parse_datetime(value: Any) -> datetime | None:
    """Parse various datetime inputs into datetime objects.

    Handles:
    - datetime objects (returned as-is)
    - ISO formatted strings (converted to datetime)
    - None values (returned as-is)

    Args:
        value: The value to parse

    Returns:
        datetime object or None

    Raises:
        ValueError: If the value cannot be parsed as a datetime
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            # Handle both standard ISO format and Z suffix
            iso_string = value.replace("Z", "+00:00") if value.endswith("Z") else value
            return datetime.fromisoformat(iso_string)
        except ValueError as e:
            error_message = f"Invalid datetime format: {value}. Expected ISO format."
            raise ValueError(error_message) from e
    error_message = f"Expected datetime, string, or None, got {type(value).__name__}"
    raise ValueError(error_message)


class BaseApiCommand(BaseModel, Generic[C]):
    """Enhanced base class for command schemas with comprehensive validation and
    utilities.

    Commands represent actions or operations that should be performed on the system.
    They are immutable data structures that carry the intent and data needed to execute
    domain operations.

    Key Features:
    1. **Strict Type Validation**: Enforces exact type matches with no implicit
        conversions
    2. **Immutable Schemas**: All schemas are frozen for data integrity
    3. **Type Conversion Utilities**: Standardized utilities for common conversion
        patterns
    4. **Domain Command Translation**: Converts API commands to domain command objects

    Required Methods (must be implemented by subclasses):
    - to_domain() -> C: Convert API command to domain command object

    Usage Example:
        class ApiCreateUser(BaseApiCommand):
            name: str
            email: str
            active: bool = True

            def to_domain(self) -> CreateUserCommand:
                return CreateUserCommand(
                    name=self.name,
                    email=self.email,
                    active=self.active
                )

    Note on Commands:
        Commands are write-only operations that don't return data. They only need
        to_domain() conversion since they flow from API to domain layer but not back.
    """

    # Strict validation configuration - IMMUTABLE AND ENFORCED
    model_config = MODEL_CONFIG

    # Type conversion utility - available to all schemas
    convert: ClassVar[TypeConversionUtility] = CONVERT

    def to_domain(self) -> C:
        """Convert the API schema instance to a domain object.

        This method must be implemented by all API schema subclasses. It should handle
        all necessary type conversions from API types to domain types.

        Key Responsibilities:
        - Convert string IDs to UUID objects using convert.string_to_uuid()
        - Convert string values to enum instances using convert.string_to_enum()
        - Convert immutable frozensets to mutable sets using convert.frozenset_to_set()
        - Convert ISO strings to datetime objects using convert.isostring_to_datetime()
        - Handle any API-specific type transformations

        Returns:
            The corresponding domain object with properly converted types

        Raises:
            NotImplementedError: If not implemented by subclass

        Example:
            def to_domain(self) -> User:
                return User(
                    id=self.convert.string_to_uuid(self.id),
                    name=self.name,
                    email=self.email,
                    tags=self.convert.frozenset_to_set(self.tags),
                    created_at=self.convert.isostring_to_datetime(self.created_at)
                )
        """
        error_message = (
            f"{self.__class__.__name__} must implement to_domain() method. "
            f"This method should convert API schema instances to domain objects "
            f"with proper type conversions using the convert utility."
        )
        raise NotImplementedError(error_message)


class BaseApiModel(BaseModel, Generic[D, S]):
    """Enhanced base class for all API schemas with comprehensive validation
    and utilities.

    This base class provides:
    - Strict validation configuration enforcement
    - Comprehensive type conversion utilities
    - Enhanced error handling with detailed context
    - Standardized conversion method patterns
    - Performance-optimized validation

    Key Features:
    1. **Strict Type Validation**: Enforces exact type matches with no implicit
        conversions
    2. **Immutable Schemas**: All schemas are frozen for data integrity
    3. **Comprehensive Error Context**: Detailed error information for debugging
    4. **Type Conversion Utilities**: Standardized utilities for common conversion
    patterns
    5. **Performance Monitoring**: Optional validation completion logging

    Required Methods (must be implemented by subclasses):
    - from_domain(domain_obj) -> Self: Convert domain object to API schema
    - to_domain() -> D: Convert API schema to domain object
    - from_orm_model(orm_model) -> Self: Convert ORM model to API schema
    - to_orm_kwargs() -> Dict: Convert API schema to ORM kwargs

    Usage Example:
        class ApiUser(BaseApiModel):
            id: str
            name: str
            email: str

            @classmethod
            def from_domain(cls, user: User) -> "ApiUser":
                return cls(
                    id=cls.convert.uuid_to_string(user.id),
                    name=user.name,
                    email=user.email
                )

            def to_domain(self) -> User:
                return User(
                    id=self.convert.string_to_uuid(self.id),
                    name=self.name,
                    email=self.email
                )

    Note on JSON Serialization:
        Pydantic's model_dump_json() method automatically handles conversion of:
        - Sets/frozensets → lists
        - UUID objects → strings (when properly configured)
        - Datetime objects → ISO strings (when properly configured)
        - Enum objects → values (when use_enum_values=True)

        Therefore, no custom field serializers are needed for standard JSON output.
    """

    # Strict validation configuration - IMMUTABLE AND ENFORCED
    model_config = MODEL_CONFIG

    # Type conversion utility - available to all schemas
    convert: ClassVar[TypeConversionUtility] = CONVERT

    @classmethod
    def from_domain(cls: type[Self], domain_obj: D) -> Self:
        """Convert a domain object to an API schema instance.

        This method must be implemented by all API schema subclasses. It should handle
        all necessary type conversions from domain types to API types.

        Key Responsibilities:
        - Convert UUID objects to strings using convert.uuid_to_string()
        - Convert enum instances to string values using convert.enum_to_string()
        - Convert mutable sets to immutable frozensets using convert.set_to_frozenset()
        - Convert datetime objects to ISO strings using convert.datetime_to_isostring()
        - Handle any domain-specific type transformations

        Args:
            domain_obj: The domain object to convert

        Returns:
            An instance of the API schema with properly converted types

        Raises:
            NotImplementedError: If not implemented by subclass

        Example:
            @classmethod
            def from_domain(cls, user: User) -> "ApiUser":
                return cls(
                    id=cls.convert.uuid_to_string(user.id),
                    name=user.name,
                    email=user.email,
                    tags=cls.convert.set_to_frozenset(user.tags),
                    created_at=cls.convert.datetime_to_isostring(user.created_at)
                )
        """
        error_message = (
            f"{cls.__name__} must implement from_domain() method. "
            f"This method should convert domain objects to API schema instances "
            f"with proper type conversions using the convert utility."
        )
        raise NotImplementedError(error_message)

    def to_domain(self) -> D:
        """Convert the API schema instance to a domain object.

        This method must be implemented by all API schema subclasses. It should handle
        all necessary type conversions from API types to domain types.

        Key Responsibilities:
        - Convert string IDs to UUID objects using convert.string_to_uuid()
        - Convert string values to enum instances using convert.string_to_enum()
        - Convert immutable frozensets to mutable sets using convert.frozenset_to_set()
        - Convert ISO strings to datetime objects using convert.isostring_to_datetime()
        - Handle any API-specific type transformations

        Returns:
            The corresponding domain object with properly converted types

        Raises:
            NotImplementedError: If not implemented by subclass

        Example:
            def to_domain(self) -> User:
                return User(
                    id=self.convert.string_to_uuid(self.id),
                    name=self.name,
                    email=self.email,
                    tags=self.convert.frozenset_to_set(self.tags),
                    created_at=self.convert.isostring_to_datetime(self.created_at)
                )
        """
        error_message = (
            f"{self.__class__.__name__} must implement to_domain() method. "
            f"This method should convert API schema instances to domain objects "
            f"with proper type conversions using the convert utility."
        )
        raise NotImplementedError(error_message)

    @classmethod
    def from_orm_model(cls: type[Self], orm_model: S) -> Self:
        """Convert an ORM model to an API schema instance.

        This method must be implemented by all API schema subclasses. It should handle
        conversion from SQLAlchemy ORM models to API schema instances.

        Key Responsibilities:
        - Extract data from ORM model relationships and attributes
        - Convert ORM types to API types (e.g., relationships to collections)
        - Handle NULL values and optional fields appropriately
        - Apply any necessary data transformations for API representation

        Args:
            orm_model: The ORM model to convert

        Returns:
            An instance of the API schema converted from the ORM model

        Raises:
            NotImplementedError: If not implemented by subclass

        Example:
            @classmethod
            def from_orm_model(cls, user_orm: UserORM) -> "ApiUser":
                return cls(
                    id=str(user_orm.id),
                    name=user_orm.name,
                    email=user_orm.email,
                    tags=frozenset(tag.name for tag in user_orm.tags),
                    created_at=(
                        cls.convert.datetime_to_isostring(user_orm.created_at)
                        if user_orm.created_at
                        else None
                    ),
                )
        """
        error_message = (
            f"{cls.__name__} must implement from_orm_model() method. "
            f"This method should convert ORM models to API schema instances."
        )
        raise NotImplementedError(error_message)

    def to_orm_kwargs(self) -> dict[str, Any]:
        """Convert the API schema instance to ORM model kwargs.

        This method must be implemented by all API schema subclasses. It should prepare
        data for ORM model creation or updates by converting API types to ORM-compatible
        types.

        Key Responsibilities:
        - Convert API types to ORM-compatible types
        - Handle relationship data appropriately (IDs vs. full objects)
        - Exclude computed or read-only fields that shouldn't be persisted
        - Apply any necessary data transformations for ORM storage

        Returns:
            Dictionary of kwargs suitable for ORM model creation/update

        Raises:
            NotImplementedError: If not implemented by subclass

        Example:
            def to_orm_kwargs(self) -> Dict[str, Any]:
                return {
                    "id": UUID(self.id),
                    "name": self.name,
                    "email": self.email,
                    "created_at": (
                        self.convert.isostring_to_datetime(self.created_at)
                        if self.created_at
                        else None
                    ),
                    # Note: tags might be handled as a separate relationship
                }
        """
        error_message = (
            f"{self.__class__.__name__} must implement to_orm_kwargs() method. "
            f"This method should convert API schema instances to ORM model kwargs."
        )
        raise NotImplementedError(error_message)


class BaseApiValueObject(BaseApiModel[V, S]):
    """Enhanced base class for value object schemas.

    Value objects represent concepts that are defined by their attributes rather than
    their identity. They are immutable and should implement equality based on their
    values.

    Characteristics:
    - No identity field (no ID)
    - Immutable by nature (frozen=True enforced)
    - Equality based on all field values
    - Used for concepts like addresses, money amounts, measurements, etc.

    Example Usage:
        class ApiAddress(BaseApiValueObject):
            street: str
            city: str
            postal_code: str
            country: str

            @classmethod
            def from_domain(cls, address: Address) -> "ApiAddress":
                return cls(
                    street=address.street,
                    city=address.city,
                    postal_code=address.postal_code,
                    country=cls.convert.enum_to_string(address.country)
                )

            def to_domain(self) -> Address:
                return Address(
                    street=self.street,
                    city=self.city,
                    postal_code=self.postal_code,
                    country=self.convert.string_to_enum(self.country, Country)
                )
    """


class BaseApiEntity(BaseApiModel[E, S]):
    """Enhanced base class for entity schemas with common entity fields and patterns.

    Entities represent concepts that have a distinct identity that persists over time,
    even if their attributes change. They include standard lifecycle fields.

    Standard Entity Fields:
    - id: Unique identifier (string representation of UUID)
    - created_at: Timestamp when entity was created
    - updated_at: Timestamp when entity was last modified
    - version: Version number for optimistic locking
    - discarded: Soft delete flag

    Example Usage:
        class ApiUser(BaseApiEntity):
            name: str
            email: str
            active: bool = True

            @classmethod
            def from_domain(cls, user: User) -> "ApiUser":
                return cls(
                    id=cls.convert.uuid_to_string(user.id),
                    name=user.name,
                    email=user.email,
                    active=user.active,
                    created_at=cls.convert.datetime_to_isostring(user.created_at),
                    updated_at=cls.convert.datetime_to_isostring(user.updated_at),
                    version=user.version,
                    discarded=user.discarded
                )
    """

    # Standard entity fields - present in all entities
    id: UUIDIdRequired
    created_at: Annotated[
        datetime | None,
        BeforeValidator(parse_datetime),
        Field(..., description="ISO timestamp when entity was created"),
    ]
    updated_at: Annotated[
        datetime | None,
        BeforeValidator(parse_datetime),
        Field(..., description="ISO timestamp when entity was last updated"),
    ]
    version: Annotated[
        int, Field(default=1, ge=1, description="Version number for optimistic locking")
    ]
    discarded: Annotated[
        bool,
        Field(
            default=False,
            description="Soft delete flag indicating if entity is discarded",
        ),
    ]
