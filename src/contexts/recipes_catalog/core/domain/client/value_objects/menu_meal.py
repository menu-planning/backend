"""Value object representing a meal placed on a menu grid."""
from datetime import time

from attrs import field, frozen
from src.contexts.seedwork.domain.value_objects.value_object import ValueObject
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts


@frozen(kw_only=True, hash=True)
class MenuMeal(ValueObject):
    """Value object representing a meal placed on a menu grid.

    Invariants:
        - Week must be positive
        - Weekday must be valid day name
        - Meal type must be non-empty

    Notes:
        Immutable. Equality by value (week, weekday, meal_type only).
        meal_id, meal_name, nutri_facts, and hour are excluded from equality/hash.
    """

    # These fields will be ignored in equality and hash calculations.
    meal_id: str = field(eq=False, hash=False)
    meal_name: str = field(eq=False, hash=False)
    nutri_facts: NutriFacts | None = field(default=None, eq=False, hash=False)
    hour: time | None = field(default=None, eq=False, hash=False)

    # These fields will be used in the generated __eq__ and __hash__.
    week: int
    weekday: str
    meal_type: str
