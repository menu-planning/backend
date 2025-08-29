from attrs import frozen
from src.contexts.seedwork.shared.domain.commands.command import Command


@frozen
class AddNonFoodProduct(Command):
    source_id: str
    name: str
    barcode: str
    user_id: str | None = None
    is_food: bool | None = None
    image_url: str | None = None
