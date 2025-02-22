from datetime import time

from attrs import frozen

from src.contexts.recipes_catalog.shared.domain.enums import MealType
from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject
from src.contexts.shared_kernel.domain.enums import Weekday
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts


@frozen(kw_only=True, hash=True)
class MenuMeal(ValueObject):
    """
    MenuMeal is a value object that represents an meal in a menu.

    Attributes:
        meal_id (str): The meal id.
        meal_name (str): The name of the meal.
        nutri_facts (NutriFacts): The nutri facts of the meal.
        meal should have.
        day (datetime.date): The day of the meal.
        hour (datetime.time): The hour of the meal.
        meal_type (MealType): The meal type.
    """

    meal_id: str
    meal_name: str
    week: int
    weekday: Weekday
    meal_type: MealType
    nutri_facts: NutriFacts | None = None
    hour: time | None = None
