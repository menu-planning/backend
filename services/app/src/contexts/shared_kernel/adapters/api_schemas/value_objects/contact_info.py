import cattrs
from attrs import asdict
from pydantic import BaseModel, Field

from src.contexts.shared_kernel.domain.value_objects.contact_info import ContactInfo


class ApiContactInfo(BaseModel):
    """A class to represent and validate a contact info."""

    main_phone: str | None = None
    main_email: str | None = None
    all_phones: set[str] = Field(default_factory=set)
    all_emails: set[str] = Field(default_factory=set)

    @classmethod
    def from_domain(cls, domain_obj: ContactInfo) -> "ApiContactInfo":
        """Creates an instance of `ApiContactInfo` from a domain model object."""
        try:
            return cls(**asdict(domain_obj))
        except Exception as e:
            raise ValueError(f"Failed to build ApiContactInfo from domain instance: {e}")

    def to_domain(self) -> ContactInfo:
        """Converts the instance to a domain model object."""
        try:
            return ContactInfo(
                main_phone=self.main_phone,
                main_email=self.main_email,
                all_phones=self.all_phones,
                all_emails=self.all_emails,
            )
        except Exception as e:
            raise ValueError(f"Failed to convert ApiContactInfo to domain model: {e}")
