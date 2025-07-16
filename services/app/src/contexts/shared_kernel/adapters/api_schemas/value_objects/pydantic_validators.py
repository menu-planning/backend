from typing import Any

from pydantic import ValidationInfo

from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import ApiTag


def validate_tags_have_correct_author_id_and_type(v: Any, tag_type: str, info: ValidationInfo) -> Any:
    """
    Validate tags field. If a dict is provided without 'type' and 'author_id',
    add them with default values and convert to ApiTag.
    """
    if v is None:
        return v
        # return frozenset()
    
    parent_author_id = None

    # Check if author_id is available (it might not be if its validation failed)
    if info.data and 'author_id' in info.data:
        parent_author_id = info.data['author_id']
    else:
        # If author_id validation failed, we can't validate tags properly
        # Just return the original value and let the author_id error be reported separately
        return v
    
    if isinstance(v, (frozenset, frozenset, list)):
        validated_tags = []
        for tag in v:
            tag_data = None
            if isinstance(tag, ApiTag):
                tag_data = tag.model_dump()
            elif isinstance(tag, dict):
                # Create a copy to avoid modifying the original
                tag_data = tag.copy()
            else:
                raise ValueError(f"Validation error: Invalid tag format: {type(tag)}. Expected dict or ApiTag.")

            # Add missing 'type' if not present
            if tag_data is None:
                raise ValueError(f"Validation error: Tag data is None.")
            
            if tag_data.get('type') != tag_type:
                raise ValueError(f"Validation error: Tag type does not match {tag_type} type.")
            
            # Add missing 'author_id' if not present
            if parent_author_id is None:
                raise ValueError(f"Validation error: Parent author_id is None.")
            
            if tag_data.get('author_id') != parent_author_id:
                raise ValueError(f"Validation error: Tag author_id does not match {tag_type} author_id.")

            # Convert to ApiTag
            validated_tags.append(ApiTag(**tag_data))
        return frozenset(validated_tags)
    
    return v