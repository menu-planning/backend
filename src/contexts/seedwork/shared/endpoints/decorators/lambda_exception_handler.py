import functools
import json
from collections.abc import Callable
from typing import Any

from pydantic_core import ValidationError

from src.contexts.seedwork.shared.adapters.exceptions.repo_exceptions import (
    EntityNotFoundError,
    MultipleEntitiesFoundError,
)

# Default CORS headers if none provided
DEFAULT_CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Authorization, Content-Type",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
}


def lambda_exception_handler(cors_headers: dict[str, str] | None = None):
    """
    Lambda exception handler decorator that includes CORS headers in error responses.

    Args:
        cors_headers: CORS headers to include in error responses.
                     If None, uses defaults.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(event: dict[str, Any], context: Any) -> dict[str, Any]:
            # Use provided CORS headers or defaults
            error_headers = (
                cors_headers if cors_headers is not None else DEFAULT_CORS_HEADERS
            )

            def create_error_response(status_code: int, message: str) -> dict[str, Any]:
                """Helper function to create standardized error responses."""
                return {
                    "statusCode": status_code,
                    "headers": error_headers,
                    "body": json.dumps({"detail": message}),
                }

            result = None
            try:
                result = await func(event, context)
            except EntityNotFoundError:
                result = create_error_response(404, "User not in database.")
            except MultipleEntitiesFoundError as e:
                result = create_error_response(409, str(e))
            except TimeoutError:
                result = create_error_response(
                    408, "Request processing time exceeded limit"
                )
            except ValidationError as e:
                result = create_error_response(422, str(e))
            except ValueError as e:
                result = create_error_response(400, f"Error processing data: {e!s}")
            except Exception as e:
                result = create_error_response(
                    500, f"An unexpected error occurred: {e!s}"
                )

            return result

        return wrapper

    return decorator
