"""Domain command to create a menu under a client aggregate."""
from attrs import field, frozen
from src.contexts.seedwork.domain.commands.command import Command
from src.contexts.shared_kernel.domain.value_objects.tag import Tag


@frozen(kw_only=True)
class CreateMenu(Command):
    """Command to create a new menu.

    Args:
        client_id: ID of the client to create the menu for
        description: Optional description for the menu
        tags: Optional set of tags to associate with the menu
        menu_id: Unique identifier for the menu (auto-generated if not provided)
    """
    client_id: str
    description: str | None = None
    tags: frozenset[Tag] | None = None
    menu_id: str = field(factory=Command.generate_uuid)
