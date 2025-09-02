from sqlalchemy import Index
from sqlalchemy.orm import Mapped, mapped_column
from src.db.base import SaBase, SerializerMixin


class TagSaModel(SerializerMixin, SaBase):
    """SQLAlchemy model for tags with uniqueness constraints and indexes.

    Attributes:
        id: Primary key, auto-incrementing integer.
        key: Tag key identifier.
        value: Tag value content.
        author_id: UUID of user who created this tag.
        type: Tag type identifier.

    Notes:
        Adheres to Tag interface. Includes composite unique index on key, value, author_id, type.
        Performance: Indexed on author_id and type for efficient filtering.
        Transactions: methods require active UnitOfWork session.
    """
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
