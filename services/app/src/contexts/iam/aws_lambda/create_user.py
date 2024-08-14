import json
import uuid
from typing import Any

import anyio
from src.contexts.iam.shared.adapters.api_schemas.commands.create_user import (
    ApiCreateUser,
)
from src.contexts.iam.shared.bootstrap.container import Container
from src.contexts.iam.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.adapters.exceptions import (
    EntityNotFoundException,
    MultipleEntitiesFoundException,
)
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import (
    lambda_exception_handler,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger


@lambda_exception_handler
async def async_create(event: dict[str, Any], context: Any) -> dict[str, Any]:
    logger.debug("Post Confirmation Trigger Event: ", json.dumps(event))
    user_attributes = event["request"]["userAttributes"]
    user_id = user_attributes["sub"]
    bus: MessageBus = Container().bootstrap()
    uow: UnitOfWork
    async with bus.uow as uow:
        try:
            await uow.users.get(user_id)
            return {
                "statusCode": 409,
                "body": json.dumps({"message": f"User {user_id} already exists."}),
            }
        except EntityNotFoundException:
            logger.info(f"User not found in database. Will create user {id}")
            api = ApiCreateUser(user_id=user_id)
            cmd = api.to_domain()
            await bus.handle(cmd)
            return {
                "statusCode": 201,
                "body": json.dumps(
                    {
                        "message": "User created successfully",
                        "user_id": user_id,
                    }
                ),
            }
        except MultipleEntitiesFoundException:
            logger.error(f"Multiple users found in database: {id}")
            return json.dumps(
                {"statuCode": 500, "body": "Multiple users found in database."}
            )
        except Exception as e:
            logger.error(f"Error: {e}")
            return json.dumps({"statuCode": 500, "body": "Internal server error."})


def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to create products.
    """
    logger.correlation_id.set(uuid.uuid4())
    return anyio.run(async_create, event, context)
