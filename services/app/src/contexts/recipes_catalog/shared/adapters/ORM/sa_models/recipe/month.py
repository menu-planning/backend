from sqlalchemy.orm import Mapped, mapped_column
from src.db.base import SaBase


class MonthSaModel(SaBase):
    __tablename__ = "months"

    id: Mapped[int] = mapped_column(primary_key=True)

    __table_args__ = {"schema": "recipes_catalog", "extend_existing": True}
