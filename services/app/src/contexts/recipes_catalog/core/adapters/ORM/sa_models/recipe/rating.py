from datetime import datetime

import src.db.sa_field_types as sa_field
from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from src.db.base import SaBase


class RatingSaModel(SaBase):
    __tablename__ = "ratings"

    user_id: Mapped[sa_field.strpk]
    recipe_id: Mapped[str] = mapped_column(
        ForeignKey("recipes_catalog.recipes.id"), primary_key=True
    )
    taste: Mapped[int] = mapped_column(index=True)
    convenience: Mapped[int] = mapped_column(index=True)
    comment: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), index=True
    )

    __table_args__ = {"schema": "recipes_catalog", "extend_existing": True}
