from sqlalchemy import Index
from sqlalchemy.orm import Mapped, mapped_column

from src.db.base import SaBase


class TagSaModel(SaBase):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    key: Mapped[str]
    value: Mapped[str]
    author_id: Mapped[str]
    type: Mapped[str]

    __table_args__ = (
        Index(
            "ix_tags_key_value_author_id_type",
            "key",
            "value",
            "author_id",
            "type",
            unique=True,
        ),
        Index(
            "ix_tags_author_id_type",
            "author_id",
            "type",
        ),
        {
            "schema": "shared_kernel",
            "extend_existing": True,
        },
    )
