"""Value object that holds macronutrient percentage breakdown."""
from attrs import frozen
from src.contexts.seedwork.domain.value_objects.value_object import ValueObject


@frozen(kw_only=True, hash=True)
class MacroDivision(ValueObject):
    """Value object representing macronutrient percentage breakdown.

    Invariants:
        - All percentages must be non-negative
        - Sum of percentages should equal 100 (not enforced)

    Notes:
        Immutable. Equality by value (carbohydrate, protein, fat).
    """
    carbohydrate: float
    protein: float
    fat: float
