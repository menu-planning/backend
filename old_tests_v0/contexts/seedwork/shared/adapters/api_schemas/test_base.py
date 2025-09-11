import pytest
from pydantic import Field, ValidationError
from src.contexts.seedwork.adapters.api_schemas.base_api_model import BaseApiModel

class TestBaseApiModel:
    """Test suite for BaseApiModel functionality."""
    
    def test_base_api_model_inheritance(self):
        """Test that BaseApiModel properly configures Pydantic models."""
        class TestModel(BaseApiModel):
            name: str = Field(..., description="Test field")
            value: int = Field(..., description="Another test field")
        
        # Verify model configuration
        assert TestModel.model_config.get('from_attributes') is True
        assert TestModel.model_config.get('validate_assignment') is True
        assert TestModel.model_config.get('extra') == 'forbid'
    
    def test_base_api_model_validation(self):
        """Test that BaseApiModel enforces strict validation."""
        class TestModel(BaseApiModel):
            name: str = Field(..., description="Test field")
            value: int = Field(..., description="Another test field")
        
        # Test valid data
        valid_data = {"name": "test", "value": 42}
        model = TestModel(**valid_data)
        assert model.name == "test"
        assert model.value == 42
        
        # Test invalid data - missing required field
        with pytest.raises(ValueError):
            TestModel(name="test")  # type: ignore
        
        # Test invalid data - wrong type
        with pytest.raises(ValueError):
            TestModel(name="test", value="not_an_int")  # type: ignore
    
    def test_base_api_model_extra_fields(self):
        """Test that BaseApiModel forbids extra fields."""
        class TestModel(BaseApiModel):
            name: str = Field(..., description="Test field")
        
        # Test that extra fields are rejected
        with pytest.raises(ValueError):
            TestModel(name="test", extra_field="value")  # type: ignore 

@pytest.mark.parametrize(
    "data,should_raise",
    [
        ({"name": "test", "value": 42}, False),  # valid
        ({"name": "test"}, True),                # missing value
        ({"name": "test", "value": "not_an_int"}, True),  # wrong type
        ({"name": "test", "value": 42, "extra": 1}, True), # extra field
    ]
)
def test_parametrized_model_validation(data, should_raise):
    class TestModel(BaseApiModel):
        name: str = Field(..., description="Test field")
        value: int = Field(..., description="Another test field")
    if should_raise:
        with pytest.raises(ValueError):
            TestModel(**data)
    else:
        model = TestModel(**data)
        assert model.name == "test"


def test_model_immutable():
    class TestModel(BaseApiModel):
        name: str = Field(..., description="Test field")
    model = TestModel(name="immutable")
    with pytest.raises(ValidationError):
        model.name = "changed"

