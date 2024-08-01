from attrs import frozen
from src.contexts.seedwork.shared.domain.commands.command import Command


@frozen(hash=True)
class InviteNutritionist(Command):
    house_id: str
    nutritionist_id: str
