"""API value object for postal addresses with validation and conversions."""

from typing import Annotated, Any

from pydantic import AfterValidator, Field
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

    street: Annotated[
        SanitizedTextOptional,
        AfterValidator(
            lambda v: validate_optional_text_length(
                v,
                max_length=255,
                message="Street name must be less than 255 characters",
            )
        ),
        Field(
            default=None, description="Street name with proper trimming and validation"
        ),
    ]
    number: Annotated[
        SanitizedTextOptional,
        Field(default=None, description="Number of the address"),
        AfterValidator(
            lambda v: validate_optional_text_length(
                v, max_length=255, message="Number must be less than 255 characters"
            )
        ),
    ]
    zip_code: Annotated[
        SanitizedTextOptional,
        Field(default=None, description="Zip code of the address"),
        AfterValidator(
            lambda v: validate_optional_text_length(
                v, max_length=20, message="Zip code must be less than 20 characters"
            )
        ),
    ]
    district: Annotated[
        SanitizedTextOptional,
        Field(default=None, description="District of the address"),
        AfterValidator(
            lambda v: validate_optional_text_length(
                v, max_length=255, message="District must be less than 255 characters"
            )
        ),
    ]
    city: Annotated[
        SanitizedTextOptional,
        Field(default=None, description="City of the address"),
        AfterValidator(
            lambda v: validate_optional_text_length(
                v, max_length=255, message="City must be less than 255 characters"
            )
        ),
    ]
    state: Annotated[
        State | None,
        Field(default=None, description="State enum"),
    ]

    complement: Annotated[
        SanitizedTextOptional,
        Field(default=None, description="Complement of the address"),
        AfterValidator(
            lambda v: validate_optional_text_length(
                v, max_length=255, message="Complement must be less than 255 characters"
            )
        ),
    ]
    note: Annotated[
        SanitizedTextOptional,
        Field(default=None, description="Note of the address"),
        AfterValidator(
            lambda v: validate_optional_text_length(
                v, max_length=255, message="Note must be less than 255 characters"
            )
        ),
    ]

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
            "state": self.state,
            "complement": self.complement,
            "note": self.note,
        }
