from attrs import frozen
from src.contexts.seedwork.shared.domain.commands.command import Command


@frozen(kw_only=True)
class CreateHousehold(Command):
    owner_id: str
    name: str
    address: str
