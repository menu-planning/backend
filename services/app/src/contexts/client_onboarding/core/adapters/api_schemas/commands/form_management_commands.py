"""
Form Management Command Schemas

Pydantic models for form setup, update, and management API requests.
Handles CRUD operations and webhook configuration for onboarding forms.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, HttpUrl, field_validator

from src.contexts.client_onboarding.core.services.typeform_url_parser import TypeformUrlParser

from src.contexts.client_onboarding.core.domain.models.onboarding_form import OnboardingFormStatus


class FormOperationType(str, Enum):
    """Types of form operations."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    ACTIVATE = "activate"
    PAUSE = "pause"
    COMPLETE = "complete"
    CONFIGURE_WEBHOOK = "configure_webhook"


class WebhookConfigurationType(str, Enum):
    """Types of webhook configurations."""
    CREATE = "create"
    UPDATE = "update"
    DELETE = "delete"
    VERIFY = "verify"


class CreateFormCommand(BaseModel):
    """Command for creating a new onboarding form."""
    
    typeform_url: str = Field(
        ..., 
        description="TypeForm URL or form ID (e.g., https://example.typeform.com/to/FORM_ID or just FORM_ID)",
        min_length=1,
        max_length=300
    )
    webhook_url: HttpUrl = Field(
        ...,
        description="URL to receive webhook notifications"
    )
    form_title: Optional[str] = Field(
        None,
        description="Optional custom title for the form",
        max_length=200
    )
    form_description: Optional[str] = Field(
        None,
        description="Optional description of the form purpose", 
        max_length=500
    )
    auto_activate: bool = Field(
        True,
        description="Whether to automatically activate the form after creation"
    )
    field_mappings: Optional[Dict[str, str]] = Field(
        None,
        description="Mapping of TypeForm field IDs to client identifier types"
    )
    
    @field_validator('typeform_url')
    @classmethod
    def validate_and_extract_typeform_id(cls, v: str) -> str:
        """Extract form ID from Typeform URL or validate form ID."""
        try:
            # Extract form ID from URL or validate direct form ID
            form_id = TypeformUrlParser.extract_form_id(v)
            # Validate the extracted/provided form ID format
            return TypeformUrlParser.validate_form_id_format(form_id)
        except ValueError as e:
            raise ValueError(f"Invalid Typeform URL or form ID: {e}")
    
    @property
    def typeform_id(self) -> str:
        """Get the extracted form ID for internal use."""
        return TypeformUrlParser.extract_form_id(self.typeform_url)


class UpdateFormCommand(BaseModel):
    """Command for updating an existing onboarding form."""
    
    form_id: int = Field(..., description="ID of the form to update", gt=0)
    webhook_url: Optional[HttpUrl] = Field(
        None,
        description="New webhook URL"
    )
    form_title: Optional[str] = Field(
        None,
        description="New form title",
        max_length=200
    )
    form_description: Optional[str] = Field(
        None,
        description="New form description", 
        max_length=500
    )
    status: Optional[OnboardingFormStatus] = Field(
        None,
        description="New form status"
    )
    field_mappings: Optional[Dict[str, str]] = Field(
        None,
        description="Updated field mappings"
    )
    
    @field_validator('form_id')
    @classmethod
    def validate_form_id(cls, v: int) -> int:
        """Validate form ID is positive."""
        if v <= 0:
            raise ValueError("Form ID must be positive")
        return v


class DeleteFormCommand(BaseModel):
    """Command for deleting an onboarding form."""
    
    form_id: int = Field(..., description="ID of the form to delete", gt=0)
    force_delete: bool = Field(
        False,
        description="Whether to force delete even if form has responses"
    )
    backup_responses: bool = Field(
        True,
        description="Whether to backup form responses before deletion"
    )
    
    @field_validator('form_id')
    @classmethod
    def validate_form_id(cls, v: int) -> int:
        """Validate form ID is positive."""
        if v <= 0:
            raise ValueError("Form ID must be positive")
        return v


class ConfigureWebhookCommand(BaseModel):
    """Command for configuring webhook settings."""
    
    form_id: int = Field(..., description="ID of the form", gt=0)
    operation: WebhookConfigurationType = Field(
        ...,
        description="Type of webhook operation to perform"
    )
    webhook_url: Optional[HttpUrl] = Field(
        None,
        description="Webhook URL for create/update operations"
    )
    webhook_secret: Optional[str] = Field(
        None,
        description="Secret for webhook signature verification",
        min_length=8,
        max_length=128
    )
    webhook_events: List[str] = Field(
        default=["form_response"],
        description="List of events to subscribe to"
    )
    retry_policy: Optional[Dict[str, Any]] = Field(
        None,
        description="Retry policy configuration for webhook delivery"
    )
    
    @field_validator('form_id')
    @classmethod
    def validate_form_id(cls, v: int) -> int:
        """Validate form ID is positive."""
        if v <= 0:
            raise ValueError("Form ID must be positive")
        return v
    
    @field_validator('webhook_events')
    @classmethod
    def validate_webhook_events(cls, v: List[str]) -> List[str]:
        """Validate webhook events list."""
        if not v:
            raise ValueError("At least one webhook event must be specified")
        valid_events = ["form_response", "form_complete", "form_start"]
        for event in v:
            if event not in valid_events:
                raise ValueError(f"Invalid webhook event: {event}")
        return v


class FormStatusCommand(BaseModel):
    """Command for changing form status."""
    
    form_id: int = Field(..., description="ID of the form", gt=0)
    new_status: OnboardingFormStatus = Field(
        ...,
        description="New status to set for the form"
    )
    reason: Optional[str] = Field(
        None,
        description="Reason for status change",
        max_length=500
    )
    
    @field_validator('form_id')
    @classmethod
    def validate_form_id(cls, v: int) -> int:
        """Validate form ID is positive."""
        if v <= 0:
            raise ValueError("Form ID must be positive")
        return v


class BulkFormOperationCommand(BaseModel):
    """Command for performing bulk operations on multiple forms."""
    
    form_ids: List[int] = Field(
        ...,
        description="List of form IDs to operate on",
        min_length=1,
        max_length=100
    )
    operation: FormOperationType = Field(
        ...,
        description="Operation to perform on all forms"
    )
    operation_params: Optional[Dict[str, Any]] = Field(
        None,
        description="Parameters specific to the operation"
    )
    
    @field_validator('form_ids')
    @classmethod
    def validate_form_ids(cls, v: List[int]) -> List[int]:
        """Validate all form IDs are positive and unique."""
        if not v:
            raise ValueError("At least one form ID must be provided")
        if len(set(v)) != len(v):
            raise ValueError("Form IDs must be unique")
        for form_id in v:
            if form_id <= 0:
                raise ValueError("All form IDs must be positive")
        return v


class FormManagementResponse(BaseModel):
    """Response for form management operations."""
    
    success: bool = Field(..., description="Whether the operation succeeded")
    operation: FormOperationType = Field(..., description="Operation that was performed")
    form_id: Optional[int] = Field(None, description="ID of the affected form")
    message: str = Field(..., description="Human-readable result message")
    
    # Operation results
    created_form_id: Optional[int] = Field(None, description="ID of newly created form")
    updated_fields: List[str] = Field(default=[], description="Fields that were updated")
    webhook_status: Optional[str] = Field(None, description="Webhook configuration status")
    
    # Metadata
    operation_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the operation was performed"
    )
    execution_time_ms: Optional[int] = Field(
        None,
        description="Operation execution time in milliseconds"
    )
    
    # Error information
    error_code: Optional[str] = Field(None, description="Error code if operation failed")
    error_details: Optional[Dict[str, Any]] = Field(None, description="Detailed error information")
    warnings: List[str] = Field(default=[], description="Non-fatal warnings from the operation")


class BulkFormOperationResponse(BaseModel):
    """Response for bulk form operations."""
    
    overall_success: bool = Field(..., description="Whether all operations succeeded")
    operation: FormOperationType = Field(..., description="Operation that was performed")
    total_forms: int = Field(..., description="Total number of forms processed", ge=0)
    successful_operations: int = Field(..., description="Number of successful operations", ge=0)
    failed_operations: int = Field(..., description="Number of failed operations", ge=0)
    
    # Detailed results
    results: List[FormManagementResponse] = Field(
        default=[],
        description="Individual operation results"
    )
    
    # Summary information
    operation_timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="When the bulk operation was started"
    )
    total_execution_time_ms: Optional[int] = Field(
        None,
        description="Total execution time for all operations in milliseconds"
    )
    
    @field_validator('successful_operations', 'failed_operations')
    @classmethod
    def validate_operation_counts(cls, v: int, info) -> int:
        """Ensure operation counts are non-negative."""
        if v < 0:
            raise ValueError("Operation counts cannot be negative")
        return v 