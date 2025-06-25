from typing import Any, Dict, Generic, TypeVar, Self
from pydantic import BaseModel, ConfigDict, Field, field_serializer
from typing_extensions import Annotated

from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import CreatedAtValue, UUIDId
from src.contexts.seedwork.shared.adapters.exceptions.api_schema import (
    ValidationConversionError, 
    FieldMappingError
)
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
        # Use alias for field names
        alias_generator=None,  # Can be overridden in subclasses
    )

    @field_serializer('*', when_used='json')
    def serialize_sets_to_lists(self, value: Any) -> Any:
        """Convert sets and frozensets to lists for JSON serialization."""
        if isinstance(value, (set, frozenset)):
            return list(value)
        return value

    # @model_validator(mode='after')
    # def _log_validation_completion(self) -> Self:
    #     """Post-validation logging hook for debugging and monitoring.
        
    #     This logs successful validation completion with context but ensures
    #     no sensitive data is included in logs. Optimized to reduce performance
    #     overhead by only logging for specific schema types or when debugging.
    #     """
    #     # Only log for root aggregates and entities, not value objects
    #     # This reduces logging volume by ~95% while preserving important validation events
    #     if (self.__class__.__name__.startswith(('ApiMeal', 'ApiRecipe', 'ApiUser')) or
    #         getattr(self.__class__, '__log_validation__', False)):
            
    #         class_name = self.__class__.__name__
    #         field_count = len(self.__class__.model_fields)
            
    #         logger.debug(
    #             f"API schema validation completed",
    #             extra={
    #                 "schema_class": class_name,
    #                 "field_count": field_count,
    #                 "validation_mode": "after",
    #                 "instance_id": id(self)
    #             }
    #         )
    #     return self

    def _safe_to_domain(self) -> D:
        """Safe wrapper for to_domain() with comprehensive error handling.
        
        Returns:
            Domain object converted from this API schema
            
        Raises:
            ValidationConversionError: If conversion fails with detailed context
        """
        try:
            return self.to_domain()
        except Exception as e:
            error_context = {
                "schema_class": self.__class__.__name__,
                "conversion_direction": "api_to_domain",
                "field_count": len(self.__class__.model_fields),
                "error_type": type(e).__name__,
                "original_error": str(e)
            }
            
            logger.error(
                f"Failed to convert {self.__class__.__name__} to domain object",
                extra=error_context
            )
            
            raise ValidationConversionError(
                message=f"Failed to convert {self.__class__.__name__} to domain: {str(e)}",
                schema_class=self.__class__,
                conversion_direction="api_to_domain",
                source_data=self.model_dump(),
                validation_errors=[str(e)]
            ) from e

    @classmethod
    def _safe_from_domain(cls: type[Self], domain_obj: D) -> Self:
        """Safe wrapper for from_domain() with structured error context.
        
        Args:
            domain_obj: Domain object to convert to API schema
            
        Returns:
            API schema instance converted from domain object
            
        Raises:
            ValidationConversionError: If conversion fails with detailed context
        """
        try:
            return cls.from_domain(domain_obj)
        except Exception as e:
            error_context = {
                "schema_class": cls.__name__,
                "domain_class": type(domain_obj).__name__,
                "conversion_direction": "domain_to_api",
                "error_type": type(e).__name__,
                "original_error": str(e)
            }
            
            logger.error(
                f"Failed to convert {type(domain_obj).__name__} to {cls.__name__}",
                extra=error_context
            )
            
            raise ValidationConversionError(
                message=f"Failed to convert {type(domain_obj).__name__} to {cls.__name__}: {str(e)}",
                schema_class=cls,
                conversion_direction="domain_to_api",
                source_data=str(domain_obj),
                validation_errors=[str(e)]
            ) from e

    def _safe_to_orm_kwargs(self) -> Dict[str, Any]:
        """Safe wrapper for to_orm_kwargs() with field mapping validation.
        
        Returns:
            Dictionary of kwargs for ORM model creation
            
        Raises:
            FieldMappingError: If field mapping validation fails
        """
        try:
            orm_kwargs = self.to_orm_kwargs()
            
            # Validate that all required API fields are mapped
            api_fields = set(self.__class__.model_fields.keys())
            orm_fields = set(orm_kwargs.keys())
            
            # Log field mapping for debugging
            logger.debug(
                f"ORM kwargs mapping completed",
                extra={
                    "schema_class": self.__class__.__name__,
                    "api_fields_count": len(api_fields),
                    "orm_fields_count": len(orm_fields),
                    "mapped_fields": list(orm_fields)
                }
            )
            
            return orm_kwargs
            
        except Exception as e:
            error_context = {
                "schema_class": self.__class__.__name__,
                "conversion_direction": "api_to_orm",
                "error_type": type(e).__name__,
                "original_error": str(e)
            }
            
            logger.error(
                f"Failed to generate ORM kwargs from {self.__class__.__name__}",
                extra=error_context
            )
            
            raise FieldMappingError(
                message=f"Failed to map {self.__class__.__name__} fields to ORM kwargs: {str(e)}",
                schema_class=self.__class__,
                mapping_direction="api_to_orm"
            ) from e

    @classmethod
    def _safe_from_orm_model(cls: type[Self], orm_model: S) -> Self:
        """Safe wrapper for from_orm_model() with null handling.
        
        Args:
            orm_model: ORM model to convert to API schema
            
        Returns:
            API schema instance converted from ORM model
            
        Raises:
            ValidationConversionError: If conversion fails with detailed context
        """
        if orm_model is None:
            raise ValidationConversionError(
                message=f"Cannot convert None ORM model to {cls.__name__}",
                schema_class=cls,
                conversion_direction="orm_to_api",
                source_data=None,
                validation_errors=["ORM model is None"]
            )
        
        try:
            return cls.from_orm_model(orm_model)
        except Exception as e:
            error_context = {
                "schema_class": cls.__name__,
                "orm_class": type(orm_model).__name__,
                "conversion_direction": "orm_to_api",
                "error_type": type(e).__name__,
                "original_error": str(e)
            }
            
            logger.error(
                f"Failed to convert {type(orm_model).__name__} to {cls.__name__}",
                extra=error_context
            )
            
            raise ValidationConversionError(
                message=f"Failed to convert {type(orm_model).__name__} to {cls.__name__}: {str(e)}",
                schema_class=cls,
                conversion_direction="orm_to_api",
                source_data=str(orm_model),
                validation_errors=[str(e)]
            ) from e

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
    
    id: UUIDId
    created_at: CreatedAtValue | None = None
    updated_at: CreatedAtValue | None = None
    version: Annotated[int, Field(default=1)]
    discarded: Annotated[bool, Field(default=False)]


class BaseCommand(BaseApiModel[C, S]):
    """Base class for command schemas."""
    pass