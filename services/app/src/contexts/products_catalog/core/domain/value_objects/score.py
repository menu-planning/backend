from __future__ import annotations

from attrs import frozen


from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject


@frozen(hash=True)
class Score(ValueObject):
    final: float | None = None
    ingredients: float | None = None
    nutrients: float | None = None
