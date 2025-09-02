"""Command to add a new non-food product to the catalog."""
from attrs import frozen
from src.contexts.seedwork.domain.commands.command import Command


@frozen
class AddNonFoodProduct(Command):
    """Command to add a new non-food product to the catalog.
    
    Attributes:
        source_id: Identifier of the data source system.
        name: Product name.
        barcode: Product barcode.
        user_id: Identifier of the user creating the product.
        is_food: Flag indicating if the product is food-related.
        image_url: URL to product image.
    
    Notes:
        Creates a new non-food product in the catalog. Used for products
        that don't require nutritional information or food-specific classifications.
    """
    source_id: str
    name: str
    barcode: str
    user_id: str | None = None
    is_food: bool | None = None
    image_url: str | None = None
