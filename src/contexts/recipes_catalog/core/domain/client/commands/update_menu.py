"""Domain command to update a menu's fields."""
from typing import Any

from attrs import frozen
from src.contexts.seedwork.domain.commands.command import Command


@frozen(kw_only=True)
class UpdateMenu(Command):
    """Command to update menu fields.

    Args:
        menu_id: ID of the menu to update
        updates: Dictionary of field names and new values to update
    """

    menu_id: str
    updates: dict[str, Any]
