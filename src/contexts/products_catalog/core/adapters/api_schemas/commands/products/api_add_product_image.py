from pydantic import BaseModel
from src.contexts.products_catalog.core.domain.commands.products.add_image import (
    AddProductImage,
)
from src.contexts.seedwork.adapters.exceptions.api_schema_errors import (
    ValidationConversionError,
)


class ApiAddProductImage(BaseModel):
    """API schema for adding an image to a product.
    
    Attributes:
        product_id: The id of the product to add the image to.
        image_url: The url of the image to add to the product.
    """

    product_id: str
    image_url: str

    def to_domain(self) -> AddProductImage:
        """Convert API schema to domain command.
        
        Returns:
            AddProductImage domain command.
            
        Raises:
            ValidationConversionError: If conversion to domain model fails.
        """
        try:
            return AddProductImage(
                product_id=self.product_id,
                image_url=self.image_url,
            )
        except Exception as e:
            error_msg = f"Failed to convert ApiAddProductImage to domain model: {e}"
            raise ValidationConversionError(
                error_msg,
                schema_class=self.__class__,
                conversion_direction="api_to_domain",
                source_data=self.model_dump(),
                validation_errors=[str(e)],
            ) from e
