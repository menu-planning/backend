from attrs import frozen
from src.contexts.seedwork.domain.commands.command import Command


@frozen
class AddProductImage(Command):
    """Command to add an image to a product.
    
    Attributes:
        product_id: Unique identifier of the product.
        image_url: URL of the image to associate with the product.
    
    Notes:
        Associates an image with an existing product. Triggers image
        processing and storage workflows.
    """
    product_id: str
    image_url: str
