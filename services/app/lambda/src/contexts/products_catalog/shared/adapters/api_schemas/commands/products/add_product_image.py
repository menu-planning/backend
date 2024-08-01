import cattrs
from pydantic import BaseModel
from src.contexts.products_catalog.shared.domain.commands import AddProductImage


class ApiAddProductImage(BaseModel):
    """
    A Pydantic model representing and validating the the data required
    to add an image to a product via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        product_id (str): The id of the product to add the image to.
        image_url (str): The url of the image to add to the product.

    Raises:
        ValueError: If the conversion to domain model fails.

    """

    product_id: str
    image_url: str

    def to_domain(self) -> AddProductImage:
        """Converts the instance to a domain model object for adding a product image."""
        try:
            return cattrs.structure(self.model_dump(), AddProductImage)
        except Exception as e:
            raise ValueError(
                f"Failed to convert ApiAddProductImage to domain model: {e}"
            )
