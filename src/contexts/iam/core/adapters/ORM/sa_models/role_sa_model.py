"""SQLAlchemy model for IAM roles (name+context composite PK)."""

from sqlalchemy.orm import Mapped, mapped_column
from src.db.base import SaBase, SerializerMixin


class RoleSaModel(SerializerMixin, SaBase):
    """SQLAlchemy model for IAM roles.
    
    Attributes:
        name: Role name (part of composite primary key).
        context: Role context (part of composite primary key).
        permissions: Comma-separated string of permissions.
    
    Notes:
        Composite primary key: (name, context). Schema: iam.
    """
    __tablename__ = "roles"

    name: Mapped[str] = mapped_column(primary_key=True)
    context: Mapped[str] = mapped_column(primary_key=True)
    permissions: Mapped[str]

    __table_args__ = ({"schema": "iam", "extend_existing": True},)
