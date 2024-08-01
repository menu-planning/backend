import cattrs
from attrs import asdict
from pydantic import BaseModel
from src.contexts.receipt_tracker.shared.domain.value_objects.product import Product


class ApiProduct(BaseModel):
    """A class to represent and validate a product."""

    id: str
    name: str
    source: str
    is_food: bool

    @classmethod
    def from_domain(cls, domain_obj: Product) -> "ApiProduct":
        """Creates an instance of `ApiProduct` from a domain model object."""
        try:
            return cls(**asdict(domain_obj))
        except Exception as e:
            raise ValueError(f"Failed to build ApiProduct from domain instance: {e}")

    def to_domain(self) -> Product:
        """Converts the instance to a domain model object."""
        try:
            return cattrs.structure(self.model_dump(), Product)
        except Exception as e:
            raise ValueError(f"Failed to convert ApiProduct to domain model: {e}")
