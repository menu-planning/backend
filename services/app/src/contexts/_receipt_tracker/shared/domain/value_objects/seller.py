from __future__ import annotations

from attrs import frozen
from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject
from src.contexts.shared_kernel.domain.value_objects.address import Address


@frozen(hash=True)
class Seller(ValueObject):
    cnpj: str
    name: str
    state_registration: str
    address: Address
