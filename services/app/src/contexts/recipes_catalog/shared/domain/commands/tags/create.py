from attrs import frozen
from src.contexts.seedwork.shared.domain.commands.command import Command


@frozen(kw_only=True)
class CreateTag(Command):
    key: str
    value: str
    author_id: str
