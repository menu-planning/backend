"""Pydantic field validators for shared kernel value objects.

This module provides helpers intended to be used from Pydantic
`field_validator` hooks to validate and normalize API-facing value objects.
"""

from typing import Any

from pydantic import ValidationInfo
from src.contexts.seedwork.adapters.exceptions.api_schema_errors import (
    ValidationConversionError,
)
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import (
    ApiTag,
)


def validate_tags_have_correct_author_id_and_type(
    v: Any, tag_type: str, info: ValidationInfo
) -> Any:
    """Validate and normalize tags for the given tag type.

    Args:
        v: Collection of tags as ApiTag instances or dicts, or non-collection value.
        tag_type: Expected tag type for all items.
        info: Pydantic validation context with access to sibling fields.

    Returns:
        Frozenset of ApiTag instances when collection provided, otherwise original value.

    Raises:
        ValidationConversionError: If tags are not dict/ApiTag, or types/author_ids do not match expected values.
    """
    if v is None:
        return v

    parent_author_id = None
    # The parent author's id is required to validate individual tag author_ids.
    if info.data and "author_id" in info.data:
        parent_author_id = info.data["author_id"]
    else:
        # Defer to the primary author_id validation error, if any.
        return v

    if isinstance(v, frozenset | list | set):
        validated_tags = []
        for tag in v:
            tag_data = None
            if isinstance(tag, ApiTag):
                tag_data = tag.model_dump()
            elif isinstance(tag, dict):
                # Copy to avoid mutating the caller's data structure.
                tag_data = tag.copy()
            else:
                raise ValidationConversionError(
                    message=f"Invalid tag format: {type(tag)}. Expected dict or ApiTag.",
                    schema_class=None,  # We don't have access to the model class in this context
                    conversion_direction="field_validation",
                    source_data=tag,
                    validation_errors=[f"Expected dict or ApiTag, got {type(tag).__name__}"]
                )

            # Ensure required fields are present and valid
            if tag_data is None:
                raise ValidationConversionError(
                    message="Tag data is None.",
                    schema_class=None,  # We don't have access to the model class in this context
                    conversion_direction="field_validation",
                    source_data=tag,
                    validation_errors=["Tag data cannot be None"]
                )

            if tag_data.get("type") != tag_type:
                raise ValidationConversionError(
                    message=f"Tag type does not match {tag_type} type.",
                    schema_class=None,  # We don't have access to the model class in this context
                    conversion_direction="field_validation",
                    source_data=tag_data,
                    validation_errors=[f"Expected type '{tag_type}', got '{tag_data.get('type')}'"]
                )

            if parent_author_id is None:
                raise ValidationConversionError(
                    message="Parent author_id is None.",
                    schema_class=None,  # We don't have access to the model class in this context
                    conversion_direction="field_validation",
                    source_data=tag_data,
                    validation_errors=["Parent author_id is required for tag validation"]
                )

            if tag_data.get("author_id") != parent_author_id:
                raise ValidationConversionError(
                    message=f"Tag author_id does not match {tag_type} author_id.",
                    schema_class=None,  # We don't have access to the model class in this context
                    conversion_direction="field_validation",
                    source_data=tag_data,
                    validation_errors=[
                        f"Expected author_id '{parent_author_id}', got '{tag_data.get('author_id')}'"
                    ]
                )

            # Convert validated dict into a rich value object
            validated_tags.append(ApiTag(**tag_data))
        return frozenset(validated_tags)

    return v
