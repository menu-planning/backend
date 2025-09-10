"""
Essential utilities for AWS Lambda endpoint handlers.

This module provides lightweight helper functions for common Lambda operations:
- Event parsing (path params, query params, body)
- Query parameter processing and filtering
- Response formatting with CORS headers

Does NOT provide (now handled by unified middleware):
- Exception handling (use @aws_lambda_exception_handler_middleware)
- Authentication (use context-specific auth middleware)
- Logging orchestration (use @aws_lambda_logging_middleware)
- Timeout management (handled by middleware timeout configuration)
"""

import json
from typing import Any

from pydantic import BaseModel


class LambdaHelpers:
    """Static utilities for AWS Lambda endpoint handlers.

    Complements unified middleware with focused helpers for event parsing and
    response formatting.
    """

    @staticmethod
    def extract_path_parameter(event: dict[str, Any], param_name: str) -> str | None:
        """Extract path parameter from Lambda event.

        Args:
            event: Lambda event dictionary containing pathParameters.
            param_name: Name of the path parameter to extract.

        Returns:
            Path parameter value or None if not found.
        """
        path_parameters = event.get("pathParameters") or {}
        return path_parameters.get(param_name)

    @staticmethod
    def extract_query_parameters(event: dict[str, Any]) -> dict[str, Any]:
        """Extract query parameters from Lambda event.

        Args:
            event: Lambda event dictionary containing queryStringParameters.

        Returns:
            Dictionary of query parameters or empty dict if none present.
        """
        return event.get("queryStringParameters") or {}

    @staticmethod
    def extract_multi_value_query_parameters(
        event: dict[str, Any],
    ) -> dict[str, list[str]]:
        """Extract multi-value query parameters from Lambda event.

        Args:
            event: Lambda event dictionary containing multiValueQueryStringParameters.

        Returns:
            Dictionary mapping parameter names to lists of values or empty dict.
        """
        return event.get("multiValueQueryStringParameters") or {}

    @staticmethod
    def extract_request_body(
        event: dict[str, Any], *, parse_json: bool = True
    ) -> str | dict[str, Any]:
        """Extract and optionally parse request body from Lambda event.

        Args:
            event: Lambda event dictionary containing body.
            parse_json: Whether to parse body as JSON.

        Returns:
            Parsed JSON dict if parse_json=True, raw string otherwise.

        Raises:
            ValueError: When parse_json=True and body contains invalid JSON.
        """
        body = event.get("body", "")

        if not body:
            return body

        if parse_json and body:
            try:
                parsed = json.loads(body)
            except json.JSONDecodeError as e:
                error_msg = "Invalid JSON in request body"
                raise ValueError(error_msg) from e
            else:
                return parsed

        return body

    @staticmethod
    def normalize_kebab_case_keys(params: dict[str, Any]) -> dict[str, Any]:
        """Convert kebab-case parameter keys to snake_case.

        Args:
            params: Dictionary with potentially kebab-case keys.

        Returns:
            Dictionary with snake_case keys.

        Example:
            {"foo-bar": "value"} -> {"foo_bar": "value"}
        """
        return {k.replace("-", "_"): v for k, v in params.items()}

    @staticmethod
    def flatten_single_item_lists(params: dict[str, Any]) -> dict[str, Any]:
        """Convert single-item lists to scalar values.

        Args:
            params: Dictionary that may contain single-item lists.

        Returns:
            Dictionary with single-item lists converted to scalars.

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
        params: dict[str, Any],
        default_limit: int = 50,
        default_sort: str = "-updated_at",
    ) -> dict[str, Any]:
        """Extract and normalize limit and sort parameters from query parameters.

        Handles both single values and lists (extracts first item from lists).

        Args:
            params: Query parameters dictionary.
            default_limit: Default limit value if not provided.
            default_sort: Default sort value if not provided.

        Returns:
            Dictionary with normalized limit and sort values.
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
    def process_query_filters_from_aws_event(
        *,
        event: dict[str, Any],
        filter_schema_class: type[BaseModel],
        use_multi_value: bool = False,
        default_limit: int = 50,
        default_sort: str = "-updated_at",
    ) -> dict[str, Any]:
        """Complete query parameter processing pipeline for filtering.

        Performs the common sequence:
        1. Extract query parameters (single or multi-value)
        2. Convert kebab-case to snake_case
        3. Handle pagination parameters (limit/sort)
        4. Flatten single-item lists
        5. Validate/normalize through Pydantic schema

        Args:
            event: Lambda event dictionary.
            filter_schema_class: Pydantic model class for filter validation.
            use_multi_value: Whether to use multi-value query parameters.
            default_limit: Default limit if not provided.
            default_sort: Default sort if not provided.

        Returns:
            Processed and normalized filters dictionary.

        Example:
            filters = LambdaHelpers.process_query_filters_from_aws_event(
                event=event,
                filter_schema_class=ApiRecipeFilter,
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

        # Apply pagination defaults
        if "limit" not in filters:
            filters["limit"] = default_limit

        if "sort" not in filters:
            filters["sort"] = default_sort

        # Flatten single-item lists for cleaner filtering
        filters = LambdaHelpers.flatten_single_item_lists(filters)

        # Validate and normalize through Pydantic schema
        try:
            final_filters = LambdaHelpers.normalize_filter_values(
                filters, filter_schema_class
            )
        except Exception:
            # Return empty filters if validation fails
            return {}
        else:
            return final_filters

    @staticmethod
    def normalize_filter_values(
        filters: dict[str, Any], filter_schema_class: type[BaseModel]
    ) -> dict[str, Any]:
        """Validate and normalize filter values using a Pydantic schema.

        Args:
            filters: Raw filters dictionary.
            filter_schema_class: Pydantic model class for validation.

        Returns:
            Normalized filters with validated values from the schema.
            Unknown parameters are preserved as-is for debugging purposes.

        Example:
            normalized = LambdaHelpers.normalize_filter_values(
                {"limit": "50", "sort": "name"},
                ApiProductFilter
            )
        """
        # Separate known and unknown parameters
        known_params = {}
        unknown_params = {}

        # Get the field names defined in the schema
        schema_fields = set(filter_schema_class.model_fields.keys())

        for key, value in filters.items():
            if key in schema_fields:
                known_params[key] = value
            else:
                unknown_params[key] = value

        # Validate only known parameters
        if known_params:
            try:
                api_filters = filter_schema_class(**known_params)
                api_dict = api_filters.model_dump()

                # Update known parameters with normalized values
                for key in known_params:
                    known_params[key] = api_dict.get(key)
            except Exception:
                # If validation fails, keep original values for known params
                pass

        # Combine normalized known params with preserved unknown params
        result = {**known_params, **unknown_params}

        return result
