import src.db.sa_field_types as sa_field
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from src.contexts.recipes_catalog.core.adapters.client.ORM.sa_models.client_associations import (
    menus_tags_association,
)
from src.contexts.recipes_catalog.core.adapters.client.ORM.sa_models.menu_meal_sa_model import (
    MenuMealSaModel,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag_sa_model import (
    TagSaModel,
)
from src.db.base import SaBase, SerializerMixin


class MenuSaModel(SerializerMixin, SaBase):
    """SQLAlchemy ORM model for menus table.

    Represents menu entities that organize meals for clients with
    scheduling information and tag-based categorization.

    Notes:
        Schema: recipes_catalog. Table: menus.
        Indexes: id, author_id, client_id, created_at.
        Foreign key: references recipes_catalog.clients.id.
        Relationships: meals (one-to-many), tags (many-to-many via association).
        Meals include week/weekday scheduling and meal type information.
    """

    __tablename__ = "menus"

    id: Mapped[sa_field.strpk]
    author_id: Mapped[str]
    client_id: Mapped[str] = mapped_column(
        ForeignKey("recipes_catalog.clients.id"),
    )
    meals: Mapped[list[MenuMealSaModel]] = relationship(
        "MenuMealSaModel",
        lazy="selectin",
        cascade="save-update, merge",
    )
    tags: Mapped[list[TagSaModel]] = relationship(
        secondary=menus_tags_association,
        lazy="selectin",
        cascade="save-update, merge",
    )
    description: Mapped[str | None]
    created_at: Mapped[sa_field.datetime_tz_created]
    updated_at: Mapped[sa_field.datetime_tz_updated]

    discarded: Mapped[bool] = mapped_column(default=False)
    version: Mapped[int] = mapped_column(nullable=False)

    __table_args__ = ({"schema": "recipes_catalog", "extend_existing": True},)
    __mapper_args__ = {"version_id_col": version}