import json
from typing import Any

import anyio

from src.contexts.recipes_catalog.core.adapters.client.api_schemas.commands.api_update_client import ApiUpdateClient
from src.contexts.recipes_catalog.core.adapters.client.api_schemas.root_aggregate.api_client import ApiClient
from src.contexts.recipes_catalog.core.adapters.external_providers.iam.iam_provider_api_for_recipes_catalog import (
    IAMProvider,
)
from src.contexts.recipes_catalog.core.bootstrap.container import Container
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
    Lambda function handler to update a client by its id.
    """
    logger.debug(f"Event received. {LambdaHelpers.extract_log_data(event, include_body=True)}")
    
    # Extract client ID from path parameters
    client_id = event.get("pathParameters", {}).get("client_id")
    if not client_id:
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Client ID is required in path parameters"}),
        }
    
    # Extract and parse request body with validation error handling
    try:
        raw_body = LambdaHelpers.extract_request_body(event, parse_json=False)
        logger.debug(f"Raw request body extracted successfully")
    except Exception as e:
        logger.error(f"Unexpected error extracting request body: {str(e)}")
        return {
            "statusCode": 500,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Internal server error during request parsing"}),
        }
    
    # Ensure body is a string and not empty
    if not isinstance(raw_body, str) or not raw_body.strip():
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Request body is required"}),
        }
    
    # Parse and validate request body as a complete client using ApiClient
    try:
        # Parse raw_body as complete client
        api_client_from_request = ApiClient.model_validate_json(raw_body)
        logger.debug(f"Successfully parsed raw_body as complete ApiClient")
    except Exception as e:
        logger.error(f"Failed to parse raw_body as complete client: {str(e)}")
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": json.dumps({"message": f"Invalid client data: {str(e)}"}),
        }

    # Business context: Check if client exists and validate permissions
    try:
        bus: MessageBus = container.bootstrap()
        uow: UnitOfWork
        async with bus.uow as uow:
            try:
                existing_client = await uow.clients.get(client_id)
                logger.debug(f"Client {client_id} found in database")
            except EntityNotFoundException:
                logger.warning(f"Client {client_id} not found in database")
                return {
                    "statusCode": 404,
                    "headers": CORS_headers,
                    "body": json.dumps({"message": f"Client {client_id} not found."}),
                }

            # Validate user authentication and get user object for permission checking
            auth_result = await LambdaHelpers.validate_user_authentication(
                event, CORS_headers, IAMProvider, return_user_object=True
            )
            if isinstance(auth_result, dict):
                return auth_result  # Return error response
            user_id, current_user = auth_result
            
            # Business context: Permission validation for client update
            if not (
                current_user.has_permission(Permission.MANAGE_CLIENTS)
                or current_user.id == existing_client.author_id
            ):
                logger.warning(f"User {current_user.id} does not have permission to update client {client_id}")
                return {
                    "statusCode": 403,
                    "headers": CORS_headers,
                    "body": json.dumps(
                        {"message": "User does not have enough privileges to update this client."}
                    ),
                }

            # Convert existing domain client to ApiClient for comparison
            try:
                existing_api_client = ApiClient.from_domain(existing_client)
                logger.debug(f"Successfully converted existing domain client to ApiClient")
            except Exception as e:
                logger.error(f"Failed to convert existing domain client to ApiClient: {str(e)}")
                return {
                    "statusCode": 500,
                    "headers": CORS_headers,
                    "body": json.dumps({"message": "Internal server error during client conversion"}),
                }

            # Create ApiUpdateClient using from_api_client with new client and old client for comparison
            try:
                api_of_update_cmd = ApiUpdateClient.from_api_client(
                    api_client=api_client_from_request,
                    old_api_client=existing_api_client
                )
                logger.debug(f"Successfully created ApiUpdateClient with only changed fields")
            except Exception as e:
                logger.error(f"Failed to create ApiUpdateClient from api clients: {str(e)}")
                return {
                    "statusCode": 500,
                    "headers": CORS_headers,
                    "body": json.dumps({"message": "Internal server error during update command creation"}),
                }

    except Exception as e:
        logger.error(f"Failed to validate client existence and permissions: {str(e)}")
        return {
            "statusCode": 500,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Internal server error during client validation"}),
        }
        
    # Convert to domain command with validation error handling
    try:
        cmd = api_of_update_cmd.to_domain()
        logger.debug(f"Successfully converted to domain command")
    except Exception as e:
        logger.error(f"Failed to convert API to domain command: {str(e)}")
        return {
            "statusCode": 500,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Internal server error during command creation"}),
        }
    
    # Business context: Client update through message bus
    try:
        await bus.handle(cmd)
        logger.debug(f"Client {client_id} updated successfully")
    except Exception as e:
        logger.error(f"Failed to update client: {str(e)}")
        return {
            "statusCode": 500,
            "headers": CORS_headers,
            "body": json.dumps({"message": "Internal server error during client update"}),
        }
    
    return {
        "statusCode": 200,
        "headers": CORS_headers,
        "body": json.dumps({"message": "Client updated successfully"}),
    }


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to update a client by its id.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
