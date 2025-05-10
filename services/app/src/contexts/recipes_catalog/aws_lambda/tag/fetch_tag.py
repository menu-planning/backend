import json
import os
import uuid
from typing import Any

import anyio

from src.contexts.recipes_catalog.shared.adapters.internal_providers.iam.api import \
    IAMProvider
from src.contexts.recipes_catalog.shared.bootstrap.container import Container
from src.contexts.recipes_catalog.shared.domain.enums import Role as EnumRoles
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.decorators.lambda_exception_handler import \
    lambda_exception_handler
from src.contexts.seedwork.shared.endpoints.exceptions import \
    BadRequestException
from src.contexts.seedwork.shared.utils import custom_serializer
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag import \
    ApiTag
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.tag.tag_filter import \
    ApiTagFilter
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger, generate_correlation_id

from ..CORS_headers import CORS_headers


@lambda_exception_handler
async def async_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to query for tags.
    """
    logger.debug(f"Event received {event}")
    is_localstack = os.getenv("IS_LOCALSTACK", "false").lower() == "true"
    if not is_localstack:
        authorizer_context = event["requestContext"]["authorizer"]
        user_id = authorizer_context.get("claims").get("sub")
        logger.debug(f"Fetching tags for user {user_id}")
        response: dict = await IAMProvider.get(user_id)
        if response.get("statusCode") != 200:
            return response
        current_user: SeedUser = response["body"]
    else:
        current_user = SeedUser(id="localstack_user", roles=[])

    query_params: dict[str, Any] | Any = (
        event.get("multiValueQueryStringParameters") if event.get("multiValueQueryStringParameters") else {}
    )
    logger.debug(f"Query params: {query_params}")
    filters = {k.replace("-", "_"): v for k, v in query_params.items()}
    filters["limit"] = int(query_params.get("limit", 50))
    filters["sort"] = query_params.get("sort", "key")

    for k, v in filters.items():
        if isinstance(v, list) and len(v) == 1:
            filters[k] = v[0]

    logger.debug('before api: %s', filters)
    api = ApiTagFilter(**filters).model_dump()
    logger.debug('after api: %s', api)
    for k, _ in filters.items():
        filters[k] = api.get(k)

    logger.debug(f"read_tags | Filters: {filters}")

    uow: UnitOfWork
    bus: MessageBus = Container().bootstrap()
    async with bus.uow as uow:
        try:
            if current_user.has_role(EnumRoles.ADMINISTRATOR):
                # only admin can query for all diet types
                tags = await uow.tags.query(filter=filters)
                return {
                    "statusCode": 200,
                    "headers": CORS_headers,
                    "body": json.dumps(
                        (
                            [ApiTag.from_domain(i).model_dump() for i in tags]
                            if tags
                            else []
                        ),
                        default=custom_serializer,
                    ),
                }
            else:
                if filters.get("author_id") is not None:
                    if filters.get("author_id") != current_user.id:
                        # only admin or the author can query for their own tags
                        return {
                            "statusCode": 403,
                            "headers": CORS_headers,
                            "body": json.dumps(
                                {"message": "User does not have enough privilegies."}
                            ),
                        }
                    tags = await uow.tags.query(filter=filters)
                else:
                    filters.update({"author_id": current_user.id})
                    logger.debug(f"Filters after adding author_id: {filters}")
                    tags = await uow.tags.query(
                        filter=filters
                    )
                    logger.debug(f"Tags found: {tags}")
                    logger.debug(f"ApiTags: {[ApiTag.from_domain(i).model_dump() for i in tags] if tags else []}")
                    return {
                        "statusCode": 200,
                        "headers": CORS_headers,
                        "body": json.dumps(
                            (
                                [
                                    ApiTag.from_domain(i).model_dump()
                                    for i in tags
                                ]
                                if tags
                                else []
                            ),
                            default=custom_serializer,
                        ),
                    }
        except BadRequestException as e:
            return {
                "statusCode": 400,
                "headers": CORS_headers,
                "body": json.dumps({"message": e}),
            }

def lambda_handler(event: dict[str, Any], context: Any) -> dict[str, Any]:
    """
    Lambda function handler to query for tags.
    """
    generate_correlation_id()
    return anyio.run(async_handler, event, context)
