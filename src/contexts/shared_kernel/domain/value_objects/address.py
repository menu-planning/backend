from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import frozen

if TYPE_CHECKING:
    from src.contexts.shared_kernel.domain.enums import State

from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject


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
