from dataclasses import fields
from datetime import time

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, composite, mapped_column

from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts import (
    NutriFactsSaModel,
)
from src.db.base import SaBase


class MenuMealSaModel(SaBase):
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
