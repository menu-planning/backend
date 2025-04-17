import cattrs
from attrs import asdict
from pydantic import BaseModel
from datetime import date
from src.contexts.shared_kernel.domain.value_objects.profile import Profile


class ApiProfile(BaseModel):
    """A class to represent and validate a profile."""

    name: str | None = None
    birthday: date | None = None
    sex: str | None = None

    @classmethod
    def from_domain(cls, domain_obj: Profile) -> "ApiProfile":
        """Creates an instance of `ApiProfile` from a domain model object."""
        try:
            return cls(**asdict(domain_obj))
        except Exception as e:
            raise ValueError(f"Failed to build ApiProfile from domain instance: {e}")

    def to_domain(self) -> Profile:
        """Converts the instance to a domain model object."""
        try:
            return cattrs.structure(self.model_dump(), Profile)
        except Exception as e:
            raise ValueError(f"Failed to convert ApiProfile to domain model: {e}")
