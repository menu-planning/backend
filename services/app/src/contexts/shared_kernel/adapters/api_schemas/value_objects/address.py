from src.contexts.seedwork.shared.adapters.api_schemas.base import BaseValueObject
from src.contexts.shared_kernel.domain.enums import State
from src.contexts.shared_kernel.domain.value_objects.address import Address
from src.contexts.shared_kernel.adapters.ORM.sa_models.address_sa_model import AddressSaModel
from src.db.base import SaBase


class ApiAddress(BaseValueObject[Address, SaBase]):
    """A class to represent and validate an address."""

    street: str | None = None
    number: str | None = None
    zip_code: str | None = None
    district: str | None = None
    city: str | None = None
    state: State | None = None
    complement: str | None = None
    note: str | None = None

    @classmethod
    def from_domain(cls, domain_address: Address) -> "ApiAddress":
        """Convert from domain object."""
        return cls(
            street=domain_address.street,
            number=domain_address.number,
            zip_code=domain_address.zip_code,
            district=domain_address.district,
            city=domain_address.city,
            state=domain_address.state,
            complement=domain_address.complement,
            note=domain_address.note
        )

    def to_domain(self) -> Address:
        """Convert to domain object."""
        return Address(
            street=self.street,
            number=self.number,
            zip_code=self.zip_code,
            district=self.district,
            city=self.city,
            state=State(self.state) if self.state else None,
            complement=self.complement,
            note=self.note
        )

    @classmethod
    def from_orm_model(cls, orm_model: AddressSaModel) -> "ApiAddress":
        """Convert from ORM model."""
        return cls(
            street=orm_model.street,
            number=orm_model.number,
            zip_code=orm_model.zip_code,
            district=orm_model.district,
            city=orm_model.city,
            state=State(orm_model.state) if orm_model.state else None,
            complement=orm_model.complement,
            note=orm_model.note
        )

    def to_orm_kwargs(self) -> dict:
        """Convert to ORM model kwargs."""
        return self.model_dump()
