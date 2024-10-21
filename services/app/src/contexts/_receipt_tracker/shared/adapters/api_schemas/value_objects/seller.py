import cattrs
from attrs import asdict
from pydantic import BaseModel
from src.contexts._receipt_tracker.shared.adapters.api_schemas.pydantic_validators import (
    CNPJStr,
)
from src.contexts._receipt_tracker.shared.domain.value_objects.seller import Seller
from src.contexts.shared_kernel.endpoints.api_schemas.value_objects.address import (
    ApiAddress,
)


class ApiSeller(BaseModel):
    """A class to represent and validate a seller."""

    name: str
    cnpj: CNPJStr
    state_registration: str
    address: ApiAddress

    @classmethod
    def from_domain(cls, domain_obj: Seller) -> "ApiSeller":
        """Creates an instance of `ApiSeller` from a domain model object."""
        try:
            return cls(**asdict(domain_obj))
        except Exception as e:
            raise ValueError(f"Failed to build ApiSeller from domain instance: {e}")

    def to_domain(self) -> Seller:
        """Converts the instance to a domain model object."""
        try:
            return cattrs.structure(self.model_dump(), Seller)
        except Exception as e:
            raise ValueError(f"Failed to convert ApiSeller to domain model: {e}")
