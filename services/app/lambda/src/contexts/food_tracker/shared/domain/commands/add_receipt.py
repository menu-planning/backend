from attrs import frozen
from src.contexts.seedwork.shared.domain.commands.command import Command


@frozen(hash=True)
class AddReceipt(Command):
    house_id: str
    cfe_key: str
    qrcode: str | None = None
