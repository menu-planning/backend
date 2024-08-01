from sqlalchemy.orm import Mapped
from src.db import sa_field_types
from src.db.base import SaBase


class SellerSaModel(SaBase):
    __tablename__ = "sellers"

    id: Mapped[sa_field_types.strpk]
    name: Mapped[str]
    state_registration: Mapped[str]
    street: Mapped[str]
    number: Mapped[str]
    zip_code: Mapped[str]
    district: Mapped[str]
    city: Mapped[str]
    state: Mapped[str]
    complement: Mapped[str | None]
    note: Mapped[str | None]

    __table_args__ = {"schema": "receipt_tracker", "extend_existing": True}
