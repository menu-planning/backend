"""API value object for contact information with validation and conversions."""

from pydantic import Field, field_validator
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import (
    EmailFieldOptional,
    PhoneFieldOptional,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_model import (
    BaseApiValueObject,
)
from src.contexts.seedwork.adapters.api_schemas.validators import (
    validate_email_format,
    validate_phone_format,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.contact_info_sa_model import (
    ContactInfoSaModel,
)
from src.contexts.shared_kernel.domain.value_objects.contact_info import ContactInfo
from src.db.base import SaBase


class ApiContactInfo(BaseApiValueObject[ContactInfo, SaBase]):
    """API schema for contact information operations.

    Attributes:
        main_phone: Primary phone number with validation.
        main_email: Primary email address with validation.
        all_phones: Immutable set of all phone numbers.
        all_emails: Immutable set of all email addresses.

    Notes:
        Boundary contract only; domain rules enforced in application layer.
        Collections use frozenset for immutability at the API boundary.
        Phone and email formats are validated automatically.
    """

    main_phone: PhoneFieldOptional = None
    main_email: EmailFieldOptional = None

    all_phones: frozenset[str] = Field(default_factory=frozenset)
    all_emails: frozenset[str] = Field(default_factory=frozenset)

    @field_validator("all_phones")
    @classmethod
    def validate_all_phones(cls, v: frozenset[str]) -> frozenset[str]:
        """Validate collection structure and individual phone formats.

        Args:
            v: Set of phone numbers.

        Returns:
            A normalized set containing valid phone numbers only.
        """
        if not v:
            return v

        validated_phones = frozenset()
        for phone in v:
            if phone:
                validated_phone = validate_phone_format(phone)
                if validated_phone:
                    validated_phones = validated_phones | {validated_phone}

        return validated_phones

    @field_validator("all_emails")
    @classmethod
    def validate_all_emails(cls, v: frozenset[str]) -> frozenset[str]:
        """Validate collection structure and individual email formats.

        Args:
            v: Set of email addresses.

        Returns:
            A normalized set containing valid email addresses only.
        """
        if not v:
            return v

        validated_emails = frozenset()
        for email in v:
            if email:
                validated_email = validate_email_format(email)
                if validated_email:
                    validated_emails = validated_emails | {validated_email}

        return validated_emails

    @classmethod
    def from_domain(cls, domain_obj: ContactInfo) -> "ApiContactInfo":
        """Create an instance from a domain model.

        Args:
            domain_obj: Source domain model.

        Returns:
            ApiContactInfo instance.
        """
        return cls(
            main_phone=domain_obj.main_phone,
            main_email=domain_obj.main_email,
            all_phones=frozenset(domain_obj.all_phones),
            all_emails=frozenset(domain_obj.all_emails),
        )

    def to_domain(self) -> ContactInfo:
        """Convert this value object into a domain model.

        Returns:
            ContactInfo domain model.
        """
        return ContactInfo(
            main_phone=self.main_phone,
            main_email=self.main_email,
            all_phones=frozenset(self.all_phones),
            all_emails=frozenset(self.all_emails),
        )

    @classmethod
    def from_orm_model(cls, orm_model: ContactInfoSaModel) -> "ApiContactInfo":
        """Create an instance from an ORM model.

        Args:
            orm_model: ORM instance with contact info fields.

        Returns:
            ApiContactInfo instance.
        """
        return cls(
            main_phone=orm_model.main_phone,
            main_email=orm_model.main_email,
            all_phones=(
                frozenset(orm_model.all_phones)
                if orm_model.all_phones is not None
                else frozenset()
            ),
            all_emails=(
                frozenset(orm_model.all_emails)
                if orm_model.all_emails is not None
                else frozenset()
            ),
        )

    def to_orm_kwargs(self) -> dict:
        """Return kwargs suitable for constructing/updating an ORM model.

        Returns:
            Mapping of ORM field names to values.
        """
        return {
            "main_phone": self.main_phone,
            "main_email": self.main_email,
            "all_phones": list(self.all_phones),
            "all_emails": list(self.all_emails),
        }
