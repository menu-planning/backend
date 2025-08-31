from datetime import time

from attrs import field, frozen
from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts


@frozen(kw_only=True, hash=True)
class MenuMeal(ValueObject):
    """
    MenuMeal is a value object that represents a meal in a menu.

    Only `week`, `weekday` and `meal_type` will be used for equality and hashing.
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
