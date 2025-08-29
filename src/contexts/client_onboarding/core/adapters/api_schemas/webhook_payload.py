"""
Webhook Payload API Schemas

Pydantic models for validating and processing TypeForm webhook payloads.
Handles form response data, event metadata, and client identification.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


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
    label: str | None = Field(None, description="Choice label")


class FieldDefinition(BaseModel):
    """Field definition from TypeForm."""

    id: str = Field(..., description="Field ID")
    title: str = Field(..., description="Field title/question")
    type: FieldType = Field(..., description="Field type")
    ref: str | None = Field(None, description="Field reference")
    allow_multiple_selections: bool | None = Field(
        None, description="Multiple selections allowed"
    )
    allow_other_choice: bool | None = Field(None, description="Other choice allowed")
    choices: list[FieldChoice] | None = Field(None, description="Available choices")


class FieldAnswer(BaseModel):
    """Answer to a form field."""

    field: FieldDefinition = Field(..., description="Field definition")
    type: FieldType = Field(..., description="Answer type")
    text: str | None = Field(None, description="Text answer")
    email: str | None = Field(None, description="Email answer")
    url: str | None = Field(None, description="URL answer")
    file_url: str | None = Field(None, description="File URL")
    number: int | float | None = Field(None, description="Number answer")
    boolean: bool | None = Field(None, description="Boolean answer")
    choice: FieldChoice | None = Field(None, description="Choice answer")
    choices: list[FieldChoice] | None = Field(
        None, description="Multiple choice answers"
    )
    date: str | None = Field(None, description="Date answer (ISO format)")
    phone_number: str | None = Field(None, description="Phone number")
    payment: dict[str, Any] | None = Field(None, description="Payment data")


class FormDefinition(BaseModel):
    """Form definition from webhook payload."""

    id: str = Field(..., description="Form ID")
    title: str = Field(..., description="Form title")
    fields: list[FieldDefinition] | None = Field(None, description="Form fields")


class FormResponse(BaseModel):
    """Form response data from webhook."""

    form_id: str = Field(..., description="Form ID")
    token: str = Field(..., description="Response token")
    landed_at: datetime = Field(..., description="When user started form")
    submitted_at: datetime = Field(..., description="When form was submitted")
    definition: FormDefinition | None = Field(None, description="Form definition")
    answers: list[FieldAnswer] = Field(..., description="Field answers")
    calculated: dict[str, Any] | None = Field(None, description="Calculated values")
    variables: dict[str, Any] | None = Field(None, description="Hidden variables")

    @field_validator("landed_at", "submitted_at", mode="before")
    @classmethod
    def parse_datetime(cls, v):
        """Parse datetime strings to datetime objects."""
        if isinstance(v, str):
            return datetime.fromisoformat(v)
        return v


class WebhookPayload(BaseModel):
    """Complete TypeForm webhook payload."""

    event_id: str = Field(..., description="Unique event ID")
    event_type: WebhookEventType = Field(..., description="Event type")
    form_response: FormResponse = Field(..., description="Form response data")

    @field_validator("event_type")
    @classmethod
    def validate_event_type(cls, v):
        """Validate that we only process form_response events."""
        if v != WebhookEventType.FORM_RESPONSE:
            error_msg = f"Unsupported event type: {v}"
            raise ValueError(error_msg)
        return v


class ProcessedFieldResponse(BaseModel):
    """Processed field response for storage."""

    field_id: str = Field(..., description="Field ID")
    field_ref: str | None = Field(None, description="Field reference")
    field_title: str = Field(..., description="Field question/title")
    field_type: FieldType = Field(..., description="Field type")
    answer_value: Any = Field(..., description="Processed answer value")
    answer_text: str | None = Field(None, description="Text representation of answer")


class ClientIdentifiers(BaseModel):
    """Client identification data extracted from responses."""

    email: str | None = Field(None, description="Client email address")
    name: str | None = Field(None, description="Client name")
    company: str | None = Field(None, description="Company name")
    phone: str | None = Field(None, description="Phone number")
    custom_identifiers: dict[str, str] = Field(
        default_factory=dict, description="Custom identification fields"
    )


class ProcessedWebhookData(BaseModel):
    """Processed webhook data ready for storage."""

    event_id: str = Field(..., description="Webhook event ID")
    event_type: WebhookEventType = Field(..., description="Event type")
    form_id: str = Field(..., description="TypeForm form ID")
    response_token: str = Field(..., description="Response token")
    submitted_at: datetime = Field(..., description="Submission timestamp")
    field_responses: list[ProcessedFieldResponse] = Field(
        ..., description="Processed field responses"
    )
    client_identifiers: ClientIdentifiers = Field(
        ..., description="Client identification data"
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )


class WebhookValidationResult(BaseModel):
    """Result of webhook validation."""

    is_valid: bool = Field(..., description="Whether payload is valid")
    form_exists: bool = Field(..., description="Whether form exists in our system")
    errors: list[str] = Field(default_factory=list, description="Validation errors")
    warnings: list[str] = Field(default_factory=list, description="Validation warnings")


class WebhookProcessingResult(BaseModel):
    """Result of webhook processing."""

    success: bool = Field(..., description="Whether processing succeeded")
    response_id: str | None = Field(None, description="Stored response ID")
    processed_data: ProcessedWebhookData | None = Field(
        None, description="Processed data"
    )
    error_message: str | None = Field(None, description="Error message if failed")
    processing_time_ms: int | None = Field(
        None, description="Processing time in milliseconds"
    )


class WebhookSecurityData(BaseModel):
    """Webhook security validation data."""

    signature: str = Field(..., description="Webhook signature header")
    timestamp: str | None = Field(None, description="Webhook timestamp header")
    payload: str = Field(..., description="Raw payload for signature verification")

    @field_validator("signature")
    @classmethod
    def validate_signature_format(cls, v):
        """Validate signature format."""
        if not v or not v.startswith(("sha256=", "sha1=")):
            error_msg = "Invalid signature format"
            raise ValueError(error_msg)
        return v


class WebhookHeaders(BaseModel):
    """Expected webhook headers for processing."""

    typeform_signature: str | None = Field(
        None, alias="Typeform-Signature", description="TypeForm signature"
    )
    content_type: str | None = Field(
        None, alias="Content-Type", description="Content type"
    )
    user_agent: str | None = Field(None, alias="User-Agent", description="User agent")

    model_config = ConfigDict(validate_by_name=True, populate_by_name=True)
