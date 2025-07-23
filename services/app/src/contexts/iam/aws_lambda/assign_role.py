import json
import os
import uuid
from typing import Any

import anyio
from src.contexts.iam.core.domain.root_aggregate.user import User
import src.contexts.iam.core.endpoints.internal.get as internal
from src.contexts.iam.core.adapters.api_schemas.commands.api_assign_role_to_user import (
    ApiAssignRoleToUser,
)
from src.contexts.iam.core.adapters.api_schemas.root_aggregate.api_user import ApiUser
from src.contexts.iam.core.bootstrap.container import Container
from src.contexts.iam.core.domain.enums import Permission
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import (
    lambda_exception_handler,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger, generate_correlation_id

from .CORS_headers import CORS_headers


@lambda_exception_handler(CORS_headers)
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    try:
        user_id = event["pathParameters"]["id"]
    except KeyError:
        logger.error("User ID not found in path parameters.")
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": json.dumps({"message": "User ID not found in path parameters."}),
        }
    body = json.loads(event.get("body", ""))

    authorizer_context = event["requestContext"]["authorizer"]
    caller_user_id = authorizer_context.get("claims").get("sub")
    response: dict = await internal.get(caller_user_id, "iam")
    if response.get("statusCode") != 200:
        return response
    
    current_user: User = ApiUser(**body).to_domain()
    if not current_user.has_permission("iam", Permission.MANAGE_ROLES):
        return {
            "statusCode": 403,
            "headers": CORS_headers,
            "body": json.dumps(
                {"message": "User does not have enough privilegies."}
            ),
        }

    api = ApiAssignRoleToUser(user_id=user_id, **body)
    cmd = api.to_domain()
    bus: MessageBus = Container().bootstrap()
    await bus.handle(cmd)
    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": json.dumps({"message": "Role assigned successfully"}),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to assign roles to a user.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
