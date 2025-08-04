"""
Webhook Payload API Schemas

Pydantic models for validating and processing TypeForm webhook payloads.
Handles form response data, event metadata, and client identification.
"""

from typing import Optional, List, Dict, Any, Union
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, field_validator, ConfigDict


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


class FieldChoice(BaseModel):
    """Choice option for multiple choice fields."""
    
    id: str = Field(..., description="Choice ID")
    label: Optional[str] = Field(None, description="Choice label")


class FieldDefinition(BaseModel):
    """Field definition from TypeForm."""
    
    id: str = Field(..., description="Field ID")
    title: str = Field(..., description="Field title/question")
    type: FieldType = Field(..., description="Field type")
    ref: Optional[str] = Field(None, description="Field reference")
    allow_multiple_selections: Optional[bool] = Field(None, description="Multiple selections allowed")
    allow_other_choice: Optional[bool] = Field(None, description="Other choice allowed")
    choices: Optional[List[FieldChoice]] = Field(None, description="Available choices")


class FieldAnswer(BaseModel):
    """Answer to a form field."""
    
    field: FieldDefinition = Field(..., description="Field definition")
    type: FieldType = Field(..., description="Answer type")
    text: Optional[str] = Field(None, description="Text answer")
    email: Optional[str] = Field(None, description="Email answer")
    url: Optional[str] = Field(None, description="URL answer")
    file_url: Optional[str] = Field(None, description="File URL")
    number: Optional[Union[int, float]] = Field(None, description="Number answer")
    boolean: Optional[bool] = Field(None, description="Boolean answer")
    choice: Optional[FieldChoice] = Field(None, description="Choice answer")
    choices: Optional[List[FieldChoice]] = Field(None, description="Multiple choice answers")
    date: Optional[str] = Field(None, description="Date answer (ISO format)")
    phone_number: Optional[str] = Field(None, description="Phone number")
    payment: Optional[Dict[str, Any]] = Field(None, description="Payment data")


class FormDefinition(BaseModel):
    """Form definition from webhook payload."""
    
    id: str = Field(..., description="Form ID")
    title: str = Field(..., description="Form title")
    fields: Optional[List[FieldDefinition]] = Field(None, description="Form fields")


class FormResponse(BaseModel):
    """Form response data from webhook."""
    
    form_id: str = Field(..., description="Form ID")
    token: str = Field(..., description="Response token")
    landed_at: datetime = Field(..., description="When user started form")
    submitted_at: datetime = Field(..., description="When form was submitted")
    definition: Optional[FormDefinition] = Field(None, description="Form definition")
    answers: List[FieldAnswer] = Field(..., description="Field answers")
    calculated: Optional[Dict[str, Any]] = Field(None, description="Calculated values")
    variables: Optional[Dict[str, Any]] = Field(None, description="Hidden variables")
    
    @field_validator('landed_at', 'submitted_at', mode='before')
    @classmethod
    def parse_datetime(cls, v):
        """Parse datetime strings to datetime objects."""
        if isinstance(v, str):
            return datetime.fromisoformat(v.replace('Z', '+00:00'))
        return v


class WebhookPayload(BaseModel):
    """Complete TypeForm webhook payload."""
    
    event_id: str = Field(..., description="Unique event ID")
    event_type: WebhookEventType = Field(..., description="Event type")
    form_response: FormResponse = Field(..., description="Form response data")
    
    @field_validator('event_type')
    @classmethod
    def validate_event_type(cls, v):
        """Validate that we only process form_response events."""
        if v != WebhookEventType.FORM_RESPONSE:
            raise ValueError(f"Unsupported event type: {v}")
        return v


class ProcessedFieldResponse(BaseModel):
    """Processed field response for storage."""
    
    field_id: str = Field(..., description="Field ID")
    field_ref: Optional[str] = Field(None, description="Field reference")
    field_title: str = Field(..., description="Field question/title")
    field_type: FieldType = Field(..., description="Field type")
    answer_value: Any = Field(..., description="Processed answer value")
    answer_text: Optional[str] = Field(None, description="Text representation of answer")


class ClientIdentifiers(BaseModel):
    """Client identification data extracted from responses."""
    
    email: Optional[str] = Field(None, description="Client email address")
    name: Optional[str] = Field(None, description="Client name")
    company: Optional[str] = Field(None, description="Company name")
    phone: Optional[str] = Field(None, description="Phone number")
    custom_identifiers: Dict[str, str] = Field(
        default_factory=dict,
        description="Custom identification fields"
    )


class ProcessedWebhookData(BaseModel):
    """Processed webhook data ready for storage."""
    
    event_id: str = Field(..., description="Webhook event ID")
    event_type: WebhookEventType = Field(..., description="Event type")
    form_id: str = Field(..., description="TypeForm form ID")
    response_token: str = Field(..., description="Response token")
    submitted_at: datetime = Field(..., description="Submission timestamp")
    field_responses: List[ProcessedFieldResponse] = Field(..., description="Processed field responses")
    client_identifiers: ClientIdentifiers = Field(..., description="Client identification data")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")


class WebhookValidationResult(BaseModel):
    """Result of webhook validation."""
    
    is_valid: bool = Field(..., description="Whether payload is valid")
    form_exists: bool = Field(..., description="Whether form exists in our system")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")


class WebhookProcessingResult(BaseModel):
    """Result of webhook processing."""
    
    success: bool = Field(..., description="Whether processing succeeded")
    response_id: Optional[str] = Field(None, description="Stored response ID")
    processed_data: Optional[ProcessedWebhookData] = Field(None, description="Processed data")
    error_message: Optional[str] = Field(None, description="Error message if failed")
    processing_time_ms: Optional[int] = Field(None, description="Processing time in milliseconds")


class WebhookSecurityData(BaseModel):
    """Webhook security validation data."""
    
    signature: str = Field(..., description="Webhook signature header")
    timestamp: Optional[str] = Field(None, description="Webhook timestamp header")
    payload: str = Field(..., description="Raw payload for signature verification")
    
    @field_validator('signature')
    @classmethod
    def validate_signature_format(cls, v):
        """Validate signature format."""
        if not v or not v.startswith(('sha256=', 'sha1=')):
            raise ValueError("Invalid signature format")
        return v


class WebhookHeaders(BaseModel):
    """Expected webhook headers for processing."""
    
    typeform_signature: Optional[str] = Field(None, alias="Typeform-Signature", description="TypeForm signature")
    content_type: Optional[str] = Field(None, alias="Content-Type", description="Content type")
    user_agent: Optional[str] = Field(None, alias="User-Agent", description="User agent")
    
    model_config = ConfigDict(
        validate_by_name=True,
        populate_by_name=True
    ) 