from attrs import asdict
from pydantic import BaseModel, field_serializer
from src.contexts.shared_kernel.domain.enums import State
from src.contexts.shared_kernel.domain.value_objects.address import Address


class ApiAddress(BaseModel):
    """A class to represent and validate an address."""

    street: str | None = None
    number: str | None = None
    zip_code: str | None = None
    district: str | None = None
    city: str | None = None
    state: State | None = None
    complement: str | None = None
    note: str | None = None

    @field_serializer("state")
    def serialize_state(self, state: State, _info):
        """Serializes the state to a domain model."""
        return state.value

    @classmethod
    def from_domain(cls, domain_obj: Address) -> "ApiAddress":
        """Creates an instance of `ApiAddress` from a domain model object."""
        try:
            return cls(**asdict(domain_obj))
        except Exception as e:
            raise ValueError(f"Failed to build ApiAddress from domain instance: {e}")

    def to_domain(self) -> Address:
        """Converts the instance to a domain model object."""
        try:
            return Address(
                street=self.street,
                number=self.number,
                zip_code=self.zip_code,
                district=self.district,
                city=self.city,
                state=self.state.value,
                complement=self.complement,
                note=self.note,
            )
        except Exception as e:
            raise ValueError(f"Failed to convert ApiAddress to domain model: {e}")
