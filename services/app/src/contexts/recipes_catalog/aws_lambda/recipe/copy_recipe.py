import json
import os
import uuid
from typing import Any

import anyio

from src.contexts.recipes_catalog.core.adapters.api_schemas.commands.recipe.copy import \
    ApiCopyRecipe
from src.contexts.recipes_catalog.core.adapters.internal_providers.iam.api import \
    IAMProvider
from src.contexts.recipes_catalog.core.bootstrap.container import Container
from src.contexts.recipes_catalog.core.domain.enums import Permission
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import \
    lambda_exception_handler
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger, generate_correlation_id

from ..CORS_headers import CORS_headers

container = Container()

@lambda_exception_handler
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    logger.debug(f"Getting recipe by id: {event}")
    
    incoming_data = json.loads(event.get("body", ""))
    api = ApiCopyRecipe(**incoming_data)
    
    is_localstack = os.getenv("IS_LOCALSTACK", "false").lower() == "true"
    if not is_localstack:
        authorizer_context = event["requestContext"]["authorizer"]
        user_id = authorizer_context.get("claims").get("sub")
        logger.debug(f"User id: {user_id}")
        response: dict = await IAMProvider.get(user_id)
        if response.get("statusCode") != 200:
            return response
        current_user: SeedUser = response["body"]
        if not (
            current_user.has_permission(Permission.MANAGE_RECIPES)
            or api.user_id == current_user.id
        ):
            return {
                "statusCode": 403,
                "headers": CORS_headers,
                "body": json.dumps(
                    {"message": "User does not have enough privilegies."}
                ),
            }
    
    path_parameters = event.get("pathParameters") if event.get("pathParameters") else {}
    logger.debug(f"Path params: {path_parameters}")

    cmd = api.to_domain()

    bus: MessageBus = Container().bootstrap()
    await bus.handle(cmd)
    return {
        "statusCode": 201,
        "headers": CORS_headers,
        "body": json.dumps({"message": "Recipe copied successfully"}),
    }

def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to create a recipe.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
