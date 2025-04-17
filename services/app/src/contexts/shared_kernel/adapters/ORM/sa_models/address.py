from dataclasses import dataclass


@dataclass
class AddressSaModel:
    street: str
    number: str
    zip_code: str
    district: str
    city: str
    state: str
    complement: str | None = None
    note: str | None = None