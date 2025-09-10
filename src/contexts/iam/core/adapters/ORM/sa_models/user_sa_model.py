"""SQLAlchemy model for IAM users with role relationship."""

import src.db.sa_field_types as sa_field
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.contexts.iam.core.adapters.ORM.sa_models.role_sa_model import RoleSaModel
from src.contexts.iam.core.adapters.ORM.sa_models.user_association_tables import (
    user_role_association,
)
from src.db.base import SaBase, SerializerMixin


class UserSaModel(SerializerMixin, SaBase):
    """SQLAlchemy model for IAM users.

    Attributes:
        id: User ID (primary key).
        discarded: Whether the user is discarded/deleted.
        version: Version number for optimistic locking.
        created_at: Timestamp when the user was created.
        updated_at: Timestamp when the user was last updated.
        roles: List of roles assigned to the user.

    Notes:
        Schema: iam. Eager-loads: roles via selectin.
    """

    __tablename__ = "users"

    id: Mapped[str] = mapped_column(primary_key=True)
    discarded: Mapped[bool]
    version: Mapped[int]
    created_at: Mapped[sa_field.datetime_tz_created]
    updated_at: Mapped[sa_field.datetime_tz_updated]
    roles: Mapped[list[RoleSaModel]] = relationship(
        secondary=user_role_association,
        lazy="selectin",
        cascade="save-update, merge",
    )

    __table_args__ = ({"schema": "iam", "extend_existing": True},)
