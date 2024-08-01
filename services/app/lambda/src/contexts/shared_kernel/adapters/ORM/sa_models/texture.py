import src.db.sa_field_types as sa_field
from sqlalchemy.orm import Mapped
from src.db.base import SaBase


class TextureSaModel(SaBase):
    __tablename__ = "textures"

    id: Mapped[sa_field.strpk]

    __table_args__ = {
        "schema": "shared_kernel",
        "extend_existing": True,
    }
