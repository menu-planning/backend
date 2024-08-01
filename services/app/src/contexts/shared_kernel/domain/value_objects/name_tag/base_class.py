from attrs import frozen
from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject


@frozen
class NameTag(ValueObject):
    name: str
