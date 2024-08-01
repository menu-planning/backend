import cattrs
from attrs import asdict
from pydantic import BaseModel, field_serializer
from src.contexts.shared_kernel.domain.enums import State
from src.contexts.shared_kernel.domain.value_objects.address import Address


class ApiAddress(BaseModel):
    """A class to represent and validate an address."""

    street: str
    number: str
    zip_code: str
    district: str
    city: str
    state: State
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
            return cattrs.structure(self.model_dump(), Address)
        except Exception as e:
            raise ValueError(f"Failed to convert ApiAddress to domain model: {e}")
