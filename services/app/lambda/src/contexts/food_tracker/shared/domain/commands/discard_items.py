from attrs import frozen
from src.contexts.seedwork.shared.domain.commands.command import Command


@frozen
class DiscardItems(Command):
    item_ids: list[str]
