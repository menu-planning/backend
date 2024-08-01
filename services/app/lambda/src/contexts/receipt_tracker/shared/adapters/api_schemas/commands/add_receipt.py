import cattrs
from attrs import asdict
from pydantic import BaseModel
from src.contexts.receipt_tracker.shared.adapters.api_schemas.pydantic_validators import (
    CfeKeyStr,
)
from src.contexts.receipt_tracker.shared.domain.commands import AddReceipt


class ApiAddReceipt(BaseModel):
    """A class to represent and validate a receipt."""

    house_id: str
    cfe_key: CfeKeyStr
    qrcode: str | None = None

    @classmethod
    def from_domain(cls, domain_obj: AddReceipt) -> "ApiAddReceipt":
        """Creates an instance of `ApiAddReceipt` from a domain model object."""
        try:
            return cls(**asdict(domain_obj))
        except Exception as e:
            raise ValueError(f"Failed to build ApiAddReceipt from domain instance: {e}")

    def to_domain(self) -> AddReceipt:
        """Converts the instance to a domain model object."""
        try:
            return cattrs.structure(self.model_dump(), AddReceipt)
        except Exception as e:
            raise ValueError(f"Failed to convert ApiAddReceipt to domain model: {e}")
