"""Domain command to copy a recipe into a target meal."""
from attrs import frozen
from src.contexts.seedwork.domain.commands.command import Command


@frozen(kw_only=True)
class CopyRecipe(Command):
    """Command to copy a recipe into a target meal.

    Args:
        user_id: ID of the user copying the recipe
        recipe_id: ID of the recipe to copy
        meal_id: ID of the target meal to copy the recipe into
    """
    user_id: str
    recipe_id: str
    meal_id: str
