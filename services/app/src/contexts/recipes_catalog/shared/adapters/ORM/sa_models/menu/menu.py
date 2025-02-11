from datetime import datetime

import src.db.sa_field_types as sa_field
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.menu.associations import (
    menus_tags_association,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.menu.menu_item import (
    MenuItemSaModel,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag import TagSaModel
from src.db.base import SaBase


class MenuSaModel(SaBase):
    __tablename__ = "menus"

    id: Mapped[sa_field.strpk]
    author_id: Mapped[str]
    client_id: Mapped[str]
    items: Mapped[list[MenuItemSaModel]] = relationship(
        "MenuItemSaModel",
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
