"""Value object for product scoring components."""
from __future__ import annotations

from attrs import frozen
from src.contexts.seedwork.domain.value_objects.value_object import ValueObject


@frozen(hash=True)
class Score(ValueObject):
    """Value object for product scoring components.
    
    Invariants:
        - final score must be between 0.0 and 1.0 if provided
        - ingredients score must be between 0.0 and 1.0 if provided
        - nutrients score must be between 0.0 and 1.0 if provided
    
    Attributes:
        final: Overall product quality score.
        ingredients: Score based on ingredient quality.
        nutrients: Score based on nutritional value.
    
    Notes:
        Immutable. Equality by value (final, ingredients, nutrients).
        Used for product quality assessment and ranking.
    """
    final: float | None = None
    ingredients: float | None = None
    nutrients: float | None = None
