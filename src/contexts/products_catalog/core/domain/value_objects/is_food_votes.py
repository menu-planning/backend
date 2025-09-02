"""Value object capturing crowd inputs about whether a product is food."""
from typing import ClassVar

from attrs import field, frozen
from src.contexts.seedwork.domain.value_objects.value_object import ValueObject


@frozen
class IsFoodVotes(ValueObject):
    """Value object capturing crowd inputs about whether a product is food.
    
    Invariants:
        - acceptance_line maps vote counts to acceptance thresholds
        - is_food_houses and is_not_food_houses are disjoint sets
        - acceptance_line values are between 0.0 and 1.0 or None
    
    Attributes:
        acceptance_line: Mapping of vote counts to acceptance thresholds.
        is_food_houses: Set of house IDs that voted this product is food.
        is_not_food_houses: Set of house IDs that voted this product is not food.
    
    Notes:
        Immutable. Equality by value (acceptance_line, is_food_houses, is_not_food_houses).
        Used for determining product food classification based on crowd consensus.
    """
    acceptance_line: dict[float, float | None] | None = field(default={
            0: None,
            3: 1,
            5: 0.7,
        })
    is_food_houses: frozenset[str] = field(factory=frozenset)
    is_not_food_houses: frozenset[str] = field(factory=frozenset)
