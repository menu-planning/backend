from datetime import datetime

from attrs import asdict
from pydantic import BaseModel, Field, NonNegativeFloat
from src.contexts.food_tracker.shared.domain.commands.add_item import AddItem
from src.contexts.food_tracker.shared.domain.commands.add_item_bulk import AddItemBulk
from src.contexts.food_tracker.shared.domain.enums import Unit
from src.contexts.food_tracker.shared.domain.value_objects.receipt import Receipt
from src.contexts.shared_kernel.domain.value_objects import Amount


class ReceiptTrackerAmount(BaseModel):
    quantity: NonNegativeFloat
    unit: Unit

    @classmethod
    def from_domain(cls, domain_obj: Amount) -> "ReceiptTrackerAmount":
        return cls(**asdict(domain_obj))

    def to_domain(self) -> Amount:
        return Amount(quantity=self.quantity, unit=self.unit)


class ReceiptTrackerSellerID(BaseModel):
    number: str


class ReceiptTrackerProduct(BaseModel):
    id: str
    name: str
    source: str
    is_food: bool


class ReceiptTrackerItem(BaseModel):
    description: str
    amount: ReceiptTrackerAmount
    price_paid: float
    price_per_unit: float
    gross_price: float
    sellers_product_code: str
    barcode: str
    discount: float
    number: int | None = None
    product: ReceiptTrackerProduct | None = None


class ReceiptTrackerReceipt(BaseModel):
    cfe_key: str
    house_ids: list[str]
    qrcode: str | None = None
    date: datetime | None = None
    state: str | None = None
    seller_id: ReceiptTrackerSellerID | None = None
    scraped: bool = False
    items: list[ReceiptTrackerItem] = Field(default_factory=list)
    discarded: bool = False
    version: int = 1

    def to_domain_receipt(self) -> Receipt:
        return Receipt(
            cfe_key=self.cfe_key,
            qrcode=self.qrcode,
        )

    def to_domain_add_item_bulk(
        self, house_ids: list[str] | None = None
    ) -> AddItemBulk:
        add_item_cmds = [
            AddItem(
                house_ids=house_ids or self.house_ids,
                date=self.date,
                description=item.description,
                amount=item.amount.model_dump() if item.amount else None,
                price_per_unit=item.price_per_unit,
                barcode=item.barcode,
                cfe_key=self.cfe_key,
                is_food=item.product.is_food if item.product else None,
                product_id=item.product.id if item.product else None,
            )
            for item in self.items
        ]
        add_same_barcode_items: dict[str, AddItem] = {}
        for item in add_item_cmds:
            if item.barcode in add_same_barcode_items:
                add_same_barcode_items[item.barcode].amount += item.amount
            else:
                add_same_barcode_items[item.barcode] = item
        return AddItemBulk(add_item_cmds=list(add_same_barcode_items.values()))
