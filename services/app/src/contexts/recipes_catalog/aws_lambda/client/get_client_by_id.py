import json
from typing import Any

import anyio

from src.contexts.recipes_catalog.core.adapters.client.api_schemas.root_aggregate.api_client import ApiClient
from src.contexts.recipes_catalog.core.adapters.internal_providers.iam.iam_provider_api_for_recipes_catalog import (
    IAMProvider,
)
from src.contexts.recipes_catalog.core.bootstrap.container import Container
from src.contexts.recipes_catalog.core.domain.enums import Permission
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.contexts.seedwork.shared.adapters.exceptions.repo_exceptions import EntityNotFoundException
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
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
    Lambda function handler to retrieve a specific client by id.
    """
    logger.debug(f"Event received. {LambdaHelpers.extract_log_data(event, include_body=True)}")
    
    if not LambdaHelpers.is_localstack_environment():
        user_id = LambdaHelpers.extract_user_id(event)
        if not user_id:
            logger.warning("User ID not found in request context")
            return {
                "statusCode": 401,
                "headers": CORS_headers,
                "body": '{"message": "User ID not found in request context"}',
            }
        
        response: dict = await IAMProvider.get(user_id)
        if response.get("statusCode") != 200:
            logger.warning(f"IAM validation failed for user {user_id}: {response.get('statusCode')}")
            response["headers"] = CORS_headers
            return response
        logger.debug(f"IAM validation successful for user: {user_id}")
    
    client_id = LambdaHelpers.extract_path_parameter(event, "client_id")
    
    if not client_id:
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": '{"message": "Client ID is required"}',
        }
    
    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        # Business context: Client retrieval by ID
        logger.debug(f"Retrieving client with ID: {client_id}")
        try:
            client = await uow.clients.get(client_id)
        except EntityNotFoundException as e:
            logger.error(f"Client not found: {client_id} - {e}")
            return {
                "statusCode": 404,
                "headers": CORS_headers,
                "body": json.dumps({"message": f"Client {client_id} not found."}),
            }
    
    # Business context: Authorization check for client access
    if not LambdaHelpers.is_localstack_environment():
        user_id = LambdaHelpers.extract_user_id(event)
        # user_id is guaranteed to exist since we validated it earlier
        assert user_id is not None, "User ID should not be None at this point"
        response: dict = await IAMProvider.get(user_id)
        current_user: SeedUser = response["body"]
        
        if not (
            current_user.has_permission(Permission.MANAGE_MENUS)
            or client.author_id == current_user.id
        ):
            logger.warning(f"User {user_id} does not have permission to access client {client_id}")
            return {
                "statusCode": 403,
                "headers": CORS_headers,
                "body": json.dumps(
                    {"message": "User does not have enough privileges."}
                ),
            }
    
    # Business context: Client found and authorized
    logger.debug(f"Client found and authorized: {client_id}")
    
    # Convert domain client to API client with validation error handling
    try:
        api = ApiClient.from_domain(client)
        logger.debug(f"Successfully converted client {client_id} to API format")
    except Exception as e:
        logger.error(f"Failed to convert client {client_id} to API format: {str(e)}")
        return {
            "statusCode": 500,
            "headers": CORS_headers,
            "body": '{"message": "Internal server error during client conversion"}',
        }
    
    # Serialize API client with validation error handling
    try:
        response_body = api.model_dump_json()
        logger.debug(f"Successfully serialized client {client_id}")
    except Exception as e:
        logger.error(f"Failed to serialize client {client_id} to JSON: {str(e)}")
        return {
            "statusCode": 500,
            "headers": CORS_headers,
            "body": '{"message": "Internal server error during response serialization"}',
        }
    
    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": response_body,
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to get a client by its id.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
