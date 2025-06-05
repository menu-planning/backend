import json
import uuid
from typing import Any

import anyio
from src.contexts.iam.core.adapters.api_schemas.commands.create_user import (
    ApiCreateUser,
)
from src.contexts.iam.core.bootstrap.container import Container
from src.contexts.iam.core.services.uow import UnitOfWork
from src.contexts.seedwork.shared.adapters.exceptions import (
    EntityNotFoundException,
    MultipleEntitiesFoundException,
)
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import (
    lambda_exception_handler,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger, generate_correlation_id

from .CORS_headers import CORS_headers


@lambda_exception_handler
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
        except EntityNotFoundException:
            logger.info(f"User not found in database. Will create user {user_id}")
            api = ApiCreateUser(user_id=user_id)
            cmd = api.to_domain()
            await bus.handle(cmd)
            logger.info(f"User {user_id} created successfully.")
            event["response"]["autoConfirmUser"] = True
            event["response"]["autoVerifyEmail"] = True
            return event
        except MultipleEntitiesFoundException:
            logger.error(f"Multiple users found in database: {id}")
            return {
                "statuCode": 500,
                "headers": CORS_headers,
                "body": json.dumps("Multiple users found in database."),
            }
        except Exception as e:
            logger.error(f"Error: {e}")
            return {"statuCode": 500, "body": json.dumps("Internal server error.")}


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to create products.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
