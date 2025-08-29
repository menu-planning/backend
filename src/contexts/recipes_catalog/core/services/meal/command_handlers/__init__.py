from .copy_meal import copy_meal_handler
from .create_meal import create_meal_handler
from .delete_meal import delete_meal_handler
from .update_meal import update_meal_handler
from .copy_recipe import copy_recipe_handler
from .create_recipe import create_recipe_handler
from .delete_recipe import delete_recipe_handler
from .update_recipe import update_recipe_handler
from .rate_recipe import rate_recipe_handler

__all__ = [
    "copy_meal_handler",
    "create_meal_handler",
    "delete_meal_handler",
    "update_meal_handler",
    "copy_recipe_handler",
    "create_recipe_handler",
    "delete_recipe_handler",
    "update_recipe_handler",
    "rate_recipe_handler",
]
