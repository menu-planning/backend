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

from .api_headers import API_headers

if TYPE_CHECKING:
    from src.contexts.shared_kernel.services.messagebus import MessageBus

import anyio
from src.contexts.iam.core.bootstrap.container import Container
from src.contexts.iam.core.domain.commands import AssignRoleToUser
from src.contexts.iam.core.domain.enums import Permission
from src.contexts.shared_kernel.middleware.auth.authentication import (
    iam_aws_auth_middleware,
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

container = Container()

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
    iam_aws_auth_middleware(),
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
    # Get authenticated user from middleware (no manual auth needed)
    auth_context = event["_auth_context"]
    current_user = auth_context.user_object

    try:
        user_id = event["pathParameters"]["id"]
    except KeyError:
        raise ValueError("User ID not found in path parameters") from None

    # Parse and validate request body using Pydantic model
    raw_body = event.get("body", "")
    if not isinstance(raw_body, str) or not raw_body.strip():
        error_message = "Request body is required and must be a non-empty string"
        raise ValueError(error_message)

    api = ApiAssignRoleToUser.model_validate_json(raw_body)

    # Business context: Permission validation for role assignment
    if not current_user.has_permission("iam", Permission.MANAGE_ROLES):
        error_message = "User does not have enough privileges for role assignment"
        raise PermissionError(error_message)

    # Convert to domain command with user_id from path parameter
    cmd = api.to_domain()
    # Create new command with user_id from path parameter
    cmd = AssignRoleToUser(user_id=user_id, role=cmd.role)

    # Business context: Role assignment through message bus
    bus: MessageBus = container.bootstrap()
    await bus.handle(cmd)

    return {
        "statusCode": HTTP_OK,
        "headers": API_headers,
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
