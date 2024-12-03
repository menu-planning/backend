from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.contexts.iam.shared.adapters.ORM.sa_models.association_tables import (
    user_role_association,
)
from src.contexts.iam.shared.adapters.ORM.sa_models.role import RoleSaModel
from src.db.base import SaBase


class UserSaModel(SaBase):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(primary_key=True)
    discarded: Mapped[bool]
    version: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
    roles: Mapped[list[RoleSaModel]] = relationship(
        secondary=user_role_association,
        lazy="selectin",
        cascade="save-update, merge",
    )

    __table_args__ = {"schema": "iam", "extend_existing": True}
