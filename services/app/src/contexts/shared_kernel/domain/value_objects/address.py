from __future__ import annotations

from attrs import frozen
from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject
from src.contexts.shared_kernel.domain.enums import State


@frozen(kw_only=True, hash=True)
class Address(ValueObject):
    street: str | None = None
    number: str | None = None
    zip_code: str | None = None
    district: str | None = None
    city: str | None = None
    state: State | None = None
    complement: str | None = None
    note: str | None = None
