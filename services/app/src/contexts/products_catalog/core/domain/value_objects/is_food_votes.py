from __future__ import annotations

from attrs import define, field
from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject


@define
class IsFoodVotes(ValueObject):
    acceptance_line: dict[float, float | None] | None = field()
    is_food_houses: set[str] = field(factory=set)
    is_not_food_houses: set[str] = field(factory=set)

    @acceptance_line.default # type: ignore
    def default_acceptance_line(self) -> dict[float, float | None]:
        return {
            0: None,
            3: 1,
            5: 0.7,
        }
