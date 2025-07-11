from typing import Optional, Any
from typing import Annotated
from pydantic import Field, BeforeValidator

from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiValueObject
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import remove_whitespace_and_empty_str
from src.contexts.shared_kernel.domain.enums import State
from src.contexts.shared_kernel.domain.value_objects.address import Address
from src.contexts.shared_kernel.adapters.ORM.sa_models.address_sa_model import AddressSaModel
from src.db.base import SaBase


class ApiAddress(BaseApiValueObject[Address, SaBase]):
    """Enhanced address schema following documented API patterns.
    
    This schema implements the four-layer conversion pattern and comprehensive
    field validation for geographic address data.
    
    Key Features:
    - State enum handling with automatic conversion
    - Comprehensive text field validation and sanitization
    - Geographic data validation through Annotated types
    - Proper type conversions between all layers
    
    Conversion Patterns:
    - Domain: Uses State enum objects
    - API: Uses State enum (Pydantic handles string conversion)
    - ORM: Stores states as strings in database
    """

    # Text fields with comprehensive validation
    street: Annotated[str | None, BeforeValidator(remove_whitespace_and_empty_str), Field(
        default=None, description="Street name with proper trimming and validation"
    )]
    number: Annotated[str | None, BeforeValidator(remove_whitespace_and_empty_str), Field(
        default=None, description="Street number or identifier"
    )]
    zip_code: Annotated[str | None, BeforeValidator(remove_whitespace_and_empty_str), Field(
        default=None, description="Postal/ZIP code"
    )]
    district: Annotated[str | None, BeforeValidator(remove_whitespace_and_empty_str), Field(
        default=None, description="District or neighborhood name"
    )]
    city: Annotated[str | None, BeforeValidator(remove_whitespace_and_empty_str), Field(
        default=None, description="City name with proper validation"
    )]
    
    # State field: Pydantic handles enum/string conversion automatically
    state: Annotated[State | None, Field(
        default=None, description="State enum (Pydantic handles string conversion automatically)"
    )]
    
    complement: Annotated[str | None, BeforeValidator(remove_whitespace_and_empty_str), Field(
        default=None, description="Additional address information (apartment, suite, etc.)"
    )]
    note: Annotated[str | None, BeforeValidator(remove_whitespace_and_empty_str), Field(
        default=None, description="Additional notes about the address"
    )]

    @classmethod
    def from_domain(cls, domain_obj: Address) -> "ApiAddress":
        """Convert domain Address to API schema with proper type conversions.
        
        Handles:
        - Direct field mapping (Pydantic handles type conversions)
        - Text field normalization through validation
        """
        return cls(
            street=domain_obj.street,
            number=domain_obj.number,
            zip_code=domain_obj.zip_code,
            district=domain_obj.district,
            city=domain_obj.city,
            state=domain_obj.state,  # Direct assignment, Pydantic handles conversion
            complement=domain_obj.complement,
            note=domain_obj.note
        )

    def to_domain(self) -> Address:
        """Convert API schema to domain Address with proper type conversions.
        
        Handles:
        - String → State enum conversion (due to use_enum_values=True config)
        - Direct field mapping for other fields
        """
        return Address(
            street=self.street,
            number=self.number,
            zip_code=self.zip_code,
            district=self.district,
            city=self.city,
            # Convert string back to State enum (Pydantic stores enum as string value)
            state=State(self.state) if self.state else None,
            complement=self.complement,
            note=self.note
        )

    @classmethod
    def from_orm_model(cls, orm_model: AddressSaModel) -> "ApiAddress":
        """Convert ORM model to API schema with proper type handling.
        
        Handles:
        - ORM string fields → API validated fields
        - State string → State enum (Pydantic handles this automatically)
        """
        return cls(
            street=orm_model.street,
            number=orm_model.number,
            zip_code=orm_model.zip_code,
            district=orm_model.district,
            city=orm_model.city,
            state=State(orm_model.state) if orm_model.state else None,
            complement=orm_model.complement,
            note=orm_model.note
        )

    def to_orm_kwargs(self) -> dict[str, Any]:
        """Convert API schema to ORM model kwargs with proper type preparation.
        
        Handles:
        - API fields → ORM compatible types
        - State is already string value due to use_enum_values=True config
        """
        return {
            'street': self.street,
            'number': self.number,
            'zip_code': self.zip_code,
            'district': self.district,
            'city': self.city,
            # State is already string value due to BaseValueObject config
            'state': self.state,
            'complement': self.complement,
            'note': self.note
        }
