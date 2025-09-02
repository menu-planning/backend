"""Typed field aliases for shared kernel API schemas.

Provides constrained/sanitized string types for tag-related models with
validation rules for length and content.

Attributes:
    TagValue: Tag value field with length 1-100 characters.
    TagKey: Tag key field with length 1-50 characters.
    TagType: Tag type field with length 1-50 characters.

Notes:
    Boundary contract only; domain rules enforced in application layer.
"""
from typing import Annotated

from pydantic import Field
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import (
    SanitizedText,
)

TagValue = Annotated[SanitizedText, Field(min_length=1, max_length=100)]
TagKey = Annotated[SanitizedText, Field(min_length=1, max_length=50)]
TagType = Annotated[SanitizedText, Field(min_length=1, max_length=50)]
