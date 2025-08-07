from datetime import datetime
from dataclasses import fields
from typing import Any, Dict
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, relationship, composite
from sqlalchemy.dialects.postgresql import JSONB

from src.contexts.recipes_catalog.core.adapters.client.ORM.sa_models.menu_sa_model import MenuSaModel
from src.contexts.shared_kernel.adapters.ORM.sa_models.address_sa_model import AddressSaModel
from src.contexts.shared_kernel.adapters.ORM.sa_models.contact_info_sa_model import ContactInfoSaModel
from src.contexts.shared_kernel.adapters.ORM.sa_models.profile_sa_model import ProfileSaModel
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag_sa_model import TagSaModel
from src.contexts.recipes_catalog.core.adapters.client.ORM.sa_models.client_associations import clients_tags_association
import src.db.sa_field_types as sa_field
from src.db.base import SaBase, SerializerMixin

class ClientSaModel(SerializerMixin,SaBase):
    __tablename__ = "clients"

    id: Mapped[sa_field.strpk]
    author_id: Mapped[str]
    profile: Mapped[ProfileSaModel] = composite(
        *[
            mapped_column(
                field.name,
                index=(
                    True
                    if (
                        field.name == "name"
                    )
                    else False
                ),
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
    onboarding_data: Mapped[Dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    menus: Mapped[list[MenuSaModel]] = relationship(
        "MenuSaModel",
        lazy="selectin",
        cascade="save-update, merge",
    )
    created_at: Mapped[datetime] = mapped_column(server_default=func.now(), index=True)
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )

    discarded: Mapped[bool] = mapped_column(default=False)
    version: Mapped[int] = mapped_column(default=1)

    __table_args__ = ({"schema": "recipes_catalog", "extend_existing": True},)