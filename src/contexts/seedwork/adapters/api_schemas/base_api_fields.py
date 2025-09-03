"""Base API field definitions and validators for common data types.

This module provides reusable field definitions with built-in validation and
sanitization for common API data types. These fields ensure consistency across
API schemas and provide automatic input cleaning and validation.

Key Features:
    - UUID fields with format validation
    - Sanitized text fields with input cleaning
    - Email and phone fields with format validation
    - URL fields with optional validation
    - Timestamp fields with automatic defaults

All fields use Pydantic validators and provide clear error messages for
validation failures.
"""

from datetime import UTC, datetime
from typing import Annotated

from pydantic import AfterValidator, BeforeValidator, Field, HttpUrl
from src.contexts.seedwork.adapters.api_schemas import validators

# ID fields
UUIDIdRequired = Annotated[
    str,
    Field(..., description="Unique identifier for the entity"),
    BeforeValidator(validators.validate_uuid_format),
]
UUIDIdOptional = Annotated[
    str | None,
    Field(default=None, description="Unique identifier for the entity"),
    AfterValidator(validators.validate_optional_uuid_format),
]

# Sanitized text fields
SanitizedText = Annotated[str, BeforeValidator(validators.sanitize_text_input)]
SanitizedTextOptional = Annotated[
    str | None, BeforeValidator(validators.sanitize_text_input)
]

# Email fields with validation
EmailField = Annotated[str, AfterValidator(validators.validate_email_format)]
EmailFieldOptional = Annotated[
    str | None, Field(default=None), AfterValidator(validators.validate_email_format)
]

# Phone fields with validation
PhoneField = Annotated[str, AfterValidator(validators.validate_phone_format)]
PhoneFieldOptional = Annotated[
    str | None, AfterValidator(validators.validate_phone_format)
]

UrlOptional = Annotated[
    HttpUrl | None,
    Field(default=None),
    BeforeValidator(validators.validate_url_optinal),
]

CreatedAtValue = Annotated[
    datetime,
    Field(default=datetime.now(UTC)),
    AfterValidator(validators.timestamp_check),
]
