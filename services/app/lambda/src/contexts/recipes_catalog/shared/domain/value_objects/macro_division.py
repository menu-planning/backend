from attrs import frozen
from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject


@frozen(kw_only=True, hash=True)
class MacroDivision(ValueObject):
    carbohydrate: str
    protein: str
    fat: str
