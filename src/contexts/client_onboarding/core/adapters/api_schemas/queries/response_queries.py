"""
Response Query Command Schemas

Pydantic models for querying stored responses for form creators with proper
authorization. Provides request/response validation for various query operations.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, field_validator
from src.contexts.client_onboarding.core.adapters.api_schemas.responses.client_identifiers import (
    ClientIdentifierSet,
)
from src.contexts.seedwork.adapters.exceptions.api_schema_errors import (
    ValidationConversionError,
)


class QueryType(str, Enum):
    """Types of queries supported."""

    RESPONSES_BY_FORM = "responses_by_form"
    RESPONSE_BY_ID = "response_by_id"
    FORMS_BY_USER = "forms_by_user"
    RESPONSES_BY_USER = "responses_by_user"


class ResponseQueryRequest(BaseModel):
    """Base request for querying responses."""

    query_type: QueryType = Field(..., description="Type of query to execute")
    user_id: str = Field(..., description="User ID making the request")
    form_id: int | None = Field(None, description="Form ID for form-specific queries")
    response_id: str | None = Field(
        None, description="TypeForm response ID for specific response queries"
    )
    limit: int | None = Field(50, ge=1, le=100, description="Maximum number of results")
    offset: int | None = Field(0, ge=0, description="Offset for pagination")

    @field_validator("form_id")
    @classmethod
    def validate_form_id_for_form_queries(cls, v, info):
        """Ensure form_id is provided for form-specific queries."""
        if info.data.get("query_type") == QueryType.RESPONSES_BY_FORM and v is None:
            error_msg = "form_id is required for responses_by_form queries"
            raise ValidationConversionError(
                error_msg,
                schema_class=cls,
                conversion_direction="field_validation",
                source_data={"form_id": v, "query_type": info.data.get("query_type")},
                validation_errors=[error_msg],
            )
        return v

    @field_validator("response_id")
    @classmethod
    def validate_response_id_for_response_queries(cls, v, info):
        """Ensure response_id is provided for specific response queries."""
        if info.data.get("query_type") == QueryType.RESPONSE_BY_ID and v is None:
            error_msg = "response_id is required for response_by_id queries"
            raise ValidationConversionError(
                error_msg,
                schema_class=cls,
                conversion_direction="field_validation",
                source_data={"response_id": v, "query_type": info.data.get("query_type")},
                validation_errors=[error_msg],
            )
        return v


class FormSummary(BaseModel):
    """Summary information about a form."""

    id: int = Field(..., description="Form database ID")
    typeform_id: str = Field(..., description="TypeForm ID")
    title: str = Field(..., description="Form title")
    status: str = Field(..., description="Form status")
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    response_count: int | None = Field(None, description="Number of responses")


class ResponseSummary(BaseModel):
    """Summary information about a response."""

    id: int = Field(..., description="Response database ID")
    response_id: str = Field(..., description="TypeForm response ID")
    form_id: int = Field(..., description="Associated form ID")
    client_identifiers: ClientIdentifierSet | None = Field(
        None, description="Extracted client identifiers"
    )
    submitted_at: datetime = Field(..., description="Response submission timestamp")
    processed_at: datetime = Field(..., description="Processing timestamp")
    response_data: dict[str, Any] | None = Field(None, description="Full response data")


class ResponseQueryResponse(BaseModel):
    """Response for query operations."""

    success: bool = Field(..., description="Whether the query was successful")
    query_type: QueryType = Field(..., description="Type of query executed")
    total_count: int = Field(0, description="Total number of matching results")
    returned_count: int = Field(0, description="Number of results in this response")
    forms: list[FormSummary] | None = Field(
        None, description="Forms matching the query"
    )
    responses: list[ResponseSummary] | None = Field(
        None, description="Responses matching the query"
    )
    pagination: dict[str, Any] | None = Field(
        None, description="Pagination information"
    )

    @field_validator("forms")
    @classmethod
    def validate_forms_for_form_queries(cls, v, info):
        """Ensure forms are provided for form queries."""
        query_type = info.data.get("query_type")
        if query_type == QueryType.FORMS_BY_USER and v is None:
            error_msg = "forms must be provided for forms_by_user queries"
            raise ValidationConversionError(
                error_msg,
                schema_class=cls,
                conversion_direction="field_validation",
                source_data={"forms": v, "query_type": query_type},
                validation_errors=[error_msg],
            )
        return v

    @field_validator("responses")
    @classmethod
    def validate_responses_for_response_queries(cls, v, info):
        """Ensure responses are provided for response queries."""
        query_type = info.data.get("query_type")
        if (
            query_type
            in [
                QueryType.RESPONSES_BY_FORM,
                QueryType.RESPONSE_BY_ID,
                QueryType.RESPONSES_BY_USER,
            ]
            and v is None
        ):
            error_msg = f"responses must be provided for {query_type} queries"
            raise ValidationConversionError(
                error_msg,
                schema_class=cls,
                conversion_direction="field_validation",
                source_data={"responses": v, "query_type": query_type},
                validation_errors=[error_msg],
            )
        return v


class BulkResponseQueryRequest(BaseModel):
    """Request for multiple queries in a single request."""

    queries: list[ResponseQueryRequest] = Field(
        ..., min_length=1, max_length=5, description="List of queries to execute"
    )
    user_id: str = Field(..., description="User ID making the request")


class BulkResponseQueryResponse(BaseModel):
    """Response for bulk query operations."""

    success: bool = Field(..., description="Whether all queries were successful")
    total_queries: int = Field(..., description="Total number of queries executed")
    successful_queries: int = Field(..., description="Number of successful queries")
    results: list[ResponseQueryResponse] = Field(
        ..., description="Results for each query"
    )
    errors: list[str] | None = Field(
        None, description="Errors encountered during processing"
    )
