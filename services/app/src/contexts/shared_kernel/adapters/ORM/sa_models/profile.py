from dataclasses import dataclass
from datetime import date


@dataclass
class ProfileSaModel:
    name: str
    birthday: date | None
    sex: str