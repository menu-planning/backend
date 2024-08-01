from datetime import datetime

import src.db.sa_field_types as sa_field
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, composite, mapped_column, relationship
from src.contexts.food_tracker.shared.adapters.internal_providers.products_catalog.api import (
    ProductSaModel,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.amount import AmountSaModel
from src.db.base import SaBase


class ItemSaModel(SaBase):
    __tablename__ = "items"

    id: Mapped[sa_field.strpk]
    house_id: Mapped[str] = mapped_column(ForeignKey("food_tracker.houses.id"))
    date: Mapped[datetime]
    description: Mapped[str]
    ids_of_products_with_similar_names: Mapped[list[str]]
    quantity: Mapped[int]
    unit: Mapped[str]
    is_food: Mapped[bool | None]
    product_id: Mapped[str | None] = mapped_column(
        ForeignKey("products_catalog.products.id")
    )
    product: Mapped[ProductSaModel | None] = relationship(lazy="selectin")
    price_per_unit: Mapped[float | None]
    barcode: Mapped[str | None]
    cfe_key: Mapped[str | None]
    discarded: Mapped[bool] = mapped_column(default=False)
    version: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
    amount: Mapped[AmountSaModel | None] = composite(AmountSaModel, "quantity", "unit")

    __table_args__ = {"schema": "food_tracker", "extend_existing": True}
