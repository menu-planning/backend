import pytest
from typing import Any, Dict, Type
from pydantic import BaseModel

@pytest.fixture
def sample_domain_object() -> Dict[str, Any]:
    """Fixture providing a sample domain object for testing schema conversions."""
    return {
        "id": "123",
        "name": "Test Object",
        "value": 42,
        "metadata": {
            "created_at": "2024-03-20T10:00:00Z",
            "updated_at": "2024-03-20T10:00:00Z"
        }
    }

@pytest.fixture
def sample_orm_model() -> Dict[str, Any]:
    """Fixture providing a sample ORM model for testing schema conversions."""
    return {
        "id": "123",
        "name": "Test Object",
        "value": 42,
        "created_at": "2024-03-20T10:00:00Z",
        "updated_at": "2024-03-20T10:00:00Z"
    }

@pytest.fixture
def sample_api_schema() -> Type[BaseModel]:
    """Fixture providing a sample API schema class for testing."""
    from pydantic import BaseModel, Field
    
    class SampleSchema(BaseModel):
        id: str = Field(..., description="Unique identifier")
        name: str = Field(..., description="Object name")
        value: int = Field(..., description="Numeric value")
        metadata: Dict[str, str] = Field(..., description="Additional metadata")
    
    return SampleSchema 