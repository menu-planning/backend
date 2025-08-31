import json
import time
from typing import TYPE_CHECKING

from src.contexts.iam.core.adapters.api_schemas.root_aggregate.api_user import ApiUser
from src.contexts.iam.core.bootstrap.container import Container
from src.contexts.iam.core.domain.root_aggregate.user import User
from src.contexts.seedwork.shared.adapters.exceptions.repo_exceptions import (
    EntityNotFoundError,
    MultipleEntitiesFoundError,
)
from src.logging.logger import structlog_logger

if TYPE_CHECKING:
    from src.contexts.iam.core.services.uow import UnitOfWork
    from src.contexts.shared_kernel.services.messagebus import MessageBus
container = Container()
logger = structlog_logger(__name__)


async def get(entity_id: str, caller_context: str) -> dict[str, int | str]:
    """Retrieve user data filtered by caller context.
    
    Args:
        entity_id: The user ID to retrieve.
        caller_context: The context to filter roles by.
        
    Returns:
        HTTP response dict with user data or error message.
    """
    start_time = time.time()
    logger.info(
        "IAM get operation started",
        operation="iam_get",
        user_id=entity_id,
        caller_context=caller_context,
        start_time=start_time
    )

    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        try:
            logger.debug(
                "Starting database query for user",
                operation="db_query",
                user_id=entity_id,
                query_type="get_user"
            )
            user = await uow.users.get(entity_id)

            db_elapsed = time.time() - start_time
            logger.debug(
                "User retrieved from database successfully",
                operation="db_query_success",
                user_id=entity_id,
                db_elapsed_seconds=round(db_elapsed, 3),
                has_roles=len(user.roles) > 0 if hasattr(user, 'roles') else False
            )

        except EntityNotFoundError:
            elapsed_time = time.time() - start_time
            logger.error(
                "User not found in database",
                operation="db_query_error",
                error_type="entity_not_found",
                user_id=entity_id,
                elapsed_seconds=round(elapsed_time, 3),
                status_code=404
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
                user_id=entity_id,
                elapsed_seconds=round(elapsed_time, 3),
                status_code=500
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
                user_id=entity_id,
                elapsed_seconds=round(elapsed_time, 3),
                status_code=500,
                exc_info=True
            )
            return {
                "statusCode": 500,
                "body": json.dumps({"message": "Internal server error."}),
            }

        logger.debug(
            "Starting role filtering process",
            operation="role_filtering",
            user_id=entity_id,
            caller_context=caller_context,
            total_roles=len(user.roles) if hasattr(user, 'roles') else 0
        )
        result = _get_user_data_with_right_context_roles(user, caller_context)

        elapsed_time = time.time() - start_time
        logger.info(
            "IAM get operation completed successfully",
            operation="iam_get_success",
            user_id=entity_id,
            caller_context=caller_context,
            elapsed_seconds=round(elapsed_time, 3),
            status_code=200
        )
        return result


def _get_user_data_with_right_context_roles(
    user: User, caller_context: str
) -> dict[str, int | str]:
    """Filter user roles by caller context and prepare API response.
    
    Args:
        user: Domain user entity.
        caller_context: Context to filter roles by.
        
    Returns:
        HTTP response dict with filtered user data.
    """
    logger.debug(
        "Converting domain user to API user",
        operation="domain_to_api_conversion",
        user_id=user.id
    )
    api_user = ApiUser.from_domain(user)

    all_roles = list(api_user.roles)
    logger.debug(
        "Retrieved user roles for filtering",
        operation="role_retrieval",
        user_id=user.id,
        total_roles_count=len(all_roles),
        target_context=caller_context
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
                    target_context=caller_context
                )
            else:
                logger.debug(
                    "Role filtered out due to context mismatch",
                    operation="role_filter",
                    user_id=user.id,
                    role_name=role.name,
                    role_context=role.context,
                    target_context=caller_context
                )

    logger.debug(
        "Role filtering completed",
        operation="role_filtering_complete",
        user_id=user.id,
        target_context=caller_context,
        filtered_roles_count=len(caller_context_roles),
        original_roles_count=len(all_roles)
    )

    new_api_user = api_user.model_copy(
        update={"roles": frozenset(caller_context_roles)}
    )
    response_body = new_api_user.model_dump_json(
        include={"id", "roles"}, exclude={"roles": {"context"}}
    )

    logger.debug(
        "API response generated successfully",
        operation="api_response_generation",
        user_id=user.id,
        response_roles_count=len(caller_context_roles),
        response_size_bytes=len(response_body)
    )
    return {"statusCode": 200} | {"body": response_body}
