import json
from typing import Any, Union

import anyio

from src.contexts.recipes_catalog.core.adapters.internal_providers.iam.api import \
    IAMProvider
from src.contexts.recipes_catalog.core.bootstrap.container import Container
from src.contexts.recipes_catalog.core.domain.enums import \
    Permission as EnumPermission
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.contexts.seedwork.shared.adapters.exceptions.repo_exceptions import \
    EntityNotFoundException
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import \
    lambda_exception_handler
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import \
    ApiTag
from src.contexts.shared_kernel.domain.value_objects.tag import Tag
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.contexts.shared_kernel.endpoints.base_endpoint_handler import LambdaHelpers
from src.logging.logger import logger, generate_correlation_id

from ..CORS_headers import CORS_headers

container = Container()


@lambda_exception_handler(CORS_headers)
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to get a tag by id.
    """
    logger.debug(f"Event received. {LambdaHelpers.extract_log_data(event, include_body=True)}")
    
    # Validate user authentication and get user object for permission checks
    auth_result = await LambdaHelpers.validate_user_authentication(
        event, CORS_headers, IAMProvider, return_user_object=True, mock_user_class=SeedUser
    )
    if isinstance(auth_result, dict):
        return auth_result  # Return error response
    _, current_user = auth_result

    tag_id = LambdaHelpers.extract_path_parameter(event, "id")
    
    if not tag_id:
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": '{"message": "Tag ID is required"}',
        }

    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        # Business context: Tag retrieval by ID
        logger.debug(f"Retrieving tag with ID: {tag_id}")
        try:
            tag: Tag = await uow.tags.get(tag_id)
        except EntityNotFoundException:
            logger.error(f"Tag not found: {tag_id}")
            return {
                "statusCode": 404,
                "headers": CORS_headers,
                "body": '{"message": "Tag not found"}',
            }
        except Exception as e:
            logger.error(f"Error retrieving tag {tag_id}: {e}")
            raise e
    
    # Business context: Tag found, checking permissions
    logger.debug(f"Tag found: {tag_id}")
    
    # Permission check (skip in localstack environment)
    if not LambdaHelpers.is_localstack_environment() and current_user:
        if not (
            current_user.has_permission(EnumPermission.MANAGE_RECIPES)
            or tag.author_id == current_user.id
        ):
            logger.warning(f"User {current_user.id} does not have permission to access tag {tag_id}")
            return {
                "statusCode": 403,
                "headers": CORS_headers,
                "body": '{"message": "User does not have enough privileges"}',
            }
        logger.debug(f"Permission check passed for user {current_user.id} accessing tag {tag_id}")
    
    # Convert domain tag to API tag with validation error handling
    try:
        validated_tag = ApiTag.from_domain(tag)
        logger.debug(f"Successfully converted tag {tag_id} to API format")
    except Exception as e:
        logger.error(f"Failed to convert tag {tag_id} to API format: {str(e)}")
        return {
            "statusCode": 500,
            "headers": CORS_headers,
            "body": '{"message": "Internal server error during tag conversion"}',
        }
    
    # Serialize API tag with validation error handling
    try:
        response_body = validated_tag.model_dump_json()
        logger.debug(f"Successfully serialized tag {tag_id}")
    except Exception as e:
        logger.error(f"Failed to serialize tag {tag_id} to JSON: {str(e)}")
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
    Lambda function handler to get a tag by its id.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)