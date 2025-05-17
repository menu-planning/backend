import uuid

from attrs import field, frozen
from src.contexts.seedwork.shared.domain.event import Event


@frozen
class FoodProductCreated(Event):
    data_source: str
    barcode: str | None = None
    product_id: str = field(factory=lambda: uuid.uuid4().hex)
