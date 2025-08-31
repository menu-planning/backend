from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import frozen
from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject

if TYPE_CHECKING:
    from src.contexts.shared_kernel.domain.enums import MeasureUnit


@frozen(kw_only=True)
class NutriValue(ValueObject):
    """
    NutriValue is a value object that represents a nutritional value.

    Attributes:
        unit: The unit of the value.
        value: The value.

    """

    unit: MeasureUnit
    value: float

    def __add__(self, other: NutriValue | None) -> NutriValue:
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
        if isinstance(other, float):
            # Handle None value - treat as 0.0 for multiplication
            self_val = self.value if self.value is not None else 0.0
            return self.replace(
                value=self_val * other,
            )
        return NotImplemented
