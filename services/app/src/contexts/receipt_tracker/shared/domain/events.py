from attrs import frozen
from src.contexts.seedwork.shared.domain.event import Event


@frozen
class ReceiptAdded(Event):
    cfe_key: str
    house_ids: list[str]
    state: str
    qrcode: str | None = None


@frozen
class ItemsAddedToReceipt(Event):
    cfe_key: str


@frozen
class ProductsAddedToItems(Event):
    cfe_key: str
