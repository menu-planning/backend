from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from src.db.base import SaBase, SerializerMixin


class IsFoodVotesSaModel(SerializerMixin, SaBase):
    __tablename__ = "houses_is_food_registry"

    house_id: Mapped[str] = mapped_column(primary_key=True)
    product_id: Mapped[str] = mapped_column(
        ForeignKey("products_catalog.products.id"), primary_key=True
    )
    is_food: Mapped[bool]

    __table_args__ = {"schema": "products_catalog", "extend_existing": True}
