from datetime import UTC, datetime
from typing import Annotated

from pydantic import AfterValidator, BeforeValidator, Field, HttpUrl

from src.contexts.seedwork.shared.adapters.api_schemas import validators

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
    str | None, Field(default=None), BeforeValidator(validators.sanitize_text_input)
]

# Email fields with validation
EmailField = Annotated[str, AfterValidator(validators.validate_email_format)]
EmailFieldOptional = Annotated[
    str | None, Field(default=None), AfterValidator(validators.validate_email_format)
]

# Phone fields with validation
PhoneField = Annotated[str, AfterValidator(validators.validate_phone_format)]
PhoneFieldOptional = Annotated[
    str | None, Field(default=None), BeforeValidator(validators.validate_phone_format)
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
