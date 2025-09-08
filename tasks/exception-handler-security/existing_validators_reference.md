# Existing Validators Reference

## Overview
This document lists all existing validators and fields that should be used in the middleware security implementation to maintain consistency with the existing codebase.

## Core Validator Files

### 1. Main Validators Module
**File**: `src/contexts/seedwork/adapters/api_schemas/validators.py`

**Key Functions**:
- `sanitize_text_input(v: str | None) -> str | None` - Main text sanitization function
- `validate_email_format(v: str | None) -> str | None` - Email validation
- `validate_phone_format(v: str | None) -> str | None` - Phone validation
- `validate_uuid_format(v: str) -> str` - UUID validation
- `validate_url_optinal(v: Any) -> HttpUrl | None` - URL validation
- `parse_datetime(value: Any) -> datetime | None` - Datetime parsing
- `parse_date(value: Any) -> date | None` - Date parsing

**Security Functions**:
- `_validate_security_patterns(text: str, field_name: str) -> None` - Security pattern validation
- `_create_validation_error(message: str) -> ValueError` - Standardized error creation

**Constants**:
- `EMAIL_MAX_LENGTH = 254`
- `EMAIL_LOCAL_PART_MAX_LENGTH = 64`
- `PHONE_MIN_DIGITS = 7`
- `PHONE_MAX_DIGITS = 15`
- `DANGEROUS_PATTERNS` - List of dangerous patterns for validation

### 2. Base API Fields Module
**File**: `src/contexts/seedwork/adapters/api_schemas/base_api_fields.py`

**Key Fields**:
- `SanitizedText` - Annotated[str, BeforeValidator(validators.sanitize_text_input)]
- `SanitizedTextOptional` - Annotated[str | None, BeforeValidator(validators.sanitize_text_input)]
- `EmailField` - Annotated[str, AfterValidator(validators.validate_email_format)]
- `EmailFieldOptional` - Annotated[str | None, Field(default=None), AfterValidator(validators.validate_email_format)]
- `PhoneField` - Annotated[str, AfterValidator(validators.validate_phone_format)]
- `PhoneFieldOptional` - Annotated[str | None, AfterValidator(validators.validate_phone_format)]
- `UUIDIdRequired` - Annotated[str, Field(..., description="Unique identifier for the entity"), BeforeValidator(validators.validate_uuid_format)]
- `UUIDIdOptional` - Annotated[str | None, Field(default=None, description="Unique identifier for the entity"), AfterValidator(validators.validate_optional_uuid_format)]
- `UrlOptional` - Annotated[HttpUrl | None, Field(default=None), BeforeValidator(validators.validate_url_optinal)]
- `DatetimeOptional` - Annotated[datetime | None, Field(default=None, description="ISO timestamp"), BeforeValidator(validators.parse_datetime)]
- `DatetimeRequired` - Annotated[datetime, Field(..., description="ISO timestamp"), BeforeValidator(validators.parse_datetime)]

### 3. Base API Model
**File**: `src/contexts/seedwork/adapters/api_schemas/base_api_model.py`

**Key Classes**:
- `BaseApiModel[D: Entity | ValueObject, S: SaBase]` - Main base class for API models
- `BaseApiCommand[C: Command]` - Base class for command schemas
- `BaseApiValueObject[V: ValueObject, S: SaBase]` - Base class for value object schemas
- `BaseApiEntity[E: Entity, S: SaBase]` - Base class for entity schemas

**Key Features**:
- `model_config = MODEL_CONFIG` - Strict validation configuration
- `convert: ClassVar[TypeConversionUtility] = CONVERT` - Type conversion utility
- `serialize_model()` - Custom serialization method
- `from_domain()`, `to_domain()`, `from_orm_model()`, `to_orm_kwargs()` - Conversion methods

## Usage in Middleware Security

### Import Statements
```python
# For sanitization
from src.contexts.seedwork.adapters.api_schemas.validators import sanitize_text_input
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import SanitizedText, SanitizedTextOptional

# For base models
from src.contexts.seedwork.adapters.api_schemas.base_api_model import BaseApiModel

# For validation
from src.contexts.seedwork.adapters.api_schemas.validators import validate_email_format, validate_phone_format
```

### Recommended Usage Patterns

1. **Text Sanitization**:
   ```python
   message: SanitizedText = Field(..., description="Sanitized error message")
   details: SanitizedTextOptional = Field(None, description="Sanitized error details")
   ```

2. **Additional Sanitization**:
   ```python
   @validator('message', 'details')
   def sanitize_sensitive_data(cls, v):
       if not v:
           return v
       # First apply existing sanitization
       sanitized = sanitize_text_input(v)
       if not sanitized:
           return sanitized
       # Add middleware-specific sanitization
       # (DB connections, API keys, file paths)
       return sanitized
   ```

3. **Base Model Inheritance**:
   ```python
   class SecurityHeaders(BaseApiModel):
       # Use existing model_config and patterns
       pass
   ```

## Dependencies for Each Phase

### Phase 1: Security Headers
- `src/contexts/seedwork/adapters/api_schemas/base_api_model.BaseApiModel`

### Phase 2: Input Sanitization
- `src/contexts/seedwork/adapters/api_schemas/validators.sanitize_text_input`
- `src/contexts/seedwork/adapters/api_schemas/base_api_fields.SanitizedText`
- `src/contexts/seedwork/adapters/api_schemas/base_api_fields.SanitizedTextOptional`

### Phase 3: Data Protection
- `src/contexts/seedwork/adapters/api_schemas/validators.sanitize_text_input`
- `src/contexts/seedwork/adapters/api_schemas/base_api_model.BaseApiModel`

## Security Features Already Available

1. **XSS Protection**: `sanitize_text_input()` removes script tags and dangerous HTML
2. **SQL Injection Protection**: `sanitize_text_input()` removes SQL injection patterns
3. **Input Validation**: Comprehensive validation for emails, phones, URLs, UUIDs
4. **Security Pattern Detection**: `_validate_security_patterns()` checks for dangerous content
5. **Type Safety**: Pydantic v2 with strict validation configuration
6. **Error Handling**: Standardized error messages with `_create_validation_error()`

## Notes

- All existing validators are already optimized for performance
- Security patterns are regularly updated in the main validators module
- The existing system handles both validation and sanitization
- All validators work with Pydantic v2 and the existing BaseApiModel patterns
- The system is designed to be extensible - middleware can add additional sanitization on top
