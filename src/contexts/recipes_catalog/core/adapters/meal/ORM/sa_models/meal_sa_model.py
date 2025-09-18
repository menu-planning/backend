from dataclasses import fields

import src.db.sa_field_types as sa_field
from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, composite, mapped_column, relationship
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.meal_associations import (
    meals_tags_association,
)
from src.contexts.recipes_catalog.core.adapters.meal.ORM.sa_models.recipe_sa_model import (
    RecipeSaModel,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts_sa_model import (
    NutriFactsSaModel,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag_sa_model import (
    TagSaModel,
)
from src.db.base import SaBase, SerializerMixin


class MealSaModel(SerializerMixin, SaBase):
    """SQLAlchemy ORM model for meals table.

    Represents a meal entity with recipes, nutritional information, and tags.
    Uses composite pattern for nutritional facts and includes full-text search
    capabilities via PostgreSQL GIN trigram indexes.

    Notes:
        Schema: recipes_catalog. Table: meals.
        Indexes: author_id, menu_id, total_time, like, weight_in_grams,
                 nutritional fields, created_at, preprocessed_name (GIN trigram).
        Relationships: recipes (selectin), tags (selectin via association table).
    """

    __tablename__ = "meals"

    id: Mapped[sa_field.strpk]
    name: Mapped[str]
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
    version: Mapped[int] = mapped_column(default=1, nullable=False)

    __table_args__ = (
        Index(
            "ix_recipes_catalog_meals_preprocessed_name_gin_trgm",
            "preprocessed_name",
            postgresql_ops={"preprocessed_name": "gin_trgm_ops"},
            postgresql_using="gin",
        ),
        {"schema": "recipes_catalog", "extend_existing": True},
    )
    __mapper_args__ = {"version_id_col": version}