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
from typing import Any, Dict, Optional, Union, List, Type
from pydantic import BaseModel


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
    def extract_log_data(
        event: Dict[str, Any], 
        include_body: bool = False,
        mask_sensitive_fields: bool = True
    ) -> Dict[str, Any]:
        """
        Extract standardized log data from Lambda event.
        
        Provides consistent logging structure across all Lambda endpoints.
        Safely handles missing fields and optionally masks sensitive data.
        
        Args:
            event: Lambda event
            include_body: Whether to include request body in log data (default: False for security)
            mask_sensitive_fields: Whether to mask potentially sensitive data like emails, 
                                 query parameters, etc. (default: True)
            
        Returns:
            Dictionary with standardized log information
            
        Example:
            log_data = LambdaHelpers.extract_log_data(event, include_body=True)
            logger.info("Request received", extra=log_data)
        """
        # Extract user claims safely
        request_context = event.get("requestContext", {})
        authorizer = request_context.get("authorizer", {})
        claims = authorizer.get("claims", {})
        
        # Extract email and potentially mask it
        email = claims.get("email")
        if mask_sensitive_fields and email:
            # Mask email but keep domain for debugging purposes
            email_parts = email.split("@")
            if len(email_parts) == 2:
                username, domain = email_parts
                # Keep first and last character of username if long enough
                if len(username) > 2:
                    masked_username = username[0] + "*" * (len(username) - 2) + username[-1]
                else:
                    masked_username = "*" * len(username)
                email = f"{masked_username}@{domain}"
            else:
                email = "[MASKED_EMAIL]"
        
        # Build log data structure
        log_data = {
            "method": event.get("httpMethod"),
            "path": event.get("path"),
            "query": event.get("queryStringParameters"),
            "path_params": event.get("pathParameters"),
            "user": claims.get("sub"),
            "email": email,
            "request_id": request_context.get("requestId"),
            "correlation_id": event.get("correlation_id"),
        }
        
        # Optionally include body (be careful with sensitive data)
        if include_body:
            body = event.get("body")
            if body and mask_sensitive_fields:
                # Only include body size for security if masking is enabled
                log_data["body_size"] = len(body) if body else 0
                log_data["body_included"] = "masked_for_security"
            else:
                log_data["body"] = body
        
        # Mask sensitive query parameters if requested
        if mask_sensitive_fields and log_data.get("query"):
            sensitive_params = {
                "password", "token", "secret", "key", "auth", "authorization",
                "api_key", "api-key", "apikey", "access_token", "access-token",
                "refresh_token", "refresh-token", "jwt", "bearer"
            }
            masked_query = {}
            for k, v in log_data["query"].items():
                if any(sensitive in k.lower() for sensitive in sensitive_params):
                    masked_query[k] = "[MASKED]"
                else:
                    masked_query[k] = v
            log_data["query"] = masked_query
        
        # Remove None values for cleaner logs
        return {k: v for k, v in log_data.items() if v is not None}

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
    def normalize_kebab_case_keys(params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert kebab-case parameter keys to snake_case.
        
        Args:
            params: Dictionary with potentially kebab-case keys
            
        Returns:
            Dictionary with snake_case keys
            
        Example:
            {"foo-bar": "value"} -> {"foo_bar": "value"}
        """
        return {k.replace("-", "_"): v for k, v in params.items()}

    @staticmethod
    def flatten_single_item_lists(params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert single-item lists to scalar values.
        
        Args:
            params: Dictionary that may contain single-item lists
            
        Returns:
            Dictionary with single-item lists converted to scalars
            
        Example:
            {"key": ["value"]} -> {"key": "value"}
            {"key": ["val1", "val2"]} -> {"key": ["val1", "val2"]} (unchanged)
        """
        result = {}
        for k, v in params.items():
            if isinstance(v, list) and len(v) == 1:
                result[k] = v[0]
            else:
                result[k] = v
        return result

    @staticmethod
    def extract_pagination_params(
        params: Dict[str, Any], 
        default_limit: int = 50,
        default_sort: str = "-updated_at"
    ) -> Dict[str, Any]:
        """
        Extract and normalize limit and sort parameters from query parameters.
        
        Handles both single values and lists (extracts first item from lists).
        
        Args:
            params: Query parameters dictionary
            default_limit: Default limit value if not provided
            default_sort: Default sort value if not provided
            
        Returns:
            Dictionary with normalized limit and sort values
        """
        result = dict(params)
        
        # Handle limit parameter
        limit_value = params.get("limit", [default_limit])
        if isinstance(limit_value, list):
            limit_value = limit_value[0] if limit_value else default_limit
        result["limit"] = int(limit_value)
        
        # Handle sort parameter
        sort_value = params.get("sort", [default_sort])
        if isinstance(sort_value, list):
            sort_value = sort_value[0] if sort_value else default_sort
        result["sort"] = sort_value
        
        return result

    @staticmethod
    def process_query_filters(
        event: Dict[str, Any],
        filter_schema_class: Type[BaseModel],
        use_multi_value: bool = False,
        default_limit: int = 50,
        default_sort: str = "-updated_at"
    ) -> Dict[str, Any]:
        """
        Complete query parameter processing pipeline for filtering.
        
        Performs the common sequence:
        1. Extract query parameters (single or multi-value)
        2. Convert kebab-case to snake_case
        3. Handle pagination parameters (limit/sort)
        4. Flatten single-item lists
        5. Validate/normalize through Pydantic schema
        
        Args:
            event: Lambda event
            filter_schema_class: Pydantic model class for filter validation
            use_multi_value: Whether to use multi-value query parameters
            default_limit: Default limit if not provided
            default_sort: Default sort if not provided
            
        Returns:
            Processed and normalized filters dictionary
            
        Example:
            filters = LambdaHelpers.process_query_filters(
                event, 
                ApiProductFilter,
                use_multi_value=True,
                default_limit=50,
                default_sort="-updated_at"
            )
        """
        # Extract query parameters
        if use_multi_value:
            query_params = LambdaHelpers.extract_multi_value_query_parameters(event)
        else:
            query_params = LambdaHelpers.extract_query_parameters(event)
        
        if not query_params:
            query_params = {}
        
        # Convert kebab-case to snake_case
        filters = LambdaHelpers.normalize_kebab_case_keys(query_params)
        
        # Handle pagination parameters if using multi-value
        if use_multi_value:
            filters = LambdaHelpers.extract_pagination_params(
                filters, default_limit, default_sort
            )
            # Flatten other single-item lists
            filters = LambdaHelpers.flatten_single_item_lists(filters)
        
        # Validate and normalize through schema
        filters = LambdaHelpers.normalize_filter_values(filters, filter_schema_class)
        
        return filters

    @staticmethod
    def normalize_filter_values(
        filters: Dict[str, Any], 
        filter_schema_class: Type[BaseModel]
    ) -> Dict[str, Any]:
        """
        Validate and normalize filter values using a Pydantic schema.
        
        Args:
            filters: Raw filters dictionary
            filter_schema_class: Pydantic model class for validation
            
        Returns:
            Normalized filters with validated values from the schema
            
        Example:
            normalized = LambdaHelpers.normalize_filter_values(
                {"limit": "50", "sort": "name"}, 
                ApiProductFilter
            )
        """
        # Create schema instance for validation
        api_filters = filter_schema_class(**filters)
        api_dict = api_filters.model_dump()
        
        # Apply normalized values back to filters
        for k in filters.keys():
            filters[k] = api_dict.get(k)
        
        return filters

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

def extract_log_data(
    event: Dict[str, Any], 
    include_body: bool = False,
    mask_sensitive_fields: bool = True
) -> Dict[str, Any]:
    """Convenience function for log data extraction."""
    return LambdaHelpers.extract_log_data(event, include_body, mask_sensitive_fields) 