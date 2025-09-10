"""SQLAlchemy model for catalog brands."""

import src.db.sa_field_types as sa_field
from sqlalchemy.orm import Mapped, mapped_column
from src.db.base import SaBase, SerializerMixin


class BrandSaModel(SerializerMixin, SaBase):
    """SQLAlchemy model for product brands.

    Represents brand entities in the products catalog.
    """

    __tablename__ = "brands"

    id: Mapped[sa_field.strpk]
    name: Mapped[str]
    author_id: Mapped[str]
    description: Mapped[str | None]
    created_at: Mapped[sa_field.datetime_tz_created]
    updated_at: Mapped[sa_field.datetime_tz_updated]
    discarded: Mapped[bool] = mapped_column(default=False)
    version: Mapped[int] = mapped_column(default=1)

    __table_args__ = ({"schema": "products_catalog", "extend_existing": True},)
