from datetime import time

from sqlalchemy import ForeignKey, Index
from sqlalchemy.orm import Mapped, mapped_column
from src.db.base import SaBase


class MenuItemSaModel(SaBase):
    __tablename__ = "menu_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    menu_id: Mapped[str | None] = mapped_column(
        ForeignKey("recipes_catalog.menus.id"),
    )
    meal_id: Mapped[str | None] = mapped_column(
        ForeignKey("recipes_catalog.meals.id"),
    )
    week: Mapped[str]
    weekday: Mapped[str]
    hour: Mapped[time]
    meal_type: Mapped[str] = mapped_column(index=True)

    __table_args__ = (
        Index(
            "menu_items_menu_id_week_weekday_meal_type_idx",
            "menu_id",
            "week",
            "weekday",
            "meal_type",
            unique=True,
        ),
        Index(
            "menu_items_menu_id_meal_type_idx",
            "menu_id",
            "meal_type",
        ),
        {"schema": "recipes_catalog", "extend_existing": True},
    )
