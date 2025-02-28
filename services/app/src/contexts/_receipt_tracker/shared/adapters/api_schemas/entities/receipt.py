from datetime import datetime

from pydantic import BaseModel, Field, field_serializer
from src.contexts._receipt_tracker.shared.adapters.api_schemas.pydantic_validators import (
    CfeKeyStr,
    CNPJStr,
)
from src.contexts._receipt_tracker.shared.adapters.api_schemas.value_objects.item import (
    ApiItem,
)
from src.contexts._receipt_tracker.shared.domain.entities.receipt import Receipt
from src.contexts._receipt_tracker.shared.domain.enums import State


class ApiReceipt(BaseModel):
    """A class to represent and validate a receipt."""

    cfe_key: CfeKeyStr
    house_ids: list[str]
    qrcode: str | None = None
    date: datetime | None = None
    state: State | None = None
    seller_id: CNPJStr | None = None
    scraped: bool = False
    items: list[ApiItem] = Field(default_factory=list)
    discarded: bool = False
    version: int = 1

    @field_serializer("state")
    def serialize_state(self, state: State, _info) -> str | None:
        return state.value if state else None

    @classmethod
    def from_domain(cls, domain_obj: Receipt) -> "ApiReceipt":
        """Create a ApiReceipt from a domain object."""
        try:
            return cls(
                cfe_key=domain_obj.id,
                house_ids=domain_obj.house_ids,
                qrcode=domain_obj.qrcode,
                date=domain_obj.date,
                state=State(domain_obj.state),
                seller_id=domain_obj.seller_id,
                scraped=domain_obj.scraped,
                items=[ApiItem.from_domain(i) for i in domain_obj.items],
                discarded=domain_obj.discarded,
                version=domain_obj.version,
            )
        except Exception as e:
            raise ValueError(f"Failed to build ApiReceipt from domain instance: {e}")

    def to_domain(self) -> Receipt:
        """Create a domain object from a ApiReceipt."""
        try:
            kwargs = self.model_dump()
            kwargs["items"] = [i.to_domain() for i in self.items]
            return Receipt(**kwargs)
        except Exception as e:
            raise ValueError(f"Failed to convert ApiReceipt to domain instance: {e}")
