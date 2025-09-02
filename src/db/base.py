"""SQLAlchemy base classes and serialization helpers.

This module provides a declarative base (`SaBase`) configured with a consistent
constraint naming convention and a type annotation map for common Python types.
It also exposes `SerializerMixin`, which adds convenience methods for mapping an
ORM instance to a dictionary and producing a JSON-style representation.
"""

import datetime
import json
from typing import Any, ClassVar

from sqlalchemy import MetaData, String
from sqlalchemy.dialects.postgresql import ARRAY, TIMESTAMP
from sqlalchemy.orm import DeclarativeBase


class SaBase(DeclarativeBase):
    """Declarative base with sensible defaults for this project.

    Configures a `type_annotation_map` for common Python types and applies a
    consistent naming convention to all constraints and indexes.

    Attributes:
        type_annotation_map: Maps Python types to SQLAlchemy column types.
        metadata: MetaData with consistent naming convention for constraints.
    """
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
    """Mixin that adds serialization helpers to SQLAlchemy models.

    Expects the mapped class to have a SQLAlchemy `mapper` attribute.

    Notes:
        Requires SQLAlchemy mapper to be available on the class.
    """
    def to_dict(self):
        """Return a dictionary of column attributes for the instance.

        The keys are column attribute names and the values are their current
        values on the instance.

        Returns:
            Dictionary mapping column names to their current values.

        Raises:
            ValueError: If a SQLAlchemy mapper is not found on the class.
        """
        mapper = getattr(self.__class__, "mapper", None)
        if mapper is None:
            err_msg = f"Mapper not found for {self.__class__}"
            raise ValueError(err_msg)
        return {c.key: getattr(self, c.key) for c in mapper.column_attrs}

    def __repr__(self):
        """Return a JSON-like string representation of the instance.

        Uses `to_dict()` and serializes values with `default=str` to handle
        non-JSON-serializable objects such as datetimes.

        Returns:
            JSON string representation of the instance.
        """
        return json.dumps(self.to_dict(), default=str)
