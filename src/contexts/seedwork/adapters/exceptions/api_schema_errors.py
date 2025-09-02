"""API Schema Exception Hierarchy.

This module defines specialized exceptions for API schema validation and
conversion perations.
All exceptions are designed to work seamlessly with Pydantic v2 validation system.

Usage Examples:
    try:
        api_meal.to_domain()
    except ValidationConversionError as e:
        logger.error(f"Failed to convert {e.schema_class} to domain: {e}")

    # Use with Pydantic field validators
    from pydantic_core import PydanticCustomError
    if duplicate_found:
        raise DuplicateItemError.create_pydantic_error(
            item_type="recipe",
            field="recipes",
            duplicate_key="id",
            duplicate_value=recipe_id
        )
"""

from typing import Any

from pydantic_core import PydanticCustomError


class ApiSchemaError(Exception):
    """Base exception for all API schema related errors.

    This is the root exception class for all API schema validation,
    conversion, and processing errors.
    """

    def __init__(self, message: str, schema_class: type | None = None, **kwargs):
        super().__init__(message)
        self.message = message
        self.schema_class = schema_class
        self.extra_data = kwargs


class ValidationConversionError(ApiSchemaError):
    """Raised when conversion between API schema and domain/ORM fails.

    This exception captures detailed context about conversion failures,
    including the direction of conversion and any intermediate state.

    Attributes:
        conversion_direction: The type of conversion that failed
        source_data: The data that failed to convert
        validation_errors: Any underlying validation errors
    """

    def __init__(
        self,
        message: str,
        schema_class: type | None = None,
        conversion_direction: str | None = None,
        source_data: Any | None = None,
        validation_errors: list | None = None,
        **kwargs,
    ):
        super().__init__(message, schema_class, **kwargs)
        self.conversion_direction = conversion_direction
        self.source_data = source_data
        self.validation_errors = validation_errors or []

    def get_context(self) -> dict[str, Any]:
        """Get full error context for logging and debugging."""
        return {
            "message": self.message,
            "schema_class": self.schema_class.__name__ if self.schema_class else None,
            "conversion_direction": self.conversion_direction,
            "validation_errors": self.validation_errors,
            "extra_data": self.extra_data,
        }


class DuplicateItemError(ApiSchemaError):
    """Raised when duplicate items are found in collections that require uniqueness.

    This exception is designed to work with Pydantic's custom error system
    and provides detailed information about the duplicate items found.

    Attributes:
        item_type: The type of item that was duplicated
        field_name: The field where the duplicate was found
        duplicate_key: The key used for uniqueness checking
        duplicate_value: The value that was duplicated
        duplicate_items: All items that share the duplicate value
    """

    def __init__(
        self,
        message: str,
        item_type: str,
        field_name: str,
        duplicate_key: str,
        duplicate_value: Any,
        duplicate_items: list | None = None,
        schema_class: type | None = None,
        **kwargs,
    ):
        super().__init__(message, schema_class, **kwargs)
        self.item_type = item_type
        self.field_name = field_name
        self.duplicate_key = duplicate_key
        self.duplicate_value = duplicate_value
        self.duplicate_items = duplicate_items or []

    @classmethod
    def create_pydantic_error(
        cls,
        item_type: str,
        field: str,
        duplicate_key: str,
        duplicate_value: Any,
        duplicate_items: list | None = None,
    ) -> PydanticCustomError:
        """Create a PydanticCustomError for use in validators.

        Args:
            item_type: Type of item that was duplicated (e.g., "recipe", "tag")
            field: Field name where duplicate was found
            duplicate_key: The key used for uniqueness (e.g., "id", "name")
            duplicate_value: The actual duplicated value
            duplicate_items: Optional list of all items with duplicate value

        Returns:
            PydanticCustomError configured for duplicate item validation
        """
        duplicate_count = len(duplicate_items) if duplicate_items else 2

        return PydanticCustomError(
            "duplicate_item_error",
            "Duplicate {item_type} found in {field}: "
            "{duplicate_count} items have {duplicate_key}={duplicate_value}",
            {
                "item_type": item_type,
                "field": field,
                "duplicate_key": duplicate_key,
                "duplicate_value": duplicate_value,
                "duplicate_count": duplicate_count,
                "duplicate_items": duplicate_items,
            },
        )


class FieldMappingError(ApiSchemaError):
    """Raised when field mapping between schema types fails.

    This occurs when there are mismatches between API schema fields
    and their corresponding domain object or ORM model fields.

    Attributes:
        missing_fields: Fields that are missing in the target
        extra_fields: Fields that are unexpected in the source
        type_mismatches: Fields with incompatible types
        mapping_direction: The direction of the failed mapping
    """

    def __init__(
        self,
        message: str,
        schema_class: type | None = None,
        missing_fields: list | None = None,
        extra_fields: list | None = None,
        type_mismatches: dict[str, tuple] | None = None,
        mapping_direction: str | None = None,
        **kwargs,
    ):
        super().__init__(message, schema_class, **kwargs)
        self.missing_fields = missing_fields or []
        self.extra_fields = extra_fields or []
        self.type_mismatches = type_mismatches or {}
        self.mapping_direction = mapping_direction

    def get_field_summary(self) -> dict[str, Any]:
        """Get a summary of all field mapping issues."""
        return {
            "missing_fields": self.missing_fields,
            "extra_fields": self.extra_fields,
            "type_mismatches": self.type_mismatches,
            "mapping_direction": self.mapping_direction,
        }
