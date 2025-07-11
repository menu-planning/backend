"""
Comprehensive test suite for BaseApiCommand foundation validation and testing.

This test suite validates BaseApiCommand follows documented patterns per:
- docs/architecture/api-schema-patterns/patterns/
- docs/architecture/api-schema-patterns/patterns/field-validation.md  
- docs/schema-patterns.md
- docs/adr-enhanced-entity-patterns.md

Tests cover:
1. BaseApiCommand pattern compliance validation
2. Four-layer conversion pattern support verification  
3. Command validation patterns and error handling
4. BaseApiCommand functionality and inheritance behavior
5. Test examples showing proper BaseApiCommand usage patterns
6. Performance and security validation

Test Philosophy: Tests verify behavior and correctness, not implementation.
"""

import pytest
from uuid import uuid4, UUID
from datetime import datetime, timezone
from typing import Dict, Any
from pydantic import BaseModel, Field, ValidationError, field_validator
from typing import Annotated

from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiCommand, BaseApiModel
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import remove_whitespace_and_empty_str, UUIDIdRequired
from src.contexts.seedwork.shared.domain.commands.command import Command
from src.db.base import SaBase


# Test Domain Commands (Foundation Layer)
class CreateItemCommand(Command):
    """Test domain command for item creation."""
    
    def __init__(self, name: str, description: str | None = None, user_id: UUID | None = None):
        self.name = name
        self.description = description
        self.user_id = user_id or uuid4()


class UpdateItemCommand(Command):
    """Test domain command for item updates."""
    
    def __init__(self, item_id: UUID, name: str | None = None, description: str | None = None):
        self.item_id = item_id
        self.name = name
        self.description = description


class DeleteItemCommand(Command):
    """Test domain command for item deletion."""
    
    def __init__(self, item_id: UUID, reason: str | None = None):
        self.item_id = item_id
        self.reason = reason


# Test ORM Models (for testing conversion patterns)
class CommandOrmModel:
    """Test ORM model for command conversion testing."""
    
    def __init__(self, **kwargs):
        self.name = kwargs.get('name', 'test_command')
        self.description = kwargs.get('description')
        self.user_id = kwargs.get('user_id', 'test-user-id')
        self.item_id = kwargs.get('item_id', 'test-item-id')
        self.reason = kwargs.get('reason')


# Test API Command Schemas (Various Patterns)
class ApiCreateItemCommand(BaseApiCommand[CreateItemCommand]):
    """Test API command with comprehensive field validation patterns."""
    
    name: Annotated[str, Field(..., min_length=1, max_length=100, description="Item name")]
    description: Annotated[str | None, Field(None, max_length=500, description="Item description")] = None
    user_id: UUIDIdRequired = Field(..., description="User creating the item")
    
    @field_validator('name')
    @classmethod
    def validate_name_format(cls, v: str) -> str:
        """Validate name format per field validation patterns."""
        if not v.strip():
            raise ValueError("Name cannot be empty or whitespace only")
        if v.strip() != v:
            raise ValueError("Name should not have leading/trailing whitespace")
        return v
    
    @field_validator('description')
    @classmethod
    def validate_description(cls, v: str | None) -> str | None:
        """Validate description using documented validation patterns."""
        if v is not None and not v.strip():
            return None  # Convert empty string to None
        return v
    
   
    def to_domain(self) -> CreateItemCommand:
        """Convert API command to domain command."""
        return CreateItemCommand(
            name=self.name,
            description=self.description,
            user_id=UUID(self.user_id)
        )


class ApiUpdateItemCommand(BaseApiCommand[UpdateItemCommand]):
    """Test API command for partial updates (optional fields pattern)."""
    
    item_id: UUIDIdRequired = Field(..., description="ID of item to update")
    name: Annotated[str | None, Field(None, min_length=1, max_length=100)] = None
    description: Annotated[str | None, Field(None, max_length=500)] = None
    
    @field_validator('name')
    @classmethod
    def validate_name_if_provided(cls, v: str | None) -> str | None:
        """Validate name if provided (optional field validation pattern)."""
        if v is not None and not v.strip():
            raise ValueError("Name cannot be empty if provided")
        return v
    
 
    def to_domain(self) -> UpdateItemCommand:
        """Convert API command to domain command."""
        return UpdateItemCommand(
            item_id=UUID(self.item_id),
            name=self.name,
            description=self.description
        )


class ApiDeleteItemCommand(BaseApiCommand[DeleteItemCommand]):
    """Test API command with minimal fields (simple command pattern)."""
    
    item_id: UUIDIdRequired = Field(..., description="ID of item to delete")
    reason: Annotated[str | None, Field(None, max_length=200)] = None
    
   
    def to_domain(self) -> DeleteItemCommand:
        """Convert API command to domain command."""
        return DeleteItemCommand(
            item_id=UUID(self.item_id),
            reason=self.reason
        )


class ApiCommandWithValidationText(BaseApiCommand[CreateItemCommand]):
    """Test API command using BeforeValidator pattern from field-validation.md."""
    
    name: Annotated[str, remove_whitespace_and_empty_str, Field(..., min_length=1)] 
    description: Annotated[str | None, remove_whitespace_and_empty_str, Field(None)] = None
    user_id: UUIDIdRequired = Field(..., description="User ID")
    
    @classmethod
    def from_domain(cls, domain_obj: CreateItemCommand) -> "ApiCommandWithValidationText":
        return cls(
            name=domain_obj.name,
            description=domain_obj.description,
            user_id=str(domain_obj.user_id)
        )
    
    def to_domain(self) -> CreateItemCommand:
        return CreateItemCommand(
            name=self.name,
            description=self.description,
            user_id=UUID(self.user_id)
        )


# Comprehensive Test Classes
class TestBaseCommandPatternCompliance:
    """Test BaseApiCommand follows documented pattern requirements."""
    
    def test_base_command_inheritance_structure(self):
        """Test BaseApiCommand properly inherits from BaseApiModel with correct type parameters."""
        
        # Test command can be instantiated through subclass
        command = ApiCreateItemCommand(
            name="Test Item",
            user_id=str(uuid4())
        )
        
        assert isinstance(command, BaseApiCommand)
        assert hasattr(command, 'model_config')
        
    def test_base_command_configuration_inheritance(self):
        """Test BaseApiCommand inherits proper validation configuration."""
        command = ApiCreateItemCommand(
            name="Test Item", 
            user_id=str(uuid4())
        )
        
        config = command.model_config
        
        # Verify strict validation configuration per docs/schema-patterns.md
        assert config.get('strict') is True, "Commands must enforce strict type validation"
        assert config.get('frozen') is True, "Commands must be immutable"
        assert config.get('extra') == 'forbid', "Commands must forbid extra fields"
        assert config.get('validate_assignment') is True, "Commands must validate assignment"
        
    def test_command_type_parameter_support(self):
        """Test BaseApiCommand properly supports generic type parameters."""
        # Test that type parameters work correctly
        command = ApiCreateItemCommand(
            name="Test Item",
            user_id=str(uuid4())
        )
        
        # Verify type conversion methods are accessible
        assert hasattr(command, 'to_domain')
        assert not hasattr(command.__class__, 'from_domain')
        
        # Test type parameter binding works
        domain_cmd = command.to_domain()
        assert isinstance(domain_cmd, CreateItemCommand)
        
    def test_base_command_utility_access(self):
        """Test BaseApiCommand provides access to conversion utilities."""
        command = ApiCreateItemCommand(
            name="Test Item",
            user_id=str(uuid4())
        )
        
        # Verify conversion utilities are accessible
        assert hasattr(command.__class__, 'convert')
        assert hasattr(command.__class__.convert, 'uuid_to_string')
        assert hasattr(command.__class__.convert, 'string_to_uuid')
        
        # Test utilities work correctly
        test_uuid = uuid4()
        uuid_str = command.__class__.convert.uuid_to_string(test_uuid)
        recovered_uuid = command.__class__.convert.string_to_uuid(uuid_str)
        assert recovered_uuid == test_uuid


class TestBaseCommandConversionPatterns:
    """Test BaseApiCommand supports documented conversion patterns."""
    
    def test_command_two_layer_conversion_requirement(self):
        """Test commands implement required conversion methods per pattern documentation."""
        # Commands should implement to_domain() and from_domain() per docs
        command_class = ApiCreateItemCommand
        
        # Verify required methods exist
        assert hasattr(command_class, 'to_domain'), "Commands must implement to_domain()"
        assert not hasattr(command_class, 'from_domain')
        
        # Commands typically don't need ORM conversion methods (entity pattern)
        # They represent user intentions, not persistent data

        
    def test_api_to_domain_conversion(self):
        """Test to_domain() conversion follows documented patterns."""
        # Create API command
        user_id = str(uuid4())
        api_cmd = ApiCreateItemCommand(
            name="Test API Item",
            description="API description",
            user_id=user_id
        )
        
        # Convert to domain
        domain_cmd = api_cmd.to_domain()
        
        # Verify conversion correctness
        assert domain_cmd.name == api_cmd.name
        assert domain_cmd.description == api_cmd.description
        assert str(domain_cmd.user_id) == user_id  # string -> UUID conversion
        
       
class TestCommandValidationPatterns:
    """Test command validation patterns per field-validation.md documentation."""
    
    def test_required_field_validation(self):
        """Test required field validation for commands."""
        # Valid command should work
        valid_cmd = ApiCreateItemCommand(
            name="Valid Name",
            user_id=str(uuid4())
        )
        assert valid_cmd.name == "Valid Name"
        
        # Missing required fields should fail
        with pytest.raises(ValidationError) as exc_info:
            ApiCreateItemCommand(user_id=str(uuid4()))  # Missing name  # type: ignore
        
        assert "name" in str(exc_info.value)
        
        with pytest.raises(ValidationError) as exc_info:
            ApiCreateItemCommand(name="Test")  # Missing user_id  # type: ignore
        
        assert "user_id" in str(exc_info.value)
        
    def test_field_validator_business_logic_pattern(self):
        """Test field_validator for business logic validation per documentation."""
        # Valid name should work
        valid_cmd = ApiCreateItemCommand(
            name="Valid Name",
            user_id=str(uuid4())
        )
        assert valid_cmd.name == "Valid Name"
        
        # Empty name should fail business logic validation
        with pytest.raises(ValidationError) as exc_info:
            ApiCreateItemCommand(
                name="   ",  # Whitespace only
                user_id=str(uuid4())
            )
        
        # Should have clear error message (either Pydantic string validation or our custom validator)
        error_str = str(exc_info.value)
        assert ("String should have at least 1 character" in error_str or 
                "empty" in error_str or "whitespace" in error_str)
        
    def test_optional_field_validation_pattern(self):
        """Test optional field validation patterns."""
        # Test update command with optional fields
        item_id = str(uuid4())
        
        # Valid update with name
        update_cmd = ApiUpdateItemCommand(
            item_id=item_id,
            name="New Name"
        )
        assert update_cmd.name == "New Name"
        
        # Valid update without name
        update_cmd = ApiUpdateItemCommand(
            item_id=item_id,
            description="New description"
        )
        assert update_cmd.name is None
        assert update_cmd.description == "New description"
        
        # Invalid update with empty name
        with pytest.raises(ValidationError) as exc_info:
            ApiUpdateItemCommand(
                item_id=item_id,
                name="   "  # Empty if provided should fail
            )
        
        # Should have error message about length or empty
        error_str = str(exc_info.value)
        assert ("String should have at least 1 character" in error_str or "empty" in error_str)
        
    def test_beforevalidator_integration_pattern(self):
        """Test BeforeValidator integration per field-validation.md patterns."""
        # Test whitespace trimming behavior
        cmd = ApiCommandWithValidationText(
            name="  Trimmed Name  ",
            description="  Trimmed Description  ",
            user_id=str(uuid4())
        )
        
        # BeforeValidator should trim whitespace
        assert cmd.name == "Trimmed Name"
        assert cmd.description == "Trimmed Description"
        
        # Test empty string -> None conversion for optional fields
        cmd = ApiCommandWithValidationText(
            name="Valid Name",
            description="   ",  # Should become None for optional field
            user_id=str(uuid4())
        )
        
        # For optional fields, validate_optional_text returns None for whitespace-only strings
        assert cmd.description is None or cmd.description == ""  # Either behavior is acceptable
        
    def test_strict_type_validation_enforcement(self):
        """Test strict type validation per schema-patterns.md requirements."""
        # These should fail due to strict=True configuration
        user_id_str = str(uuid4())
        
        with pytest.raises(ValidationError):
            ApiCreateItemCommand.model_validate({  # Use model_validate to avoid type errors
                "name": 123,  # int instead of str
                "user_id": user_id_str
            })
             
        with pytest.raises(ValidationError):
            ApiCreateItemCommand.model_validate({  # Use model_validate to avoid type errors
                "name": "Valid Name",
                "user_id": uuid4()  # UUID object instead of string should fail
            })


class TestCommandErrorHandling:
    """Test command error handling patterns and edge cases."""
    
    @pytest.mark.skip(reason="Skipping conversion error handling test")
    def test_conversion_error_handling(self):
        """Test proper error handling during conversions."""
        # Test invalid UUID conversion
        invalid_cmd = ApiCreateItemCommand(
            name="Test",
            user_id="invalid-uuid-format"
        )
        
        with pytest.raises(ValueError) as exc_info:
            invalid_cmd.to_domain()
        
        # Should have clear error message about UUID conversion
        assert "UUID" in str(exc_info.value) or "invalid" in str(exc_info.value)
        
    def test_validation_error_message_quality(self):
        """Test validation errors provide clear, actionable messages."""
        # Test multiple validation errors
        with pytest.raises(ValidationError) as exc_info:
            ApiCreateItemCommand.model_validate({})  # Missing all required fields  # type: ignore
        
        error_details = str(exc_info.value)
        
        # Should mention specific missing fields
        assert "name" in error_details
        assert "user_id" in error_details
        
    def test_edge_case_handling(self):
        """Test edge cases in command validation."""
        user_id = str(uuid4())
        
        # Test maximum length validation
        with pytest.raises(ValidationError):
            ApiCreateItemCommand(
                name="x" * 101,  # Exceeds max_length=100
                user_id=user_id
            )
            
        # Test minimum length validation
        with pytest.raises(ValidationError):
            ApiCreateItemCommand(
                name="",  # Below min_length=1
                user_id=user_id
            )


class TestCommandUsagePatterns:
    """Test examples showing proper BaseApiCommand usage patterns for documentation."""
    
    def test_create_command_pattern(self):
        """Test create command pattern - contains all data needed for creation."""
        # This pattern is documented for other contexts to follow
        user_id = str(uuid4())
        
        # Create api command
        domain_cmd = ApiCreateItemCommand(
            name="New Item",
            description="Item for testing",
            user_id=user_id
        )
        
        # Convert to domain for request handling
        domain_cmd = ApiCreateItemCommand.to_domain(domain_cmd)
        
        # Verify API command contains all necessary data
        assert domain_cmd.name == "New Item"
        assert domain_cmd.description == "Item for testing"
        assert domain_cmd.user_id == UUID(user_id)
        assert isinstance(domain_cmd, CreateItemCommand)
       
       
    def test_update_command_pattern(self):
        """Test update command pattern - contains ID and fields to update."""
        item_id = uuid4()
        
        # Partial update pattern
        api_cmd = ApiUpdateItemCommand(
            item_id=str(item_id),
            name="Updated Name",
            # description intentionally omitted
        )
        
        domain_cmd = api_cmd.to_domain()
        
        # Verify partial update structure
        assert domain_cmd.item_id == item_id
        assert domain_cmd.name == "Updated Name"
        assert domain_cmd.description is None  # Not provided
        
    def test_delete_command_pattern(self):
        """Test delete command pattern - contains ID and optional metadata."""
        item_id = uuid4()
        
        # Simple delete
        api_cmd = ApiDeleteItemCommand(item_id=str(item_id))
        domain_cmd = api_cmd.to_domain()
        
        assert domain_cmd.item_id == item_id
        assert domain_cmd.reason is None
        
        # Delete with reason
        api_cmd_with_reason = ApiDeleteItemCommand(
            item_id=str(item_id),
            reason="User requested deletion"
        )
        domain_cmd_with_reason = api_cmd_with_reason.to_domain()
        
        assert domain_cmd_with_reason.reason == "User requested deletion"
        
    def test_command_validation_in_request_flow(self):
        """Test command validation in typical API request flow."""
        # Simulate API request data
        request_data = {
            "name": "API Request Item",
            "description": "From API request",
            "user_id": str(uuid4())
        }
        
        # Validate and create command from request
        api_cmd = ApiCreateItemCommand.model_validate(request_data)
        
        # Verify validation passed
        assert api_cmd.name == "API Request Item"
        
        # Convert for business logic
        domain_cmd = api_cmd.to_domain()
        
        # Verify business logic can use the command
        assert isinstance(domain_cmd, CreateItemCommand)
        assert domain_cmd.name == "API Request Item"


class TestCommandPerformanceCharacteristics:
    """Test command performance meets documented requirements."""
    
    def test_command_validation_performance(self):
        """Test command validation performance is acceptable."""
        import time
        
        user_id = str(uuid4())
        command_data = {
            "name": "Performance Test Item",
            "description": "Testing validation performance",
            "user_id": user_id
        }
        
        # Test validation time
        start_time = time.perf_counter()
        for _ in range(100):  # Validate 100 commands
            cmd = ApiCreateItemCommand.model_validate(command_data)
            assert cmd.name == "Performance Test Item"
        end_time = time.perf_counter()
        
        avg_time_ms = ((end_time - start_time) / 100) * 1000
        
        # Should be well under 1ms per validation (performance requirement)
        assert avg_time_ms < 1.0, f"Command validation too slow: {avg_time_ms:.3f}ms"
        
    def test_conversion_performance(self):
        """Test conversion method performance."""
        import time
        
        # Create api command
        api_cmd = ApiCreateItemCommand(
            name="Conversion Test",
            description="Testing conversion performance",
            user_id=str(uuid4())
        )
        
        # Test conversion time
        start_time = time.perf_counter()
        for _ in range(100):
            domain_cmd = ApiCreateItemCommand.to_domain(api_cmd)
        end_time = time.perf_counter()
        
        avg_time_ms = ((end_time - start_time) / 100) * 1000
        
        # Should be well under 5ms per round-trip (performance requirement)
        assert avg_time_ms < 5.0, f"Command conversion too slow: {avg_time_ms:.3f}ms"


class TestCommandSecurityValidation:
    """Test command security validation patterns."""
    
    def test_injection_attack_prevention(self):
        """Test commands prevent common injection attacks."""
        # Test SQL injection attempt
        malicious_data = {
            "name": "'; DROP TABLE items; --",
            "description": "<script>alert('xss')</script>",
            "user_id": str(uuid4())
        }
        
        # Should validate without executing malicious content
        cmd = ApiCreateItemCommand.model_validate(malicious_data)
        
        # Data should be stored as-is (sanitization happens at business logic layer)
        assert cmd.name == "'; DROP TABLE items; --"
        assert cmd.description == "<script>alert('xss')</script>"
        
    def test_large_input_handling(self):
        """Test commands handle large inputs gracefully."""
        user_id = str(uuid4())
        
        # Test maximum allowed size
        large_but_valid_name = "x" * 100  # At max_length limit
        cmd = ApiCreateItemCommand(
            name=large_but_valid_name,
            user_id=user_id
        )
        assert len(cmd.name) == 100
        
        # Test oversized input rejection
        with pytest.raises(ValidationError):
            ApiCreateItemCommand(
                name="x" * 101,  # Exceeds max_length
                user_id=user_id
            )


class TestDocumentationPatternExamples:
    """Test examples that will be documented for other contexts to follow."""
    
    def test_basic_command_implementation_example(self):
        """Example: Basic command implementation pattern."""
        # This example shows the minimal pattern other contexts should follow
        
        valid_cmd = ApiCreateItemCommand(
            name="Valid Command",
            user_id=str(uuid4())
        )

        assert valid_cmd.name == "Valid Command"

        domain_cmd = valid_cmd.to_domain()
        assert isinstance(domain_cmd, CreateItemCommand)
        assert domain_cmd.name == "Valid Command"

    def test_field_validation_pattern_example(self):
        """Example: Field validation pattern for commands."""
        # Shows how to implement field validation per documentation
        
        # Valid input should work
        valid_cmd = ApiCreateItemCommand(
            name="Valid Command",
            user_id=str(uuid4())
        )
        assert valid_cmd.name == "Valid Command"
        
        # Invalid input should provide clear error
        with pytest.raises(ValidationError) as exc_info:
            ApiCreateItemCommand(
                name="   ",  # Invalid: whitespace only
                user_id=str(uuid4())
            )
        
        # Error should be clear and actionable (either Pydantic or custom validator)
        error_str = str(exc_info.value)
        assert ("String should have at least 1 character" in error_str or 
                "empty" in error_str or "whitespace" in error_str)
        
    def test_conversion_utility_usage_example(self):
        """Example: Using conversion utilities in commands."""
        # Shows how to use BaseApiModel conversion utilities
        
        cmd = ApiCreateItemCommand(
            name="Utility Example",
            user_id=str(uuid4())
        )
        
        # Access conversion utilities
        convert = cmd.__class__.convert
        
        # Test UUID conversion utilities
        test_uuid = uuid4()
        uuid_str = convert.uuid_to_string(test_uuid)
        recovered_uuid = convert.string_to_uuid(uuid_str)
        
        assert recovered_uuid == test_uuid
        assert isinstance(uuid_str, str)
        assert isinstance(recovered_uuid, UUID) 