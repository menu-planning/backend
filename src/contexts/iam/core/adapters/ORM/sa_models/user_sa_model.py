from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.contexts.iam.core.adapters.ORM.sa_models.role_sa_model import RoleSaModel
from src.contexts.iam.core.adapters.ORM.sa_models.user_association_tables import (
    user_role_association,
)
from src.db.base import SaBase, SerializerMixin


class UserSaModel(SerializerMixin, SaBase):
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
