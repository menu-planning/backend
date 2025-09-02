from dataclasses import dataclass


@dataclass
class AddressSaModel:
    """SQLAlchemy composite dataclass for address fields.

    Attributes:
        street: Street name.
        number: Address number.
        zip_code: Postal code.
        district: District name.
        city: City name.
        state: State identifier.
        complement: Address complement.
        note: Additional notes.

    Notes:
        Lightweight dataclass mirror of address fields used in ORM composites.
        All fields are optional to support partial address data.
    """
    street: str | None = None
    number: str | None = None
    zip_code: str | None = None
    district: str | None = None
    city: str | None = None
    state: str | None = None
    complement: str | None = None
    note: str | None = None
