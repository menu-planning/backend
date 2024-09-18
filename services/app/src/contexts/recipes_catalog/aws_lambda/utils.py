import json
from typing import Any

from pydantic import BaseModel
from src.contexts.recipes_catalog.shared.adapters.api_schemas.commands.tags.create import (
    ApiCreateTag,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.tags.base_class import (
    ApiTag,
)
from src.contexts.recipes_catalog.shared.adapters.api_schemas.entities.tags.tag_filter import (
    ApiTagFilter,
)
from src.contexts.recipes_catalog.shared.domain.commands.tags.base_classes import (
    DeleteTag,
)
from src.contexts.recipes_catalog.shared.domain.entities.tags.base_classes import Tag
from src.contexts.recipes_catalog.shared.domain.enums import (
    Permission as EnumPermission,
)
from src.contexts.recipes_catalog.shared.domain.enums import Role as EnumRoles
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.adapters.exceptions import EntityNotFoundException
from src.contexts.seedwork.shared.adapters.repository import CompositeRepository
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.exceptions import BadRequestException
from src.contexts.shared_kernel.domain.enums import Privacy
from src.contexts.shared_kernel.endpoints.api_schemas.value_objects.name_tag.base_class import (
    ApiNameTag,
)
from src.contexts.shared_kernel.endpoints.api_schemas.value_objects.name_tag.name_tag_filter import (
    ApiNameTagFilter,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus


async def create_tag(
    tag_data: ApiCreateTag,
    current_user: SeedUser,
    bus: MessageBus,
):
    if tag_data.author_id and not (
        current_user.has_permission(EnumPermission.MANAGE_RECIPES)
        or current_user.id == tag_data.author_id
    ):
        return {
            "statusCode": 403,
            "body": json.dumps({"message": "User does not have enough privilegies."}),
        }
    else:
        tag_data.author_id = current_user.id
    cmd = tag_data.to_domain()

    await bus.handle(cmd)


async def delete_tag(
    id: int,
    current_user: SeedUser,
    uow_repo_name: str,
    delete_cmd_class: type[DeleteTag],
    bus: MessageBus,
):

    uow: UnitOfWork
    async with bus.uow as uow:
        repo: CompositeRepository = getattr(uow, uow_repo_name)
        try:
            tag: Tag = await repo.get(id)
        except EntityNotFoundException:
            return {
                "statusCode": 404,
                "body": json.dumps({"message": f"Tag {id} not in database."}),
            }
    if not (
        current_user.has_permission(EnumPermission.MANAGE_RECIPES)
        or tag.author_id == current_user.id
    ):
        return {
            "statusCode": 403,
            "body": json.dumps({"message": "User does not have enough privilegies."}),
        }
    cmd = delete_cmd_class(id=id)
    await bus.handle(cmd)


async def read_tag(
    tag_id: int,
    current_user: SeedUser,
    uow_repo_name: str,
    api_schema_class: type[ApiTag],
    bus: MessageBus,
):

    uow: UnitOfWork
    async with bus.uow as uow:
        repo: CompositeRepository = getattr(uow, uow_repo_name)
        try:
            tag: Tag = await repo.get(tag_id)
        except EntityNotFoundException:
            return {
                "statusCode": 404,
                "body": json.dumps({"message": f"Tag {id} not in database."}),
            }
    if not (
        current_user.has_permission(EnumPermission.MANAGE_RECIPES)
        or tag.author_id == current_user.id
        or tag.privacy == Privacy.PUBLIC
    ):
        return {
            "statusCode": 403,
            "body": json.dumps({"message": "User does not have enough privilegies."}),
        }
    return api_schema_class.from_domain(tag)


async def read_tags(
    *,
    event: dict[str, Any],
    current_user: SeedUser,
    uow_repo_name: str,
    bus: MessageBus,
    api_schema_class: type[ApiTag],
    api_filter_class: type[BaseModel] = ApiTagFilter,
):
    query_params = (
        event.get("queryStringParameters") if event.get("queryStringParameters") else {}
    )
    filters = {k.replace("-", "_"): v for k, v in query_params.items()}
    filters["limit"] = int(query_params.get("limit", 50))
    filters["sort"] = query_params.get("sort", "-created_at")

    api = api_filter_class(**filters).model_dump()
    for k, _ in filters.items():
        filters[k] = api.get(k)

    uow: UnitOfWork
    async with bus.uow as uow:
        repo: CompositeRepository = getattr(uow, uow_repo_name)
        try:
            if current_user.has_role(EnumRoles.ADMINISTRATOR):
                # only admin can query for all diet types
                tags = await repo.query(filter=filters)
                return [api_schema_class.from_domain(i) for i in tags] if tags else []
            else:
                if filters.get("author_id") is not None:
                    if filters.get("author_id") != current_user.id:
                        # only admin or the author can query for their own tags
                        return {
                            "statusCode": 403,
                            "body": json.dumps(
                                {"message": "User does not have enough privilegies."}
                            ),
                        }
                    tags = await repo.query(filter=filters)
                else:
                    # query for all private tags owned by the user
                    own_recipes = await repo.query(
                        filter=filters
                        | {"author_id": current_user.id}
                        | {"privacy": Privacy.PRIVATE}
                    )
                    # query for all public tags
                    public_recipes = await repo.query(
                        filter=filters | {"privacy": Privacy.PUBLIC}
                    )
                    tags = own_recipes + public_recipes
                return [api_schema_class.from_domain(i) for i in tags] if tags else []
        except BadRequestException as e:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": e}),
            }


async def read_name_tag(
    tag_id: int,
    uow_repo_name: str,
    api_schema_class: type[ApiNameTag],
    bus: MessageBus,
):

    uow: UnitOfWork
    async with bus.uow as uow:
        repo: CompositeRepository = getattr(uow, uow_repo_name)
        try:
            tag: Tag = await repo.get(tag_id)
        except EntityNotFoundException:
            return {
                "statusCode": 404,
                "body": json.dumps({"message": f"Tag {tag_id} not in database."}),
            }
    return api_schema_class.from_domain(tag)


async def read_name_tags(
    event: dict[str, Any],
    uow_repo_name: str,
    api_schema_class: type[ApiNameTag],
    bus: MessageBus,
):
    query_params = (
        event.get("queryStringParameters") if event.get("queryStringParameters") else {}
    )
    filters = {k.replace("-", "_"): v for k, v in query_params.items()}
    filters["limit"] = int(query_params.get("limit", 50))
    filters["sort"] = query_params.get("sort", "name")

    api = ApiNameTagFilter(**filters).model_dump()
    for k, _ in filters.items():
        filters[k] = api.get(k)

    uow: UnitOfWork
    async with bus.uow as uow:
        repo: CompositeRepository = getattr(uow, uow_repo_name)
        try:
            tags = await repo.query(filter=filters)
            return [api_schema_class.from_domain(i) for i in tags] if tags else []
        except BadRequestException as e:
            return {
                "statusCode": 400,
                "body": json.dumps({"message": e}),
            }
