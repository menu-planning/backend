from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any
from uuid import UUID

from src.contexts.seedwork.shared.adapters.exceptions.api_schema import (
    ValidationConversionError,
)


class TypeConversionUtility:
    """Comprehensive type conversion utilities for API schema standardization.

    This utility class provides standardized methods for converting between different
    type representations commonly used across domain, API, and ORM layers.

    Key Conversion Patterns:
    - UUID ↔ String: Domain entities use UUID objects, API uses string representations
    - Enum ↔ String: Domain business rules use enums, API uses string values
    - Set ↔ FrozenSet ↔ List: Domain uses mutable sets, API uses immutable frozensets
    - DateTime ↔ ISO String: Domain uses datetime objects, API uses ISO 8601 strings
    - Decimal ↔ Float: Financial data precision handling

    Usage Example:
        # Domain to API conversions
        api_id = TypeConversionUtility.uuid_to_string(domain_entity.id)
        api_tags = TypeConversionUtility.set_to_frozenset(domain_entity.tags)

        # API to domain conversions
        domain_id = TypeConversionUtility.string_to_uuid(api_schema.id)
        domain_tags = TypeConversionUtility.frozenset_to_set(api_schema.tags)
    """

    @staticmethod
    def uuid_to_string(uuid_value: UUID | None) -> str | None:
        """Convert UUID to string representation.

        Args:
            uuid_value: UUID object or None

        Returns:
            String representation of UUID or None

        Raises:
            ValidationConversionError: If UUID conversion fails
        """
        if uuid_value is None:
            return None
        try:
            return str(uuid_value)
        except Exception as e:
            raise ValidationConversionError(
                message=f"Failed to convert UUID to string: {e!s}",
                conversion_direction="uuid_to_string",
                source_data=uuid_value,
                validation_errors=[str(e)],
            ) from e

    @staticmethod
    def string_to_uuid(string_value: str | None) -> UUID | None:
        """Convert string to UUID object.

        Args:
            string_value: String representation of UUID or None

        Returns:
            UUID object or None

        Raises:
            ValidationConversionError: If string is not a valid UUID format
        """
        if string_value is None:
            return None
        try:
            return UUID(string_value)
        except (ValueError, TypeError) as e:
            raise ValidationConversionError(
                message=(
                    f"Failed to convert string to UUID: '{string_value}' "
                    f"is not a valid UUID format"
                ),
                conversion_direction="string_to_uuid",
                source_data=string_value,
                validation_errors=[str(e)],
            ) from e

    @staticmethod
    def enum_to_string(enum_value: Enum | None) -> str | None:
        """Convert enum to string representation.

        Args:
            enum_value: Enum instance or None

        Returns:
            String value of enum or None
        """
        if enum_value is None:
            return None
        return enum_value.value if hasattr(enum_value, "value") else str(enum_value)

    @staticmethod
    def string_to_enum(string_value: str | None, enum_class: type[Enum]) -> Enum | None:
        """Convert string to enum instance.

        Args:
            string_value: String representation of enum value
            enum_class: Enum class to convert to

        Returns:
            Enum instance or None

        Raises:
            ValidationConversionError: If string is not a valid enum value
        """
        if string_value is None:
            return None
        try:
            return enum_class(string_value)
        except (ValueError, KeyError) as e:
            valid_values = [item.value for item in enum_class]
            raise ValidationConversionError(
                message=(
                    f"'{string_value}' is not a valid {enum_class.__name__} "
                    f"value. Valid values: {valid_values}"
                ),
                conversion_direction="string_to_enum",
                source_data=string_value,
                validation_errors=[str(e)],
            ) from e

    @staticmethod
    def set_to_frozenset(set_value: set[Any] | None) -> frozenset[Any] | None:
        """Convert mutable frozenset to immutable frozenset.

        Args:
            set_value: Mutable frozenset or None

        Returns:
            Immutable frozenset or None
        """
        if set_value is None:
            return None
        return frozenset(set_value)

    @staticmethod
    def frozenset_to_set(frozenset_value: frozenset[Any] | None) -> set[Any] | None:
        """Convert immutable frozenset to mutable frozenset.

        Args:
            frozenset_value: Immutable frozenset or None

        Returns:
            Mutable frozenset or None
        """
        if frozenset_value is None:
            return None
        return set(frozenset_value)

    @staticmethod
    def list_to_frozenset(list_value: list[Any] | None) -> frozenset[Any] | None:
        """Convert list to immutable frozenset (removes duplicates).

        Args:
            list_value: List or None

        Returns:
            Immutable frozenset or None
        """
        if list_value is None:
            return None
        return frozenset(list_value)

    @staticmethod
    def frozenset_to_list(frozenset_value: frozenset[Any] | None) -> list[Any] | None:
        """Convert immutable frozenset to list.

        Args:
            frozenset_value: Immutable frozenset or None

        Returns:
            List or None
        """
        if frozenset_value is None:
            return None
        return list(frozenset_value)

    @staticmethod
    def datetime_to_isostring(datetime_value: datetime | None) -> str | None:
        """Convert datetime to ISO 8601 string.

        Args:
            datetime_value: Datetime object or None

        Returns:
            ISO 8601 formatted string or None
        """
        if datetime_value is None:
            return None
        return datetime_value.isoformat()

    @staticmethod
    def isostring_to_datetime(isostring_value: str | None) -> datetime | None:
        """Convert ISO 8601 string to datetime object.

        Args:
            isostring_value: ISO 8601 formatted string or None

        Returns:
            Datetime object or None

        Raises:
            ValidationConversionError: If string is not valid ISO 8601 format
        """
        if isostring_value is None:
            return None
        try:
            return datetime.fromisoformat(isostring_value)
        except (ValueError, AttributeError) as e:
            raise ValidationConversionError(
                message=(
                    f"Failed to convert string to datetime: '{isostring_value}' "
                    f"is not a valid ISO 8601 format"
                ),
                conversion_direction="isostring_to_datetime",
                source_data=isostring_value,
                validation_errors=[str(e)],
            ) from e

    @staticmethod
    def decimal_to_float(decimal_value: Decimal | None) -> float | None:
        """Convert Decimal to float (with precision loss warning).

        Args:
            decimal_value: Decimal object or None

        Returns:
            Float value or None
        """
        if decimal_value is None:
            return None
        return float(decimal_value)

    @staticmethod
    def float_to_decimal(
        float_value: float | None, precision: int = 2
    ) -> Decimal | None:
        """Convert float to Decimal with specified precision.

        Args:
            float_value: Float value or None
            precision: Number of decimal places (default: 2)

        Returns:
            Decimal object with specified precision or None
        """
        if float_value is None:
            return None
        return Decimal(str(round(float_value, precision)))

    @staticmethod
    def frozenset_to_comma_string(frozenset_value: frozenset[str] | None) -> str | None:
        """Convert frozenset of strings to comma-separated string.

        Used for ORM storage where collections are denormalized as comma-separated
        values.

        Args:
            frozenset_value: Immutable frozenset of strings or None

        Returns:
            Comma-separated string or None
        """
        if frozenset_value is None:
            return None
        if not frozenset_value:  # Empty frozenset
            return ""
        return ",".join(sorted(frozenset_value))  # Sort for consistent output

    @staticmethod
    def comma_string_to_frozenset(comma_string: str | None) -> frozenset[str] | None:
        """Convert comma-separated string to frozenset of strings.

        Used for converting from ORM denormalized storage to API collections.

        Args:
            comma_string: Comma-separated string or None

        Returns:
            Immutable frozenset of strings or None
        """
        if comma_string is None:
            return None
        if not comma_string.strip():  # Empty string
            return frozenset()
        # Split, strip whitespace, and filter empty strings
        items = [item.strip() for item in comma_string.split(",") if item.strip()]
        return frozenset(items)

    @staticmethod
    def set_to_comma_string(set_value: set[str] | None) -> str | None:
        """Convert frozenset of strings to comma-separated string.

        Args:
            set_value: Mutable frozenset of strings or None

        Returns:
            Comma-separated string or None
        """
        if set_value is None:
            return None
        if not set_value:  # Empty frozenset
            return ""
        return ",".join(sorted(set_value))  # Sort for consistent output

    @staticmethod
    def comma_string_to_set(comma_string: str | None) -> set[str] | None:
        """Convert comma-separated string to frozenset of strings.

        Args:
            comma_string: Comma-separated string or None

        Returns:
            Mutable frozenset of strings or None
        """
        if comma_string is None:
            return None
        if not comma_string.strip():  # Empty string
            return set()
        # Split, strip whitespace, and filter empty strings
        items = [item.strip() for item in comma_string.split(",") if item.strip()]
        return set(items)
