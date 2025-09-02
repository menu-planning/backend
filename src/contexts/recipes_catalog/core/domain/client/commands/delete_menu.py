"""Domain command to delete a menu from a client aggregate."""
from attrs import frozen
from src.contexts.seedwork.domain.commands.command import Command


@frozen(kw_only=True)
class DeleteMenu(Command):
    """Command to delete an existing menu.

    Args:
        menu_id: ID of the menu to delete
    """

    menu_id: str

