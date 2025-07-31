import json
from typing import Any

import anyio

from src.contexts.recipes_catalog.core.adapters.internal_providers.iam.iam_provider_api_for_recipes_catalog import (
    IAMProvider,
)
from src.contexts.recipes_catalog.core.bootstrap.container import Container
from src.contexts.recipes_catalog.core.domain.client.commands.delete_client import DeleteClient
from src.contexts.recipes_catalog.core.domain.enums import Permission
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.contexts.seedwork.shared.adapters.exceptions.repo_exceptions import EntityNotFoundException
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import (
    lambda_exception_handler,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.contexts.shared_kernel.endpoints.base_endpoint_handler import LambdaHelpers
from src.logging.logger import logger, generate_correlation_id

from ..CORS_headers import CORS_headers

container = Container()

@lambda_exception_handler(CORS_headers)
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to delete a client.
    """
    logger.debug(f"Event received. {LambdaHelpers.extract_log_data(event)}")
    
    # Extract client ID from path parameters
    client_id = event.get("pathParameters", {}).get("id")
    if not client_id:
        logger.error("Client ID not provided in path parameters")
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Client ID is required"}),
        }
    
    # Validate user authentication and get user object for permission checking
    auth_result = await LambdaHelpers.validate_user_authentication(
        event, CORS_headers, IAMProvider, return_user_object=True
    )
    if isinstance(auth_result, dict):
        return auth_result  # Return error response
    _, current_user = auth_result
    
    # Business context: Get client to verify existence and check permissions
    try:
        bus: MessageBus = container.bootstrap()
        uow: UnitOfWork
        async with bus.uow as uow:
            client = await uow.clients.get(client_id)
            logger.debug(f"Client found: {client_id}, author: {client.author_id}")
    except EntityNotFoundException:
        logger.warning(f"Client {client_id} not found in database")
        return {
            "statusCode": 404,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Client not found"}),
        }
    except Exception as e:
        logger.error(f"Unexpected error retrieving client {client_id}: {str(e)}")
        return {
            "statusCode": 500,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Internal server error during client retrieval"}),
        }
    
    # Business context: Permission validation for client deletion
    if not (
        current_user.has_permission(Permission.MANAGE_CLIENTS)
        or client.author_id == current_user.id
    ):
        logger.warning(f"User {current_user.id} does not have permission to delete client {client_id} (author: {client.author_id})")
        return {
            "statusCode": 403,
            "headers": CORS_headers,
            "body": json.dumps(
                {"message": "User does not have enough privileges."}
            ),
        }
    
    # Business context: Client deletion through message bus
    try:
        cmd = DeleteClient(client_id=client_id)
        await bus.handle(cmd)
        logger.debug(f"Client deleted successfully: {client_id}")
    except Exception as e:
        logger.error(f"Failed to delete client {client_id}: {str(e)}")
        return {
            "statusCode": 500,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Internal server error during client deletion"}),
        }
    
    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": json.dumps({"message": "Client deleted successfully"}),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to delete a client.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
