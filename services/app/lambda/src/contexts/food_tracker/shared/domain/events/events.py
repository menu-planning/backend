import uuid

from attrs import field, frozen
from src.contexts.seedwork.shared.domain.event import Event


@frozen(hash=True)
class ReceiptCreated(Event):
    house_id: str
    cfe_key: str
    qrcode: str | None = None


@frozen(hash=True)
class ItemAdded(Event):
    item_id: str = field(factory=lambda: uuid.uuid4().hex)


@frozen(hash=True)
class ItemIsFoodChanged(Event):
    house_id: str
    item_id: str
    barcode: str
    is_food: bool


@frozen(hash=True)
class WrongProductAllocated(Event):
    item_id: str
    description: str
    product_id: str


@frozen(hash=True)
class ProductNotFound(Event):
    item_id: str
    description: str
    barcode: str


@frozen(hash=True)
class MemberInvited(Event):
    house_id: str
    member_id: str


@frozen(hash=True)
class NutritionistInvited(Event):
    house_id: str
    nutritionist_id: str
