"""
Form Configuration API Schemas

Pydantic models for TypeForm configuration requests and responses.
Handles form setup, webhook configuration, and form status management.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime

from pydantic import BaseModel, Field, HttpUrl, field_validator, ConfigDict

from src.contexts.client_onboarding.core.domain.models.onboarding_form import OnboardingFormStatus
from src.contexts.client_onboarding.core.services.integrations.typeform.url_parser import TypeformUrlParser


class FormConfigurationRequest(BaseModel):
    """Request schema for configuring a new onboarding form."""
    
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


class FormConfigurationResponse(BaseModel):
    """Response schema for form configuration operations."""
    
    id: int = Field(..., description="Internal form ID")
    typeform_id: str = Field(..., description="TypeForm form ID")
    user_id: str = Field(..., description="Form owner ID")
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
    
    typeform_url: str = Field(
        ...,
        description="TypeForm URL or form ID to validate (e.g., https://example.typeform.com/to/FORM_ID or just FORM_ID)",
        min_length=1,
        max_length=300
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