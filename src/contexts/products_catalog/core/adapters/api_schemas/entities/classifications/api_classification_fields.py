"""Field definitions for classification API schemas.

Provides validated field types for classification entities with proper
constraints and validation rules.
"""
from typing import Annotated

import src.contexts.seedwork.adapters.api_schemas.validators as validators
from pydantic import AfterValidator, Field
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import (
    SanitizedText,
    SanitizedTextOptional,
    UUIDIdRequired,
)

# Required string fields with validation
ClassificationNameRequired = Annotated[
    SanitizedText,
    Field(
        ...,
        max_length=500,
        description="Name of the classification",
    ),
]

ClassificationAuthorIdRequired = Annotated[
    UUIDIdRequired,
    Field(..., description="Identifier of the classification's author"),
]

# Optional string fields
ClassificationDescriptionOptional = Annotated[
    SanitizedTextOptional,
    Field(default=None, description="Description of the classification"),
    AfterValidator(lambda v: validators.validate_optional_text_length(v, 1000, "Description must be less than 1000 characters")),
]
