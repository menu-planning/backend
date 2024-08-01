from attrs import frozen
from src.contexts.seedwork.shared.domain.commands.command import Command


@frozen(hash=True)
class RemoveMember(Command):
    house_id: str
    member_id: str
