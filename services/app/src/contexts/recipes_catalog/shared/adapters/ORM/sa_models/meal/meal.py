from dataclasses import fields
from datetime import datetime

from sqlalchemy import ForeignKey, Index, func
from sqlalchemy.orm import Mapped, composite, mapped_column, relationship

import src.db.sa_field_types as sa_field
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.meal.associations import (
    meals_tags_association,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.recipe.recipe import (
    RecipeSaModel,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts import (
    NutriFactsSaModel,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag import TagSaModel
from src.db.base import SaBase


class MealSaModel(SaBase):
    __tablename__ = "meals"

    id: Mapped[sa_field.strpk]
    name: Mapped[str | None]
    preprocessed_name: Mapped[str]
    description: Mapped[str | None]
    recipes: Mapped[list[RecipeSaModel]] = relationship(
        "RecipeSaModel",
        lazy="selectin",
        cascade="save-update, merge",
    )
    author_id: Mapped[str] = mapped_column(index=True)
    menu_id: Mapped[str | None] = mapped_column(
        ForeignKey("recipes_catalog.menus.id"), index=True
    )
    notes: Mapped[str | None]
    total_time: Mapped[int | None] = mapped_column(index=True)
    tags: Mapped[list[TagSaModel]] = relationship(
        secondary=meals_tags_association,
        lazy="selectin",
        cascade="save-update, merge",
    )
    like: Mapped[bool | None] = mapped_column(index=True)
    weight_in_grams: Mapped[int | None] = mapped_column(index=True)
    calorie_density: Mapped[float | None] = mapped_column(index=True)
    carbo_percentage: Mapped[float | None] = mapped_column(index=True)
    protein_percentage: Mapped[float | None] = mapped_column(index=True)
    total_fat_percentage: Mapped[float | None] = mapped_column(index=True)
    nutri_facts: Mapped[NutriFactsSaModel] = composite(
        *[
            mapped_column(
                field.name,
                index=(
                    True
                    if (
                        field.name == "calories"
                        or field.name == "protein"
                        or field.name == "carbohydrate"
                        or field.name == "total_fat"
                        or field.name == "saturated_fat"
                        or field.name == "trans_fat"
                        or field.name == "sugar"
                        or field.name == "salt"
                    )
                    else False
                ),
            )
            for field in fields(NutriFactsSaModel)
        ],
    )
    image_url: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    discarded: Mapped[bool] = mapped_column(default=False)
    version: Mapped[int] = mapped_column(default=1)

    __table_args__ = (
        Index(
            "ix_recipes_catalog_meals_preprocessed_name_gin_trgm",
            "preprocessed_name",
            postgresql_ops={"preprocessed_name": "gin_trgm_ops"},
            postgresql_using="gin",
        ),
        {"schema": "recipes_catalog", "extend_existing": True},
    )
