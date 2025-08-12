from typing import Any

import anyio
from pydantic import TypeAdapter, ValidationError

from src.contexts.recipes_catalog.core.adapters.external_providers.iam.iam_provider_api_for_recipes_catalog import \
    IAMProvider
from src.contexts.recipes_catalog.core.bootstrap.container import Container
from src.contexts.recipes_catalog.core.domain.enums import Role as EnumRoles
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import \
    lambda_exception_handler
from src.contexts.seedwork.shared.endpoints.exceptions import \
    BadRequestException
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag import \
    ApiTag
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.api_tag_filter import \
    ApiTagFilter
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.contexts.shared_kernel.endpoints.base_endpoint_handler import LambdaHelpers
from src.logging.logger import logger, generate_correlation_id

from ..CORS_headers import CORS_headers

container = Container()

TagListAdapter = TypeAdapter(list[ApiTag])


def _extract_and_validate_filters(event: dict[str, Any]) -> dict[str, Any]:
    """
    Extract and validate query filters from the Lambda event.
    
    This function handles the complete query parameter processing pipeline:
    1. Extract query parameters
    2. Normalize kebab-case to snake_case
    3. Handle pagination parameters
    4. Validate through Pydantic schema
    
    Returns:
        dict: Validated filter parameters
        
    Raises:
        BadRequestException: If query parameters are invalid
    """
    logger.debug("Starting query parameter extraction and validation")
    
    try:
        filters = LambdaHelpers.process_query_filters(
            event,
            ApiTagFilter,
            use_multi_value=True,
            default_limit=50,
            default_sort="key"
        )
        logger.debug(f"Successfully processed query filters: {filters}")
        return filters
        
    except ValidationError as e:
        error_details = "; ".join([f"{err['loc'][0] if err['loc'] else 'unknown'}: {err['msg']}" for err in e.errors()])
        logger.warning(f"Query parameter validation failed: {error_details}")
        raise BadRequestException(f"Invalid query parameters: {error_details}")
        
    except Exception as e:
        logger.error(f"Unexpected error during query parameter processing: {str(e)}", exc_info=True)
        raise BadRequestException(f"Failed to process query parameters: {str(e)}")


def _apply_authorization_filters(filters: dict[str, Any], current_user: SeedUser | None) -> dict[str, Any]:
    """
    Apply user-specific authorization filters based on user role and permissions.
    
    Args:
        filters: Base query filters
        current_user: Authenticated user (None for LocalStack)
        
    Returns:
        dict: Filters with authorization constraints applied
        
    Raises:
        Exception: Returns error response dict that should be returned directly
    """
    # Admin users can query all tags without restrictions
    if current_user and current_user.has_role(EnumRoles.ADMINISTRATOR):
        logger.debug(f"Admin user - no additional authorization filters applied")
        return filters
    
    # Handle author_id filtering for non-admin users
    if filters.get("author_id") is not None:
        if current_user and filters.get("author_id") != current_user.id:
            logger.warning(
                f"User {current_user.id if current_user else 'unknown'} "
                f"attempted to access tags of another user: {filters.get('author_id')}"
            )
            raise Exception({
                "statusCode": 403,
                "headers": CORS_headers,
                "body": '{"message": "User does not have enough privileges."}',
            })
        logger.debug("User querying their own tags - author_id filter validated")
    else:
        # Auto-add current user's ID to filter for non-admin users
        if current_user:
            filters = filters.copy()  # Don't mutate the original dict
            filters["author_id"] = current_user.id
            logger.debug(f"Non-admin user - added author_id filter: {current_user.id}")
        else:
            logger.debug("LocalStack environment - no author_id filter applied")
    
    return filters


async def _query_tags(filters: dict[str, Any]) -> list:
    """
    Execute the tag query using the message bus and unit of work.
    
    Args:
        filters: Validated and authorized query filters
        
    Returns:
        list: List of tag domain objects
    """
    logger.debug(f"Executing tag query with filters: {filters}")
    
    bus: MessageBus = container.bootstrap()
    async with bus.uow as uow:
        tags = await uow.tags.query(filter=filters)
    
    logger.debug(f"Tag query completed - found {len(tags)} tags")
    return tags


def _convert_tags_to_api_format(tags: list) -> list[ApiTag]:
    """
    Convert domain tags to API format with error handling.
    
    Args:
        tags: List of domain tag objects
        
    Returns:
        list[ApiTag]: Successfully converted API tags
    """
    logger.debug(f"Converting {len(tags)} domain tags to API format")
    
    api_tags = []
    conversion_errors = 0
    
    for i, tag in enumerate(tags):
        try:
            api_tag = ApiTag.from_domain(tag)
            api_tags.append(api_tag)
        except Exception as e:
            conversion_errors += 1
            logger.warning(
                f"Failed to convert tag to API format - Tag index: {i}, "
                f"Tag ID: {getattr(tag, 'id', 'unknown')}, Error: {str(e)}"
            )
            # Continue processing other tags instead of failing completely
    
    if conversion_errors > 0:
        logger.warning(f"Tag conversion completed with {conversion_errors} errors out of {len(tags)} total tags")
    
    logger.debug(f"Successfully converted {len(api_tags)} tags to API format")
    return api_tags


def _serialize_response(api_tags: list[ApiTag]) -> bytes:
    """
    Serialize API tags to JSON response body.
    
    Args:
        api_tags: List of API tag objects
        
    Returns:
        bytes: JSON serialized response body
        
    Raises:
        Exception: Returns error response dict that should be returned directly
    """
    try:
        response_body = TagListAdapter.dump_json(api_tags)
        logger.debug(f"Successfully serialized {len(api_tags)} tags to JSON")
        return response_body
    except Exception as e:
        logger.error(f"Failed to serialize tag list to JSON: {str(e)}")
        raise Exception({
            "statusCode": 500,
            "headers": CORS_headers,
            "body": '{"message": "Internal server error during response serialization"}',
        })


@lambda_exception_handler(CORS_headers)
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to query for tags.
    
    This handler implements a complete tag querying workflow with:
    - Query parameter validation
    - User authentication and authorization
    - Role-based access control
    - Robust error handling and logging
    """
    logger.debug(f"Event received. {LambdaHelpers.extract_log_data(event, include_body=True)}")
    
    try:
        # Step 1: Extract and validate query parameters
        filters = _extract_and_validate_filters(event)
        
        # Step 2: Authenticate user and get user object for authorization
        auth_result = await LambdaHelpers.validate_user_authentication(
            event, CORS_headers, IAMProvider, return_user_object=True, mock_user_class=SeedUser
        )
        if isinstance(auth_result, dict):
            return auth_result  # Return error response
        _, current_user = auth_result
        
        # Step 3: Apply authorization filters based on user role
        authorized_filters = _apply_authorization_filters(filters, current_user)
        
        # Step 4: Execute the query
        tags = await _query_tags(authorized_filters)
        
        # Step 5: Convert to API format
        api_tags = _convert_tags_to_api_format(tags)
        
        # Step 6: Serialize response
        response_body = _serialize_response(api_tags)
        
        logger.debug(f"Tag query completed successfully - returning {len(api_tags)} tags")
        return {
            "statusCode": 200,
            "headers": CORS_headers,
            "body": response_body,
        }
        
    except BadRequestException as e:
        logger.warning(f"Bad request while processing tag query: {str(e)}")
        return {
            "statusCode": 400,
            "headers": CORS_headers,
            "body": f'{{"message": "{str(e)}"}}',
        }
    
    except Exception as e:
        # Handle cases where helper functions return error response dicts
        if isinstance(e.args[0], dict) and "statusCode" in e.args[0]:
            logger.debug("Returning structured error response from helper function")
            return e.args[0]
        
        # Re-raise unexpected errors to be handled by lambda_exception_handler
        logger.error(f"Unexpected error in tag query handler: {str(e)}", exc_info=True)
        raise


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler entry point.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
