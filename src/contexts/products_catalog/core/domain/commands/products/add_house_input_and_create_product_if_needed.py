"""Command to record a house input and create product when necessary."""
from attrs import frozen
from src.contexts.seedwork.domain.commands.command import Command


@frozen
class AddHouseInputAndCreateProductIfNeeded(Command):
    """Command to record a house input and create product when necessary.
    
    Attributes:
        barcode: Product barcode for identification.
        house_id: Identifier of the house/establishment.
        is_food: Flag indicating if the input is food-related.
    
    Notes:
        Records house input data and creates a product entry if one doesn't
        exist for the given barcode. Used for tracking household inventory
        and product usage.
    """
    barcode: str
    house_id: str
    is_food: bool
