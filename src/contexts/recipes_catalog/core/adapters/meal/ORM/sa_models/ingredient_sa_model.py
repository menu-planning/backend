"""SQLAlchemy model for ingredients in recipes catalog schema."""

import src.db.sa_field_types as sa_field
from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from src.db.base import SaBase, SerializerMixin


class IngredientSaModel(SerializerMixin, SaBase):
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
    created_at: Mapped[sa_field.datetime_tz_updated]

    __table_args__ = (
        Index(
            "ix_recipes_catalog_ingredients_preprocessed_name_gin_trgm",
            "preprocessed_name",
            postgresql_ops={"preprocessed_name": "gin_trgm_ops"},
            postgresql_using="gin",
        ),
        {"schema": "recipes_catalog", "extend_existing": True},
    )
