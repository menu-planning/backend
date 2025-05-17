from attrs import frozen
from src.contexts.seedwork.shared.domain.commands.command import Command


@frozen
class AddHouseInputAndCreateProductIfNeeded(Command):
    barcode: str
    house_id: str
    is_food: bool
