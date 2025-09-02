from dataclasses import fields
from datetime import time

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, composite, mapped_column
from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts_sa_model import (
    NutriFactsSaModel,
)
from src.db.base import SaBase, SerializerMixin


class MenuMealSaModel(SerializerMixin, SaBase):
    """SQLAlchemy ORM model for menu meals table.

    Represents scheduled meals within menus with week/weekday scheduling,
    meal type classification, and nutritional information. Uses composite
    pattern for nutritional facts with selective indexing.

    Notes:
        Schema: recipes_catalog. Table: menu_meals.
        Indexes: id (auto-increment primary key), menu_id, meal_name, meal_type.
        Composite indexes: (menu_id, week, weekday, meal_type) unique,
                          (menu_id, meal_type) for meal type queries.
        Foreign keys: references menus.id and meals.id.
        Composite fields: nutri_facts with selective indexing on key nutritional values.
    """

    __tablename__ = "menu_meals"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    menu_id: Mapped[str | None] = mapped_column(
        ForeignKey("recipes_catalog.menus.id"), index=True
    )
    meal_id: Mapped[str] = mapped_column(
        ForeignKey("recipes_catalog.meals.id"),
    )
    meal_name: Mapped[str] = mapped_column(index=True)
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
    week: Mapped[str]
    weekday: Mapped[str]
    hour: Mapped[time | None]
    meal_type: Mapped[str] = mapped_column(index=True)

    __table_args__ = (
        Index(
            "ix_menu_meals_menu_id_week_weekday_meal_type",
            "menu_id",
            "week",
            "weekday",
            "meal_type",
            unique=True,
        ),
        Index(
            "ix_menu_meals_menu_id_meal_type",
            "menu_id",
            "meal_type",
        ),
        {"schema": "recipes_catalog", "extend_existing": True},
    )
