from dataclasses import fields
from typing import Any

import src.db.sa_field_types as sa_field
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, composite, mapped_column, relationship
from src.contexts.recipes_catalog.core.adapters.client.ORM.sa_models.client_associations import (
    clients_tags_association,
)
from src.contexts.recipes_catalog.core.adapters.client.ORM.sa_models.menu_sa_model import (
    MenuSaModel,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.address_sa_model import (
    AddressSaModel,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.contact_info_sa_model import (
    ContactInfoSaModel,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.profile_sa_model import (
    ProfileSaModel,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag_sa_model import (
    TagSaModel,
)
from src.db.base import SaBase, SerializerMixin


class ClientSaModel(SerializerMixin, SaBase):
    """SQLAlchemy ORM model for clients table.

    Represents client entities with composite fields for profile, contact info,
    and address. Includes tag associations and menu relationships.

    Notes:
        Schema: recipes_catalog. Table: clients.
        Indexes: id, author_id, profile.name, created_at.
        Composite fields: profile, contact_info, address using dataclass fields.
        Relationships: tags (many-to-many via association), menus (one-to-many).
        JSONB field: onboarding_data for flexible client onboarding information.
    """

    __tablename__ = "clients"

    id: Mapped[sa_field.strpk]
    author_id: Mapped[str]
    profile: Mapped[ProfileSaModel] = composite(
        *[
            mapped_column(
                field.name,
                index=(field.name == "name"),
            )
            for field in fields(ProfileSaModel)
        ],
    )
    contact_info: Mapped[ContactInfoSaModel] = composite(
        *[
            mapped_column(
                field.name,
            )
            for field in fields(ContactInfoSaModel)
        ],
    )
    address: Mapped[AddressSaModel] = composite(
        *[
            mapped_column(
                field.name,
            )
            for field in fields(AddressSaModel)
        ],
    )
    tags: Mapped[list[TagSaModel]] = relationship(
        secondary=clients_tags_association,
        lazy="selectin",
        cascade="save-update, merge",
    )
    notes: Mapped[str | None]
    onboarding_data: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    menus: Mapped[list[MenuSaModel]] = relationship(
        "MenuSaModel",
        lazy="selectin",
        cascade="save-update, merge",
    )
    created_at: Mapped[sa_field.datetime_tz_created]
    updated_at: Mapped[sa_field.datetime_tz_updated]

    discarded: Mapped[bool] = mapped_column(default=False)
    version: Mapped[int] = mapped_column(default=1)

    __table_args__ = ({"schema": "recipes_catalog", "extend_existing": True},)
