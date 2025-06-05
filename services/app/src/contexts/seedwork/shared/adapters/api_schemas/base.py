from datetime import datetime
from typing import Any, Dict, Generic, TypeVar, Self
from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing_extensions import Annotated
import re

from src.contexts.seedwork.shared.domain.commands.command import Command
from src.contexts.seedwork.shared.domain.entity import Entity
from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject
from src.db.base import SaBase
from src.logging.logger import logger

D = TypeVar('D', bound=Entity | ValueObject | Command)
E = TypeVar('E', bound=Entity)
V = TypeVar('V', bound=ValueObject)
C = TypeVar('C', bound=Command)
S = TypeVar('S', bound=SaBase)

class BaseApiModel(BaseModel, Generic[D, S]):
    """Base class for all API schemas with shared configuration and utilities."""
    
    model_config = ConfigDict(
        # Make the model immutable
        frozen=True,
        # Enable strict mode for better type checking
        strict=True,
        # Convert from attributes to fields
        from_attributes=True,
        # Forbid extra fields in the model
        extra='forbid',
        # Validate default values
        validate_default=True,
        # Use enum values instead of enum objects
        use_enum_values=True,
        # Allow population by field name
        populate_by_name=True,
        # Validate assignment
        validate_assignment=True,
        # Use JSON compatible types
        json_encoders={
            # Add custom JSON encoders here if needed
        },
        # Use alias for field names
        alias_generator=None,  # Can be overridden in subclasses
    )

    @classmethod
    def from_domain(cls: type[Self], domain_obj: D) -> Self:
        """Convert a domain object to an API schema instance.
        
        Args:
            domain_obj: The domain object to convert
            
        Returns:
            An instance of the API schema
        """
        raise NotImplementedError("Subclasses must implement from_domain")

    def to_domain(self) -> D:
        """Convert the API schema instance to a domain object.
        
        Returns:
            The corresponding domain object
        """
        raise NotImplementedError("Subclasses must implement to_domain")

    @classmethod
    def from_orm_model(cls: type[Self], orm_model: S) -> Self:
        """Convert an ORM model to an API schema instance.
        
        Args:
            orm_model: The ORM model to convert
            
        Returns:
            An instance of the API schema
        """
        raise NotImplementedError("Subclasses must implement from_orm_model")

    def to_orm_kwargs(self) -> Dict[str, Any]:
        """Convert the API schema instance to ORM model kwargs.
        
        Returns:
            Dictionary of kwargs for ORM model creation
        """
        raise NotImplementedError("Subclasses must implement to_orm_kwargs")


class BaseValueObject(BaseApiModel[V, S]):
    """Base class for value objects."""
    pass
    # def assert_domain_and_api_schema_match(self, value_obj: V) -> None:
    #     """Assert that the domain object and the API schema have the same fields."""
    #     for field in self.__class__.model_fields.keys():
    #         if field not in [f.name for f in fields(value_obj.__class__)]:
    #             raise ValueError(f"Field {field} not found in domain object")
    #         if getattr(self, field) != getattr(value_obj, field):
    #             raise ValueError(f"Field {field} does not match")

class BaseEntity(BaseApiModel[E, S]):
    """Base class for entity schemas with common fields."""
    
    id: Annotated[str, Field(min_length=1, max_length=36)]
    created_at: Annotated[datetime, Field(default_factory=datetime.now)]
    updated_at: Annotated[datetime, Field(default_factory=datetime.now)]
    version: Annotated[int, Field(default=1)]
    discarded: Annotated[bool, Field(default=False)]

    @field_validator('id', mode='before')
    @classmethod
    def validate_uuid_format(cls, v: str) -> str:
        """Log a warning if the ID is not in UUID hex format."""
        if not re.match(r'^[0-9a-f]{32}$', v):
            logger.warning(f"ID '{v}' is not in UUID hex format (32 hexadecimal characters)")
        return v

class BaseCommand(BaseApiModel[C, S]):
    """Base class for command schemas."""
    pass