import cattrs
from attrs import asdict
from pydantic import BaseModel, NonNegativeFloat, NonNegativeInt
from src.contexts._receipt_tracker.shared.adapters.api_schemas.value_objects.product import (
    ApiProduct,
)
from src.contexts._receipt_tracker.shared.domain.value_objects.item import Item
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.amount import (
    ApiAmount,
)


class ApiItem(BaseModel):
    """A class to represent and validate an item."""

    description: str
    amount: ApiAmount
    price_paid: NonNegativeFloat
    price_per_unit: NonNegativeFloat
    gross_price: NonNegativeFloat
    sellers_product_code: str
    barcode: str
    discount: NonNegativeFloat | None = None
    number: NonNegativeInt | None = None
    product: ApiProduct | None = None

    @classmethod
    def from_domain(cls, domain_obj: Item) -> "ApiItem":
        """Creates an instance of `ApiItem` from a domain model object."""
        try:
            return cls(**asdict(domain_obj))
        except Exception as e:
            raise ValueError(f"Failed to build ApiItem from domain instance: {e}")

    def to_domain(self) -> Item:
        """Converts the instance to a domain model object."""
        try:
            return cattrs.structure(self.model_dump(), Item)
        except Exception as e:
            raise ValueError(f"Failed to convert ApiItem to domain model: {e}")
