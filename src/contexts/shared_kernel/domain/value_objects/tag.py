from __future__ import annotations

from attrs import frozen

from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject


@frozen(kw_only=True, hash=True)
class Tag(ValueObject):
    key: str
    value: str
    author_id: str
    type: str
