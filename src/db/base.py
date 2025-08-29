import datetime
import json
from typing import Any, ClassVar

from sqlalchemy import MetaData, String
from sqlalchemy.dialects.postgresql import ARRAY, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase


class SaBase(DeclarativeBase):
    type_annotation_map: ClassVar[dict[type, Any]] = {
        list[str]: ARRAY(String),
        datetime: TIMESTAMP(timezone=True),
    }
    metadata = MetaData(
        naming_convention={
            "ix": "ix_%(column_0_label)s",
            "uq": "uq_%(table_name)s_%(column_0_name)s",
            "ck": "ck_%(table_name)s_`%(constraint_name)s`",
            "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
            "pk": "pk_%(table_name)s",
        }
    )


class SerializerMixin:
    def to_dict(self):
        mapper = getattr(self.__class__, "mapper", None)
        if mapper is None:
            err_msg = f"Mapper not found for {self.__class__}"
            raise ValueError(err_msg)
        return {c.key: getattr(self, c.key) for c in mapper.column_attrs}

    def __repr__(self):
        return json.dumps(self.to_dict(), default=str)
