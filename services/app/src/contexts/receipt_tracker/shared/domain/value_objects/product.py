from __future__ import annotations

from attrs import frozen
from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject


@frozen(hash=True)
class Product(ValueObject):
    id: str
    source: str
    name: str
    is_food: str
