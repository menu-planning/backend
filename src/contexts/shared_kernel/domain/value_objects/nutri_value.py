from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import frozen
from src.contexts.seedwork.domain.value_objects.value_object import ValueObject

if TYPE_CHECKING:
    from src.contexts.shared_kernel.domain.enums import MeasureUnit


@frozen(kw_only=True)
class NutriValue(ValueObject):
    """Value object representing a nutritional value with unit.

    Attributes:
        unit: Measurement unit for the nutritional value.
        value: Numeric value of the nutrient.

    Notes:
        Immutable. Equality by value (unit and value).
        Supports arithmetic operations with unit compatibility.
    """

    unit: MeasureUnit
    value: float

    def __add__(self, other: NutriValue | None) -> NutriValue:
        """Add another nutritional value to this one.

        Args:
            other: Nutritional value to add, or None to return self.

        Returns:
            New NutriValue with summed values and compatible unit.

        Notes:
            Handles unit compatibility and None values as zero.
        """
        if other is None:
            return self
        if isinstance(other, NutriValue):
            # Handle unit compatibility
            if self.unit != other.unit:
                # For nutrition aggregation, we should have matching units
                # If they don't match, use the non-None unit or self.unit as fallback
                result_unit = self.unit if self.unit is not None else other.unit
            else:
                result_unit = self.unit

            # Handle None values - treat as 0.0 for nutrition aggregation
            self_val = self.value if self.value is not None else 0.0
            other_val = other.value if other.value is not None else 0.0

            return self.replace(value=self_val + other_val, unit=result_unit)
        return NotImplemented

    def __sub__(self, other: NutriValue | None) -> NutriValue:
        """Subtract another nutritional value from this one.

        Args:
            other: Nutritional value to subtract, or None to return self.

        Returns:
            New NutriValue with subtracted values and compatible unit.

        Notes:
            Handles unit compatibility and None values as zero.
        """
        if other is None:
            return self
        if isinstance(other, NutriValue):
            # Handle unit compatibility
            if self.unit != other.unit:
                # For nutrition operations, we should have matching units
                # If they don't match, use the non-None unit or self.unit as fallback
                result_unit = self.unit if self.unit is not None else other.unit
            else:
                result_unit = self.unit

            # Handle None values - treat as 0.0 for nutrition operations
            self_val = self.value if self.value is not None else 0.0
            other_val = other.value if other.value is not None else 0.0

            return self.replace(value=self_val - other_val, unit=result_unit)
        return NotImplemented

    def __mul__(self, other: float) -> NutriValue:
        """Multiply this nutritional value by a scalar.

        Args:
            other: Scalar multiplier.

        Returns:
            New NutriValue with multiplied value and same unit.

        Notes:
            Handles None values as zero for multiplication.
        """
        if isinstance(other, float):
            # Handle None value - treat as 0.0 for multiplication
            self_val = self.value if self.value is not None else 0.0
            return self.replace(
                value=self_val * other,
            )
        return NotImplemented
