from attrs import frozen

from src.contexts.seedwork.shared.domain.commands.command import Command
from src.contexts.shared_kernel.domain.value_objects.tag import Tag

@frozen(kw_only=True)
class CreateClient(Command):
    """Command to create a new client."""

    author_id: str
    profile: str
    contact_info: str | None = None
    address: str | None = None
    notes: str | None = None
    tags: set[Tag] | None = None