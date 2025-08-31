from pydantic import Field, field_validator
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import (
    EmailFieldOptional,
    PhoneFieldOptional,
)
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import (
    BaseApiValueObject,
)
from src.contexts.seedwork.shared.adapters.api_schemas.validators import (
    validate_email_format,
    validate_phone_format,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.contact_info_sa_model import (
    ContactInfoSaModel,
)
from src.contexts.shared_kernel.domain.value_objects.contact_info import ContactInfo
from src.db.base import SaBase


class ApiContactInfo(BaseApiValueObject[ContactInfo, SaBase]):
    """
    API schema for contact information with comprehensive validation.

    Implements four-layer conversion pattern:
    - to_domain(): API → Domain (business logic validation)
    - from_domain(): Domain → API (collection type conversion)
    - from_orm_model(): ORM → API (handle ORM list to API frozenset conversion)
    - to_orm_kwargs(): API → ORM (prepare data for persistence)

    Field validation follows documented patterns:
    - Email fields use BeforeValidator for format validation
    - Phone fields use BeforeValidator for international format support
    - Collections use frozenset for immutability in API layer
    """

    # Contact fields with comprehensive validation
    main_phone: PhoneFieldOptional = None
    main_email: EmailFieldOptional = None

    # Collections using frozenset for API consistency (immutable)
    all_phones: frozenset[str] = Field(default_factory=frozenset)
    all_emails: frozenset[str] = Field(default_factory=frozenset)

    @field_validator("all_phones")
    @classmethod
    def validate_all_phones(cls, v: frozenset[str]) -> frozenset[str]:
        """Validate all_phones collection structure and individual phone formats."""
        if not v:
            return v

        # Validate each phone number in the collection
        validated_phones = frozenset()
        for phone in v:
            if phone:  # Skip empty strings
                validated_phone = validate_phone_format(phone)
                if validated_phone:
                    validated_phones = validated_phones | {validated_phone}

        return validated_phones

    @field_validator("all_emails")
    @classmethod
    def validate_all_emails(cls, v: frozenset[str]) -> frozenset[str]:
        """Validate all_emails collection structure and individual email formats."""
        if not v:
            return v

        # Validate each email in the collection
        validated_emails = frozenset()
        for email in v:
            if email:  # Skip empty strings
                validated_email = validate_email_format(email)
                if validated_email:
                    validated_emails = validated_emails | {validated_email}

        return validated_emails

    @classmethod
    def from_domain(cls, domain_obj: ContactInfo) -> "ApiContactInfo":
        """
        Convert domain ContactInfo to API schema.

        Handles collection type conversion: frozenset[str] → frozenset[str]
        """
        return cls(
            main_phone=domain_obj.main_phone,
            main_email=domain_obj.main_email,
            # Convert domain sets to API frozensets
            all_phones=frozenset(domain_obj.all_phones),
            all_emails=frozenset(domain_obj.all_emails),
        )

    def to_domain(self) -> ContactInfo:
        """
        Convert API schema to domain ContactInfo.

        Handles collection type conversion: frozenset[str] → frozenset[str]
        """
        return ContactInfo(
            main_phone=self.main_phone,
            main_email=self.main_email,
            # Convert API frozensets to domain sets
            all_phones=frozenset(self.all_phones),
            all_emails=frozenset(self.all_emails),
        )

    @classmethod
    def from_orm_model(cls, orm_model: ContactInfoSaModel) -> "ApiContactInfo":
        """
        Convert ORM model to API schema.

        Handles collection type conversion: list[str] | None → frozenset[str]
        """
        return cls(
            main_phone=orm_model.main_phone,
            main_email=orm_model.main_email,
            # Convert ORM lists to API frozensets, handle None values
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
        """
        Convert API schema to ORM model kwargs.

        Handles collection type conversion: frozenset[str] → list[str]
        """
        return {
            "main_phone": self.main_phone,
            "main_email": self.main_email,
            # Convert API frozensets to ORM lists
            "all_phones": list(self.all_phones),
            "all_emails": list(self.all_emails),
        }
