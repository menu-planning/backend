from src.contexts.recipes_catalog.core.services.meal.event_handlers.meal_deleted_handler import (
    remove_meals_from_menu,
)
from src.contexts.recipes_catalog.core.services.meal.event_handlers.updated_attr_on_meal_that_reflect_on_menu_handler import (
    update_menu_meals,
)

__all__ = [
    "remove_meals_from_menu",
    "update_menu_meals",
]
