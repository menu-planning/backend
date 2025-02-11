from __future__ import annotations

from attrs import frozen
from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject


@frozen(kw_only=True, hash=True)
class Amount(ValueObject):
    quantity: float
    unit: str

    def __add__(self, other):
        if isinstance(other, Amount) and self.unit == other.unit:
            return Amount(
                quantity=self.quantity + other.quantity,
                unit=self.unit,
            )
        return NotImplemented
