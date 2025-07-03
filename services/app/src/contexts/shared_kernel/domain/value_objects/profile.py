from datetime import date
from attrs import frozen

from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject


@frozen(kw_only=True)
class Profile(ValueObject):
    """Represents client profile information."""
    name: str
    sex: str
    birthday: date
    