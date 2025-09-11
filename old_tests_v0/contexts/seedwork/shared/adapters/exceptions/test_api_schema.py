"""Tests for API Schema Exception Hierarchy."""

import pytest
from typing import Any
from pydantic_core import PydanticCustomError

from src.contexts.seedwork.adapters.exceptions.api_schema_errors import (
    ApiSchemaError,
    ValidationConversionError,
    DuplicateItemError,
    FieldMappingError
)


class DummyApiSchema:
    """Dummy class for testing schema_class parameter."""
    pass


class TestApiSchemaError:
    """Test base ApiSchemaError functionality."""
    
    def test_basic_initialization(self):
        """Test basic exception initialization."""
        error = ApiSchemaError("Test error")
        
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.schema_class is None
        assert error.extra_data == {}
    
    def test_initialization_with_schema_class(self):
        """Test initialization with schema class."""
        error = ApiSchemaError("Test error", schema_class=DummyApiSchema)
        
        assert error.schema_class == DummyApiSchema
        assert error.message == "Test error"
    
    def test_initialization_with_extra_data(self):
        """Test initialization with extra keyword arguments."""
        error = ApiSchemaError(
            "Test error", 
            custom_field="custom_value",
            another_field=42
        )
        
        assert error.extra_data == {
            "custom_field": "custom_value",
            "another_field": 42
        }


class TestValidationConversionError:
    """Test ValidationConversionError functionality."""
    
    def test_basic_initialization(self):
        """Test basic initialization of conversion error."""
        error = ValidationConversionError("Conversion failed")
        
        assert str(error) == "Conversion failed"
        assert error.conversion_direction is None
        assert error.source_data is None
        assert error.validation_errors == []
    
    def test_full_initialization(self):
        """Test initialization with all parameters."""
        source_data = {"id": "123", "name": "test"}
        validation_errors = ["field required", "invalid type"]
        
        error = ValidationConversionError(
            "Complex conversion failed",
            schema_class=DummyApiSchema,
            conversion_direction="api_to_domain",
            source_data=source_data,
            validation_errors=validation_errors,
            custom_field="custom_value"
        )
        
        assert error.message == "Complex conversion failed"
        assert error.schema_class == DummyApiSchema
        assert error.conversion_direction == "api_to_domain"
        assert error.source_data == source_data
        assert error.validation_errors == validation_errors
        assert error.extra_data["custom_field"] == "custom_value"
    
    def test_get_context(self):
        """Test context retrieval for debugging."""
        error = ValidationConversionError(
            "Context test",
            schema_class=DummyApiSchema,
            conversion_direction="domain_to_orm",
            validation_errors=["error1", "error2"],
            extra_field="extra_value"
        )
        
        context = error.get_context()
        
        expected_context = {
            'message': 'Context test',
            'schema_class': 'DummyApiSchema',
            'conversion_direction': 'domain_to_orm',
            'validation_errors': ['error1', 'error2'],
            'extra_data': {'extra_field': 'extra_value'}
        }
        
        assert context == expected_context
    
    def test_get_context_with_none_schema_class(self):
        """Test context when schema_class is None."""
        error = ValidationConversionError("Test error")
        context = error.get_context()
        
        assert context['schema_class'] is None


class TestDuplicateItemError:
    """Test DuplicateItemError functionality."""
    
    def test_basic_initialization(self):
        """Test basic initialization of duplicate item error."""
        error = DuplicateItemError(
            "Duplicate found",
            item_type="recipe",
            field_name="recipes",
            duplicate_key="id",
            duplicate_value="recipe-123"
        )
        
        assert str(error) == "Duplicate found"
        assert error.item_type == "recipe"
        assert error.field_name == "recipes"
        assert error.duplicate_key == "id"
        assert error.duplicate_value == "recipe-123"
        assert error.duplicate_items == []
    
    def test_full_initialization(self):
        """Test initialization with all parameters."""
        duplicate_items = [
            {"id": "recipe-123", "name": "Recipe A"},
            {"id": "recipe-123", "name": "Recipe B"}
        ]
        
        error = DuplicateItemError(
            "Duplicate recipes found",
            item_type="recipe",
            field_name="recipes",
            duplicate_key="id",
            duplicate_value="recipe-123",
            duplicate_items=duplicate_items,
            schema_class=DummyApiSchema
        )
        
        assert error.duplicate_items == duplicate_items
        assert error.schema_class == DummyApiSchema
    
    def test_create_pydantic_error_basic(self):
        """Test creating basic PydanticCustomError."""
        pydantic_error = DuplicateItemError.create_pydantic_error(
            item_type="tag",
            field="tags",
            duplicate_key="name",
            duplicate_value="vegetarian"
        )
        
        assert isinstance(pydantic_error, PydanticCustomError)
        assert pydantic_error.type == "duplicate_item_error"
        
        # Check error context - use 'context' not 'ctx'
        context: dict[str, Any] = pydantic_error.context or {}
        assert context["item_type"] == "tag"
        assert context["field"] == "tags"
        assert context["duplicate_key"] == "name"
        assert context["duplicate_value"] == "vegetarian"
        assert context["duplicate_count"] == 2  # Default when no items provided
        assert context["duplicate_items"] is None
    
    def test_create_pydantic_error_with_items(self):
        """Test creating PydanticCustomError with duplicate items."""
        duplicate_items = [
            {"name": "vegetarian", "category": "diet"},
            {"name": "vegetarian", "category": "preference"},
            {"name": "vegetarian", "category": "restriction"}
        ]
        
        pydantic_error = DuplicateItemError.create_pydantic_error(
            item_type="tag",
            field="tags",
            duplicate_key="name",
            duplicate_value="vegetarian",
            duplicate_items=duplicate_items
        )
        
        context: dict[str, Any] = pydantic_error.context or {}
        assert context["duplicate_count"] == 3
        assert context["duplicate_items"] == duplicate_items
    
    def test_pydantic_error_message_formatting(self):
        """Test that the error message template works correctly."""
        pydantic_error = DuplicateItemError.create_pydantic_error(
            item_type="ingredient",
            field="ingredients",
            duplicate_key="name",
            duplicate_value="salt"
        )
        
        # The message template should be properly formatted
        expected_template = 'Duplicate {item_type} found in {field}: {duplicate_count} items have {duplicate_key}={duplicate_value}'
        assert pydantic_error.message_template == expected_template


class TestFieldMappingError:
    """Test FieldMappingError functionality."""
    
    def test_basic_initialization(self):
        """Test basic initialization of field mapping error."""
        error = FieldMappingError("Field mapping failed")
        
        assert str(error) == "Field mapping failed"
        assert error.missing_fields == []
        assert error.extra_fields == []
        assert error.type_mismatches == {}
        assert error.mapping_direction is None
    
    def test_full_initialization(self):
        """Test initialization with all field mapping details."""
        missing_fields = ["created_at", "updated_at"]
        extra_fields = ["unexpected_field"]
        type_mismatches = {
            "id": ("str", "UUID"),
            "count": ("str", "int")
        }
        
        error = FieldMappingError(
            "Complex mapping failed",
            schema_class=DummyApiSchema,
            missing_fields=missing_fields,
            extra_fields=extra_fields,
            type_mismatches=type_mismatches,
            mapping_direction="api_to_orm"
        )
        
        assert error.missing_fields == missing_fields
        assert error.extra_fields == extra_fields
        assert error.type_mismatches == type_mismatches
        assert error.mapping_direction == "api_to_orm"
        assert error.schema_class == DummyApiSchema
    
    def test_get_field_summary(self):
        """Test field summary retrieval."""
        missing_fields = ["field1", "field2"]
        extra_fields = ["field3"]
        type_mismatches = {"field4": ("str", "int")}
        
        error = FieldMappingError(
            "Summary test",
            missing_fields=missing_fields,
            extra_fields=extra_fields,
            type_mismatches=type_mismatches,
            mapping_direction="test_direction"
        )
        
        summary = error.get_field_summary()
        
        expected_summary = {
            'missing_fields': missing_fields,
            'extra_fields': extra_fields,
            'type_mismatches': type_mismatches,
            'mapping_direction': 'test_direction'
        }
        
        assert summary == expected_summary


class TestExceptionInheritance:
    """Test exception inheritance chain."""
    
    def test_inheritance_chain(self):
        """Test that all exceptions inherit correctly."""
        # All API schema exceptions should inherit from ApiSchemaError
        assert issubclass(ValidationConversionError, ApiSchemaError)
        assert issubclass(DuplicateItemError, ApiSchemaError)
        assert issubclass(FieldMappingError, ApiSchemaError)
        
        # All should ultimately inherit from Exception
        assert issubclass(ApiSchemaError, Exception)
        assert issubclass(ValidationConversionError, Exception)
        assert issubclass(DuplicateItemError, Exception)
        assert issubclass(FieldMappingError, Exception)
    
    def test_exception_catching(self):
        """Test that exceptions can be caught by their base classes."""
        try:
            raise ValidationConversionError("Test error")
        except ApiSchemaError as e:
            assert isinstance(e, ValidationConversionError)
            assert isinstance(e, ApiSchemaError)
        
        try:
            raise DuplicateItemError(
                "Test duplicate",
                item_type="test",
                field_name="test_field",
                duplicate_key="test_key",
                duplicate_value="test_value"
            )
        except ApiSchemaError as e:
            assert isinstance(e, DuplicateItemError)
            assert isinstance(e, ApiSchemaError)


class TestPydanticIntegration:
    """Test integration with Pydantic validation system."""
    
    def test_pydantic_custom_error_creation(self):
        """Test that PydanticCustomError is created correctly."""
        error = DuplicateItemError.create_pydantic_error(
            item_type="user",
            field="users",
            duplicate_key="email",
            duplicate_value="test@example.com"
        )
        
        assert isinstance(error, PydanticCustomError)
        assert hasattr(error, 'type')
        assert hasattr(error, 'message_template')
        assert hasattr(error, 'context')
        
        # Verify the error can be raised
        with pytest.raises(PydanticCustomError):
            raise error 