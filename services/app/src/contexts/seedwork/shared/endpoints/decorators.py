import functools
import json
from typing import Any, Callable

from anyio import fail_after
from pydantic_core import ValidationError
from src.contexts.seedwork.shared.adapters.exceptions import (
    EntityNotFoundException,
    MultipleEntitiesFoundException,
)


def timeout_after(timeout: int = 10):
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            with fail_after(timeout):
                return await func(*args, **kwargs)

        return wrapper

    return decorator


def lambda_exception_handler(func: Callable) -> Callable:
    @functools.wraps(func)
    async def wrapper(event: dict[str, Any], context: Any) -> dict[str, Any]:
        try:
            return await func(event, context)
        except EntityNotFoundException as e:
            return {"statusCode": 404, "body": json.dumps({"detail": str(e)})}
        except MultipleEntitiesFoundException as e:
            return {"statusCode": 409, "body": json.dumps({"detail": str(e)})}
        except TimeoutError as e:
            return {
                "statusCode": 408,
                "body": json.dumps(
                    {"detail": "Request processing time exceeded limit"}
                ),
            }
        except ValidationError as e:
            return {"statusCode": 422, "body": json.dumps({"detail": str(e)})}
        except ValueError as e:
            return {
                "statusCode": 400,
                "body": json.dumps({"detail": f"Error processing data: {str(e)}"}),
            }
        except Exception as e:
            return {
                "statusCode": 500,
                "body": json.dumps(
                    {"detail": f"An unexpected error occurred: {str(e)}"}
                ),
            }

    return wrapper
