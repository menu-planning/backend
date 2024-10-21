from datetime import datetime

from attrs import frozen
from src.contexts._receipt_tracker.shared.domain.value_objects.item import Item
from src.contexts._receipt_tracker.shared.domain.value_objects.product import Product
from src.contexts._receipt_tracker.shared.domain.value_objects.seller import Seller
from src.contexts.seedwork.shared.domain.commands.command import Command


@frozen
class AddReceipt(Command):
    house_id: str
    cfe_key: str
    qrcode: str | None = None


@frozen
class CreateSellerAndUpdateWithScrapedData(Command):
    cfe_key: str
    date: datetime
    seller: Seller
    items: list[Item]


@frozen
class UpdateProducts(Command):
    cfe_key: str
    barcode_product_mapping: dict[str, Product]
