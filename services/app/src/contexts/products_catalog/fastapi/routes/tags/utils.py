from fastapi import APIRouter, HTTPException, Request
from src.contexts.products_catalog.fastapi.bootstrap import fastapi_bootstrap
from src.contexts.products_catalog.shared.adapters.api_schemas.commands.tags.base_class import (
    ApiCreateTag,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.entities.tags.base_tag import (
    ApiTag,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.entities.tags.filter import (
    ApiTagFilter,
)
from src.contexts.products_catalog.shared.domain.commands.tags.base_classes import (
    DeleteTag,
)
from src.contexts.products_catalog.shared.domain.entities.tags import Tag
from src.contexts.products_catalog.shared.domain.enums import (
    Permission as EnumPermission,
)
from src.contexts.products_catalog.shared.services.uow import UnitOfWork
from src.contexts.seedwork.shared.adapters.exceptions import EntityNotFoundException
from src.contexts.seedwork.shared.adapters.repository import CompositeRepository
from src.contexts.seedwork.shared.domain.value_objects.user import SeedUser
from src.contexts.seedwork.shared.endpoints.exceptions import BadRequestException
from src.contexts.shared_kernel.services.messagebus import MessageBus

router = APIRouter()


# TODO: Implement update_tag endpoint


async def read_tags(
    request: Request,
    current_user: SeedUser,
    uow_repo_name: str,
    api_schema_class: type[ApiTag],
    bus: MessageBus,
):
    queries = request.query_params
    filters = {k.replace("-", "_"): v for k, v in queries.items()}
    filters["limit"] = int(queries.get("limit", 500))
    filters["sort"] = queries.get("sort", "-date")
    api = ApiTagFilter(**filters).model_dump()
    for k, _ in filters.items():
        filters[k] = api.get(k)

    uow: UnitOfWork
    async with bus.uow as uow:
        repo: CompositeRepository = getattr(uow, uow_repo_name)
        try:
            tags = await repo.query(filter=filters)
            return [api_schema_class.from_domain(i) for i in tags] if tags else []
        except BadRequestException as e:
            raise HTTPException(status_code=400, detail=str(e))


async def create_tag(
    tag_data: type[ApiCreateTag],
    current_user: SeedUser,
    bus: MessageBus,
):
    if not (current_user.has_permission(EnumPermission.MANAGE_PRODUCTS)):
        raise HTTPException(
            status_code=403, detail="User does not have enough privilegies."
        )
    cmd = tag_data.to_domain()

    await bus.handle(cmd)


async def delete_tag(
    tag_id: int,
    current_user: SeedUser,
    uow_repo_name: str,
    delete_cmd_class: type[DeleteTag],
    bus: MessageBus,
):

    uow: UnitOfWork
    async with bus.uow as uow:
        repo: CompositeRepository = getattr(uow, uow_repo_name)
        try:
            tag: Tag = await repo.get(tag_id)
        except EntityNotFoundException:
            raise HTTPException(
                status_code=404, detail=f"Tag {tag_id} not in database."
            )
    if not (
        current_user.has_permission(EnumPermission.MANAGE_PRODUCTS)
        or tag.author_id == current_user.id
    ):
        raise HTTPException(
            status_code=403, detail="User does not have enough privilegies."
        )
    cmd = delete_cmd_class(id=tag_id)
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
            raise HTTPException(
                status_code=404, detail=f"Tag {tag_id} not in database."
            )
    if not (
        current_user.has_permission(EnumPermission.MANAGE_PRODUCTS)
        or tag.author_id == current_user.id
    ):
        raise HTTPException(
            status_code=403, detail="User does not have enough privilegies."
        )
    return api_schema_class.from_domain(tag)
