from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from src.db.base import SaBase


class ItemSaModel(SaBase):
    __tablename__ = "items"

    number: Mapped[int] = mapped_column(primary_key=True)
    receipt_id: Mapped[str] = mapped_column(
        ForeignKey("receipt_tracker.receipts.id"), primary_key=True
    )
    description: Mapped[str]
    quantity: Mapped[float]
    unit: Mapped[str]
    price_paid: Mapped[float]
    price_per_unit: Mapped[float]
    gross_price: Mapped[float]
    sellers_product_code: Mapped[str]
    barcode: Mapped[str]
    discount: Mapped[float | None]
    product_id: Mapped[str | None]
    product_name: Mapped[str | None]
    product_source: Mapped[str | None]
    product_is_food: Mapped[bool | None]

    __table_args__ = {"schema": "receipt_tracker", "extend_existing": True}
