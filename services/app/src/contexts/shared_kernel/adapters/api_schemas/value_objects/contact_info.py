from src.contexts.seedwork.shared.adapters.api_schemas.base import BaseValueObject
from src.contexts.shared_kernel.domain.value_objects.contact_info import ContactInfo
from src.contexts.shared_kernel.adapters.ORM.sa_models.contact_info_sa_model import ContactInfoSaModel
from src.db.base import SaBase
from pydantic import Field


class ApiContactInfo(BaseValueObject[ContactInfo, SaBase]):
    """A class to represent and validate a contact info."""

    main_phone: str | None = None
    main_email: str | None = None
    all_phones: set[str] = Field(default_factory=set)
    all_emails: set[str] = Field(default_factory=set)

    @classmethod
    def from_domain(cls, domain_obj: ContactInfo) -> "ApiContactInfo":
        """Creates an instance of `ApiContactInfo` from a domain model object."""
        return cls(
            main_phone=domain_obj.main_phone,
            main_email=domain_obj.main_email,
            all_phones=domain_obj.all_phones,
            all_emails=domain_obj.all_emails,
        )

    def to_domain(self) -> ContactInfo:
        """Converts the instance to a domain model object."""
        return ContactInfo(
            main_phone=self.main_phone,
            main_email=self.main_email,
            all_phones=self.all_phones,
            all_emails=self.all_emails,
        )

    @classmethod
    def from_orm_model(cls, orm_model: ContactInfoSaModel) -> "ApiContactInfo":
        """Convert from ORM model."""
        data = {
            "main_phone": orm_model.main_phone,
            "main_email": orm_model.main_email,
            "all_phones": set(orm_model.all_phones) if orm_model.all_phones is not None else set(),
            "all_emails": set(orm_model.all_emails) if orm_model.all_emails is not None else set(),
        }
        return cls.model_validate(data)

    def to_orm_kwargs(self) -> dict:
        """Convert to ORM model kwargs."""
        data = self.model_dump()
        data["all_phones"] = list(data["all_phones"])
        data["all_emails"] = list(data["all_emails"])
        return data
