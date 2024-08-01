from attrs import frozen
from src.contexts.menu_planning.shared.domain.value_objects.address import Address
from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject


@frozen
class ContactInfo(ValueObject):
    email: str
    phone: str
    address: Address
