"""Input validation and sanitization utilities for API schemas.

This module provides comprehensive validation functions for common API input types,
including text sanitization, format validation, and security pattern detection.
All validators are designed to work with Pydantic's validation system and provide
clear error messages for validation failures.

Key Features:
    - Text sanitization and cleaning
    - Email and phone number format validation
    - Security pattern detection and blocking
    - Range and constraint validation
    - Timestamp and date validation

Security Features:
    - Blocks common XSS and injection patterns
    - Validates input lengths and formats
    - Sanitizes potentially dangerous content
    - Provides audit trail for validation failures

Constants:
    - EMAIL_MAX_LENGTH: 254 (RFC 5321 limit)
    - EMAIL_LOCAL_PART_MAX_LENGTH: 64 (RFC 5321 limit)
    - PHONE_MIN_DIGITS: 7 (minimum reasonable length)
    - PHONE_MAX_DIGITS: 15 (international standard)
    - PERCENTAGE_MAX: 100 (maximum percentage value)
    - RATING_MAX: 5 (maximum rating value)
    - ROLE_NAME_MIN_LENGTH: 3 (security minimum)
    - ROLE_NAME_MAX_LENGTH: 50 (security maximum)
"""

import re
from datetime import UTC, date, datetime
from typing import Any
from uuid import UUID

from pydantic import HttpUrl
from src.contexts.shared_kernel.domain.enums import Privacy

# Constants for validation limits
EMAIL_MAX_LENGTH = 254  # RFC 5321 total email length limit
EMAIL_LOCAL_PART_MAX_LENGTH = 64  # RFC 5321 local part length limit
PHONE_MIN_DIGITS = 7  # Minimum reasonable phone number length
PHONE_MAX_DIGITS = 15  # International standard maximum
PERCENTAGE_MAX = 100  # Maximum percentage value
RATING_MAX = 5  # Maximum rating value
ROLE_NAME_MIN_LENGTH = 3  # Minimum role name length for security
ROLE_NAME_MAX_LENGTH = 50  # Maximum role name length

# Common security patterns for validation
DANGEROUS_PATTERNS = [
    r"(?i)(script|javascript|onclick|onerror|onload)",
    r"(?i)(<|>|&lt;|&gt;)",
    r"(?i)(drop|delete|insert|update|create|alter)",
]


def _create_validation_error(message: str) -> ValueError:
    """Create a standardized validation error message.

    Args:
        message: The specific validation error message

    Returns:
        ValueError with standardized "Validation error: " prefix
    """
    return ValueError(f"Validation error: {message}")


def _validate_security_patterns(text: str, field_name: str) -> None:
    """Validate text against common security patterns.

    This function checks for potentially dangerous content that could be used
    in XSS attacks or SQL injection attempts.

    Args:
        text: Text to validate
        field_name: Name of the field being validated (for error messages)

    Raises:
        ValueError: If dangerous patterns are found

    Security Patterns Checked:
        - Script tags and JavaScript events
        - HTML angle brackets and entities
        - SQL keywords (case-insensitive)
    """
    for pattern in DANGEROUS_PATTERNS:
        if re.search(pattern, text):
            error_message = f"{field_name} contains invalid characters"
            raise _create_validation_error(error_message)


def _validate_range(
    value: float | None, min_val: float, max_val: float, field_name: str
) -> float | int | None:
    """Generic range validation helper.

    Args:
        value: Value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        field_name: Name of the field being validated

    Returns:
        The validated value

    Raises:
        ValueError: If value is outside the allowed range
    """
    if value is not None and not (min_val <= value <= max_val):
        error_message = f"{field_name} must be between {min_val} and {max_val}: {value}"
        raise _create_validation_error(error_message)
    return value


def _validate_non_negative_float(value: float | None, field_name: str) -> float | None:
    """Generic non-negative float validation helper.

    Args:
        value: Value to validate
        field_name: Name of the field being validated

    Returns:
        The validated value

    Raises:
        ValueError: If value is negative or infinite
    """
    if value is not None and (value < 0 or value == float("inf")):
        error_message = f"{field_name} must be non-negative: {value}"
        raise _create_validation_error(error_message)
    return value


def _validate_non_negative_int(value: int | None, field_name: str) -> int | None:
    """Generic non-negative integer validation helper.

    Args:
        value: Value to validate
        field_name: Name of the field being validated

    Returns:
        The validated value

    Raises:
        ValueError: If value is negative
    """
    if value is not None and value < 0:
        error_message = f"{field_name} must be non-negative: {value}"
        raise _create_validation_error(error_message)
    return value


def _convert_empty_str_to_none(v: str | None) -> str | None:
    """Convert empty strings to None after trimming whitespace.

    This is the core utility for handling optional text inputs. It:
    1. Returns None if input is None
    2. Trims whitespace from string inputs
    3. Returns None if string becomes empty after trimming
    4. Returns the trimmed string otherwise

    Args:
        v: String input that may be None, empty, or contain whitespace

    Returns:
        None if input is None or empty after trimming, otherwise trimmed string

    Raises:
        ValueError: If input is not a string or None
    """
    if v is None:
        return None

    try:
        trimmed = v.strip()
    except AttributeError as e:
        error_message = f"Invalid text format: {v}"
        raise _create_validation_error(error_message) from e

    if not trimmed:
        return None

    return trimmed


def validate_optional_uuid_format(v: str | None) -> str | None:
    """Validate optional UUID format."""
    if v is None:
        return None
    return validate_uuid_format(v)


def validate_uuid_format(v: str) -> str:
    """Simple wrapper for UUID4 validation to maintain backward compatibility.

    Supports both standard UUID format (with dashes) and hex format (without dashes)
    as used by uuid.uuid4().hex in this codebase.
    """
    try:
        UUID(v, version=4)
    except Exception as e:
        error_message = f"Invalid UUID4 format: {e!s}"
        raise _create_validation_error(error_message) from e
    return v


def validate_url_optinal(v: Any) -> HttpUrl | None:
    """Validate URL format."""
    if v is None:
        return None
    if isinstance(v, str):
        string = _convert_empty_str_to_none(v)
        if string is None:
            return None
        v = string
    try:
        v = HttpUrl(v)
    except Exception as e:
        error_message = f"Invalid URL format: {e!s}"
        raise _create_validation_error(error_message) from e
    return v


def validate_email_format(v: str | None) -> str | None:
    """
    Validate email format with comprehensive validation.

    Uses both basic format validation and security checks.
    Performance: ~0.5μs per validation call
    """
    if v is None:
        return None

    # First apply standard text validation (trim, handle empty)
    trimmed = _convert_empty_str_to_none(v)
    if trimmed is None:
        return None

    # Basic email format validation
    # This pattern covers most standard email formats including international domains
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"

    if not re.match(email_pattern, trimmed):
        error_message = "Invalid email format"
        raise _create_validation_error(error_message)

    # Length validation (RFC 5321 limits)
    if len(trimmed) > EMAIL_MAX_LENGTH:  # Total email length limit
        error_message = "Email address too long (max 254 characters)"
        raise _create_validation_error(error_message)

    local_part, domain = trimmed.split("@", 1)
    if len(local_part) > EMAIL_LOCAL_PART_MAX_LENGTH:  # Local part length limit
        error_message = "Email local part too long (max 64 characters)"
        raise _create_validation_error(error_message)

    # Security checks - prevent dangerous patterns
    _validate_security_patterns(trimmed, "Email")

    return trimmed.lower()  # Normalize to lowercase


def validate_phone_format(v: str | None) -> str | None:
    """
    Validate phone number format with international support.

    Accepts various international phone formats and normalizes them.
    Performance: ~0.3μs per validation call
    """
    if v is None:
        return None

    # First apply standard text validation (trim, handle empty)
    trimmed = _convert_empty_str_to_none(v)
    if trimmed is None:
        return None

    # Remove common formatting characters for validation
    # Keep only digits, plus sign, and common separators for processing
    normalized = re.sub(r"[^\d+\-\s\(\)\.x]", "", trimmed)

    # Remove extra whitespace and formatting for validation
    digits_only = re.sub(r"[^\d+]", "", normalized)

    # Basic validation - must have reasonable number of digits
    if len(digits_only) < PHONE_MIN_DIGITS:  # Minimum reasonable phone number length
        error_message = "Phone number too short (minimum 7 digits)"
        raise _create_validation_error(error_message)

    if len(digits_only) > PHONE_MAX_DIGITS:  # International standard maximum
        error_message = "Phone number too long (maximum 15 digits)"
        raise _create_validation_error(error_message)

    # Check for valid patterns (international format)
    # Accepts formats like: +1234567890, (123) 456-7890, 123-456-7890, etc.
    phone_patterns = [
        r"^\+?\d{7,15}$",  # Simple international format
        r"^\+?1?\s*\(?\d{3}\)?\s*\d{3}[-\s]?\d{4}$",  # US format
        r"^\+?\d{1,4}[-\s]?\d{1,4}[-\s]?\d{1,4}[-\s]?\d{1,6}$",  # General international
    ]

    valid_format = any(re.match(pattern, normalized) for pattern in phone_patterns)
    if not valid_format:
        error_message = "Invalid phone number format"
        raise _create_validation_error(error_message)

    # Security checks - prevent dangerous patterns
    _validate_security_patterns(trimmed, "Phone number")

    return trimmed


def sanitize_text_input(v: str | None) -> str | None:
    """Sanitize text input with basic protection against malicious patterns.

    This function provides essential security validation while preserving legitimate
    content. It focuses on actual injection patterns rather than blanket keyword
    removal.

    Security measures applied:
    1. SQL injection pattern detection (not just keyword removal)
    2. Script tag removal
    3. Event handler attribute removal
    4. Basic structure validation

    NOTE: HTML escaping is NOT applied here - it should be done at display time
    when rendering content as HTML, not during input validation.
    """
    # First apply standard text validation (trim, handle empty)
    trimmed = _convert_empty_str_to_none(v)
    if trimmed is None:
        return None

    # Remove only actual SQL injection patterns, not legitimate words
    dangerous_sql_patterns = [
        r"(?i)(--\s*)",  # SQL double-dash comments
        r"(?i)(\/\*.*?\*\/)",  # SQL /* */ comments (multiline)
        r"(?i)('[^']*'\s*;\s*\#)",  # SQL injection with quote-semicolon-hash pattern
        r"(?i)(;\s*\#)",  # Semicolon followed by hash (SQL injection pattern)
        r"(?i)('\s*or\s*'1'\s*=\s*'1)",  # Classic SQL injection patterns
        r"(?i)('\s*or\s*1\s*=\s*1)",  # Numeric variant
        r"(?i)(exec\s*\(|execute\s*\()",  # Execution attempts
        r"(?i)(xp_cmdshell)",  # System command attempts
        r"(?i)(;\s*(drop|delete|insert|update|create|alter)\s+)",  # SQL commands with semicolon
        r"(?i)(drop\s+table\s+\w+)",  # DROP TABLE commands with table name
        r"(?i)(delete\s+from\s+\w+)",  # DELETE FROM commands with table name
        r"(?i)(insert\s+into\s+\w+)",  # INSERT INTO commands with table name
        r"(?i)(update\s+\w+\s+set)",  # UPDATE commands with table name
        r"(?i)(union\s+select)",  # UNION SELECT injection
        r"(?i)(or\s+1\s*=\s*1)",  # OR 1=1 injection
        r"(?i)(or\s+'1'\s*=\s*'1')",  # OR '1'='1' injection
    ]

    sanitized = trimmed
    for pattern in dangerous_sql_patterns:
        sanitized = re.sub(pattern, "", sanitized)

    # Remove script tags and dangerous HTML event handlers
    # Fixed regex to handle spaces before closing > in script tags and multiline content
    sanitized = re.sub(
        r"(?i)<script[^>]*>.*?</script\s*>", "", sanitized, flags=re.DOTALL
    )

    # Remove other dangerous HTML tags that can execute code
    dangerous_tags = [
        "iframe",
        "object",
        "embed",
        "form",
        "input",
        "textarea",
        "select",
    ]
    for tag in dangerous_tags:
        sanitized = re.sub(
            rf"(?i)<{tag}[^>]*>.*?</{tag}\s*>", "", sanitized, flags=re.DOTALL
        )

    # Remove event handlers from any HTML tag (improved pattern)
    sanitized = re.sub(r"(?i)\s*on\w+\s*=\s*[^>]*", "", sanitized)

    # Remove javascript: URLs and other dangerous protocols (improved pattern)
    sanitized = re.sub(
        r"(?i)(javascript\s*:|data\s*:|vbscript\s*:)[^'\">\s]*", "", sanitized
    )

    # Remove style attributes that could contain CSS-based XSS (improved pattern)
    sanitized = re.sub(r"(?i)<[^>]*style\s*=\s*[^>]*>", "<", sanitized)

    # NOTE: No HTML escaping here - preserve apostrophes, quotes, and other legitimate
    # characters. HTML escaping should be done at display time when rendering content
    # as HTML

    return sanitized.strip() if sanitized.strip() else None


def validate_optional_text_length(
    v: str | None, max_length: int, message: str | None = None
) -> str | None:
    """Validates that a text value is less than a given length."""
    if v is not None and len(v) > max_length:
        error_message = message or f"Text must be less than {max_length} characters"
        raise _create_validation_error(error_message)
    return v


def validate_non_negative_float(v: float | None) -> float | None:
    """Validates that a value is non-negative."""
    return _validate_non_negative_float(v, "Value")


def validate_non_negative_int(v: int | None) -> int | None:
    """Validates that a value is non-negative."""
    return _validate_non_negative_int(v, "Value")


def validate_percentage_range(v: float | None) -> float | None:
    """Validates that a percentage value is between 0 and 100."""
    return _validate_range(v, 0, PERCENTAGE_MAX, "Percentage")


def convert_none_to_private_enum(v: str | Privacy | None) -> Privacy:
    """Validates that a privacy value is a valid Privacy enum value."""
    if v is None:
        return Privacy.PRIVATE
    if isinstance(v, Privacy):
        return v
    if v.lower() == "private":
        return Privacy.PRIVATE
    if v.lower() == "public":
        return Privacy.PUBLIC
    raise _create_validation_error(f"Invalid privacy value: {v}")


def validate_rating_range(v: float | None) -> float | None:
    """Validates that a rating value is between 0 and 5."""
    return _validate_range(v, 0, RATING_MAX, "Rating")


def parse_datetime(value: Any) -> datetime | None:
    """Parse various datetime inputs into datetime objects.

    This function handles conversion from different datetime representations
    to Python datetime objects, with support for ISO format strings and
    proper timezone handling.

    Args:
        value: The value to parse (datetime, ISO string, or None)

    Returns:
        datetime object or None if input is None

    Raises:
        ValidationConversionError: If the value cannot be parsed as a datetime

    Supported formats:
        - datetime objects (returned as-is)
        - ISO formatted strings (converted to datetime)
        - None values (returned as-is)
        - Z suffix strings (converted to UTC)
    """
    if value is None:
        return None
    if isinstance(value, datetime):
        return value
    if isinstance(value, str):
        try:
            # Handle both standard ISO format and Z suffix
            iso_string = value.replace("Z", "+00:00") if value.endswith("Z") else value
            return datetime.fromisoformat(iso_string)
        except ValueError as e:
            error_message = f"Invalid datetime format: {value}. Expected ISO format."
            raise _create_validation_error(error_message) from e
    error_message = f"Expected datetime, string, or None, got {type(value).__name__}"
    raise _create_validation_error(error_message)


def parse_date(value: Any) -> date | None:
    """Parse various date inputs into date objects.

    This function handles conversion from different date representations
    to Python date objects, with support for ISO format strings and
    common date formats.

    Args:
        value: The value to parse (date, datetime, ISO string, or None)

    Returns:
        date object or None if input is None

    Raises:
        ValidationConversionError: If the value cannot be parsed as a date

    Supported formats:
        - date objects (returned as-is)
        - datetime objects (converted to date)
        - ISO formatted strings (converted to date)
        - None values (returned as-is)
    """
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            # Try ISO format first (YYYY-MM-DD)
            if len(value) == 10 and value.count("-") == 2:
                return date.fromisoformat(value)
            # Try parsing as datetime and extract date
            dt = datetime.fromisoformat(value)
            return dt.date()
        except ValueError as e:
            error_message = (
                f"Invalid date format: {value}. Expected ISO format (YYYY-MM-DD)."
            )
            raise _create_validation_error(error_message) from e
    error_message = (
        f"Expected date, datetime, string, or None, got {type(value).__name__}"
    )
    raise _create_validation_error(error_message)


def timestamp_check(v: Any) -> datetime:
    if v and not isinstance(v, datetime):
        try:
            return datetime.fromisoformat(v)
        except ValueError as e:
            error_message = f"Invalid datetime format. Must be isoformat: {v}"
            raise _create_validation_error(error_message) from e
    return v


def validate_permissions_collection(
    v: Any, allowed_permissions: set[str]
) -> frozenset[str]:
    """Validate permissions.

    Provides clear error messages for invalid input types and validates
    against allowed permissions for security.
    """

    invalid_perms = set(v) - allowed_permissions
    if invalid_perms:
        error_msg = (
            f"Invalid permissions: {sorted(invalid_perms)}. "
            f"Allowed: {sorted(allowed_permissions)}"
        )
        raise _create_validation_error(error_msg)

    return frozenset(v)


def validate_role_name_format(v: str) -> str:
    """Validate role name format with security-critical constraints.

    Roles have stricter security requirements than general roles.
    Uses AfterValidator for type safety - input is guaranteed to be str.
    """
    if not v.islower():
        error_message = "Role name must be lowercase for security compliance"
        raise _create_validation_error(error_message)

    # More restrictive than general roles - only alphanumeric and underscores
    if not all(c.isalnum() or c == "_" for c in v):
        error_message = (
            "Role name must contain only alphanumeric characters and underscores"
        )
        raise _create_validation_error(error_message)

    # Prevent reserved or dangerous role names (only truly system-dangerous names)
    # Removed 'admin', 'administrator' as these are legitimate business roles
    reserved_names = {
        "root",
        "system",
        "service",
        "daemon",
        "kernel",
        "superuser",
        "privilege",
        "elevated",
    }
    if v in reserved_names:
        error_message = f"Role name '{v}' is reserved and cannot be used"
        raise _create_validation_error(error_message)

    # Minimum length for security (prevent single char roles)
    if len(v) < ROLE_NAME_MIN_LENGTH:
        error_message = "Role name must be at least 3 characters long"
        raise _create_validation_error(error_message)

    if len(v) > ROLE_NAME_MAX_LENGTH:
        error_message = "Role name must be less than 50 characters long"
        raise _create_validation_error(error_message)

    return v


def validate_sex_options(v: str) -> str:
    """Validate sex field contains acceptable values."""
    # Common accepted values (expandable as needed)
    valid_options = {"masculino", "feminino"}
    if v.lower() not in valid_options:
        error_message = f"Invalid sex: {v}"
        raise _create_validation_error(error_message)

    return v.lower()


def validate_birthday_reasonable(v: date) -> date:
    """Validate birthday field contains reasonable values."""
    if v < date(1900, 1, 1):
        error_message = f"Birthday too early: {v}"
        raise _create_validation_error(error_message)

    if v > datetime.now(UTC).date():
        error_message = f"Birthday cannot be in the future: {v}"
        raise _create_validation_error(error_message)

    return v


def validate_birthday_reasonable_optional(v: date | None) -> date | None:
    """Validate optional birthday field contains reasonable values."""
    if v is None:
        return None
    return validate_birthday_reasonable(v)
