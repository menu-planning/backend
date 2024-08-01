from datetime import datetime

from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.contexts.receipt_tracker.shared.adapters.ORM.sa_models.association_tables import (
    receipts_houses_association,
)
from src.contexts.receipt_tracker.shared.adapters.ORM.sa_models.house import (
    HousesSaModel,
)
from src.contexts.receipt_tracker.shared.adapters.ORM.sa_models.item import ItemSaModel
from src.db import sa_field_types
from src.db.base import SaBase


class ReceiptSaModel(SaBase):
    __tablename__ = "receipts"

    id: Mapped[sa_field_types.strpk]
    qrcode: Mapped[str | None]
    date: Mapped[datetime | None]
    state: Mapped[str | None]
    seller_id: Mapped[str | None] = mapped_column(
        ForeignKey("receipt_tracker.sellers.id")
    )
    items: Mapped[list[ItemSaModel]] = relationship(lazy="selectin")
    scraped: Mapped[bool | None]
    products_added: Mapped[bool]
    discarded: Mapped[bool]
    version: Mapped[int]
    house_ids: Mapped[list[HousesSaModel]] = relationship(
        secondary=receipts_houses_association, lazy="selectin"
    )

    __table_args__ = {"schema": "receipt_tracker", "extend_existing": True}
