from datetime import datetime
from dataclasses import fields
from sqlalchemy import func
from sqlalchemy.orm import Mapped, mapped_column, relationship, composite

from src.contexts.recipes_catalog.core.adapters.ORM.sa_models.menu.menu import MenuSaModel
from src.contexts.shared_kernel.adapters.ORM.sa_models.address import AddressSaModel
from src.contexts.shared_kernel.adapters.ORM.sa_models.contact_info import ContactInfoSaModel
from src.contexts.shared_kernel.adapters.ORM.sa_models.profile import ProfileSaModel
from src.contexts.shared_kernel.adapters.ORM.sa_models.tag.tag import TagSaModel
import src.db.sa_field_types as sa_field
from src.db.base import SaBase, SerializerMixin
from src.contexts.recipes_catalog.core.adapters.ORM.sa_models.client.associations import (
    clients_tags_association,
)

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