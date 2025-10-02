"""Internal endpoint helpers for IAM data retrieval.

Provides coroutines used by Lambda handlers and other services to fetch IAM
users and filter their roles by caller context. These functions handle the
application layer orchestration between domain services and external API
boundaries.
"""

import json
import time
from typing import TYPE_CHECKING

from src.contexts.iam.core.adapters.api_schemas.root_aggregate.api_user import ApiUser
from src.contexts.iam.core.bootstrap.container import Container
from src.contexts.iam.core.domain.root_aggregate.user import User
from src.contexts.seedwork.adapters.repositories.repository_exceptions import (
    EntityNotFoundError,
    MultipleEntitiesFoundError,
)
from src.logging.logger import get_logger

if TYPE_CHECKING:
    from src.contexts.iam.core.services.uow import UnitOfWork
    from src.contexts.shared_kernel.services.messagebus import MessageBus
container = Container()
logger = get_logger(__name__)


async def get(id: str, caller_context: str) -> dict[str, int | str]:
    """Retrieve user data filtered by caller context.

    Fetches a user from the repository and filters their roles to only include
    those matching the specified caller context. Returns a standardized HTTP
    response format suitable for Lambda handlers.

    Args:
        id: UUID v4 identifier of the user to retrieve.
        caller_context: Context string to filter user roles by.

    Returns:
        HTTP response dict containing:
            - statusCode: HTTP status code (200, 404, or 500)
            - body: JSON string with user data or error message

    Raises:
        EntityNotFoundError: When user with id does not exist.
        MultipleEntitiesFoundError: When multiple users found for id.
        Exception: For unexpected database or system errors.

    Notes:
        Maps to User aggregate retrieval and role filtering domain logic.
        All database operations occur within a single UnitOfWork transaction.
        Logs operation timing and error details for observability.
    """
    start_time = time.time()
    # logger.info(
    #     "IAM get operation started",
    #     operation="iam_get",
    #     user_id=id,
    #     caller_context=caller_context,
    #     start_time=start_time,
    # )

    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow_factory() as uow:
        try:
            # logger.debug(
            #     "Starting database query for user",
            #     operation="db_query",
            #     user_id=id,
            #     query_type="get_user",
            # )
            user = await uow.users.get(id)

            db_elapsed = time.time() - start_time
            # logger.debug(
            #     "User retrieved from database successfully",
            #     operation="db_query_success",
            #     user_id=id,
            #     db_elapsed_seconds=round(db_elapsed, 3),
            #     has_roles=len(user.roles) > 0 if hasattr(user, "roles") else False,
            # )

        except EntityNotFoundError:
            elapsed_time = time.time() - start_time
            logger.error(
                "User not found in database",
                operation="db_query_error",
                error_type="entity_not_found",
                user_id=id,
                elapsed_seconds=round(elapsed_time, 3),
                status_code=404,
            )
            return {
                "statusCode": 404,
                "body": json.dumps({"message": "User not in database."}),
            }
        except MultipleEntitiesFoundError:
            elapsed_time = time.time() - start_time
            logger.error(
                "Multiple users found for single ID",
                operation="db_query_error",
                error_type="multiple_entities_found",
                user_id=id,
                elapsed_seconds=round(elapsed_time, 3),
                status_code=500,
            )
            return {
                "statusCode": 500,
                "body": json.dumps({"message": "Multiple users found in database."}),
            }
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(
                "Unexpected database error",
                operation="db_query_error",
                error_type="unexpected_error",
                error_class=type(e).__name__,
                error_message=str(e),
                user_id=id,
                elapsed_seconds=round(elapsed_time, 3),
                status_code=500,
                exc_info=True,
            )
            return {
                "statusCode": 500,
                "body": json.dumps({"message": "Internal server error."}),
            }

        # logger.debug(
        #     "Starting role filtering process",
        #     operation="role_filtering",
        #     user_id=id,
        #     caller_context=caller_context,
        #     total_roles=len(user.roles) if hasattr(user, "roles") else 0,
        # )
        result = _get_user_data_with_right_context_roles(user, caller_context)

        elapsed_time = time.time() - start_time
        # logger.info(
        #     "IAM get operation completed successfully",
        #     operation="iam_get_success",
        #     user_id=id,
        #     caller_context=caller_context,
        #     elapsed_seconds=round(elapsed_time, 3),
        #     status_code=200,
        # )
        return result


def _get_user_data_with_right_context_roles(
    user: User, caller_context: str
) -> dict[str, int | str]:
    """Filter user roles by caller context and prepare API response.

    Converts domain User entity to API schema, filters roles by caller context,
    and generates HTTP response with filtered user data. Excludes role context
    field from response to prevent information leakage.

    Args:
        user: Domain User aggregate with roles collection.
        caller_context: Context string to match against role contexts.

    Returns:
        HTTP response dict with:
            - statusCode: 200 (always successful)
            - body: JSON string containing user ID and filtered roles

    Notes:
        Side effect: logs role filtering details for debugging.
        Creates new ApiUser instance with filtered roles collection.
    """
    logger.debug(
        "Converting domain user to API user",
        operation="domain_to_api_conversion",
        user_id=user.id,
    )
    api_user = ApiUser.from_domain(user)

    all_roles = list(api_user.roles)
    logger.debug(
        "Retrieved user roles for filtering",
        operation="role_retrieval",
        user_id=user.id,
        total_roles_count=len(all_roles),
        target_context=caller_context,
    )

    caller_context_roles = []
    if all_roles:
        for role in all_roles:
            if role.context == caller_context:
                caller_context_roles.append(role)
                logger.debug(
                    "Role matched target context",
                    operation="role_match",
                    user_id=user.id,
                    role_name=role.name,
                    role_context=role.context,
                    target_context=caller_context,
                )
            else:
                logger.debug(
                    "Role filtered out due to context mismatch",
                    operation="role_filter",
                    user_id=user.id,
                    role_name=role.name,
                    role_context=role.context,
                    target_context=caller_context,
                )

    logger.debug(
        "Role filtering completed",
        operation="role_filtering_complete",
        user_id=user.id,
        target_context=caller_context,
        filtered_roles_count=len(caller_context_roles),
        original_roles_count=len(all_roles),
    )

    # Create new role objects without the context field for the response
    filtered_roles = []
    for role in caller_context_roles:
        # Create a new role object without the context field
        filtered_role = {"name": role.name, "permissions": list(role.permissions)}
        filtered_roles.append(filtered_role)

    response_data = {"id": api_user.id, "roles": filtered_roles}
    response_body = json.dumps(response_data)

    logger.debug(
        "API response generated successfully",
        operation="api_response_generation",
        user_id=user.id,
        response_roles_count=len(caller_context_roles),
        response_size_bytes=len(response_body),
    )
    return {"statusCode": 200} | {"body": response_body}
