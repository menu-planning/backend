# Shared modules for client onboarding Lambda functions

from src.contexts.client_onboarding.aws_lambda.shared.cors_headers import CORS_headers
from src.contexts.client_onboarding.aws_lambda.shared.query_executor import (
    execute_query,
)

__all__ = [
    "CORS_headers",
    "execute_query",
]
