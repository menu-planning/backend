from datetime import datetime

import src.db.sa_field_types as sa_field
from sqlalchemy import Index, func
from sqlalchemy.orm import Mapped, mapped_column
from src.db.base import SaBase


class TagSaModel(SaBase):
    __tablename__ = "tags"

    id: Mapped[sa_field.strpk]
    name: Mapped[str] = mapped_column(index=True)
    author_id: Mapped[str] = mapped_column(index=True)
    description: Mapped[str | None]
    privacy: Mapped[str | None] = mapped_column(default="private", index=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
    discarded: Mapped[bool] = mapped_column(default=False)
    version: Mapped[int] = mapped_column(default=1)
    type: Mapped[str]

    __mapper_args__ = {
        "polymorphic_on": "type",
        "polymorphic_identity": "tags",
    }

    __table_args__ = (
        Index(
            "ix_name_author_id_type_active",
            "name",
            "author_id",
            "type",
            unique=True,
            postgresql_where=(discarded == False),
        ),
        {
            "schema": "recipes_catalog",
            "extend_existing": True,
        },
    )
