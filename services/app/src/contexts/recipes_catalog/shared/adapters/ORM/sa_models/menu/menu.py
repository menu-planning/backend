from datetime import datetime

from sqlalchemy import ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

import src.db.sa_field_types as sa_field
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.menu.associations import (
    menus_tags_association,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.menu.menu_meal import (
    MenuMealSaModel,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag import TagSaModel
from src.db.base import SaBase


class MenuSaModel(SaBase):
    __tablename__ = "menus"

    id: Mapped[sa_field.strpk]
    author_id: Mapped[str]
    client_id: Mapped[str] = mapped_column(
        ForeignKey("recipes_catalog.clients.id"),
    )
    meals: Mapped[list[MenuMealSaModel]] = relationship(
        "MenuMealSaModel",
        lazy="selectin",
        cascade="save-update, merge",
    )
    tags: Mapped[list[TagSaModel]] = relationship(
        secondary=menus_tags_association,
        lazy="selectin",
        cascade="save-update, merge",
    )
    description: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    discarded: Mapped[bool] = mapped_column(default=False)
    version: Mapped[int] = mapped_column(default=1)

    __table_args__ = ({"schema": "recipes_catalog", "extend_existing": True},)
