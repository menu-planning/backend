from dataclasses import fields
from datetime import datetime

import src.db.sa_field_types as sa_field
from sqlalchemy import ForeignKey, Index, func
from sqlalchemy.orm import Mapped, composite, mapped_column, relationship
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.associations import (
    recipes_diet_types_association,
    recipes_season_association,
    recipes_tags_association,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.ingredient import (
    IngredientSaModel,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.month import (
    MonthSaModel,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.rating import (
    RatingSaModel,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.tags import (
    CategorySaModel,
    MealPlanningSaModel,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.diet_type import DietTypeSaModel
from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts import (
    NutriFactsSaModel,
)
from src.db.base import SaBase


class RecipeSaModel(SaBase):
    __tablename__ = "recipes"

    id: Mapped[sa_field.strpk]
    name: Mapped[str | None]
    preprocessed_name: Mapped[str]
    description: Mapped[str | None]
    ingredients: Mapped[list[IngredientSaModel]] = relationship(
        "IngredientSaModel", lazy="selectin"
    )
    instructions: Mapped[str]
    author_id: Mapped[str]
    utensils: Mapped[str | None]
    total_time: Mapped[int | None]
    servings: Mapped[int | None]
    notes: Mapped[str | None]
    diet_types: Mapped[list[DietTypeSaModel]] = relationship(
        secondary=recipes_diet_types_association, lazy="selectin"
    )
    categories: Mapped[list[CategorySaModel]] = relationship(
        secondary=recipes_tags_association, lazy="selectin"
    )
    cuisine_id: Mapped[str | None] = mapped_column(
        ForeignKey("shared_kernel.cuisines.id"),
    )
    flavor_id: Mapped[str | None] = mapped_column(
        ForeignKey("shared_kernel.flavors.id")
    )
    texture_id: Mapped[str | None] = mapped_column(
        ForeignKey("shared_kernel.textures.id")
    )
    meal_planning: Mapped[list[MealPlanningSaModel]] = relationship(
        secondary=recipes_tags_association, lazy="selectin"
    )
    privacy: Mapped[str | None]
    ratings: Mapped[list[RatingSaModel]] = relationship(lazy="selectin")
    weight_in_grams: Mapped[float | None]
    calorie_density: Mapped[float | None]
    carbo_percentage: Mapped[float | None]
    protein_percentage: Mapped[float | None]
    total_fat_percentage: Mapped[float | None]
    nutri_facts: Mapped[NutriFactsSaModel] = composite(
        *[mapped_column(i.name) for i in fields(NutriFactsSaModel)]
    )
    season: Mapped[list[MonthSaModel]] = relationship(
        secondary=recipes_season_association, lazy="selectin"
    )
    image_url: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    discarded: Mapped[bool] = mapped_column(default=False)
    version: Mapped[int] = mapped_column(default=1)
    average_taste_rating: Mapped[float | None]
    average_convenience_rating: Mapped[float | None]

    __table_args__ = (
        Index(
            "ix_recipes_catalog_recipes_preprocessed_name_gin_trgm",
            "preprocessed_name",
            postgresql_ops={"preprocessed_name": "gin_trgm_ops"},
            postgresql_using="gin",
        ),
        {"schema": "recipes_catalog", "extend_existing": True},
    )
