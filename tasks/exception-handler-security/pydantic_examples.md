# Pydantic v2 Security Implementation Examples

## Overview
This document shows concrete examples of how to implement security features using Pydantic v2, following the existing `BaseApiModel` patterns.

## 1. Security Headers Model

```python
# src/contexts/shared_kernel/middleware/error_handling/security_headers.py
from src.contexts.seedwork.adapters.api_schemas.base_api_model import BaseApiModel
from pydantic import Field, validator
from typing import Dict, Any

class SecurityHeaders(BaseApiModel):
    """Pydantic model for HTTP security headers using BaseApiModel patterns."""
    
    x_content_type_options: str = Field(default="nosniff", description="Prevent MIME type sniffing")
    x_frame_options: str = Field(default="DENY", description="Prevent clickjacking")
    x_xss_protection: str = Field(default="1; mode=block", description="XSS protection")
    strict_transport_security: str = Field(default="max-age=31536000; includeSubDomains", description="HSTS")
    referrer_policy: str = Field(default="strict-origin-when-cross-origin", description="Referrer policy")
    content_security_policy: str = Field(default="default-src 'self'", description="CSP")
    
    @validator('x_content_type_options')
    def validate_content_type_options(cls, v):
        if v not in ["nosniff"]:
            raise ValueError("Invalid X-Content-Type-Options value")
        return v
    
    @validator('x_frame_options')
    def validate_frame_options(cls, v):
        if v not in ["DENY", "SAMEORIGIN"]:
            raise ValueError("Invalid X-Frame-Options value")
        return v
    
    def to_dict(self) -> Dict[str, str]:
        """Convert to dictionary for HTTP headers."""
        return {
            "X-Content-Type-Options": self.x_content_type_options,
            "X-Frame-Options": self.x_frame_options,
            "X-XSS-Protection": self.x_xss_protection,
            "Strict-Transport-Security": self.strict_transport_security,
            "Referrer-Policy": self.referrer_policy,
            "Content-Security-Policy": self.content_security_policy,
        }
```

## 2. Sanitized Error Message Model

```python
# src/contexts/shared_kernel/middleware/error_handling/sanitized_models.py
from src.contexts.seedwork.adapters.api_schemas.base_api_model import BaseApiModel
from src.contexts.seedwork.adapters.api_schemas.base_api_fields import SanitizedText, SanitizedTextOptional
from src.contexts.seedwork.adapters.api_schemas.validators import sanitize_text_input
from pydantic import Field, validator
import re
from typing import Any

class SanitizedErrorMessage(BaseApiModel):
    """Pydantic model for sanitized error messages using existing validators."""
    
    # Use existing SanitizedText fields for automatic sanitization
    message: SanitizedText = Field(..., description="Sanitized error message")
    details: SanitizedTextOptional = Field(None, description="Sanitized error details")
    
    @validator('message', 'details')
    def sanitize_sensitive_data(cls, v):
        """Additional sanitization for sensitive data patterns on top of existing validators."""
        if not v:
            return v
            
        # First apply existing sanitization (XSS, SQL injection, etc.)
        sanitized = sanitize_text_input(v)
        if not sanitized:
            return sanitized
            
        # Add middleware-specific sensitive data sanitization
        # Sanitize database connection strings
        sanitized = re.sub(r'postgresql://[^@]+@[^/]+', 'postgresql://***:***@***', sanitized)
        sanitized = re.sub(r'mysql://[^@]+@[^/]+', 'mysql://***:***@***', sanitized)
        
        # Sanitize API keys
        sanitized = re.sub(r'api[_-]?key["\s]*[:=]["\s]*[a-zA-Z0-9_-]+', 'api_key="***"', sanitized, flags=re.IGNORECASE)
        sanitized = re.sub(r'token["\s]*[:=]["\s]*[a-zA-Z0-9_-]+', 'token="***"', sanitized, flags=re.IGNORECASE)
        
        # Sanitize file paths
        sanitized = re.sub(r'/[a-zA-Z0-9_/-]+\.(py|pyc|log|db|sqlite)', '/***/***.py', sanitized)
        
        return sanitized
```

## 3. Secure Error Response Model

```python
# src/contexts/shared_kernel/middleware/error_handling/secure_models.py
from src.contexts.seedwork.adapters.api_schemas.base_api_model import BaseApiModel
from pydantic import Field, validator
from typing import Optional, Dict, Any
import os

class SecureErrorResponse(BaseApiModel):
    """Pydantic model for secure error responses using BaseApiModel patterns."""
    
    message: str = Field(..., description="Sanitized error message")
    details: Optional[str] = Field(None, description="Sanitized error details")
    stack_trace: Optional[str] = Field(None, description="Stack trace (only in development)")
    internal_details: Optional[str] = Field(None, description="Internal details (only in development)")
    
    @validator('stack_trace')
    def filter_stack_trace(cls, v):
        """Filter stack traces in production."""
        if os.getenv('ENVIRONMENT') == 'production':
            return None
        return v
    
    @validator('internal_details')
    def filter_internal_details(cls, v):
        """Filter internal details in production."""
        if os.getenv('ENVIRONMENT') == 'production':
            return None
        return v
    
    @validator('message', 'details')
    def sanitize_all_text(cls, v):
        """Sanitize all text fields."""
        if not isinstance(v, str):
            return v
        
        # Apply all sanitization rules
        sanitized = SanitizedErrorMessage(message=v)
        return sanitized.message
```

## 4. Enhanced ErrorResponse Integration

```python
# src/contexts/shared_kernel/middleware/error_handling/error_response.py
from src.contexts.seedwork.adapters.api_schemas.base_api_model import BaseApiModel
from pydantic import Field, validator
from typing import Optional, Dict, Any
from .security_headers import SecurityHeaders
from .secure_models import SecureErrorResponse

class ErrorResponse(BaseApiModel):
    """Enhanced error response with security features."""
    
    # Existing fields
    error_type: str = Field(..., description="Error type")
    message: str = Field(..., description="Error message")
    details: Optional[str] = Field(None, description="Error details")
    status_code: int = Field(..., description="HTTP status code")
    
    # New security fields
    headers: Optional[Dict[str, str]] = Field(None, description="Security headers")
    sanitized_message: Optional[str] = Field(None, description="Sanitized message")
    
    @validator('message')
    def sanitize_message(cls, v):
        """Sanitize error message."""
        if not isinstance(v, str):
            return v
        
        # Use Pydantic sanitization
        sanitized = SanitizedErrorMessage(message=v)
        return sanitized.message
    
    @validator('details')
    def sanitize_details(cls, v):
        """Sanitize error details."""
        if not v or not isinstance(v, str):
            return v
        
        # Use Pydantic sanitization
        sanitized = SanitizedErrorMessage(message=v)
        return sanitized.message
    
    def add_security_headers(self) -> 'ErrorResponse':
        """Add security headers to error response."""
        security_headers = SecurityHeaders()
        self.headers = security_headers.to_dict()
        return self
    
    def to_secure_response(self) -> SecureErrorResponse:
        """Convert to secure error response."""
        return SecureErrorResponse(
            message=self.sanitized_message or self.message,
            details=self.details,
            stack_trace=getattr(self, 'stack_trace', None),
            internal_details=getattr(self, 'internal_details', None)
        )
```

## 5. Exception Handler Integration

```python
# src/contexts/shared_kernel/middleware/error_handling/exception_handler.py
from .error_response import ErrorResponse
from .security_headers import SecurityHeaders
from .secure_models import SecureErrorResponse

class ExceptionHandlerMiddleware:
    """Enhanced exception handler with Pydantic v2 security."""
    
    def create_error_response(self, exception: Exception, context: Any) -> ErrorResponse:
        """Create secure error response using Pydantic models."""
        
        # Create base error response
        error_response = ErrorResponse(
            error_type=self._get_error_type(exception),
            message=str(exception),
            details=self._get_error_details(exception),
            status_code=self._get_status_code(exception)
        )
        
        # Add security headers
        error_response.add_security_headers()
        
        # Convert to secure response
        secure_response = error_response.to_secure_response()
        
        return secure_response
```

## Key Benefits

1. **Consistency**: Uses same `BaseApiModel` patterns as existing code
2. **Type Safety**: Pydantic v2 provides full type validation
3. **Security**: Built-in sanitization and validation
4. **Maintainability**: Clear separation of concerns
5. **Testability**: Easy to test individual components
6. **Performance**: Pydantic v2 is optimized for performance
7. **AWS Lambda**: Works seamlessly with existing Lambda integration
