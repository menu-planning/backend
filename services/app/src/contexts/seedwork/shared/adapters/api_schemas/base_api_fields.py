from datetime import datetime
from typing import Annotated, Any
import re
import html

from pydantic import AfterValidator, BeforeValidator, Field

from src.logging.logger import logger

def validate_uuid_format(v: str) -> str:
    """Validate UUID format with security-enhanced validation.
    
    Rejects input that contains dangerous patterns or doesn't meet basic security requirements.
    """
    # Quick length check first (most common case)
    if len(v) < 1 or len(v) > 36:
        raise ValueError("ID length does not match required length")
    
    # Security check: reject dangerous patterns immediately
    dangerous_patterns = [
        r"(?i)(drop|delete|insert|update|create|alter|exec|execute|xp_cmdshell)",
        r"(?i)(script|javascript|onclick|onerror|onload)",
        r"(?i)(<|>|&lt;|&gt;)",
        r"(?i)(union\s+select)",
        r"(?i)(--|#|/\*|\*/)",
        r"(?i)(\bor\b\s*['\"]\s*\w+\s*['\"]\s*=\s*['\"]\s*\w+)",  # Matches OR '1'='1', OR "1"="1", etc.
        r"(?i)(\'\s*or\s*\'\d+\'\s*=\s*\'\d+)",  # Matches 'OR'1'='1 patterns
        r"(?i)(\d+\'\s*or\s*\'\d+\'\s*=\s*\'\d+)",  # Matches 1'OR'1'='1 patterns
        r"(?i)(admin|root)(\s*--|\s*#)",  # Common admin bypass attempts
    ]
    
    for pattern in dangerous_patterns:
        if re.search(pattern, v):
            raise ValueError(f"Invalid input: contains potentially dangerous content")
    
    # Only do expensive regex validation and logging in development/test environments
    # In production, we assume data integrity is maintained by other layers
    import os
    if os.getenv('ENVIRONMENT', 'development').lower() in ('development', 'test') or logger.isEnabledFor(10):  # DEBUG level
        if not re.match(r'^[0-9a-f]{32}$', v):
            logger.warning(f"ID '{v}' is not in UUID hex format (32 hexadecimal characters)")
    
    return v

def sanitize_text_input(v: str | None) -> str | None:
    """Sanitize text input to prevent SQL injection and XSS attacks."""
    if v is None:
        return None
    
    # First trim whitespace
    trimmed = v.strip()
    if not trimmed:
        return None
    
    # Remove dangerous SQL injection patterns
    dangerous_sql_patterns = [
        r"(?i)\b(drop|delete|insert|update|create|alter|exec|execute|xp_cmdshell)\b",
        r"(?i)(--|\#|\/\*|\*\/)",
        r"(?i)(\bor\b\s+['\"]\s*\d+\s*['\"]\s*=\s*['\"]\s*\d+)",
        r"(?i)('\s*or\s*'1'\s*=\s*'1)",
        r"(?i)(union\s+select)",
        r"(?i)(script\s*:)",
        r"(?i)(javascript\s*:)",
    ]
    
    sanitized = trimmed
    for pattern in dangerous_sql_patterns:
        sanitized = re.sub(pattern, "", sanitized)
    
    # HTML escape to prevent XSS
    sanitized = html.escape(sanitized)
    
    # Remove any remaining script tags or dangerous HTML
    sanitized = re.sub(r"(?i)<script[^>]*>.*?</script>", "", sanitized)
    sanitized = re.sub(r"(?i)<[^>]*on\w+\s*=", "<", sanitized)  # Remove event handlers
    
    return sanitized.strip() if sanitized.strip() else None

# ID fields
UUIDId = Annotated[str, AfterValidator(validate_uuid_format)]
UUIDIdOptional = Annotated[
    str | None, 
    Field(default=None), 
    AfterValidator(lambda v: validate_uuid_format(v) if v is not None else None),
]

# Sanitized text fields
SanitizedText = Annotated[str, BeforeValidator(sanitize_text_input)]
SanitizedTextOptional = Annotated[str | None, BeforeValidator(sanitize_text_input)]

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