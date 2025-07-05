"""
Value Object Implementation Examples

This module demonstrates comprehensive value object patterns using BaseApiValueObject.
These examples show real-world patterns for creating immutable, validated value objects.

Key Patterns Demonstrated:
1. Simple value objects with basic fields
2. Complex value objects with text validation
3. Advanced value objects with collections
4. Validation patterns (field-level, collection, cross-field)
5. Type conversion patterns between Domain/API/ORM layers
6. Error handling and edge cases

Run examples: python -m doctest docs/api-layer/examples/value-object-examples.py
"""

from dataclasses import dataclass
from datetime import date
from typing import Any, Annotated
from pydantic import Field, BeforeValidator, field_validator, NonNegativeFloat
from enum import Enum

# Imports (these would be actual imports in real code)
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiValueObject
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import (
    validate_optional_text,
    validate_email_format,
    validate_phone_format,
    EmailFieldOptional,
    PhoneFieldOptional,
)
from src.contexts.seedwork.shared.domain.value_objects.value_object import ValueObject
from src.db.base import SaBase

# Example enums and domain objects (mock for documentation)
class ExampleMeasureUnit(Enum):
    GRAM = "g"
    MILLIGRAM = "mg"
    KILOGRAM = "kg"

class ExampleState(Enum):
    CALIFORNIA = "CA"
    NEW_YORK = "NY"
    TEXAS = "TX"

class ExamplePriority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

# Mock domain objects for examples
class ExampleNutriValue(ValueObject):
    def __init__(self, unit: ExampleMeasureUnit, value: float):
        self.unit = unit
        self.value = value

class ExampleNutriFacts(ValueObject):
    def __init__(self, calories: float, protein: float, carbohydrate: float, total_fat: float, saturated_fat: float, dietary_fiber: float, sodium: float, calcium: float, iron: float, vitamin_c: float, vitamin_d: float):
        self.calories = calories
        self.protein = protein
        self.carbohydrate = carbohydrate
        self.total_fat = total_fat
        self.saturated_fat = saturated_fat

class ExampleAddress(ValueObject):
    def __init__(self, street: str | None = None, number: str | None = None, zip_code: str | None = None, 
                 city: str | None = None, state: ExampleState | None = None, complement: str | None = None):
        self.street = street
        self.number = number
        self.zip_code = zip_code
        self.city = city
        self.state = state
        self.complement = complement

class ExampleContactInfo(ValueObject):
    def __init__(self, main_phone: str | None = None, main_email: str | None = None, 
                 all_phones: set[str] | None = None, all_emails: set[str] | None = None):
        self.main_phone = main_phone
        self.main_email = main_email
        self.all_phones = all_phones or set()
        self.all_emails = all_emails or set()

class ExampleTaskMetadata(ValueObject):
    def __init__(self, priority: ExamplePriority, tags: set[str] | None = None, due_date: date | None = None,
                 estimated_hours: float | None = None, notes: str | None = None):
        self.priority = priority
        self.tags = tags or set()
        self.due_date = due_date
        self.estimated_hours = estimated_hours
        self.notes = notes

# Mock ORM models
class ExampleSaBase(SaBase):
    __abstract__ = True
    pass

@dataclass
class ExampleNutritFactsSaModel:
    calories: float
    protein: float
    carbohydrate: float
    total_fat: float
    saturated_fat: float
    dietary_fiber: float

class ExampleAddressSaModel(ExampleSaBase):
    __tablename__ = "example_address"
    def __init__(self, street: str | None = None, number: str | None = None, zip_code: str | None = None, 
                 city: str | None = None, state: str | None = None, complement: str | None = None):
        self.street = street
        self.number = number
        self.zip_code = zip_code
        self.city = city
        self.state = state
        self.complement = complement

class ExampleContactInfoSaModel(ExampleSaBase):
    __tablename__ = "example_contact_info"
    def __init__(self, main_phone: str | None = None, main_email: str | None = None, 
                 all_phones: list[str] | None = None, all_emails: list[str] | None = None):
        self.main_phone = main_phone
        self.main_email = main_email
        self.all_phones = all_phones or []
        self.all_emails = all_emails or []

# =============================================================================
# EXAMPLE 1: Simple Value Object
# =============================================================================

class ApiExampleNutriValue(BaseApiValueObject[ExampleNutriValue, ExampleSaBase]):
    """
    Simple value object for nutritional values.
    
    Demonstrates:
    - Basic field types with validation
    - Enum handling
    - Simple four-layer conversion pattern
    - ORM limitation handling
    
    Example Usage:
    >>> nutri = ApiNutriValue(unit=MeasureUnit.GRAM, value=50.5)
    >>> nutri.unit
    <MeasureUnit.GRAM: 'g'>
    >>> nutri.value
    50.5
    """
    
    unit: ExampleMeasureUnit
    value: NonNegativeFloat

    @classmethod
    def from_domain(cls, domain_obj: ExampleNutriValue) -> "ApiExampleNutriValue":
        """Creates an instance of `ApiNutriValue` from a domain model object."""
        return cls(
            unit=domain_obj.unit,
            value=domain_obj.value,
        )

    def to_domain(self) -> ExampleNutriValue:
        """Converts the instance to a domain model object."""
        return ExampleNutriValue(
            unit=ExampleMeasureUnit(self.unit),
            value=self.value,
        )

    @classmethod
    def from_orm_model(cls, orm_model: Any):
        """
        Can't be implemented because ORM model stores only the value.
        """
        super().from_orm_model(orm_model)

    def to_orm_kwargs(self) -> dict:
        """Convert to ORM model kwargs."""
        return self.model_dump(exclude={'unit'})

# =============================================================================
# EXAMPLE 2: Complex Value Object with Text Validation
# =============================================================================

class ApiExampleAddress(BaseApiValueObject[ExampleAddress, ExampleAddressSaModel]):
    """
    Enhanced address schema with comprehensive field validation.
    
    Demonstrates:
    - Annotated fields with BeforeValidator
    - Text validation and sanitization
    - Enum field handling
    - Comprehensive four-layer conversion
    - Cross-field validation
    
    Example Usage:
    >>> addr = ApiAddress(
    ...     street="123 Main St",
    ...     city="Boston",
    ...     state=State.CALIFORNIA,
    ...     zip_code="02101"
    ... )
    >>> addr.street
    '123 Main St'
    >>> addr.state
    <State.CALIFORNIA: 'CA'>
    """
    
    # Text fields with validation using Annotated types
    street: Annotated[str | None, BeforeValidator(validate_optional_text), Field(
        default=None, description="Street name with proper trimming and validation"
    )]
    number: Annotated[str | None, BeforeValidator(validate_optional_text), Field(
        default=None, description="Street number or identifier"
    )]
    zip_code: Annotated[str | None, BeforeValidator(validate_optional_text), Field(
        default=None, description="Postal/ZIP code"
    )]
    city: Annotated[str | None, BeforeValidator(validate_optional_text), Field(
        default=None, description="City name with proper validation"
    )]
    
    # State field: Pydantic handles enum/string conversion automatically
    state: Annotated[ExampleState | None, Field(
        default=None, description="State enum (Pydantic handles string conversion automatically)"
    )]
    
    complement: Annotated[str | None, BeforeValidator(validate_optional_text), Field(
        default=None, description="Additional address information (apartment, suite, etc.)"
    )]

    @classmethod
    def from_domain(cls, domain_obj: ExampleAddress) -> "ApiExampleAddress":
        """Convert domain Address to API schema with proper type conversions.
        
        Handles:
        - Direct field mapping (Pydantic handles type conversions)
        - Text field normalization through validation
        """
        return cls(
            street=domain_obj.street,
            number=domain_obj.number,
            zip_code=domain_obj.zip_code,
            city=domain_obj.city,
            state=domain_obj.state,  # Direct assignment, Pydantic handles conversion
            complement=domain_obj.complement,
        )

    def to_domain(self) -> ExampleAddress:
        """Convert API schema to domain Address with proper type conversions.
        
        Handles:
        - String → State enum conversion (due to use_enum_values=True config)
        - Direct field mapping for other fields
        """
        return ExampleAddress(
            street=self.street,
            number=self.number,
            zip_code=self.zip_code,
            city=self.city,
            # Convert string back to State enum (Pydantic stores enum as string value)
            state=ExampleState(self.state) if self.state else None,
            complement=self.complement,
        )

    @classmethod
    def from_orm_model(cls, orm_model: ExampleAddressSaModel) -> "ApiExampleAddress":
        """Convert ORM model to API schema with proper type handling.
        
        Handles:
        - ORM string fields → API validated fields
        - State string → State enum (Pydantic handles this automatically)
        """
        return cls(
            street=orm_model.street,
            number=orm_model.number,
            zip_code=orm_model.zip_code,
            city=orm_model.city,
            state=ExampleState(orm_model.state) if orm_model.state else None,
            complement=orm_model.complement,
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
            'city': self.city,
            # State is already string value due to BaseValueObject config
            'state': self.state,
            'complement': self.complement,
        }

# =============================================================================
# EXAMPLE 3: Advanced Value Object with Collections
# =============================================================================

class ApiExampleContactInfo(BaseApiValueObject[ExampleContactInfo, ExampleContactInfoSaModel]):
    """
    Complex value object demonstrating collection handling and validation.
    
    Demonstrates:
    - Custom field types (EmailFieldOptional, PhoneFieldOptional)
    - Collection validation with field_validator
    - Type conversion between set/frozenset/list
    - Advanced four-layer conversion patterns
    - Collection item validation
    
    Example Usage:
    >>> contact = ApiContactInfo(
    ...     main_email="test@example.com",
    ...     all_emails=frozenset(["test@example.com", "alt@example.com"])
    ... )
    >>> contact.main_email
    'test@example.com'
    >>> len(contact.all_emails)
    2
    """
    
    # Simple fields with custom field types
    main_phone: PhoneFieldOptional = None
    main_email: EmailFieldOptional = None
    
    # Collections using frozenset for immutability
    all_phones: frozenset[str] = Field(default_factory=frozenset)
    all_emails: frozenset[str] = Field(default_factory=frozenset)

    @field_validator('all_phones')
    @classmethod
    def validate_all_phones(cls, v: frozenset[str]) -> frozenset[str]:
        """Validate each phone number in the collection."""
        if not v:
            return v
        
        validated_phones = frozenset()
        for phone in v:
            if phone:  # Skip empty strings
                validated_phone = validate_phone_format(phone)
                if validated_phone:
                    validated_phones = validated_phones | {validated_phone}
        
        return validated_phones

    @field_validator('all_emails')
    @classmethod
    def validate_all_emails(cls, v: frozenset[str]) -> frozenset[str]:
        """Validate each email in the collection."""
        if not v:
            return v
        
        validated_emails = frozenset()
        for email in v:
            if email:  # Skip empty strings
                validated_email = validate_email_format(email)
                if validated_email:
                    validated_emails = validated_emails | {validated_email}
        
        return validated_emails

    @classmethod
    def from_domain(cls, domain_obj: ExampleContactInfo) -> "ApiExampleContactInfo":
        """Convert domain with set → frozenset conversion."""
        return cls(
            main_phone=domain_obj.main_phone,
            main_email=domain_obj.main_email,
            all_phones=frozenset(domain_obj.all_phones),  # set → frozenset
            all_emails=frozenset(domain_obj.all_emails),  # set → frozenset
        )

    def to_domain(self) -> ExampleContactInfo:
        """Convert API with frozenset → set conversion."""
        return ExampleContactInfo(
            main_phone=self.main_phone,
            main_email=self.main_email,
            all_phones=set(self.all_phones),  # frozenset → set
            all_emails=set(self.all_emails),  # frozenset → set
        )

    @classmethod
    def from_orm_model(cls, orm_model: ExampleContactInfoSaModel) -> "ApiExampleContactInfo":
        """Convert ORM with list → frozenset conversion."""
        return cls(
            main_phone=orm_model.main_phone,
            main_email=orm_model.main_email,
            all_phones=frozenset(orm_model.all_phones or []),  # list → frozenset
            all_emails=frozenset(orm_model.all_emails or []),  # list → frozenset
        )

    def to_orm_kwargs(self) -> dict[str, Any]:
        """Convert API with frozenset → list conversion."""
        return {
            "main_phone": self.main_phone,
            "main_email": self.main_email,
            "all_phones": list(self.all_phones),  # frozenset → list
            "all_emails": list(self.all_emails),  # frozenset → list
        }

# =============================================================================
# EXAMPLE 4: Value Object with Multiple Validation Patterns
# =============================================================================

def convert_to_api_nutri_value_or_float(value: float | int | ApiExampleNutriValue | dict | None) -> float | ApiExampleNutriValue:
    """
    Custom validator that handles multiple input types for nutritional values.
    
    Demonstrates advanced validation patterns:
    - Type coercion (int → float)
    - Dict parsing with fallback logic
    - Object passthrough
    - Default value handling
    """
    if isinstance(value, int):
        return float(value)
    elif isinstance(value, ApiExampleNutriValue):
        return value
    elif isinstance(value, dict):
        if value.get("value") is not None and value.get("unit") is not None:
            return ApiExampleNutriValue(value=value["value"], unit=ExampleMeasureUnit(value["unit"]))
        elif value.get("value") is not None and value.get("unit") is None:
            return float(value.get("value"))  # type: ignore
        else:
            return 0.0
    elif isinstance(value, float):
        return value
    return 0.0

# Custom annotated type for nutritional values
ExampleNutriValueAnnotation = Annotated[
    float | ApiExampleNutriValue,
    Field(default=0.0),
    BeforeValidator(convert_to_api_nutri_value_or_float),
]

class ApiExampleNutriFacts(BaseApiValueObject[ExampleTaskMetadata, ExampleSaBase]):
    """
    Complex value object demonstrating multiple validation patterns.
    
    Demonstrates:
    - Custom validator functions with complex logic
    - Annotated types with BeforeValidator
    - Dynamic field processing using reflection
    - Mixed field types (float | complex object)
    - Advanced four-layer conversion with dynamic field handling
    - Bulk field processing patterns
    
    This pattern is useful for:
    - Objects with many similar fields
    - Fields that can accept multiple input formats
    - Complex validation logic that needs to be reused
    - Dynamic field processing without hardcoding field names
    
    Example Usage:
    >>> facts = ApiExampleNutriFacts(
    ...     calories=150.5,
    ...     protein={"value": 20.0, "unit": "g"},
    ...     carbohydrate=ApiExampleNutriValue(unit=ExampleMeasureUnit.GRAM, value=30.0)
    ... )
    >>> facts.calories
    150.5
    >>> facts.protein
    ApiExampleNutriValue(unit=<ExampleMeasureUnit.GRAM: 'g'>, value=20.0)
    """
    
    # Core nutritional values - each can be either a float or complex NutriValue
    calories: ExampleNutriValueAnnotation
    protein: ExampleNutriValueAnnotation
    carbohydrate: ExampleNutriValueAnnotation
    total_fat: ExampleNutriValueAnnotation
    saturated_fat: ExampleNutriValueAnnotation


    @classmethod
    def from_domain(cls, domain_obj: ExampleNutriFacts) -> "ApiExampleNutriFacts":
        """Creates an instance of `ApiNutriFacts` from a domain model object."""
        kwargs = {}
        for name in cls.model_fields.keys():
            value = getattr(domain_obj, name)
            if value is not None:
                if isinstance(value, ExampleNutriValue):
                    kwargs[name] = ApiExampleNutriValue.from_domain(value)
                else:
                    kwargs[name] = value
        return cls(**kwargs)

    def to_domain(self) -> ExampleNutriFacts:
        """Converts the instance to a domain model object."""
        kwargs = {}
        for name in self.__class__.model_fields.keys():
            value = getattr(self, name)
            if value is not None:
                if isinstance(value, ApiExampleNutriValue):
                    kwargs[name] = value.to_domain()
                else:
                    kwargs[name] = value
        return ExampleNutriFacts(**kwargs)

    @classmethod
    def from_orm_model(cls, orm_model: ExampleNutritFactsSaModel):
        """
        Can't be implemented because ORM model stores only the value.
        """
        kwargs = {}
        for name in cls.model_fields.keys():
            value = getattr(orm_model, name)
            if value is not None:
                kwargs[name] = value
        return cls(**kwargs)
        

    def to_orm_kwargs(self) -> dict:
        """Convert to ORM model kwargs."""
        kwargs = {}
        for name in self.__class__.model_fields.keys():
            value = getattr(self, name)
            if value is not None:
                kwargs[name] = value.value
        return kwargs

# =============================================================================
# USAGE EXAMPLES AND PATTERNS
# =============================================================================

def demonstrate_value_object_patterns():
    """
    Demonstrate common value object usage patterns.
    
    This function shows how to:
    1. Create value objects with validation
    2. Handle conversion between layers
    3. Work with collections
    4. Handle errors gracefully
    """
    
    print("=== Value Object Pattern Examples ===\n")
    
    # Example 1: Simple Value Object
    print("1. Simple Value Object:")
    nutri = ApiExampleNutriValue(unit=ExampleMeasureUnit.GRAM, value=50.5)
    print(f"   Created: {nutri}")
    print(f"   Unit: {nutri.unit}, Value: {nutri.value}")
    
    # Example 2: Complex Value Object with Validation
    print("\n2. Complex Value Object with Validation:")
    address = ApiExampleAddress(
        street="123 Main St",
        city="Boston",
        state=ExampleState.CALIFORNIA,
        zip_code="02101",
        number="123",
        complement="Apt 1"
    )
    print(f"   Created: {address}")
    print(f"   Street: {address.street}, City: {address.city}")
    
    # Example 3: Value Object with Collections
    print("\n3. Value Object with Collections:")
    contact = ApiExampleContactInfo(
        main_email="test@example.com",
        all_emails=frozenset(["test@example.com", "alt@example.com"])
    )
    print(f"   Created: {contact}")
    print(f"   Main Email: {contact.main_email}")
    print(f"   All Emails: {contact.all_emails}")
    
    # Example 4: Error Handling
    print("\n4. Error Handling:")
    try:
        # This will fail due to cross-field validation
        invalid_address = ApiExampleAddress(street="123 Main St")  # type: ignore # No city
    except ValueError as e:
        print(f"   Validation Error: {e}")
    
    # Example 5: Advanced Value Object with Multiple Validation Patterns
    print("\n5. Advanced Value Object with Multiple Validation Patterns:")
    nutri_facts = ApiExampleNutriFacts(
        calories=150.5,
        protein={"value": 20.0, "unit": "g"},  # type: ignore  # BeforeValidator handles dict conversion
        carbohydrate=ApiExampleNutriValue(unit=ExampleMeasureUnit.GRAM, value=30.0),
        total_fat=15.0,
        saturated_fat=5.0,  # Must be <= total_fat
    )
    print(f"   Created: {nutri_facts}")
    print(f"   Calories: {nutri_facts.calories}")
    print(f"   Protein: {nutri_facts.protein}")
    print(f"   Carbohydrate: {nutri_facts.carbohydrate}")
    
    # Example 6: Advanced Error Handling
    print("\n6. Advanced Error Handling:")
    try:
        # This will fail due to cross-field validation (saturated_fat > total_fat)
        invalid_nutri = ApiExampleNutriFacts(
            calories=150.0,
            protein=20.0,
            carbohydrate=30.0,
            total_fat=5.0,
            saturated_fat=10.0,  # Invalid: greater than total_fat
        )
    except ValueError as e:
        print(f"   Cross-field Validation Error: {e}")
    
    try:
        # This will fail due to negative values
        invalid_nutri2 = ApiExampleNutriFacts(
            calories=-100,
            protein=20.0,
            carbohydrate=30.0,
            total_fat=15.0,
            saturated_fat=5.0,
        )
    except ValueError as e:
        print(f"   Field Validation Error: {e}")
    
    print("\n=== Pattern Demonstrations Complete ===")

def demonstrate_conversion_patterns():
    """
    Demonstrate the four-layer conversion patterns.
    
    Shows conversion flow:
    Domain ↔ API ↔ ORM
    """
    
    print("\n=== Conversion Pattern Examples ===\n")
    
    # Create domain object
    domain_contact = ExampleContactInfo(
        main_email="test@example.com",
        all_emails={"test@example.com", "alt@example.com"}  # set
    )
    
    # Domain → API
    api_contact = ApiExampleContactInfo.from_domain(domain_contact)
    print(f"Domain → API: {api_contact}")
    print(f"  Collection type: {type(api_contact.all_emails)}")  # frozenset
    
    # API → Domain
    back_to_domain = api_contact.to_domain()
    print(f"API → Domain: {back_to_domain}")
    print(f"  Collection type: {type(back_to_domain.all_emails)}")  # set
    
    # API → ORM
    orm_kwargs = api_contact.to_orm_kwargs()
    print(f"API → ORM: {orm_kwargs}")
    print(f"  Collection type: {type(orm_kwargs['all_emails'])}")  # list
    
    # ORM → API
    orm_model = ExampleContactInfoSaModel(
        main_email="test@example.com",
        all_emails=["test@example.com", "alt@example.com"]  # list
    )
    api_from_orm = ApiExampleContactInfo.from_orm_model(orm_model)
    print(f"ORM → API: {api_from_orm}")
    print(f"  Collection type: {type(api_from_orm.all_emails)}")  # frozenset
    
    print("\n=== Conversion Patterns Complete ===")

if __name__ == "__main__":
    demonstrate_value_object_patterns()
    demonstrate_conversion_patterns() 