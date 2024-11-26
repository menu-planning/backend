import src.db.sa_field_types as sa_field
from sqlalchemy.orm import Mapped
from src.db.base import SaBase


class MealTypeSaModel(SaBase):
    __tablename__ = "meal_types"

    id: Mapped[sa_field.strpk]

    __table_args__ = {
        "schema": "shared_kernel",
        "extend_existing": True,
    }
