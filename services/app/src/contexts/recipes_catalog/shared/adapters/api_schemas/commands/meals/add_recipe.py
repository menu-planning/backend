from src.contexts.recipes_catalog.shared.domain.entities.recipe import Recipe
from src.contexts.seedwork.shared.domain.commands.command import Command


class AddNewRecipeToMeal(Command):
    meal_id: str
    recipe: Recipe


class CopyExistingRecipeToMeal(Command):
    meal_id: str
    recipe_id: str
