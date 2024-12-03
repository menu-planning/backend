from datetime import datetime

import src.db.sa_field_types as sa_field
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.contexts.food_tracker.shared.adapters.ORM.sa_models.associations_tables import (
    HousesMembersAssociation,
    HousesNutritionistsAssociation,
    HousesReceiptsAssociation,
)
from src.db.base import SaBase


class HouseSaModel(SaBase):
    __tablename__ = "houses"

    id: Mapped[sa_field.strpk]
    name: Mapped[str]
    owner_id: Mapped[str] = mapped_column(index=True)
    members: Mapped[list[HousesMembersAssociation]] = relationship(
        lazy="selectin",
        cascade="save-update, merge",
    )
    nutritionists: Mapped[list[HousesNutritionistsAssociation]] = relationship(
        lazy="selectin",
        cascade="save-update, merge",
    )
    receipts: Mapped[list[HousesReceiptsAssociation]] = relationship(
        lazy="selectin",
        cascade="save-update, merge",
    )
    discarded: Mapped[bool] = mapped_column(default=False)
    version: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = {"schema": "food_tracker", "extend_existing": True}
