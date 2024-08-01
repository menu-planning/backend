import src.db.sa_field_types as sa_field
from sqlalchemy.orm import Mapped
from src.db.base import SaBase


class ReceiptSaModel(SaBase):
    __tablename__ = "receipts"

    id: Mapped[sa_field.strpk]
    qrcode: Mapped[str | None]

    __table_args__ = {"schema": "food_tracker", "extend_existing": True}
