"""Delete tag command for recipes catalog domain."""
from attrs import frozen
from src.contexts.seedwork.domain.commands.command import Command


@frozen(kw_only=True)
class DeleteTag(Command):
    """Command to delete an existing tag.

    Args:
        id: ID of the tag to delete.
    """
    id: str
