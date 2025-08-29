from datetime import date
from typing import Annotated, Any

from pydantic import AfterValidator, Field

from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import (
    SanitizedText,
)
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import (
    BaseApiValueObject,
)
from src.contexts.seedwork.shared.adapters.api_schemas.validators import (
    validate_birthday_reasonable,
    validate_sex_options,
)
from src.contexts.shared_kernel.domain.value_objects.profile import Profile
from src.db.base import SaBase


class ApiProfile(BaseApiValueObject[Profile, SaBase]):
    """A class to represent and validate a profile."""

    name: Annotated[SanitizedText, Field(..., min_length=1, max_length=255)]
    birthday: Annotated[date, AfterValidator(validate_birthday_reasonable)]
    sex: Annotated[str, AfterValidator(validate_sex_options)]

    @classmethod
    def from_domain(cls, domain_obj: Profile) -> "ApiProfile":
        """Creates an instance of `ApiProfile` from a domain model object."""
        return cls(
            name=domain_obj.name,
            birthday=domain_obj.birthday,
            sex=domain_obj.sex,
        )

    def to_domain(self) -> Profile:
        """Converts the instance to a domain model object."""
        return Profile(
            name=self.name,
            birthday=self.birthday,
            sex=self.sex,
        )

    @classmethod
    def from_orm_model(cls, orm_model: Any) -> "ApiProfile":
        """Convert from ORM model to API schema with proper type handling."""
        if orm_model is None:
            error_message = "ORM model cannot be None"
            raise ValueError(error_message)

        return cls(
            name=orm_model.name,
            birthday=orm_model.birthday,
            sex=orm_model.sex,
        )

    def to_orm_kwargs(self) -> dict[str, Any]:
        """Convert to ORM model kwargs with proper type handling."""
        return {
            "name": self.name,
            "birthday": self.birthday,
            "sex": self.sex,
        }
