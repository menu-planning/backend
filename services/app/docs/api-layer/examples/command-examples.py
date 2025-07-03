"""
Command Examples for API Layer Documentation

This module contains working examples of API command patterns used in the menu-planning application.
These examples demonstrate proper inheritance, validation, and conversion patterns.
"""

from typing import Optional
from uuid import UUID
from pydantic import Field, field_validator

from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import BaseApiCommand
from src.contexts.seedwork.shared.adapters.api_schemas.base_api_fields import UUIDId


# Example 1: Basic Command Pattern
class ApiCreateUser(BaseApiCommand):
    """
    Example command for creating a new user.
    
    This demonstrates the basic command pattern with required fields,
    validation, and domain conversion.
    """
    
    # Required fields
    user_id: UUIDId = Field(..., description="Unique identifier for the user")
    name: str = Field(..., min_length=1, max_length=100, description="User's full name")
    email: str = Field(..., description="User's email address")
    
    # Optional fields with defaults
    active: bool = Field(default=True, description="Whether the user is active")
    role: str = Field(default="user", description="User's role in the system")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """Validate email format."""
        if '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower()
    
    def to_domain(self) -> dict:
        """Convert API command to domain command.
        
        This method is required for all commands and handles the conversion
        from API-level data to domain-level command objects.
        """
        # In a real implementation, this would import and return the actual domain command
        # For documentation purposes, we'll return a dict representation
        return {
            "command_type": "CreateUser",
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "active": self.active,
            "role": self.role
        }


# Example 2: Update Command Pattern with Classmethod
class ApiUpdateUser(BaseApiCommand):
    """
    Example command for updating user information.
    
    This demonstrates the update command pattern with optional fields
    and the from_api_<entity> classmethod pattern.
    """
    
    # Required identifier
    user_id: UUIDId = Field(..., description="ID of the user to update")
    
    # Optional update fields
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Updated name")
    email: Optional[str] = Field(None, description="Updated email address")
    active: Optional[bool] = Field(None, description="Updated active status")
    role: Optional[str] = Field(None, description="Updated role")
    
    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        """Validate email format if provided."""
        if v is not None and '@' not in v:
            raise ValueError('Invalid email format')
        return v.lower() if v else v
    
    def to_domain(self) -> dict:
        """Convert API command to domain command."""
        return {
            "command_type": "UpdateUser",
            "user_id": self.user_id,
            "name": self.name,
            "email": self.email,
            "active": self.active,
            "role": self.role
        }
    
    @classmethod
    def from_api_user(cls, user_id: str, user_data: dict) -> "ApiUpdateUser":
        """Create update command from existing user data.
        
        This classmethod is useful for partial updates where you want to
        update only specific fields of an existing user.
        """
        return cls(
            user_id=user_id,
            name=user_data.get("name"),
            email=user_data.get("email"),
            active=user_data.get("active"),
            role=user_data.get("role")
        )


# Example 3: Complex Command with Nested Data
class ApiCreateMenu(BaseApiCommand):
    """
    Example command for creating a menu with nested meal data.
    
    This demonstrates handling complex nested data structures in commands.
    """
    
    menu_id: UUIDId = Field(..., description="Unique identifier for the menu")
    client_id: UUIDId = Field(..., description="Client who owns this menu")
    name: str = Field(..., min_length=1, max_length=200, description="Menu name")
    description: Optional[str] = Field(None, max_length=1000, description="Menu description")
    
    # Nested data structure
    meals: list[dict] = Field(default_factory=list, description="List of meals in the menu")
    
    @field_validator('meals')
    @classmethod
    def validate_meals(cls, v):
        """Validate meal data structure."""
        for meal in v:
            if not isinstance(meal, dict):
                raise ValueError('Each meal must be a dictionary')
            if 'meal_id' not in meal:
                raise ValueError('Each meal must have a meal_id')
        return v
    
    def to_domain(self) -> dict:
        """Convert API command to domain command."""
        return {
            "command_type": "CreateMenu",
            "menu_id": self.menu_id,
            "client_id": self.client_id,
            "name": self.name,
            "description": self.description,
            "meals": self.meals
        }


# Example 4: Delete Command Pattern
class ApiDeleteUser(BaseApiCommand):
    """
    Example command for deleting a user.
    
    This demonstrates the simple delete command pattern.
    """
    
    user_id: UUIDId = Field(..., description="ID of the user to delete")
    
    # Optional soft delete fields
    reason: Optional[str] = Field(None, max_length=500, description="Reason for deletion")
    hard_delete: bool = Field(default=False, description="Whether to permanently delete")
    
    def to_domain(self) -> dict:
        """Convert API command to domain command."""
        return {
            "command_type": "DeleteUser",
            "user_id": self.user_id,
            "reason": self.reason,
            "hard_delete": self.hard_delete
        }


# Example 5: Command with Business Logic Validation
class ApiTransferMeal(BaseApiCommand):
    """
    Example command for transferring a meal between menus.
    
    This demonstrates business logic validation in commands.
    """
    
    meal_id: UUIDId = Field(..., description="ID of the meal to transfer")
    source_menu_id: UUIDId = Field(..., description="Source menu ID")
    target_menu_id: UUIDId = Field(..., description="Target menu ID")
    
    # Business logic fields
    copy_mode: bool = Field(default=False, description="Whether to copy instead of move")
    preserve_timing: bool = Field(default=True, description="Whether to preserve meal timing")
    
    @field_validator('target_menu_id')
    @classmethod
    def validate_different_menus(cls, v, values):
        """Ensure source and target menus are different."""
        if 'source_menu_id' in values and v == values['source_menu_id']:
            raise ValueError('Source and target menus must be different')
        return v
    
    def to_domain(self) -> dict:
        """Convert API command to domain command."""
        return {
            "command_type": "TransferMeal",
            "meal_id": self.meal_id,
            "source_menu_id": self.source_menu_id,
            "target_menu_id": self.target_menu_id,
            "copy_mode": self.copy_mode,
            "preserve_timing": self.preserve_timing
        }


# Example 6: AWS Lambda Integration Example
def lambda_handler_example(event, context):
    """
    Example AWS Lambda handler showing command usage.
    
    This demonstrates how commands integrate with AWS Lambda events.
    """
    try:
        # Parse and validate command from Lambda event
        command_data = event.get('body', {})
        command_type = event.get('command_type', 'create_user')
        
        # Route to appropriate command based on type
        if command_type == 'create_user':
            api_command = ApiCreateUser.model_validate(command_data)
        elif command_type == 'update_user':
            api_command = ApiUpdateUser.model_validate(command_data)
        elif command_type == 'delete_user':
            api_command = ApiDeleteUser.model_validate(command_data)
        else:
            raise ValueError(f"Unknown command type: {command_type}")
        
        # Convert to domain command
        domain_command = api_command.to_domain()
        
        # Process through domain layer (in real implementation)
        # result = message_bus.handle(domain_command)
        result = {"success": True, "command": domain_command}
        
        return {
            "statusCode": 200,
            "body": {
                "success": True,
                "result": result
            }
        }
        
    except Exception as e:
        return {
            "statusCode": 400,
            "body": {
                "success": False,
                "error": str(e)
            }
        }


# Example 7: Command Testing Pattern
def test_command_validation():
    """
    Example test showing how to test command validation.
    
    This demonstrates testing patterns for API commands.
    """
    # Test valid command
    valid_data = {
        "user_id": "550e8400-e29b-41d4-a716-446655440000",
        "name": "John Doe",
        "email": "john@example.com"
    }
    
    command = ApiCreateUser.model_validate(valid_data)
    assert command.name == "John Doe"
    assert command.email == "john@example.com"
    assert command.active is True  # Default value
    
    # Test domain conversion
    domain_command = command.to_domain()
    assert domain_command["command_type"] == "CreateUser"
    assert domain_command["user_id"] == "550e8400-e29b-41d4-a716-446655440000"
    
    # Test validation errors
    try:
        ApiCreateUser.model_validate({
            "user_id": "invalid-uuid",
            "name": "",  # Too short
            "email": "invalid-email"  # Missing @
        })
        assert False, "Should have raised validation error"
    except Exception as e:
        assert "validation error" in str(e).lower()


if __name__ == "__main__":
    # Run example tests
    test_command_validation()
    print("All command examples working correctly!") 