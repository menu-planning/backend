from __future__ import annotations

from attrs import frozen
from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject


@frozen(hash=True)
class Address(ValueObject):
    street: str
    number: str
    zip_code: str
    district: str
    city: str
    state: str
    complement: str | None = None
    note: str | None = None
