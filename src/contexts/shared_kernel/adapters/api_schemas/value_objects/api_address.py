"""API value object for postal addresses with validation and conversions."""

from typing import Annotated, Any

from pydantic import AfterValidator, BeforeValidator, Field
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import (
    SanitizedTextOptional,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_model import (
    BaseApiValueObject,
)
from src.contexts.seedwork.adapters.api_schemas.validators import (
    validate_optional_text_length,
)
from src.contexts.shared_kernel.adapters.ORM.sa_models.address_sa_model import (
    AddressSaModel,
)
from src.contexts.shared_kernel.domain.enums import State
from src.contexts.shared_kernel.domain.value_objects.address import Address
from src.db.base import SaBase
from src.contexts.seedwork.adapters.api_schemas import validators

SanitizedTextOptional_255_MAX = Annotated[
    SanitizedTextOptional,
    AfterValidator(
        lambda v: validate_optional_text_length(v, max_length=255, message="Attribute name must be less than 255 characters")
    )
]

class ApiAddress(BaseApiValueObject[Address, SaBase]):
    """API schema for address operations.

    Attributes:
        street: Street name with proper trimming and validation, max 255 characters.
        number: Number of the address, max 255 characters.
        zip_code: Zip code of the address, max 20 characters.
        district: District of the address, max 255 characters.
        city: City of the address, max 255 characters.
        state: State enum value.
        complement: Complement of the address, max 255 characters.
        note: Note of the address, max 255 characters.

    Notes:
        Boundary contract only; domain rules enforced in application layer.
        All string fields are sanitized and trimmed automatically.
    """

    street: SanitizedTextOptional_255_MAX = None
    number: SanitizedTextOptional_255_MAX = None
    zip_code: SanitizedTextOptional_255_MAX = None
    district: SanitizedTextOptional_255_MAX = None
    city: SanitizedTextOptional_255_MAX = None
    state: State | None = None
    complement: SanitizedTextOptional_255_MAX = None
    note: SanitizedTextOptional_255_MAX = None

    @classmethod
    def from_domain(cls, domain_obj: Address) -> "ApiAddress":
        """Create an instance from a domain model.

        Args:
            domain_obj: Source domain model.

        Returns:
            ApiAddress instance.
        """
        return cls(
            street=domain_obj.street,
            number=domain_obj.number,
            zip_code=domain_obj.zip_code,
            district=domain_obj.district,
            city=domain_obj.city,
            state=domain_obj.state,
            complement=domain_obj.complement,
            note=domain_obj.note,
        )

    def to_domain(self) -> Address:
        """Convert this value object into a domain model.

        Returns:
            Address domain model.
        """
        return Address(
            street=self.street,
            number=self.number,
            zip_code=self.zip_code,
            district=self.district,
            city=self.city,
            state=State(self.state) if self.state else None,
            complement=self.complement,
            note=self.note,
        )

    @classmethod
    def from_orm_model(cls, orm_model: AddressSaModel) -> "ApiAddress":
        """Create an instance from an ORM model.

        Args:
            orm_model: ORM instance with address fields.

        Returns:
            ApiAddress instance.
        """
        return cls(
            street=orm_model.street,
            number=orm_model.number,
            zip_code=orm_model.zip_code,
            district=orm_model.district,
            city=orm_model.city,
            state=State(orm_model.state) if orm_model.state else None,
            complement=orm_model.complement,
            note=orm_model.note,
        )

    def to_orm_kwargs(self) -> dict[str, Any]:
        """Return kwargs suitable for constructing/updating an ORM model.

        Returns:
            Mapping of ORM field names to values.
        """
        return {
            "street": self.street,
            "number": self.number,
            "zip_code": self.zip_code,
            "district": self.district,
            "city": self.city,
            "state": self.state.value if self.state else None,
            "complement": self.complement,
            "note": self.note,
        }
