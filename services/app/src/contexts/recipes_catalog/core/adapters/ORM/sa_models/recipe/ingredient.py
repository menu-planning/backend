from datetime import datetime
from decimal import Decimal

import src.db.sa_field_types as sa_field
from sqlalchemy import ForeignKey, Index, Numeric, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from src.db.base import SaBase


class IngredientSaModel(SaBase):
    __tablename__ = "ingredients"

    name: Mapped[sa_field.strpk]
    preprocessed_name: Mapped[str]
    quantity: Mapped[float]
    unit: Mapped[str]
    recipe_id: Mapped[str] = mapped_column(
        ForeignKey("recipes_catalog.recipes.id"), primary_key=True
    )
    position: Mapped[int]
    full_text: Mapped[str | None]
    product_id: Mapped[str | None] = mapped_column(index=True)
    created_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now(), index=True
    )

    __table_args__ = (
        Index(
            "ix_recipes_catalog_ingredients_preprocessed_name_gin_trgm",
            "preprocessed_name",
            postgresql_ops={"preprocessed_name": "gin_trgm_ops"},
            postgresql_using="gin",
        ),
        # UniqueConstraint(
        #     "recipe_id",
        #     "position",
        #     name="uq_recipes_catalog_ingredients_recipe_id_position",
        # ),
        {"schema": "recipes_catalog", "extend_existing": True},
    )
