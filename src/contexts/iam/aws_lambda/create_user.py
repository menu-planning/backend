"""AWS Cognito post-confirmation trigger to ensure an app user exists.

Creates a new IAM user if one is not already present after Cognito confirms a
user registration. Uses the message bus to dispatch a domain command.
"""

import json
from typing import TYPE_CHECKING, Any

import anyio
from src.config.app_config import get_app_settings
from src.contexts.iam.core.adapters.api_schemas.commands.api_create_user import (
    ApiCreateUser,
)
from src.contexts.iam.core.bootstrap.container import Container
from src.contexts.seedwork.adapters.repositories.repository_exceptions import (
    EntityNotFoundError,
    MultipleEntitiesFoundError,
)
from src.contexts.shared_kernel.middleware.decorators.async_endpoint_handler import (
    async_endpoint_handler,
)
from src.contexts.shared_kernel.middleware.error_handling.exception_handler import (
    aws_lambda_exception_handler_middleware,
)
from src.contexts.shared_kernel.middleware.logging.structured_logger import (
    aws_lambda_logging_middleware,
)
from src.logging.logger import generate_correlation_id

from .api_headers import CORS_headers

if TYPE_CHECKING:
    from src.contexts.iam.core.services.uow import UnitOfWork
    from src.contexts.shared_kernel.services.messagebus import MessageBus

container = Container()


@async_endpoint_handler(
    aws_lambda_logging_middleware(
        logger_name="iam.create_user",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
        include_event=get_app_settings().enviroment == "development",
    ),
    aws_lambda_exception_handler_middleware(
        name="create_user_exception_handler",
        logger_name="iam.create_user.errors",
    ),
    timeout=30.0,
    name="create_user_handler",
)
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """Handle AWS Cognito post-confirmation trigger for user creation.

    Request:
        Body: Cognito post-confirmation event with userName field
        Auth: AWS Cognito trigger context (no explicit auth required)

    Responses:
        200: User created successfully or already exists
        409: User already exists in database
        500: Error during user creation or database operation

    Idempotency:
        Yes. Key: userName. Duplicate calls return existing user status.

    Notes:
        Maps to CreateUser command and translates errors to HTTP codes.
        Auto-confirms and verifies email for newly created users.
    """
    user_id = event["userName"]
    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow_factory() as uow:
        try:
            await uow.users.get(user_id)
            return {
                "statusCode": 409,
                "headers": CORS_headers,
                "body": json.dumps(f"User {user_id} already exists."),
            }
        except EntityNotFoundError:
            # User not found in database, creating new user
            api = ApiCreateUser(user_id=user_id)
            cmd = api.to_domain()
            await bus.handle(cmd)

            event["response"]["autoConfirmUser"] = True
            event["response"]["autoVerifyEmail"] = True
            return event
        except MultipleEntitiesFoundError:
            raise RuntimeError("Multiple users found in database") from None
        except Exception as e:
            raise RuntimeError(f"Error creating user: {e}") from e


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """AWS Lambda entrypoint for user creation.

    Args:
        event: AWS Lambda event containing Cognito post-confirmation data.
        context: AWS Lambda context object.

    Returns:
        dict[str, Any]: HTTP response with status code and body.

    Notes:
        Sync wrapper that runs the async handler with AnyIO runtime.
        Generates correlation ID for request tracing.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
