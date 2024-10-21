from sqlalchemy.orm import Mapped
from src.db import sa_field_types
from src.db.base import SaBase


class HousesSaModel(SaBase):
    __tablename__ = "houses"

    id: Mapped[sa_field_types.strpk]

    __table_args__ = {"schema": "receipt_tracker", "extend_existing": True}
