"""Domain command to delete a recipe entity."""
from attrs import frozen
from src.contexts.seedwork.domain.commands.command import Command


@frozen(kw_only=True)
class DeleteRecipe(Command):
    """Command to delete an existing recipe.

    Args:
        recipe_id: ID of the recipe to delete
    """
    recipe_id: str
