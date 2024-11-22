from dataclasses import fields
from datetime import datetime

import src.db.sa_field_types as sa_field
from sqlalchemy import ForeignKey, Index, func
from sqlalchemy.orm import Mapped, composite, mapped_column, relationship
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.recipe.associations import (
    recipes_allergens_association,
    recipes_diet_types_association,
    recipes_season_association,
    recipes_tags_association,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.recipe.ingredient import (
    IngredientSaModel,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.recipe.month import (
    MonthSaModel,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.recipe.rating import (
    RatingSaModel,
)
from src.contexts.recipes_catalog.shared.adapters.ORM.sa_models.recipe.tags import (
    CategorySaModel,
    MealPlanningSaModel,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.allergen import AllergenSaModel
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
    author_id: Mapped[str] = mapped_column(index=True)
    meal_id: Mapped[str | None] = mapped_column(
        ForeignKey("recipes_catalog.meals.id"),
    )
    utensils: Mapped[str | None]
    total_time: Mapped[int | None] = mapped_column(index=True)
    servings: Mapped[int | None]
    notes: Mapped[str | None]
    diet_types: Mapped[list[DietTypeSaModel]] = relationship(
        secondary=recipes_diet_types_association, lazy="selectin"
    )
    categories: Mapped[list[CategorySaModel]] = relationship(
        secondary=recipes_tags_association, lazy="selectin"
    )
    cuisine_id: Mapped[str | None] = mapped_column(
        ForeignKey("shared_kernel.cuisines.id"), index=True
    )
    flavor_id: Mapped[str | None] = mapped_column(
        ForeignKey("shared_kernel.flavors.id"), index=True
    )
    texture_id: Mapped[str | None] = mapped_column(
        ForeignKey("shared_kernel.textures.id"), index=True
    )
    allergens: Mapped[list[AllergenSaModel]] = relationship(
        secondary=recipes_allergens_association, lazy="selectin"
    )
    meal_planning: Mapped[list[MealPlanningSaModel]] = relationship(
        secondary=recipes_tags_association, lazy="selectin"
    )
    privacy: Mapped[str | None]
    ratings: Mapped[list[RatingSaModel]] = relationship(lazy="selectin")
    weight_in_grams: Mapped[float | None] = mapped_column(index=True)
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
    season: Mapped[list[MonthSaModel]] = relationship(
        secondary=recipes_season_association, lazy="selectin"
    )
    image_url: Mapped[str | None]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    discarded: Mapped[bool] = mapped_column(default=False)
    version: Mapped[int] = mapped_column(default=1)
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
