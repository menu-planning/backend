from attrs import frozen
from src.contexts.seedwork.shared.domain.commands.command import Command


@frozen(kw_only=True)
class DeleteMenu(Command):
    # client_id: str
    menu_id: str

