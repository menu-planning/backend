from datetime import date

from attrs import frozen
from src.contexts.seedwork.domain.value_objects.value_object import ValueObject


@frozen(kw_only=True)
class Profile(ValueObject):
    """Value object representing client profile information.

    Attributes:
        name: Full name of the person.
        sex: Gender identification.
        birthday: Date of birth.

    Notes:
        Immutable. Equality by value (all fields).
    """

    name: str
    sex: str
    birthday: date
