import cattrs
from pydantic import BaseModel
from src.contexts.products_catalog.core.adapters.api_schemas import (
    UniqueBarcode,
)
from src.contexts.products_catalog.core.domain.commands.products import (
    AddHouseInputAndCreateProductIfNeeded,
)


class ApiAddHouseInputAndCreateProductIfNeeded(BaseModel):
    """
    A Pydantic model representing and validating the data required
    for a house to mark the product as food or non food via the API.

    This model is used for input validation and serialization of domain
    objects in API requests and responses.

    Attributes:
        barcode (str): The barcode of the product.
        house_id (str): The id of the house.
        is_food (bool): Whether the product is food or not.

    Raises:
        ValueError: If the conversion to domain model fails.

    """

    barcode: UniqueBarcode
    house_id: str
    is_food: bool

    def to_domain(self) -> AddHouseInputAndCreateProductIfNeeded:
        """Converts the instance to a domain model object for adding a house input."""
        try:
            return cattrs.structure(
                self.model_dump(), AddHouseInputAndCreateProductIfNeeded
            )
        except Exception as e:
            error_msg = (
                f"Failed to convert ApiAddHouseInputAndCreateProductIfNeeded "
                f"to domain model: {e}"
            )
            raise ValueError(error_msg) from e
