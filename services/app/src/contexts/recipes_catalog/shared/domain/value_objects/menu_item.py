from datetime import datetime

from attrs import frozen
from src.contexts.recipes_catalog.shared.domain.enums import MealType
from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject
from src.contexts.shared_kernel.domain.enums import Weekday


@frozen(kw_only=True, hash=True)
class MenuItem(ValueObject):
    """
    MenuItem is a value object that represents an meal in a menu.

    Attributes:
        meal_id (str): The meal id.
        day (datetime.date): The day of the meal.
        hour (datetime.time): The hour of the meal.
        meal_type (MealType): The meal type.

    """

    meal_id: str
    week: int
    weekday: Weekday
    hour: datetime.time
    meal_type: MealType
