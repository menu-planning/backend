"""
Form Configuration API Schemas

Pydantic models for TypeForm configuration requests and responses.
Handles form setup, webhook configuration, and form status management.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, field_validator, ConfigDict

from ..models.onboarding_form import OnboardingFormStatus


class FormConfigurationRequest(BaseModel):
    """Request schema for configuring a new onboarding form."""
    
    typeform_id: str = Field(
        ..., 
        description="TypeForm form ID",
        min_length=1,
        max_length=100
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
    
    @field_validator('typeform_id')
    @classmethod
    def validate_typeform_id(cls, v):
        """Validate TypeForm ID format."""
        if not v or not v.strip():
            raise ValueError("TypeForm ID cannot be empty")
        return v.strip()


class FormConfigurationResponse(BaseModel):
    """Response schema for form configuration operations."""
    
    id: int = Field(..., description="Internal form ID")
    typeform_id: str = Field(..., description="TypeForm form ID")
    user_id: int = Field(..., description="Form owner ID")
    webhook_url: Optional[str] = Field(None, description="Configured webhook URL")
    webhook_id: Optional[str] = Field(None, description="TypeForm webhook ID")
    status: OnboardingFormStatus = Field(..., description="Form status")
    form_title: Optional[str] = Field(None, description="Form title")
    form_description: Optional[str] = Field(None, description="Form description")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    
    model_config = ConfigDict(from_attributes=True)


class FormConfigurationUpdate(BaseModel):
    """Schema for updating form configuration."""
    
    webhook_url: Optional[HttpUrl] = Field(
        None,
        description="New webhook URL"
    )
    form_title: Optional[str] = Field(
        None,
        description="Updated form title",
        max_length=200
    )
    form_description: Optional[str] = Field(
        None,
        description="Updated form description",
        max_length=500
    )
    status: Optional[OnboardingFormStatus] = Field(
        None,
        description="Updated form status"
    )


class FormListResponse(BaseModel):
    """Response schema for listing user forms."""
    
    forms: List[FormConfigurationResponse] = Field(
        ...,
        description="List of configured forms"
    )
    total_count: int = Field(..., description="Total number of forms")
    page: int = Field(..., description="Current page number")
    page_size: int = Field(..., description="Number of items per page")


class WebhookConfigurationRequest(BaseModel):
    """Request schema for webhook configuration."""
    
    form_id: int = Field(..., description="Internal form ID")
    webhook_url: HttpUrl = Field(..., description="Webhook endpoint URL")
    enabled: bool = Field(True, description="Whether webhook is enabled")


class WebhookConfigurationResponse(BaseModel):
    """Response schema for webhook configuration."""
    
    webhook_id: str = Field(..., description="TypeForm webhook ID")
    webhook_url: str = Field(..., description="Configured webhook URL")
    enabled: bool = Field(..., description="Webhook enabled status")
    created_at: datetime = Field(..., description="Webhook creation timestamp")
    form_id: int = Field(..., description="Associated form ID")


class FormValidationRequest(BaseModel):
    """Request schema for validating TypeForm access."""
    
    typeform_id: str = Field(
        ...,
        description="TypeForm ID to validate",
        min_length=1,
        max_length=100
    )
    
    @field_validator('typeform_id')
    @classmethod
    def validate_typeform_id(cls, v):
        """Validate TypeForm ID format."""
        if not v or not v.strip():
            raise ValueError("TypeForm ID cannot be empty")
        return v.strip()


class FormValidationResponse(BaseModel):
    """Response schema for form validation."""
    
    is_valid: bool = Field(..., description="Whether form is accessible")
    form_title: Optional[str] = Field(None, description="Form title from TypeForm")
    form_id: str = Field(..., description="Validated TypeForm ID")
    error_message: Optional[str] = Field(None, description="Error details if validation failed")
    permissions: Dict[str, bool] = Field(
        default_factory=dict,
        description="Available permissions for the form"
    )


class ErrorResponse(BaseModel):
    """Standard error response schema."""
    
    error: str = Field(..., description="Error type/code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[Dict[str, Any]] = Field(
        None,
        description="Additional error details"
    )
    timestamp: datetime = Field(
        default_factory=datetime.utcnow,
        description="Error timestamp"
    ) 