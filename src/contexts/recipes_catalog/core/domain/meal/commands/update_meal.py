"""Domain command to update meal fields."""
from typing import Any

from attrs import frozen
from src.contexts.seedwork.domain.commands.command import Command


@frozen(kw_only=True)
class UpdateMeal(Command):
    """Command to update meal fields.

    Args:
        meal_id: ID of the meal to update
        updates: Dictionary of field names and new values to update
    """
    meal_id: str
    updates: dict[str, Any]