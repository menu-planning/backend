from src.contexts.recipes_catalog.core.services.meal.command_handlers.copy_meal_handler import (
    copy_meal_handler,
)
from src.contexts.recipes_catalog.core.services.meal.command_handlers.copy_recipe_handler import (
    copy_recipe_handler,
)
from src.contexts.recipes_catalog.core.services.meal.command_handlers.create_meal_handler import (
    create_meal_handler,
)
from src.contexts.recipes_catalog.core.services.meal.command_handlers.create_recipe_handler import (
    create_recipe_handler,
)
from src.contexts.recipes_catalog.core.services.meal.command_handlers.delete_meal_handler import (
    delete_meal_handler,
)
from src.contexts.recipes_catalog.core.services.meal.command_handlers.delete_recipe_handler import (
    delete_recipe_handler,
)
from src.contexts.recipes_catalog.core.services.meal.command_handlers.update_meal_handler import (
    update_meal_handler,
)
from src.contexts.recipes_catalog.core.services.meal.command_handlers.update_recipe_handler import (
    update_recipe_handler,
)

__all__ = [
    "create_meal_handler",
    "create_recipe_handler",
    "delete_meal_handler",
    "delete_recipe_handler",
    "update_meal_handler",
    "update_recipe_handler",
    "copy_recipe_handler",
    "copy_meal_handler",
]
