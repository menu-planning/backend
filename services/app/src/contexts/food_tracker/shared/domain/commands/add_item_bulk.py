from attrs import frozen
from src.contexts.food_tracker.shared.domain.commands.add_item import AddItem
from src.contexts.seedwork.shared.domain.commands.command import Command


@frozen
class AddItemBulk(Command):
    add_item_cmds: list[AddItem]
