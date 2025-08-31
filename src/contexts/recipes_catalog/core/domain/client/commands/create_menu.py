from attrs import field, frozen
from src.contexts.seedwork.shared.domain.commands.command import Command
from src.contexts.shared_kernel.domain.value_objects.tag import Tag


@frozen(kw_only=True)
class CreateMenu(Command):
    """Command to create a new menu."""
    # author_id: str
    client_id: str
    description: str | None = None
    tags: frozenset[Tag] | None = None
    menu_id: str = field(factory=Command.generate_uuid)  # Default to a new UUID if not provided
