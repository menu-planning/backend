import cattrs
from attrs import asdict
from pydantic import BaseModel
from src.contexts.receipt_tracker.shared.adapters.api_schemas.pydantic_validators import (
    CfeKeyStr,
)
from src.contexts.receipt_tracker.shared.adapters.api_schemas.value_objects.product import (
    ApiProduct,
)
from src.contexts.receipt_tracker.shared.domain.commands import UpdateProducts


class ApiUpdateProducts(BaseModel):
    """A class to represent and validate a receipt."""

    cfe_key: CfeKeyStr
    barcode_product_mapping: dict[str, ApiProduct]

    @classmethod
    def from_domain(cls, domain_obj: UpdateProducts) -> "ApiUpdateProducts":
        """Creates an instance of `ApiUpdateProducts` from a domain model object."""
        try:
            return cls(**asdict(domain_obj))
        except Exception as e:
            raise ValueError(
                f"Failed to build ApiUpdateProducts from domain instance: {e}"
            )

    def to_domain(self) -> UpdateProducts:
        """Converts the instance to a domain model object."""
        try:
            return cattrs.structure(self.model_dump(), UpdateProducts)
        except Exception as e:
            raise ValueError(
                f"Failed to convert ApiUpdateProducts to domain model: {e}"
            )
