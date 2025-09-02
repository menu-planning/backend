"""Create tag command for recipes catalog domain."""
from attrs import frozen
from src.contexts.seedwork.domain.commands.command import Command


@frozen(kw_only=True)
class CreateTag(Command):
    """Command to create a new tag.

    Args:
        key: Tag identifier key.
        value: Tag display value.
        author_id: ID of the user creating the tag.
        type: Type/category of the tag.
    """
    key: str
    value: str
    author_id: str
    type: str
