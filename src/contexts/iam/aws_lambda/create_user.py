import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.contexts.iam.core.services.uow import UnitOfWork
    from src.contexts.shared_kernel.services.messagebus import MessageBus

import anyio
from src.contexts.client_onboarding.aws_lambda.shared.cors_headers import CORS_headers
from src.contexts.iam.core.adapters.api_schemas.commands.api_create_user import (
    ApiCreateUser,
)
from src.contexts.iam.core.bootstrap.container import Container
from src.contexts.seedwork.shared.adapters.exceptions.repo_exceptions import (
    EntityNotFoundError,
    MultipleEntitiesFoundError,
)
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import (
    lambda_exception_handler,
)
from src.logging.logger import StructlogFactory, generate_correlation_id

logger = StructlogFactory.get_logger(__name__)


@lambda_exception_handler(CORS_headers)
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    logger.debug("Post Confirmation Trigger Event: " + json.dumps(event))
    user_id = event["userName"]
    bus: MessageBus = Container().bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        try:
            await uow.users.get(user_id)
            return {
                "statusCode": 409,
                "headers": CORS_headers,
                "body": json.dumps(f"User {user_id} already exists."),
            }
        except EntityNotFoundError:
            logger.info(
                "User not found in database, creating new user",
                action="create_user_start",
                business_context="user_registration"
            )
            api = ApiCreateUser(user_id=user_id)
            cmd = api.to_domain()
            await bus.handle(cmd)
            logger.info(
                "User created successfully",
                action="create_user_success",
                business_context="user_registration"
            )
            event["response"]["autoConfirmUser"] = True
            event["response"]["autoVerifyEmail"] = True
            return event
        except MultipleEntitiesFoundError:
            logger.error(
                "Multiple users found in database",
                action="create_user_error",
                error_type="MultipleEntitiesFoundError",
                business_context="user_registration"
            )
            return {
                "statuCode": 500,
                "headers": CORS_headers,
                "body": json.dumps("Multiple users found in database."),
            }
        except Exception as e:
            logger.error(
                "Error creating user",
                action="create_user_error",
                error_type=type(e).__name__,
                error_message=str(e),
                business_context="user_registration",
                exc_info=True
            )
            return {"statuCode": 500, "body": json.dumps("Internal server error.")}


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to create products.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
