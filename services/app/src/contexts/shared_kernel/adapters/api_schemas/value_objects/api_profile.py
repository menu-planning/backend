from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiValueObject
from src.contexts.shared_kernel.domain.value_objects.profile import Profile
from src.db.base import SaBase
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import SanitizedText
from datetime import date
from pydantic import Field, field_validator
from typing import Any

class ApiProfile(BaseApiValueObject[Profile, SaBase]):
    """A class to represent and validate a profile."""

    name: SanitizedText = Field(..., min_length=1, max_length=255)
    birthday: date
    sex: str

    @field_validator('sex')
    @classmethod
    def validate_sex_options(cls, v: str) -> str:
        """Validate sex field contains acceptable values."""      
        # Common accepted values (expandable as needed)
        valid_options = {'masculino', 'feminino'}
        if v.lower() not in valid_options:
            raise ValueError(f"Invalid sex: {v}")
        
        return v.lower()

    @field_validator('birthday')
    @classmethod
    def validate_birthday_reasonable(cls, v: date) -> date:
        """Validate birthday is within reasonable range."""      
        from datetime import date as date_class
        today = date_class.today()
        
        # Check for reasonable birth year (not future, not impossibly old)
        if v > today:
            raise ValueError("Birthday cannot be in the future")
        
        # Check for reasonable age (assuming max 150 years)
        min_birth_year = today.year - 150
        if v.year < min_birth_year:
            raise ValueError(f"Birthday year must be after {min_birth_year}")
            
        return v

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
            raise ValueError("ORM model cannot be None")
            
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
