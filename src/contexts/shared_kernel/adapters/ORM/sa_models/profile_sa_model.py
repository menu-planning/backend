from dataclasses import dataclass
from datetime import date


@dataclass
class ProfileSaModel:
    """SQLAlchemy composite dataclass for profile fields.

    Attributes:
        name: Person's name.
        birthday: Date of birth.
        sex: Sex identifier.

    Notes:
        Dataclass mirror used for ORM composite profile fields.
        Name and sex are required fields.
    """
    name: str
    birthday: date | None
    sex: str
