"""Domain command to update recipe fields."""
from typing import Any

from attrs import frozen
from src.contexts.seedwork.domain.commands.command import Command


@frozen(kw_only=True)
class UpdateRecipe(Command):
    """Command to update recipe fields.

    Args:
        recipe_id: ID of the recipe to update
        updates: Dictionary of field names and new values to update
    """
    recipe_id: str
    updates: dict[str, Any]
