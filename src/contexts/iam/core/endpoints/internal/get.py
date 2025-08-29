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
from src.logging.logger import logger

if TYPE_CHECKING:
    from src.contexts.iam.core.services.uow import UnitOfWork
    from src.contexts.shared_kernel.services.messagebus import MessageBus
container = Container()


async def get(entity_id: str, caller_context: str) -> dict[str, int | str]:
    start_time = time.time()
    logger.info(
        f"Internal IAM get() called - User: {entity_id}, "
        f"Caller context: {caller_context}"
    )

    bus: MessageBus = container.bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        try:
            logger.debug(f"Querying database for user: {entity_id}")
            user = await uow.users.get(entity_id)

            db_elapsed = time.time() - start_time
            logger.debug(
                f"User retrieved from database in {db_elapsed:.3f}s - User: {entity_id}"
            )

        except EntityNotFoundError:
            elapsed_time = time.time() - start_time
            logger.error(
                f"User not found in database after {elapsed_time:.3f}s - "
                f"User: {entity_id}"
            )
            return {
                "statusCode": 404,
                "body": json.dumps({"message": "User not in database."}),
            }
        except MultipleEntitiesFoundError:
            elapsed_time = time.time() - start_time
            logger.error(
                f"Multiple users found in database after {elapsed_time:.3f}s - "
                f"User: {entity_id}"
            )
            return {
                "statusCode": 500,
                "body": json.dumps({"message": "Multiple users found in database."}),
            }
        except Exception as e:
            elapsed_time = time.time() - start_time
            logger.error(
                f"Database error after {elapsed_time:.3f}s for user {entity_id} - "
                f"Error: {type(e).__name__}: {e!s}"
            )
            return {
                "statusCode": 500,
                "body": json.dumps({"message": "Internal server error."}),
            }

        logger.debug(
            f"Processing user data and filtering roles for context: {caller_context}"
        )
        result = _get_user_data_with_right_context_roles(user, caller_context)

        elapsed_time = time.time() - start_time
        logger.info(
            f"Internal IAM get() completed successfully in {elapsed_time:.3f}s - "
            f"User: {entity_id}, Context: {caller_context}"
        )
        return result


def _get_user_data_with_right_context_roles(
    user: User, caller_context: str
) -> dict[str, int | str]:
    logger.debug(f"Converting domain user to API user - User: {user.id}")
    api_user = ApiUser.from_domain(user)

    all_roles = list(api_user.roles)
    logger.debug(
        f"User has {len(all_roles)} total roles across all contexts - User: {user.id}"
    )

    caller_context_roles = []
    if all_roles:
        for role in all_roles:
            if role.context == caller_context:
                caller_context_roles.append(role)
                logger.debug(
                    f"Role matched context '{caller_context}' - Role: {role.name}, "
                    f"User: {user.id}"
                )
            else:
                logger.debug(
                    f"Role filtered out (context mismatch) - Role: {role.name}, "
                    f"Context: {role.context}, Expected: {caller_context}, "
                    f"User: {user.id}"
                )

    logger.debug(
        f"Filtered to {len(caller_context_roles)} roles for "
        f"context '{caller_context}' - User: {user.id}"
    )

    new_api_user = api_user.model_copy(
        update={"roles": frozenset(caller_context_roles)}
    )
    response_body = new_api_user.model_dump_json(
        include={"id", "roles"}, exclude={"roles": {"context"}}
    )

    logger.debug(
        f"Generated API response for user {user.id} "
        f"with {len(caller_context_roles)} roles"
    )
    return {"statusCode": 200} | {"body": response_body}
