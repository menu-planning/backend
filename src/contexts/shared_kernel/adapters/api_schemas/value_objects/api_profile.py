"""API schema value object for profile with conversions to domain/ORM."""

from datetime import date
from typing import Annotated, Any

from pydantic import AfterValidator, Field
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import (
    SanitizedText,
)
from src.contexts.seedwork.adapters.api_schemas.base_api_model import (
    BaseApiValueObject,
)
from src.contexts.seedwork.adapters.api_schemas.validators import (
    validate_birthday_reasonable,
    validate_sex_options,
)
from src.contexts.seedwork.adapters.exceptions.api_schema_errors import (
    ValidationConversionError,
)
from src.contexts.shared_kernel.domain.value_objects.profile import Profile
from src.db.base import SaBase


class ApiProfile(BaseApiValueObject[Profile, SaBase]):
    """API schema for profile operations.

    Attributes:
        name: Person's name, length 1-255 characters.
        birthday: Date of birth with reasonable validation.
        sex: Sex identifier with validation.

    Notes:
        Boundary contract only; domain rules enforced in application layer.
        Name field is sanitized and trimmed automatically.
        Birthday validation ensures reasonable date ranges.
    """

    name: Annotated[SanitizedText, Field(..., min_length=1, max_length=255)]
    birthday: Annotated[date, AfterValidator(validate_birthday_reasonable)]
    sex: Annotated[str, AfterValidator(validate_sex_options)]

    @classmethod
    def from_domain(cls, domain_obj: Profile) -> "ApiProfile":
        """Create an instance from a domain model.

        Args:
            domain_obj: Source domain model.

        Returns:
            ApiProfile instance.
        """
        return cls(
            name=domain_obj.name,
            birthday=domain_obj.birthday,
            sex=domain_obj.sex,
        )

    def to_domain(self) -> Profile:
        """Convert this value object into a domain model.

        Returns:
            Profile domain model.
        """
        return Profile(
            name=self.name,
            birthday=self.birthday,
            sex=self.sex,
        )

    @classmethod
    def from_orm_model(cls, orm_model: Any) -> "ApiProfile":
        """Create an instance from an ORM model.

        Args:
            orm_model: ORM instance with ``name``, ``birthday``, and ``sex``.

        Returns:
            ApiProfile instance.

        Raises:
            ValidationConversionError: If ``orm_model`` is None.
        """
        if orm_model is None:
            raise ValidationConversionError(
                message="ORM model cannot be None",
                schema_class=cls,
                conversion_direction="orm_to_api",
                source_data=None,
                validation_errors=["ORM model is required for conversion"]
            )

        return cls(
            name=orm_model.name,
            birthday=orm_model.birthday,
            sex=orm_model.sex,
        )

    def to_orm_kwargs(self) -> dict[str, Any]:
        """Return kwargs suitable for constructing/updating an ORM model.

        Returns:
            Mapping of ORM field names to values.
        """
        return {
            "name": self.name,
            "birthday": self.birthday,
            "sex": self.sex,
        }
