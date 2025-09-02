from __future__ import annotations

from typing import TYPE_CHECKING

from attrs import frozen

if TYPE_CHECKING:
    from src.contexts.shared_kernel.domain.enums import State

from src.contexts.seedwork.domain.value_objects.value_object import ValueObject


@frozen(kw_only=True, hash=True)
class Address(ValueObject):
    """Value object representing a postal address.

    Attributes:
        street: Street name.
        number: Building number.
        zip_code: Postal code.
        district: Neighborhood or district.
        city: City name.
        state: Geographic state.
        complement: Additional address information.
        note: Optional address notes.

    Notes:
        Immutable. Equality by value (all fields).
    """
    street: str | None = None
    number: str | None = None
    zip_code: str | None = None
    district: str | None = None
    city: str | None = None
    state: State | None = None
    complement: str | None = None
    note: str | None = None
