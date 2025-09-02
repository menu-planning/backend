from typing import Annotated, Any

from pydantic import AfterValidator, ValidationInfo
from src.contexts.products_catalog.core.domain.root_aggregate.product import Product
from src.contexts.seedwork.adapters.exceptions.api_schema_errors import (
    ValidationConversionError,
)

MIN_SCORE = 0
MAX_SCORE = 100


def _score_range(v: Any):
    if v is not None and (v < MIN_SCORE or v > MAX_SCORE):
        error_msg = f"Score must be an int from {MIN_SCORE} to {MAX_SCORE}: {v}"
        raise ValidationConversionError(
            message=error_msg,
            conversion_direction="field_validation",
            source_data=v,
            validation_errors=[f"Value {v} is outside valid range [{MIN_SCORE}, {MAX_SCORE}]"]
        )
    return v


ScoreValue = Annotated[float | None, AfterValidator(_score_range)]


def _unique_barcode(v: Any):
    if not Product.is_barcode_unique(v):
        error_msg = f"Barcode must be 13 digits: {v}"
        raise ValidationConversionError(
            message=error_msg,
            conversion_direction="field_validation",
            source_data=v,
            validation_errors=[f"Barcode {v} is not unique or invalid format"]
        )
    return v


UniqueBarcode = Annotated[str | None, AfterValidator(_unique_barcode)]


def validate_edible_yield_range(value: float | None, info: ValidationInfo) -> float:
    """Validate that edible yield is within valid range (0, 1].

    Args:
        value: The edible yield value to validate
        info: Pydantic validation context

    Returns:
        The validated edible yield value

    Raises:
        ValidationConversionError: If the value is outside the valid range
    """
    if value is None:
        return 1.0  # Default value

    if not (0 < value <= 1):
        error_msg = f"Edible yield must be > 0 and <= 1, got: {value}"
        raise ValidationConversionError(
            message=error_msg,
            schema_class=info.data.get("__class__") if info.data else None,
            conversion_direction="field_validation",
            source_data=value,
            validation_errors=[f"Value {value} is outside valid range (0, 1]"]
        )

    return value


def validate_kg_per_unit_range(value: float | None, info: ValidationInfo) -> float | None:
    """Validate that kg per unit is within valid range [0, infinity).

    Args:
        value: The kg per unit value to validate
        info: Pydantic validation context

    Returns:
        The validated kg per unit value

    Raises:
        ValidationConversionError: If the value is outside the valid range
    """
    if value is None:
        return None

    if value < 0:
        error_msg = f"Kg per unit must be >= 0, got: {value}"
        raise ValidationConversionError(
            message=error_msg,
            schema_class=info.data.get("__class__") if info.data else None,
            conversion_direction="field_validation",
            source_data=value,
            validation_errors=[f"Value {value} is outside valid range [0, infinity)"]
        )

    return value
