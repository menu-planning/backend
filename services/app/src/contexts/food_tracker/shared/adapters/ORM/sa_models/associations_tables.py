import src.db.sa_field_types as sa_field
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.contexts.food_tracker.shared.adapters.ORM.sa_models.receipts import (
    ReceiptSaModel,
)
from src.db.base import SaBase


class HousesReceiptsAssociation(SaBase):
    __tablename__ = "houses_receipts_association"

    house_id: Mapped[str] = mapped_column(
        ForeignKey("food_tracker.houses.id"), primary_key=True
    )
    receipt_id: Mapped[str] = mapped_column(
        ForeignKey("food_tracker.receipts.id"), primary_key=True
    )
    state: Mapped[str]
    receipt: Mapped[ReceiptSaModel] = relationship(
        lazy="selectin",
        cascade="save-update, merge",
    )

    __table_args__ = {"schema": "food_tracker", "extend_existing": True}


class HousesMembersAssociation(SaBase):
    __tablename__ = "houses_members_association"

    house_id: Mapped[str] = mapped_column(
        ForeignKey("food_tracker.houses.id"), primary_key=True
    )
    # TODO: add foreignkey
    user_id: Mapped[sa_field.strpk]

    __table_args__ = {"schema": "food_tracker", "extend_existing": True}


class HousesNutritionistsAssociation(SaBase):
    __tablename__ = "houses_nutritionists_association"

    house_id: Mapped[str] = mapped_column(
        ForeignKey("food_tracker.houses.id"), primary_key=True
    )
    # TODO: add foreignkey
    user_id: Mapped[sa_field.strpk]

    __table_args__ = {"schema": "food_tracker", "extend_existing": True}
