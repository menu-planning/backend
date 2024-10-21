from __future__ import annotations

from attrs import frozen
from src.contexts._receipt_tracker.shared.domain.value_objects.product import Product
from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject
from src.contexts.shared_kernel.domain.value_objects import Amount


@frozen
class Item(ValueObject):
    description: str
    amount: Amount
    price_paid: float
    price_per_unit: float
    gross_price: float
    sellers_product_code: str
    barcode: str
    discount: float
    number: int | None = None
    product: Product | None = None

    @staticmethod
    def unique_barcode(barcode: str) -> str:
        try:
            return int(barcode) > 999999
        except Exception:
            return False

    def __add__(self, other: Item):
        if isinstance(other, Item) and other.description == self.description:
            return Item(
                description=self.description,
                amount=self.amount + other.amount,
                price_paid=self.price_paid + other.price_paid,
                price_per_unit=self.price_per_unit,
                gross_price=self.gross_price + other.gross_price,
                sellers_product_code=self.sellers_product_code,
                barcode=self.barcode,
                discount=self.discount + other.discount,
                product=self.product,
            )
        return NotImplemented
