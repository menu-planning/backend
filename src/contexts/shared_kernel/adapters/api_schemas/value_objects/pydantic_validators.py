from typing import Any

from pydantic import ValidationInfo
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import (
    ApiTag,
)


def validate_tags_have_correct_author_id_and_type(
    v: Any, tag_type: str, info: ValidationInfo
) -> Any:
    """
    Validate tags field. If a dict is provided without 'type' and 'author_id',
    add them with default values and convert to ApiTag.
    """
    if v is None:
        return v

    parent_author_id = None

    # Check if author_id is available (it might not be if its validation failed)
    if info.data and "author_id" in info.data:
        parent_author_id = info.data["author_id"]
    else:
        # If author_id validation failed, we can't validate tags properly
        # Just return the original value and let the author_id error be
        # reported separately
        return v

    if isinstance(v, frozenset | list | set):
        validated_tags = []
        for tag in v:
            tag_data = None
            if isinstance(tag, ApiTag):
                tag_data = tag.model_dump()
            elif isinstance(tag, dict):
                # Create a copy to avoid modifying the original
                tag_data = tag.copy()
            else:
                error_message = (
                    f"Validation error: Invalid tag format: "
                    f"{type(tag)}. Expected dict or ApiTag."
                )
                raise ValueError(error_message)

            # Add missing 'type' if not present
            if tag_data is None:
                error_message = "Validation error: Tag data is None."
                raise ValueError(error_message)

            if tag_data.get("type") != tag_type:
                error_message = (
                    f"Validation error: Tag type does not match {tag_type} type."
                )
                raise ValueError(error_message)

            # Add missing 'author_id' if not present
            if parent_author_id is None:
                error_message = "Validation error: Parent author_id is None."
                raise ValueError(error_message)

            if tag_data.get("author_id") != parent_author_id:
                error_message = (
                    f"Validation error: Tag author_id does not match "
                    f"{tag_type} author_id."
                )
                raise ValueError(error_message)

            # Convert to ApiTag
            validated_tags.append(ApiTag(**tag_data))
        return frozenset(validated_tags)

    return v
