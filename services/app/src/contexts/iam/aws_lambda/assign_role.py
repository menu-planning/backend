import json
import os
import uuid
from typing import Any

import anyio
import src.contexts.iam.shared.endpoints.internal.get as internal
from src.contexts.iam.shared.adapters.api_schemas.commands.assign_role_to_user import (
    ApiAssignRoleToUser,
)
from src.contexts.iam.shared.adapters.api_schemas.entities.user import ApiUser
from src.contexts.iam.shared.bootstrap.container import Container
from src.contexts.iam.shared.domain.enums import Permission
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import (
    lambda_exception_handler,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger


@lambda_exception_handler
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    is_localstack = os.getenv("IS_LOCALSTACK", "false").lower() == "true"
    if not is_localstack:
        authorizer_context = event["requestContext"]["authorizer"]
        caller_user_id = authorizer_context.get("claims").get("sub")
        response: dict = await internal.get(caller_user_id, "iam")
        if response.get("statusCode") != 200:
            return response
        current_user: SeedUser = ApiUser(**json.loads(response["body"])).to_domain()
        if not current_user.has_permission("iam", Permission.MANAGE_ROLES):
            return {
                "statusCode": 403,
                "body": json.dumps(
                    {"message": "User does not have enough privilegies."}
                ),
            }
    path_parameters = event.get("pathParameters", {})
    user_id = path_parameters.get("id")
    body = event.get("body", "")
    api = ApiAssignRoleToUser(user_id=user_id, **body)
    cmd = api.to_domain()
    bus: MessageBus = Container().bootstrap()
    await bus.handle(cmd)
    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Role assigned successfully"}),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to assign roles to a user.
    """
    logger.correlation_id.set(uuid.uuid4())
    return anyio.run(async_handler, event, context)
