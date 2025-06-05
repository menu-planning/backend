from typing import Any, Dict, Type, Protocol
from pydantic import BaseModel

class DomainConvertible(Protocol):
    """Protocol for schemas that can convert from domain objects."""
    @classmethod
    def from_domain(cls, domain_object: Dict[str, Any]) -> 'DomainConvertible':
        ...

class OrmConvertible(Protocol):
    """Protocol for schemas that can convert from ORM models."""
    @classmethod
    def from_orm_model(cls, orm_model: Dict[str, Any]) -> 'OrmConvertible':
        ...

def assert_schema_validation(schema_class: Type[BaseModel], valid_data: Dict[str, Any], invalid_data: Dict[str, Any]) -> None:
    """
    Helper function to test schema validation with valid and invalid data.
    
    Args:
        schema_class: The Pydantic schema class to test
        valid_data: Dictionary of valid data that should pass validation
        invalid_data: Dictionary of invalid data that should fail validation
    """
    # Test valid data
    model = schema_class(**valid_data)
    for key, value in valid_data.items():
        assert getattr(model, key) == value
    
    # Test invalid data
    try:
        schema_class(**invalid_data)
        raise AssertionError(f"Schema {schema_class.__name__} should have rejected invalid data")
    except ValueError:
        pass

def assert_schema_conversion(
    schema_class: Type[DomainConvertible],
    domain_object: Dict[str, Any],
    expected_api_data: Dict[str, Any]
) -> None:
    """
    Helper function to test domain object to API schema conversion.
    
    Args:
        schema_class: The Pydantic schema class to test
        domain_object: Dictionary representing a domain object
        expected_api_data: Dictionary of expected API data after conversion
    """
    api_model = schema_class.from_domain(domain_object)
    for key, value in expected_api_data.items():
        assert getattr(api_model, key) == value

def assert_orm_conversion(
    schema_class: Type[OrmConvertible],
    orm_model: Dict[str, Any],
    expected_api_data: Dict[str, Any]
) -> None:
    """
    Helper function to test ORM model to API schema conversion.
    
    Args:
        schema_class: The Pydantic schema class to test
        orm_model: Dictionary representing an ORM model
        expected_api_data: Dictionary of expected API data after conversion
    """
    api_model = schema_class.from_orm_model(orm_model)
    for key, value in expected_api_data.items():
        assert getattr(api_model, key) == value 