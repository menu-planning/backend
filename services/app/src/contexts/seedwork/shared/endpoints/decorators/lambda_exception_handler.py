import functools
import json
from typing import Any, Callable, Dict, Optional

from pydantic_core import ValidationError
from src.contexts.seedwork.shared.adapters.exceptions.repo_exceptions import (
    EntityNotFoundException,
    MultipleEntitiesFoundException,
)

# Default CORS headers if none provided
DEFAULT_CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Headers": "Authorization, Content-Type",
    "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
}


def lambda_exception_handler(cors_headers: Optional[Dict[str, str]] = None):
    """
    Lambda exception handler decorator that includes CORS headers in error responses.
    
    Args:
        cors_headers: CORS headers to include in error responses. If None, uses defaults.
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(event: dict[str, Any], context: Any) -> dict[str, Any]:
            # Use provided CORS headers or defaults
            error_headers = cors_headers if cors_headers is not None else DEFAULT_CORS_HEADERS
            
            try:
                return await func(event, context)
            except EntityNotFoundException as e:
                return {
                    "statusCode": 404, 
                    "headers": error_headers,
                    "body": json.dumps({"message": "User not in database."})
                }
            except MultipleEntitiesFoundException as e:
                return {
                    "statusCode": 409, 
                    "headers": error_headers,
                    "body": json.dumps({"detail": str(e)})
                }
            except TimeoutError as e:
                return {
                    "statusCode": 408,
                    "headers": error_headers,
                    "body": json.dumps(
                        {"detail": "Request processing time exceeded limit"}
                    ),
                }
            except ValidationError as e:
                return {
                    "statusCode": 422, 
                    "headers": error_headers,
                    "body": json.dumps({"detail": str(e)})
                }
            except ValueError as e:
                return {
                    "statusCode": 400,
                    "headers": error_headers,
                    "body": json.dumps({"detail": f"Error processing data: {str(e)}"}),
                }
            except Exception as e:
                return {
                    "statusCode": 500,
                    "headers": error_headers,
                    "body": json.dumps(
                        {"detail": f"An unexpected error occurred: {str(e)}"}
                    ),
                }

        return wrapper
    return decorator
