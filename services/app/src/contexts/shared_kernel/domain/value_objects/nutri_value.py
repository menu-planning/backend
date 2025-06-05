from __future__ import annotations

from attrs import frozen
from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject
from src.contexts.shared_kernel.domain.enums import MeasureUnit


@frozen(kw_only=True)
class NutriValue(ValueObject):
    """
    NutriValue is a value object that represents a nutritional value.

    Attributes:
        unit: The unit of the value.
        value: The value.

    """

    unit: MeasureUnit | None = None
    value: float | None = None

    def __add__(self, other: NutriValue | None) -> NutriValue:
        if other is None:
            return self
        if isinstance(other, NutriValue) and self.unit == other.unit and self.value is not None and other.value is not None:
            return self.replace(
                value=self.value + other.value,
            )
        return NotImplemented

    def __sub__(self, other: NutriValue | None) -> NutriValue:
        if other is None:
            return self
        if isinstance(other, NutriValue) and self.unit == other.unit and self.value is not None and other.value is not None:
            return self.replace(
                value=self.value - other.value,
            )
        return NotImplemented

    def __mul__(self, other: float) -> "NutriValue":
        if isinstance(other, float) and self.value is not None:
            return self.replace(
                value=self.value * other,
            )
        return NotImplemented
