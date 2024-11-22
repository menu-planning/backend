from dataclasses import fields
from datetime import date, datetime, time

import src.db.sa_field_types as sa_field
from sqlalchemy import ForeignKey, Index, func
from sqlalchemy.orm import Mapped, composite, mapped_column, relationship
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.recipe.recipe import (
    RecipeSaModel,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts import (
    NutriFactsSaModel,
)
from src.db.base import SaBase


class MenuSaModel(SaBase):
    __tablename__ = "menus"

    id: Mapped[sa_field.strpk]
    name: Mapped[str | None]
    preprocessed_name: Mapped[str]
    description: Mapped[str | None]
    recipes: Mapped[list[RecipeSaModel]] = relationship(
        "RecipeSaModel", lazy="selectin"
    )
    author_id: Mapped[str]
    menu_id: Mapped[str | None] = mapped_column(
        ForeignKey("recipes_catalog.menus.id"),
    )
    menu: Mapped[str | None] = relationship("MenuSaModel", lazy="selectin")
    day: Mapped[date | None]
    hour: Mapped[time | None]
    notes: Mapped[str | None]
    category_id: Mapped[str | None] = mapped_column(
        ForeignKey("shared_kernel.categories.id"),
    )
    category: Mapped[str | None] = relationship("CategorySaModel", lazy="selectin")
    tagert_nutri_facts: Mapped[NutriFactsSaModel] = composite(
        *[mapped_column(i.name) for i in fields(NutriFactsSaModel)]
    )
    like: Mapped[bool | None]
    image_url: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    discarded: Mapped[bool] = mapped_column(default=False)
    version: Mapped[int] = mapped_column(default=1)

    __table_args__ = (
        Index(
            "ix_recipes_catalog_recipes_preprocessed_name_gin_trgm",
            "preprocessed_name",
            postgresql_ops={"preprocessed_name": "gin_trgm_ops"},
            postgresql_using="gin",
        ),
        {"schema": "recipes_catalog", "extend_existing": True},
    )
