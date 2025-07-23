"""
Simple utilities for AWS Lambda endpoint handlers.

This module provides lightweight helper functions for common Lambda operations:
- Event parsing (path params, query params, body, user ID)
- Response formatting with CORS headers
- Basic auth helper integration

Does NOT provide:
- Exception handling (use @lambda_exception_handler decorator)
- Timeout management (handled by MessageBus)
- Logging orchestration (handle in specific handlers/MessageBus)
"""

import json
import os
from typing import Any, Dict, Optional, Union, List


class LambdaHelpers:
    """
    Static utilities for AWS Lambda endpoint handlers.
    
    Provides simple, focused helpers for common Lambda operations without
    trying to be a framework. Use alongside existing patterns:
    - @lambda_exception_handler for exception handling
    - MessageBus for business logic and timeouts
    - Direct IAMProvider.get() calls for auth
    
    Usage:
        @lambda_exception_handler
        async def async_handler(event, context):
            user_id = LambdaHelpers.extract_user_id(event)
            recipe_id = LambdaHelpers.extract_path_parameter(event, "id")
            body = LambdaHelpers.extract_request_body(event)
            
            # Business logic...
            
            # Build response directly
            return {
                "statusCode": 200,
                "headers": LambdaHelpers.get_default_cors_headers(),
                "body": json.dumps(result)
            }
    """
    
    @staticmethod
    def extract_path_parameter(event: Dict[str, Any], param_name: str) -> Optional[str]:
        """Extract path parameter from Lambda event."""
        path_parameters = event.get("pathParameters") or {}
        return path_parameters.get(param_name)

    @staticmethod
    def extract_query_parameters(event: Dict[str, Any]) -> Dict[str, Any]:
        """Extract query parameters from Lambda event."""
        return event.get("queryStringParameters") or {}

    @staticmethod
    def extract_multi_value_query_parameters(event: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extract multi-value query parameters from Lambda event."""
        return event.get("multiValueQueryStringParameters") or {}

    @staticmethod
    def extract_request_body(event: Dict[str, Any], parse_json: bool = True) -> Union[str, Dict[str, Any]]:
        """
        Extract request body from Lambda event.
        
        Args:
            event: Lambda event
            parse_json: Whether to parse body as JSON
            
        Returns:
            Parsed JSON dict if parse_json=True, raw string otherwise
        """
        body = event.get("body", "")
        if parse_json and body:
            try:
                return json.loads(body)
            except json.JSONDecodeError:
                raise ValueError("Invalid JSON in request body")
        return body

    @staticmethod
    def extract_user_id(event: Dict[str, Any]) -> Optional[str]:
        """Extract user ID from Lambda event authorizer context."""
        try:
            return event["requestContext"]["authorizer"]["claims"]["sub"]
        except (KeyError, TypeError):
            return None

    @staticmethod
    def is_localstack_environment() -> bool:
        """Check if running in localstack environment."""
        return os.getenv("IS_LOCALSTACK", "false").lower() == "true"

    @staticmethod
    def get_default_cors_headers() -> Dict[str, str]:
        """Get default CORS headers."""
        return {
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Authorization, Content-Type",
            "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
        }

    @staticmethod
    def format_error_response(
        message: str,
        status_code: int = 500,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        cors_headers: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Format error response (though @lambda_exception_handler usually handles this).
        
        Args:
            message: Error message
            status_code: HTTP status code
            error_code: Optional error code
            details: Optional error details
            cors_headers: Custom CORS headers (uses defaults if None)
            
        Returns:
            Formatted Lambda error response dict
        """
        headers = cors_headers or LambdaHelpers.get_default_cors_headers()
        
        error_body: Dict[str, Any] = {"message": message}
        if error_code:
            error_body["error_code"] = error_code
        if details:
            error_body["details"] = details

        return {
            "statusCode": status_code,
            "headers": headers,
            "body": json.dumps(error_body)
        }


# For backward compatibility during migration
BaseEndpointHandler = LambdaHelpers

# Convenience functions for common patterns
def extract_path_parameter(event: Dict[str, Any], param_name: str) -> Optional[str]:
    """Convenience function for path parameter extraction."""
    return LambdaHelpers.extract_path_parameter(event, param_name)

def extract_user_id(event: Dict[str, Any]) -> Optional[str]:
    """Convenience function for user ID extraction."""
    return LambdaHelpers.extract_user_id(event) 