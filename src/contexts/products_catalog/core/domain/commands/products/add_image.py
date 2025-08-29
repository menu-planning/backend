from attrs import frozen
from src.contexts.seedwork.shared.domain.commands.command import Command


@frozen
class AddProductImage(Command):
    product_id: str
    image_url: str
