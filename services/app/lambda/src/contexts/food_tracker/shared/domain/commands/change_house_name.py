from attrs import frozen
from src.contexts.seedwork.shared.domain.commands.command import Command


@frozen(hash=True)
class ChangeHouseName(Command):
    house_id: str
    name: str
