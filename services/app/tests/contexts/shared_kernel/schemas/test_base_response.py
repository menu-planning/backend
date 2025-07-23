"""
Unit tests for base response schemas.

Tests all base response schema classes for proper validation,
serialization, and integration with existing patterns.
"""

import pytest
from datetime import datetime
from typing import Dict, Any
from pydantic import ValidationError

from src.contexts.shared_kernel.schemas.base_response import (
    BaseResponse,
    SuccessResponse,
    CreatedResponse,
    NoContentResponse,
    CollectionResponse,
    MessageResponse,
    SuccessMessageResponse,
    CreatedMessageResponse
)

# Mock data for testing
MOCK_CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,POST,PUT,DELETE",
    "Content-Type": "application/json"
}

class MockApiModel:
    """Mock API model for testing generic response types."""
    
    def __init__(self, id: str, name: str):
        self.id = id
        self.name = name
    
    def model_dump(self) -> Dict[str, Any]:
        return {"id": self.id, "name": self.name}

class TestBaseResponse:
    """Test cases for BaseResponse class."""
    
    def test_base_response_creation_valid(self):
        """Test creating a valid BaseResponse instance."""
        data = {"id": "123", "name": "test"}
        response = BaseResponse[Dict[str, str]](
            statusCode=200,
            headers=MOCK_CORS_HEADERS,
            body=data,
            metadata={"timestamp": "2024-01-15T10:00:00Z"}
        )
        
        assert response.statusCode == 200
        assert response.headers == MOCK_CORS_HEADERS
        assert response.body == data
        assert response.metadata == {"timestamp": "2024-01-15T10:00:00Z"}
    
    def test_base_response_invalid_status_code(self):
        """Test BaseResponse with invalid status code."""
        with pytest.raises(ValidationError) as exc_info:
            BaseResponse[str](
                statusCode=99,  # Invalid status code (< 100)
                headers={},
                body="test"
            )
        
        # Verify that a validation error occurred for statusCode
        assert exc_info.value is not None
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("statusCode",) for error in errors)
    
    def test_base_response_immutable(self):
        """Test that BaseResponse is immutable."""
        response = BaseResponse[str](
            statusCode=200,
            headers={},
            body="test"
        )
        
        with pytest.raises(ValidationError):
            response.statusCode = 404
    
    def test_base_response_generic_typing(self):
        """Test BaseResponse with different generic types."""
        # String type
        str_response = BaseResponse[str](
            statusCode=200,
            headers={},
            body="hello world"
        )
        assert str_response.body == "hello world"
        
        # List type
        list_response = BaseResponse[list[str]](
            statusCode=200,
            headers={},
            body=["item1", "item2"]
        )
        assert list_response.body == ["item1", "item2"]
        
        # Dict type
        dict_response = BaseResponse[Dict[str, Any]](
            statusCode=200,
            headers={},
            body={"key": "value", "number": 42}
        )
        assert dict_response.body == {"key": "value", "number": 42}

class TestSuccessResponse:
    """Test cases for SuccessResponse class."""
    
    def test_success_response_default_status(self):
        """Test SuccessResponse uses 200 as default status code."""
        response = SuccessResponse[str](
            headers=MOCK_CORS_HEADERS,
            body="success"
        )
        
        assert response.statusCode == 200
        assert response.body == "success"
    
    def test_success_response_custom_2xx_status(self):
        """Test SuccessResponse with custom 2xx status code."""
        response = SuccessResponse[str](
            statusCode=202,
            headers=MOCK_CORS_HEADERS,
            body="accepted"
        )
        
        assert response.statusCode == 202
    
    def test_success_response_invalid_non_2xx_status(self):
        """Test SuccessResponse rejects non-2xx status codes."""
        with pytest.raises(ValidationError) as exc_info:
            SuccessResponse[str](
                statusCode=404,  # Not a 2xx status code
                headers={},
                body="error"
            )
        
        # Verify that a validation error occurred for statusCode  
        assert exc_info.value is not None
        errors = exc_info.value.errors()
        assert any(error["loc"] == ("statusCode",) for error in errors)

class TestCreatedResponse:
    """Test cases for CreatedResponse class."""
    
    def test_created_response_default_status(self):
        """Test CreatedResponse uses 201 as default status code."""
        response = CreatedResponse[Dict[str, str]](
            headers=MOCK_CORS_HEADERS,
            body={"id": "new-resource-id"}
        )
        
        assert response.statusCode == 201
        assert response.body == {"id": "new-resource-id"}
    
    def test_created_response_with_metadata(self):
        """Test CreatedResponse with creation metadata."""
        created_at = datetime.now()
        response = CreatedResponse[Dict[str, str]](
            headers=MOCK_CORS_HEADERS,
            body={"id": "new-resource-id"},
            metadata={"created_at": created_at.isoformat(), "location": "/api/resources/new-resource-id"}
        )
        
        assert response.statusCode == 201
        assert response.metadata is not None
        assert response.metadata["location"] == "/api/resources/new-resource-id"

class TestNoContentResponse:
    """Test cases for NoContentResponse class."""
    
    def test_no_content_response_default_status(self):
        """Test NoContentResponse uses 204 as default status code."""
        response = NoContentResponse(headers=MOCK_CORS_HEADERS)
        
        assert response.statusCode == 204
        assert response.headers == MOCK_CORS_HEADERS
    
    def test_no_content_response_minimal(self):
        """Test NoContentResponse with minimal configuration."""
        response = NoContentResponse()
        
        assert response.statusCode == 204
        assert response.headers == {}

class TestCollectionResponse:
    """Test cases for CollectionResponse class."""
    
    def test_collection_response_basic(self):
        """Test basic CollectionResponse functionality."""
        items = [{"id": "1", "name": "item1"}, {"id": "2", "name": "item2"}]
        collection = CollectionResponse[Dict[str, str]](
            items=items,
            total_count=10,
            page_size=2,
            current_page=1,
            has_next=True,
            has_previous=False
        )
        
        assert collection.items == items
        assert collection.total_count == 10
        assert collection.page_size == 2
        assert collection.current_page == 1
        assert collection.has_next is True
        assert collection.has_previous is False
    
    def test_collection_response_total_pages_calculation(self):
        """Test total_pages property calculation."""
        # Test with exact division
        collection = CollectionResponse[str](
            items=["a", "b"],
            total_count=10,
            page_size=5
        )
        assert collection.total_pages == 2
        
        # Test with remainder
        collection = CollectionResponse[str](
            items=["a", "b", "c"],
            total_count=11,
            page_size=5
        )
        assert collection.total_pages == 3
        
        # Test with zero items
        collection = CollectionResponse[str](
            items=[],
            total_count=0,
            page_size=10
        )
        assert collection.total_pages == 0
    
    def test_collection_response_validation_errors(self):
        """Test CollectionResponse validation constraints."""
        # Negative total_count
        with pytest.raises(ValidationError):
            CollectionResponse[str](
                items=[],
                total_count=-1,
                page_size=10
            )
        
        # Zero page_size
        with pytest.raises(ValidationError):
            CollectionResponse[str](
                items=[],
                total_count=0,
                page_size=0
            )
        
        # Zero current_page
        with pytest.raises(ValidationError):
            CollectionResponse[str](
                items=[],
                total_count=0,
                page_size=10,
                current_page=0
            )
    
    def test_collection_response_in_success_response(self):
        """Test CollectionResponse wrapped in SuccessResponse."""
        items = [{"id": "1"}, {"id": "2"}]
        collection = CollectionResponse[Dict[str, str]](
            items=items,
            total_count=2,
            page_size=10
        )
        
        response = SuccessResponse[CollectionResponse[Dict[str, str]]](
            headers=MOCK_CORS_HEADERS,
            body=collection
        )
        
        assert response.statusCode == 200
        assert response.body.items == items
        assert response.body.total_count == 2

class TestMessageResponse:
    """Test cases for MessageResponse class."""
    
    def test_message_response_basic(self):
        """Test basic MessageResponse functionality."""
        message = MessageResponse(
            message="Operation completed successfully",
            details={"operation_id": "op-123", "timestamp": "2024-01-15T10:00:00Z"}
        )
        
        assert message.message == "Operation completed successfully"
        assert message.details == {"operation_id": "op-123", "timestamp": "2024-01-15T10:00:00Z"}
    
    def test_message_response_no_details(self):
        """Test MessageResponse without details."""
        message = MessageResponse(message="Simple success message")
        
        assert message.message == "Simple success message"
        assert message.details is None
    
    def test_message_response_immutable(self):
        """Test MessageResponse immutability."""
        message = MessageResponse(message="test")
        
        with pytest.raises(ValidationError):
            message.message = "changed"

class TestConvenienceAliases:
    """Test cases for convenience type aliases."""
    
    def test_success_message_response(self):
        """Test SuccessMessageResponse convenience alias."""
        message = MessageResponse(
            message="Recipe created successfully",
            details={"recipe_id": "recipe-123"}
        )
        
        response = SuccessMessageResponse(
            headers=MOCK_CORS_HEADERS,
            body=message
        )
        
        assert response.statusCode == 200
        assert isinstance(response.body, MessageResponse)
        assert response.body.message == "Recipe created successfully"
    
    def test_created_message_response(self):
        """Test CreatedMessageResponse convenience alias."""
        message = MessageResponse(
            message="User created successfully",
            details={"user_id": "user-456", "status": "active"}
        )
        
        response = CreatedMessageResponse(
            headers=MOCK_CORS_HEADERS,
            body=message
        )
        
        assert response.statusCode == 201
        assert isinstance(response.body, MessageResponse)
        assert response.body.details is not None
        assert response.body.details["user_id"] == "user-456"

class TestResponseSerialization:
    """Test cases for response serialization."""
    
    def test_response_json_serialization(self):
        """Test JSON serialization of responses."""
        message = MessageResponse(
            message="Test message",
            details={"key": "value"}
        )
        
        response = SuccessResponse[MessageResponse](
            headers=MOCK_CORS_HEADERS,
            body=message,
            metadata={"processed_at": "2024-01-15T10:00:00Z"}
        )
        
        # Test that model_dump_json() works
        json_str = response.model_dump_json()
        assert isinstance(json_str, str)
        
        # Test that model_dump() returns a dictionary
        data = response.model_dump()
        assert isinstance(data, dict)
        assert data["statusCode"] == 200
        assert data["body"]["message"] == "Test message"
    
    def test_collection_response_json_serialization(self):
        """Test JSON serialization of collection responses."""
        items = [{"id": "1", "name": "test1"}, {"id": "2", "name": "test2"}]
        collection = CollectionResponse[Dict[str, str]](
            items=items,
            total_count=2,
            page_size=10
        )
        
        # Test serialization
        data = collection.model_dump()
        assert data["items"] == items
        assert data["total_count"] == 2
        # Note: total_pages is a computed property and not included in serialization
        # But we can verify it works when accessed directly
        assert collection.total_pages == 1 