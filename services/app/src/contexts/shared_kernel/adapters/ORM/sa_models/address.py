from dataclasses import dataclass


@dataclass
class AddressSaModel:
    street: str | None = None
    number: str | None = None
    zip_code: str | None = None
    district: str | None = None
    city: str | None = None
    state: str | None = None
    complement: str | None = None
    note: str | None = None