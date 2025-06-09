import json
import os
import uuid
from typing import Any

import anyio

from src.contexts.recipes_catalog.core.adapters.client.api_schemas.commands.create_client import ApiCreateClient
from src.contexts.recipes_catalog.core.adapters.internal_providers.iam.api import (
    IAMProvider,
)
from src.contexts.recipes_catalog.core.bootstrap.container import Container
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import (
    lambda_exception_handler,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger, generate_correlation_id

from ..CORS_headers import CORS_headers


@lambda_exception_handler
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    logger.debug(f"Event received {event}")

    body = json.loads(event.get("body", ""))
    
    authorizer_context = event["requestContext"]["authorizer"]
    user_id = authorizer_context.get("claims").get("sub")
    response: dict = await IAMProvider.get(user_id)
    if response.get("statusCode") != 200:
        return response
    
    current_user: SeedUser = response["body"]
    
    body["author_id"] = current_user.id

    for tag in body.get("tags", []):
        tag["author_id"] = body["author_id"]
        tag["type"] = "client"

    for menu in body.get("menus", []):
        for tag in menu.get("tags", []):
            tag["author_id"] = body["author_id"]
            tag["type"] = "menu"

    api = ApiCreateClient(**body)
    cmd = api.to_domain()
    bus: MessageBus = Container().bootstrap()
    await bus.handle(cmd)
    return {
        "statusCode": 201,
        "headers": CORS_headers,
        "body": json.dumps({"message": "Client created successfully"}),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to create a client.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
