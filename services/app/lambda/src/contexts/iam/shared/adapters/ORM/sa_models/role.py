from sqlalchemy.orm import Mapped, mapped_column
from src.db.base import SaBase


class RoleSaModel(SaBase):
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(primary_key=True)
    context: Mapped[str] = mapped_column(primary_key=True)
    permissions: Mapped[str]

    __table_args__ = {"schema": "iam", "extend_existing": True}
