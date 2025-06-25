from datetime import datetime
from typing import Annotated, Any
import re

from pydantic import AfterValidator, Field

from src.logging.logger import logger

def validate_uuid_format(v: str) -> str:
    """Validate UUID format with optimized performance.
    
    Only logs warnings for non-UUID formats when running in DEBUG mode or tests,
    avoiding performance impact in production scenarios.
    """
    # Quick length check first (most common case)
    if len(v) < 1 or len(v) > 36:
        raise ValueError("ID length does not match required length")
    
    # Only do expensive regex validation and logging in development/test environments
    # In production, we assume data integrity is maintained by other layers
    import os
    if os.getenv('ENVIRONMENT', 'development').lower() in ('development', 'test') or logger.isEnabledFor(10):  # DEBUG level
        if not re.match(r'^[0-9a-f]{32}$', v):
            logger.warning(f"ID '{v}' is not in UUID hex format (32 hexadecimal characters)")
    
    return v

# ID fields
UUIDId = Annotated[str, AfterValidator(validate_uuid_format)]
UUIDIdOptional = Annotated[
    str | None, 
    Field(default=None), 
    AfterValidator(lambda v: validate_uuid_format(v) if v is not None else None),
]

def _timestamp_check(v: Any) -> datetime:
    if v and not isinstance(v, datetime):
        try:
            return datetime.fromisoformat(v)
        except ValueError as e:
            raise ValueError(f"Invalid datetime format. Must be isoformat: {v}") from e
    return v


CreatedAtValue = Annotated[datetime, Field(default=datetime.now()), AfterValidator(_timestamp_check)]

# def trim_whitespace(v: str | None) -> str | None:
#     """Trim whitespace from string. For use with AfterValidator."""
#     if v is None:
#         return None
#     return v.strip()

# def trim_whitespace_with_default(v: str | None, value_if_none: Any) -> str | None:
#     """Trim whitespace with default value support. Legacy function."""
#     if v is None and value_if_none:
#         return value_if_none
#     if v is None:
#         return None
#     return v.strip()

def validate_optional_text(v: str | None) -> str | None:
    """Validate optional text: trim whitespace and return None if empty or None."""
    if v is None:
        return None
    
    trimmed = v.strip()
    if not trimmed:  # Empty string after trimming
        return None
    
    return trimmed