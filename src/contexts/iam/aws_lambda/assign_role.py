import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.contexts.iam.core.domain.root_aggregate.user import User
    from src.contexts.shared_kernel.services.messagebus import MessageBus

import anyio

import src.contexts.iam.core.endpoints.internal.get as internal
from src.contexts.client_onboarding.aws_lambda.shared.cors_headers import CORS_headers
from src.contexts.iam.core import Container, Permission
from src.contexts.iam.core.adapters import ApiAssignRoleToUser, ApiUser
from src.contexts.seedwork import lambda_exception_handler
from src.logging.logger import generate_correlation_id, logger

# Constants
HTTP_OK = 200
HTTP_BAD_REQUEST = 400
HTTP_FORBIDDEN = 403


@lambda_exception_handler(CORS_headers)
async def async_handler(event: dict[str, Any], _: Any) -> dict[str, Any]:
    try:
        user_id = event["pathParameters"]["id"]
    except KeyError:
        logger.error("User ID not found in path parameters.")
        return {
            "statusCode": HTTP_BAD_REQUEST,
            "headers": CORS_headers,
            "body": json.dumps({"message": "User ID not found in path parameters."}),
        }
    body = json.loads(event.get("body", ""))

    authorizer_context = event["requestContext"]["authorizer"]
    caller_user_id = authorizer_context.get("claims").get("sub")
    response: dict = await internal.get(caller_user_id, "iam")
    if response.get("statusCode") != HTTP_OK:
        return response

    current_user: User = ApiUser(**body).to_domain()
    if not current_user.has_permission("iam", Permission.MANAGE_ROLES):
        return {
            "statusCode": HTTP_FORBIDDEN,
            "headers": CORS_headers,
            "body": json.dumps({"message": "User does not have enough privilegies."}),
        }

    api = ApiAssignRoleToUser(user_id=user_id, **body)
    cmd = api.to_domain()
    bus: MessageBus = Container().bootstrap()
    await bus.handle(cmd)
    return {
        "statusCode": HTTP_OK,
        "headers": CORS_headers,
        "body": json.dumps({"message": "Role assigned successfully"}),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to assign roles to a user.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
