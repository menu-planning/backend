from attrs import frozen
from src.contexts.menu_planning.shared.domain.enums import State
from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject


@frozen
class Address(ValueObject):
    street: str
    number: str
    complement: str
    neighborhood: str
    city: str
    state: State
    zip_code: str
