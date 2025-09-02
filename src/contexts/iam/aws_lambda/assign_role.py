"""AWS Lambda handlers for IAM role assignment.

Provides an async handler wrapped by a sync entrypoint for assigning roles to
users. Validates authorization context, checks permissions, and dispatches a
domain command via the message bus.
"""

import json
from typing import TYPE_CHECKING, Any

from src.contexts.iam.core.adapters.api_schemas.commands.api_assign_role_to_user import (
    ApiAssignRoleToUser,
)
from src.contexts.iam.core.adapters.api_schemas.root_aggregate.api_user import ApiUser

if TYPE_CHECKING:
    from src.contexts.iam.core.domain.root_aggregate.user import User
    from src.contexts.shared_kernel.services.messagebus import MessageBus

import anyio
import src.contexts.iam.core.internal_endpoints.get as internal
from src.contexts.iam.core.bootstrap.container import Container
from src.contexts.iam.core.domain.enums import Permission
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

HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_FORBIDDEN = 403


@async_endpoint_handler(
    aws_lambda_logging_middleware(
        logger_name="iam.assign_role",
        log_request=True,
        log_response=True,
        log_timing=True,
        include_event_summary=True,
    ),
    aws_lambda_exception_handler_middleware(
        name="assign_role_exception_handler",
        logger_name="iam.assign_role.errors",
    ),
    timeout=30.0,
    name="assign_role_handler",
)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    """Handle POST /users/{id}/roles for role assignment.

    Request:
        Path: {id} (user ID to assign role to)
        Body: ApiAssignRoleToUser schema with role assignment data
        Auth: AWS Cognito JWT with user claims in authorizer context

    Responses:
        200: Role assigned successfully
        400: Invalid request data or missing parameters
        403: Insufficient permissions or user validation failed

    Idempotency:
        No. Multiple calls may result in duplicate role assignments.

    Notes:
        Maps to AssignRoleToUser command and translates errors to HTTP codes.
        Validates caller permissions before executing role assignment.
    """
    # Extract authentication context directly from AWS Lambda event
    try:
        authorizer_context = event["requestContext"]["authorizer"]
        claims = authorizer_context.get("claims", {})
        caller_user_id = claims.get("sub")

        if not caller_user_id:
            raise ValueError("Missing user ID in authorization context")
    except (KeyError, AttributeError) as e:
        raise ValueError(f"Invalid authorization context: {e}") from e

    try:
        user_id = event["pathParameters"]["id"]
    except KeyError:
        raise ValueError("User ID not found in path parameters") from None

    try:
        body = json.loads(event.get("body", ""))
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in request body: {e}") from e

    # Validate caller user exists and is active using direct IAM call
    response: dict = await internal.get(caller_user_id, "iam")
    if response.get("statusCode") != HTTP_OK:
        raise PermissionError("Caller user validation failed - user not found or inactive")

    try:
        target_user: User = ApiUser(**body).to_domain()
    except Exception as e:
        raise ValueError(f"Invalid user data in request body: {e}") from e

    # Check user permissions for role assignment
    if not target_user.has_permission("iam", Permission.MANAGE_ROLES):
        raise PermissionError("User does not have enough privileges for role assignment")

    # Prepare and execute role assignment command
    try:
        api = ApiAssignRoleToUser(user_id=user_id, **body)
        cmd = api.to_domain()
        bus: MessageBus = Container().bootstrap()

        await bus.handle(cmd)

    except Exception as e:
        raise RuntimeError(f"Role assignment failed during command execution: {e}") from e

    return {
        "statusCode": HTTP_OK,
        "body": json.dumps({"message": "Role assigned successfully"}),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """AWS Lambda entrypoint for role assignment.

    Args:
        event: AWS Lambda event containing request data and authorizer context.
        context: AWS Lambda context object.

    Returns:
        dict[str, Any]: HTTP response with status code and body.

    Notes:
        Sync wrapper that runs the async handler with AnyIO runtime.
        Generates correlation ID for request tracing.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
