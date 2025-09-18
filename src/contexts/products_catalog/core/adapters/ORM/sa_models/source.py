"""SQLAlchemy model for catalog sources."""

import src.db.sa_field_types as sa_field
from sqlalchemy.orm import Mapped, mapped_column
from src.db.base import SaBase, SerializerMixin


class SourceSaModel(SerializerMixin, SaBase):
    """SQLAlchemy model for product sources.

    Represents data sources for products in the catalog.
    """

    __tablename__ = "sources"

    id: Mapped[sa_field.strpk]
    name: Mapped[str]
    author_id: Mapped[str]
    description: Mapped[str | None]
    created_at: Mapped[sa_field.datetime_tz_created]
    updated_at: Mapped[sa_field.datetime_tz_updated]
    discarded: Mapped[bool] = mapped_column(default=False)
    version: Mapped[int] = mapped_column(default=1, nullable=False)

    __table_args__ = ({"schema": "products_catalog", "extend_existing": True},)
    __mapper_args__ = {"version_id_col": version}
