import json
import os
import uuid
from typing import Any

import anyio

from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.recipe.create import \
    ApiCreateRecipe
from src.contexts.recipes_catalog.shared.adapters.internal_providers.iam.api import \
    IAMProvider
from src.contexts.recipes_catalog.shared.bootstrap.container import Container
from src.contexts.recipes_catalog.shared.domain.enums import Permission
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import \
    lambda_exception_handler
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger, generate_correlation_id

from ..CORS_headers import CORS_headers

container = Container()

@lambda_exception_handler
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    logger.debug(f"Event received {event}")
    is_localstack = os.getenv("IS_LOCALSTACK", "false").lower() == "true"
    body = json.loads(event.get("body", ""))
    author_id = body.get("author_id", "")
    if not is_localstack:
        authorizer_context = event["requestContext"]["authorizer"]
        user_id = authorizer_context.get("claims").get("sub")
        response: dict = await IAMProvider.get(user_id)
        logger.debug(f"Response from IAMProvider {response}")
        if response.get("statusCode") != 200:
            return response
        current_user: SeedUser = response["body"]
        if author_id and not (
            current_user.has_permission(Permission.MANAGE_RECIPES)
            or current_user.id == author_id
        ):
            return {
                "statusCode": 403,
                "headers": CORS_headers,
                "body": json.dumps(
                    {"message": "User does not have enough privilegies."}
                ),
            }
        else:
            body["author_id"] = current_user.id
 
    for tag in body.get("tags", []):
        tag["author_id"] = body["author_id"]
        tag["type"] = "recipe"

    logger.debug(f"Body {body}")
    logger.debug(f"Api {ApiCreateRecipe(**body)}")
    api = ApiCreateRecipe(**body)
    logger.debug(f"Creating recipe {api}")
    cmd = api.to_domain()
    bus: MessageBus = container.bootstrap()
    await bus.handle(cmd)
    return {
        "statusCode": 201,
        "headers": CORS_headers,
        "body": json.dumps({"message": "Recipe created successfully"}),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to create a recipe.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
