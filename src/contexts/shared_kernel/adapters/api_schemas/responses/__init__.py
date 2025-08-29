"""
Shared Kernel Schemas

Common response and error schemas used across all contexts.
"""

# Base Response Types
# Error Response Types
from src.contexts.shared_kernel.adapters.api_schemas.responses.base_response import (
    BaseResponse,
    CreatedResponse,
    MessageResponse,
    NoContentResponse,
    SuccessResponse,
)

# Collection Response Types
from src.contexts.shared_kernel.adapters.api_schemas.responses.collection_response import (
    CollectionResponse,
    create_paginated_response,
)
from src.contexts.shared_kernel.adapters.api_schemas.responses.error_response import (
    AuthenticationErrorResponse,
    AuthorizationErrorResponse,
    BusinessRuleErrorResponse,
    ConflictErrorResponse,
    ErrorDetail,
    ErrorResponse,
    ErrorType,
    InternalErrorResponse,
    NotFoundErrorResponse,
    TimeoutErrorResponse,
    ValidationErrorResponse,
    create_detail_error,
    create_message_error,
)

__all__ = [
    # Base Response Types
    "BaseResponse",
    "SuccessResponse",
    "CreatedResponse",
    "NoContentResponse",
    "MessageResponse",
    # Collection Response Types
    "CollectionResponse",
    "create_paginated_response",
    # Error Response Types
    "ErrorResponse",
    "ErrorType",
    "ErrorDetail",
    "ValidationErrorResponse",
    "NotFoundErrorResponse",
    "AuthenticationErrorResponse",
    "AuthorizationErrorResponse",
    "ConflictErrorResponse",
    "BusinessRuleErrorResponse",
    "TimeoutErrorResponse",
    "InternalErrorResponse",
    "create_detail_error",
    "create_message_error",
]
