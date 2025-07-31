"""
TypeForm Webhook Payload Validation Schemas

Pydantic models for TypeForm webhook signature validation and payload structure.
Handles webhook security, event processing, and data validation for TypeForm form responses.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum
from hashlib import sha256
import hmac

from pydantic import BaseModel, Field, field_validator, model_validator, ConfigDict


class WebhookEventType(str, Enum):
    """TypeForm webhook event types."""
    FORM_RESPONSE = "form_response"


class FieldType(str, Enum):
    """TypeForm field types for response validation."""
    SHORT_TEXT = "short_text"
    LONG_TEXT = "long_text"
    MULTIPLE_CHOICE = "multiple_choice"
    PICTURE_CHOICE = "picture_choice"
    YES_NO = "yes_no"
    DROPDOWN = "dropdown"
    NUMBER = "number"
    RATING = "rating"
    EMAIL = "email"
    WEBSITE = "website"
    FILE_UPLOAD = "file_upload"
    DATE = "date"
    PHONE_NUMBER = "phone_number"
    PAYMENT = "payment"
    LEGAL = "legal"
    OPINION_SCALE = "opinion_scale"


class WebhookSignatureValidation(BaseModel):
    """Webhook signature validation data for security verification."""
    
    signature: str = Field(..., description="TypeForm signature header (sha256=...)")
    payload: str = Field(..., description="Raw JSON payload for signature verification")
    secret: str = Field(..., description="Webhook secret for verification")
    
    @field_validator('signature')
    def validate_signature_format(cls, v: str) -> str:
        """Validate TypeForm signature format."""
        if not v or not v.startswith('sha256='):
            raise ValueError("Invalid TypeForm signature format - must start with 'sha256='")
        return v
    
    @model_validator(mode='after')
    @staticmethod
    def verify_signature(values: 'WebhookSignatureValidation') -> 'WebhookSignatureValidation':
        """Verify the webhook signature against the payload."""
        expected_signature = WebhookSignatureValidation._generate_signature(values.payload, values.secret)
        provided_signature = values.signature
        
        if not hmac.compare_digest(expected_signature, provided_signature):
            raise ValueError("Webhook signature verification failed")
        
        return values
    
    @staticmethod
    def _generate_signature(payload: str, secret: str) -> str:
        """Generate expected signature for payload."""
        signature = hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            sha256
        ).hexdigest()
        return f"sha256={signature}"


class WebhookHeaders(BaseModel):
    """Expected webhook headers for processing and validation."""
    
    typeform_signature: str = Field(..., alias="Typeform-Signature", description="TypeForm signature header")
    content_type: str = Field(default="application/json", alias="Content-Type", description="Content type")
    user_agent: Optional[str] = Field(None, alias="User-Agent", description="User agent")
    typeform_event_id: Optional[str] = Field(None, alias="Typeform-Event-Id", description="Unique event ID")
    
    model_config = ConfigDict(
        populate_by_name=True,
        str_strip_whitespace=True
    )
    
    @field_validator('content_type')
    def validate_content_type(cls, v: str) -> str:
        """Validate content type is JSON."""
        if v != "application/json":
            raise ValueError("Content-Type must be application/json")
        return v


class FieldChoice(BaseModel):
    """Choice option for multiple choice fields."""
    
    id: str = Field(..., description="Choice ID")
    label: Optional[str] = Field(None, description="Choice label")
    ref: Optional[str] = Field(None, description="Choice reference")


class FieldDefinition(BaseModel):
    """Field definition from TypeForm webhook payload."""
    
    id: str = Field(..., description="Field ID")
    title: str = Field(..., description="Field title/question")
    type: FieldType = Field(..., description="Field type")
    ref: Optional[str] = Field(None, description="Field reference")
    allow_multiple_selections: Optional[bool] = Field(None, description="Multiple selections allowed")
    allow_other_choice: Optional[bool] = Field(None, description="Other choice allowed")
    choices: Optional[List[FieldChoice]] = Field(None, description="Available choices")
    properties: Optional[Dict[str, Any]] = Field(None, description="Additional field properties")


class FieldAnswer(BaseModel):
    """Answer to a form field with comprehensive type support."""
    
    field: FieldDefinition = Field(..., description="Field definition")
    type: FieldType = Field(..., description="Answer type")
    
    # Answer value fields based on type
    text: Optional[str] = Field(None, description="Text answer")
    email: Optional[str] = Field(None, description="Email answer")
    url: Optional[str] = Field(None, description="URL answer")
    file_url: Optional[str] = Field(None, description="File URL")
    number: Optional[Union[int, float]] = Field(None, description="Number answer")
    boolean: Optional[bool] = Field(None, description="Boolean answer")
    choice: Optional[FieldChoice] = Field(None, description="Single choice answer")
    choices: Optional[List[FieldChoice]] = Field(None, description="Multiple choice answers")
    date: Optional[str] = Field(None, description="Date answer (ISO format)")
    phone_number: Optional[str] = Field(None, description="Phone number")
    payment: Optional[Dict[str, Any]] = Field(None, description="Payment data")
    
    @field_validator('email')
    def validate_email(cls, v: Optional[str]) -> Optional[str]:
        """Basic email validation."""
        if v and '@' not in v:
            raise ValueError("Invalid email format")
        return v
    
    @field_validator('date')
    def validate_date_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate date is in ISO format."""
        if v:
            try:
                datetime.fromisoformat(v.replace('Z', '+00:00'))
            except ValueError:
                raise ValueError("Date must be in ISO format")
        return v


class FormDefinition(BaseModel):
    """Form definition from webhook payload."""
    
    id: str = Field(..., description="Form ID")
    title: str = Field(..., description="Form title")
    fields: Optional[List[FieldDefinition]] = Field(None, description="Form fields")
    settings: Optional[Dict[str, Any]] = Field(None, description="Form settings")
    
    @field_validator('id')
    def validate_form_id(cls, v: str) -> str:
        """Validate form ID is not empty."""
        if not v or not v.strip():
            raise ValueError("Form ID cannot be empty")
        return v.strip()


class FormResponse(BaseModel):
    """Form response data from TypeForm webhook."""
    
    form_id: str = Field(..., description="Form ID")
    token: str = Field(..., description="Unique response token")
    landed_at: datetime = Field(..., description="When user started form")
    submitted_at: datetime = Field(..., description="When form was submitted")
    definition: Optional[FormDefinition] = Field(None, description="Form definition")
    answers: List[FieldAnswer] = Field(..., description="Field answers")
    calculated: Optional[Dict[str, Any]] = Field(None, description="Calculated values")
    variables: Optional[Dict[str, Any]] = Field(None, description="Hidden variables")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    @field_validator('landed_at', 'submitted_at', mode='before')
    def parse_datetime(cls, v: Union[str, datetime]) -> datetime:
        """Parse datetime strings to datetime objects."""
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v
    
    @field_validator('token')
    def validate_token(cls, v: str) -> str:
        """Validate response token is not empty."""
        if not v or not v.strip():
            raise ValueError("Response token cannot be empty")
        return v.strip()
    
    @model_validator(mode='after')
    @staticmethod
    def validate_submission_order(values: 'FormResponse') -> 'FormResponse':
        """Validate that submitted_at is after landed_at."""
        if values.submitted_at < values.landed_at:
            raise ValueError("Submission time cannot be before landing time")
        return values


class TypeFormWebhookPayload(BaseModel):
    """Complete TypeForm webhook payload with validation."""
    
    event_id: str = Field(..., description="Unique event ID")
    event_type: WebhookEventType = Field(..., description="Event type")
    form_response: FormResponse = Field(..., description="Form response data")
    
    @field_validator('event_type')
    def validate_event_type(cls, v: WebhookEventType) -> WebhookEventType:
        """Validate that we only process form_response events."""
        if v != WebhookEventType.FORM_RESPONSE:
            raise ValueError(f"Unsupported event type: {v}")
        return v
    
    @field_validator('event_id')
    def validate_event_id(cls, v: str) -> str:
        """Validate event ID is not empty."""
        if not v or not v.strip():
            raise ValueError("Event ID cannot be empty")
        return v.strip()


class WebhookValidationResult(BaseModel):
    """Result of comprehensive webhook validation."""
    
    is_valid: bool = Field(..., description="Overall validation result")
    signature_valid: bool = Field(..., description="Signature validation result")
    payload_valid: bool = Field(..., description="Payload structure validation result")
    form_exists: bool = Field(..., description="Whether form exists in our system")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    processing_hints: Dict[str, Any] = Field(default_factory=dict, description="Hints for processing")


class WebhookProcessingContext(BaseModel):
    """Context information for webhook processing."""
    
    webhook_id: Optional[str] = Field(None, description="Internal webhook configuration ID")
    form_id: Optional[int] = Field(None, description="Internal form ID")
    user_id: Optional[int] = Field(None, description="Form owner user ID")
    processing_timestamp: datetime = Field(default_factory=datetime.utcnow, description="Processing start time")
    source_ip: Optional[str] = Field(None, description="Source IP address")
    user_agent: Optional[str] = Field(None, description="User agent from headers") 