from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column

import src.db.sa_field_types as sa_field
from src.db.base import SaBase, SerializerMixin


class BrandSaModel(SerializerMixin, SaBase):
    __tablename__ = "brands"

    id: Mapped[sa_field.strpk]
    name: Mapped[str]
    author_id: Mapped[str]
    description: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
    discarded: Mapped[bool] = mapped_column(default=False)
    version: Mapped[int] = mapped_column(default=1)

    __table_args__ = ({"schema": "products_catalog", "extend_existing": True},)
