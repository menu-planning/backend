from pydantic import BaseModel
from src.contexts.products_catalog.core.adapters.api_schemas.pydantic_validators import (
    UniqueBarcode,
)
from src.contexts.products_catalog.core.domain.commands.products import (
    AddHouseInputAndCreateProductIfNeeded,
)
from src.contexts.seedwork.adapters.exceptions.api_schema_errors import (
    ValidationConversionError,
)


class ApiAddHouseInputAndCreateProductIfNeeded(BaseModel):
    """API schema for house input on product food classification.
    
    Attributes:
        barcode: The barcode of the product.
        house_id: The id of the house.
        is_food: Whether the product is food or not.
    """

    barcode: UniqueBarcode
    house_id: str
    is_food: bool

    def to_domain(self) -> AddHouseInputAndCreateProductIfNeeded:
        """Convert API schema to domain command.
        
        Returns:
            AddHouseInputAndCreateProductIfNeeded domain command.
            
        Raises:
            ValidationConversionError: If conversion to domain model fails.
        """
        try:
            return AddHouseInputAndCreateProductIfNeeded(
                barcode=self.barcode if self.barcode else "",
                house_id=self.house_id,
                is_food=self.is_food,
            )
        except Exception as e:
            error_msg = (
                f"Failed to convert ApiAddHouseInputAndCreateProductIfNeeded "
                f"to domain model: {e}"
            )
            raise ValidationConversionError(
                error_msg,
                schema_class=self.__class__,
                conversion_direction="api_to_domain",
                source_data=self.model_dump(),
                validation_errors=[str(e)],
            ) from e
