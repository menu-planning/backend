"""SQLAlchemy model for the `recipes` table in recipes catalog schema."""

from dataclasses import fields

import src.db.sa_field_types as sa_field
from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, composite, mapped_column, relationship
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.ingredient_sa_model import (
    IngredientSaModel,
)
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.meal_associations import (
    recipes_tags_association,
)
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.rating_sa_model import (
    RatingSaModel,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts_sa_model import (
    NutriFactsSaModel,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag_sa_model import (
    TagSaModel,
)
from src.db.base import SaBase, SerializerMixin


class RecipeSaModel(SerializerMixin, SaBase):
    """ORM mapping for recipes, with relationships to ingredients, ratings and tags."""

    __tablename__ = "recipes"

    id: Mapped[sa_field.strpk]
    name: Mapped[str]
    preprocessed_name: Mapped[str]
    description: Mapped[str | None]
    ingredients: Mapped[list[IngredientSaModel]] = relationship(
        "IngredientSaModel",
        lazy="selectin",
        order_by="IngredientSaModel.position",
        cascade="all, delete-orphan",
    )
    instructions: Mapped[str]
    author_id: Mapped[str] = mapped_column(index=True)
    meal_id: Mapped[str] = mapped_column(
        ForeignKey("recipes_catalog.meals.id", ondelete="CASCADE"),
    )
    utensils: Mapped[str | None]
    total_time: Mapped[int | None] = mapped_column(index=True)
    notes: Mapped[str | None]
    tags: Mapped[list[TagSaModel]] = relationship(
        secondary=recipes_tags_association,
        lazy="selectin",
        cascade="save-update, merge, delete",
    )
    privacy: Mapped[str | None]
    ratings: Mapped[list[RatingSaModel]] = relationship(
        "RatingSaModel",
        lazy="selectin",
        order_by="RatingSaModel.created_at",
        cascade="all, delete-orphan",
    )
    weight_in_grams: Mapped[int | None] = mapped_column(index=True)
    calorie_density: Mapped[float | None] = mapped_column(index=True)
    carbo_percentage: Mapped[float | None] = mapped_column(index=True)
    protein_percentage: Mapped[float | None] = mapped_column(index=True)
    total_fat_percentage: Mapped[float | None] = mapped_column(index=True)
    nutri_facts: Mapped[NutriFactsSaModel] = composite(
        *[
            mapped_column(
                field.name,
                index=field.name
                in {
                    "calories",
                    "protein",
                    "carbohydrate",
                    "total_fat",
                    "saturated_fat",
                    "trans_fat",
                    "sugar",
                    "salt",
                },
            )
            for field in fields(NutriFactsSaModel)
        ],
    )
    image_url: Mapped[str | None]
    created_at: Mapped[sa_field.datetime_tz_created]
    updated_at: Mapped[sa_field.datetime_tz_updated]

    discarded: Mapped[bool] = mapped_column(default=False)
    version: Mapped[int] = mapped_column(nullable=False)
    average_taste_rating: Mapped[float | None] = mapped_column(index=True)
    average_convenience_rating: Mapped[float | None] = mapped_column(index=True)

    __table_args__ = (
        Index(
            "ix_recipes_catalog_recipes_preprocessed_name_gin_trgm",
            "preprocessed_name",
            postgresql_ops={"preprocessed_name": "gin_trgm_ops"},
            postgresql_using="gin",
        ),
        {"schema": "recipes_catalog", "extend_existing": True},
    )
    __mapper_args__ = {"version_id_col": version}