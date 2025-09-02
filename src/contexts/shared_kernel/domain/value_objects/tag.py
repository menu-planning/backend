from __future__ import annotations

from attrs import frozen
from src.contexts.seedwork.domain.value_objects.value_object import ValueObject


@frozen(kw_only=True, hash=True)
class Tag(ValueObject):
    """Value object representing an entity annotation tag.

    Attributes:
        key: Tag category or namespace.
        value: Tag value or label.
        author_id: Identifier of the tag creator.
        type: Tag classification type.

    Notes:
        Immutable. Equality by value (all fields).
    """
    key: str
    value: str
    author_id: str
    type: str
