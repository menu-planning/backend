from attrs import frozen
from src.contexts.products_catalog.shared.domain.commands.products.add_food_product import (
    AddFoodProduct,
)
from src.contexts.seedwork.shared.domain.commands.command import Command


@frozen
class AddFoodProductBulk(Command):
    add_product_cmds: list[AddFoodProduct]
