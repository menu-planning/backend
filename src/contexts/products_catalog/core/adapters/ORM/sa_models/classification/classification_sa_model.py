"""Base SQLAlchemy model for catalog classification entities."""

from typing import Any, ClassVar

import src.db.sa_field_types as sa_field
from sqlalchemy.orm import Mapped, mapped_column
from src.db.base import SaBase, SerializerMixin


class ClassificationSaModel(SerializerMixin, SaBase):
    """Base SQLAlchemy model for classification entities.

    Provides polymorphic inheritance for different types of classifications
    such as categories, food groups, and process types.
    """

    __tablename__ = "classifications"

    id: Mapped[sa_field.strpk]
    name: Mapped[str]
    author_id: Mapped[str]
    description: Mapped[str | None]
    created_at: Mapped[sa_field.datetime_tz_created]
    updated_at: Mapped[sa_field.datetime_tz_updated]
    discarded: Mapped[bool] = mapped_column(default=False)
    version: Mapped[int] = mapped_column(default=1, nullable=False)
    type: Mapped[str]

    __mapper_args__: ClassVar[dict[str, Any]] = {
        "polymorphic_on": "type",
        "polymorphic_identity": "classifications",
    }

    __table_args__ = ({"schema": "products_catalog", "extend_existing": True},)
    __mapper_args__ = {"version_id_col": version}