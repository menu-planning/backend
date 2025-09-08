"""
External Provider API Schema: Form Response

Pydantic models for form response data used in internal provider endpoints.
These schemas define the structure for cross-context communication between
client onboarding and other contexts.
"""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class ApiFormResponse(BaseModel):
    """API schema for form response data in cross-context communication.

    Serializes FormResponse domain objects for internal provider endpoints
    and cross-context communication. Handles datetime serialization and
    provides mapping methods for domain integration.

    Attributes:
        id: Internal form response ID
        form_id: Associated onboarding form ID
        response_id: TypeForm response ID
        submission_id: TypeForm submission ID (optional)
        response_data: Raw TypeForm response data
        client_identifiers: Extracted client identification data (optional)
        submitted_at: Form submission timestamp (ISO format, optional)
        processed_at: Response processing timestamp (ISO format, optional)
        created_at: Record creation timestamp (ISO format, optional)
        updated_at: Record update timestamp (ISO format, optional)

    Notes:
        Boundary contract for cross-context communication.
        Datetime fields serialized as ISO format strings.
    """

    model_config = ConfigDict(
        from_attributes=True,
    )

    id: int = Field(..., description="Internal form response ID")
    form_id: int = Field(..., description="Associated onboarding form ID")
    response_id: str = Field(..., description="TypeForm response ID")
    submission_id: str | None = Field(None, description="TypeForm submission ID")

    # Core data fields
    response_data: dict[str, Any] = Field(..., description="Raw TypeForm response data")
    client_identifiers: dict[str, Any] | None = Field(
        None, description="Extracted client identification data (email, phone, etc.)"
    )

    # Timestamps
    submitted_at: str | None = Field(
        None, description="When form was submitted (ISO format)"
    )
    processed_at: str | None = Field(
        None, description="When response was processed (ISO format)"
    )
    created_at: str | None = Field(
        None, description="When record was created (ISO format)"
    )
    updated_at: str | None = Field(
        None, description="When record was last updated (ISO format)"
    )

    @field_serializer("submitted_at", "processed_at", "created_at", "updated_at")
    def serialize_datetime_fields(self, value: str | None) -> str | None:
        """Serialize datetime fields to ISO format strings.

        Args:
            value: The datetime string value to serialize

        Returns:
            ISO format string or None if value is None
        """
        if value is None:
            return None
        # If it's already a string, return as-is
        if isinstance(value, str):
            return value
        # If it's a datetime object, convert to ISO format
        if isinstance(value, datetime):
            return value.isoformat()
        return value

    @classmethod
    def from_domain(cls, form_response) -> "ApiFormResponse":
        """Create ApiFormResponse from domain FormResponse object.

        Args:
            form_response: FormResponse domain object

        Returns:
            ApiFormResponse instance with serialized data
        """
        return cls(
            id=form_response.id,
            form_id=form_response.form_id,
            response_id=form_response.response_id,
            submission_id=form_response.submission_id,
            response_data=form_response.response_data,
            client_identifiers=form_response.client_identifiers,
            submitted_at=(
                form_response.submitted_at.isoformat()
                if form_response.submitted_at
                else None
            ),
            processed_at=(
                form_response.processed_at.isoformat()
                if form_response.processed_at
                else None
            ),
            created_at=(
                form_response.created_at.isoformat()
                if form_response.created_at
                else None
            ),
            updated_at=(
                form_response.updated_at.isoformat()
                if form_response.updated_at
                else None
            ),
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the form response
        """
        return self.model_dump()


class ApiFormResponseList(BaseModel):
    """API schema for multiple form responses with pagination metadata.

    Used for listing multiple form responses with metadata and pagination
    information in cross-context communication.

    Attributes:
        responses: List of form response objects
        count: Total number of responses in this batch
        context: Requesting context name
        offset: Pagination offset (optional)
        limit: Pagination limit (optional)
        total_available: Total responses available (optional)

    Notes:
        Boundary contract for cross-context communication.
        Supports pagination metadata for large result sets.
    """

    model_config = ConfigDict(from_attributes=True)

    responses: list[ApiFormResponse] = Field(..., description="List of form responses")
    count: int = Field(..., description="Total number of responses")
    context: str = Field(..., description="Requesting context name")

    # Optional pagination metadata
    offset: int | None = Field(None, description="Pagination offset")
    limit: int | None = Field(None, description="Pagination limit")
    total_available: int | None = Field(None, description="Total responses available")

    @classmethod
    def from_domain_list(
        cls,
        form_responses: list,
        caller_context: str,
        offset: int | None = None,
        limit: int | None = None,
        total_available: int | None = None,
    ) -> "ApiFormResponseList":
        """Create ApiFormResponseList from list of domain FormResponse objects.

        Args:
            form_responses: List of FormResponse domain objects
            caller_context: The context making the request
            offset: Optional pagination offset
            limit: Optional pagination limit
            total_available: Optional total available count

        Returns:
            ApiFormResponseList instance with serialized data
        """
        api_responses = [
            ApiFormResponse.from_domain(response) for response in form_responses
        ]

        return cls(
            responses=api_responses,
            count=len(api_responses),
            context=caller_context,
            offset=offset,
            limit=limit,
            total_available=total_available,
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of the form response list
        """
        return self.model_dump()


class ApiClientIdentifiers(BaseModel):
    """API schema for client identifier data extracted from form responses.

    Standardizes client identification data across contexts for
    cross-context communication and data sharing.

    Attributes:
        email: Client email address (optional)
        phone: Client phone number (optional)
        user_id: Associated user ID (optional)
        first_name: Client first name (optional)
        last_name: Client last name (optional)
        company: Client company (optional)
        custom_identifiers: Additional custom identifier fields (optional)

    Notes:
        Boundary contract for cross-context communication.
        All fields optional to handle partial data extraction.
    """

    model_config = ConfigDict(from_attributes=True)

    email: str | None = Field(None, description="Client email address")
    phone: str | None = Field(None, description="Client phone number")
    user_id: str | None = Field(None, description="Associated user ID")
    first_name: str | None = Field(None, description="Client first name")
    last_name: str | None = Field(None, description="Client last name")
    company: str | None = Field(None, description="Client company")

    # Additional identifier fields
    custom_identifiers: dict[str, Any] | None = Field(
        None, description="Additional custom identifier fields"
    )

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON serialization.

        Returns:
            Dictionary representation of client identifiers (excludes None values)
        """
        return self.model_dump(exclude_none=True)
