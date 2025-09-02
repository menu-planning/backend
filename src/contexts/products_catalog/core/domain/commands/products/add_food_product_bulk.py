from attrs import frozen
from src.contexts.products_catalog.core.domain.commands.products.add_food_product import (
    AddFoodProduct,
)
from src.contexts.seedwork.domain.commands.command import Command


@frozen
class AddFoodProductBulk(Command):
    """Command to add multiple food products to the catalog in a single operation.
    
    Attributes:
        add_product_cmds: List of individual AddFoodProduct commands to execute.
    
    Notes:
        Batch operation for efficient bulk product creation. Each command
        in the list is processed individually with its own transaction scope.
    """
    add_product_cmds: list[AddFoodProduct]
