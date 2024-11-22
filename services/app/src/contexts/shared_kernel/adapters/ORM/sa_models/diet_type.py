from datetime import datetime

import src.db.sa_field_types as sa_field
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column
from src.db.base import SaBase


class DietTypeSaModel(SaBase):
    __tablename__ = "diet_types"

    id: Mapped[sa_field.strpk]
    name: Mapped[str] = mapped_column(index=True)
    author_id: Mapped[str]
    description: Mapped[str | None]
    privacy: Mapped[str | None] = mapped_column(default="private")
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
    discarded: Mapped[bool] = mapped_column(default=False)
    version: Mapped[int] = mapped_column(default=1)

    __table_args__ = {
        "schema": "shared_kernel",
        "extend_existing": True,
    }
