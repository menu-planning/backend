from pydantic import BaseModel
from src.contexts.food_tracker.shared.domain.value_objects.receipt import Receipt


class ApiReceipt(BaseModel):
    cfe_key: str
    qrcode: str | None = None

    @classmethod
    def from_domain(cls, receipt: Receipt) -> "ApiReceipt":
        return cls(cfe_key=receipt.cfe_key, qrcode=receipt.qrcode)

    def to_domain(self) -> Receipt:
        return Receipt(cfe_key=self.cfe_key, qrcode=self.qrcode)
