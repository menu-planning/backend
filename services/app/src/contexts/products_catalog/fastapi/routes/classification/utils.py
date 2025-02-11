from fastapi import APIRouter, HTTPException, Request
from src.contexts.products_catalog.fastapi.bootstrap import fastapi_bootstrap
from src.contexts.products_catalog.shared.adapters.api_schemas.commands.classification.base_class import (
    ApiCreateClassification,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.entities.classifications.base_class import (
    ApiClassification,
)
from src.contexts.products_catalog.shared.adapters.api_schemas.entities.classifications.filter import (
    ApiClassificationFilter,
)
from src.contexts.products_catalog.shared.domain.commands.classifications.base_classes import (
    DeleteClassification,
)
from src.contexts.products_catalog.shared.domain.entities.classification import (
    Classification,
)
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


# TODO: Implement update_classification endpoint


async def read_classifications(
    request: Request,
    current_user: SeedUser,
    uow_repo_name: str,
    api_schema_class: type[ApiClassification],
    bus: MessageBus,
):
    queries = request.query_params
    filters = {k.replace("-", "_"): v for k, v in queries.items()}
    filters["limit"] = int(queries.get("limit", 500))
    filters["sort"] = queries.get("sort", "-date")
    api = ApiClassificationFilter(**filters).model_dump()
    for k, _ in filters.items():
        filters[k] = api.get(k)

    uow: UnitOfWork
    async with bus.uow as uow:
        repo: CompositeRepository = getattr(uow, uow_repo_name)
        try:
            classifications = await repo.query(filter=filters)
            return (
                [api_schema_class.from_domain(i) for i in classifications]
                if classifications
                else []
            )
        except BadRequestException as e:
            raise HTTPException(status_code=400, detail=str(e))


async def create_classification(
    classification_data: type[ApiCreateClassification],
    current_user: SeedUser,
    bus: MessageBus,
):
    if not (current_user.has_permission(EnumPermission.MANAGE_PRODUCTS)):
        raise HTTPException(
            status_code=403, detail="User does not have enough privilegies."
        )
    cmd = classification_data.to_domain()

    await bus.handle(cmd)


async def delete_classification(
    classification_id: int,
    current_user: SeedUser,
    uow_repo_name: str,
    delete_cmd_class: type[DeleteClassification],
    bus: MessageBus,
):

    uow: UnitOfWork
    async with bus.uow as uow:
        repo: CompositeRepository = getattr(uow, uow_repo_name)
        try:
            classification: Classification = await repo.get(classification_id)
        except EntityNotFoundException:
            raise HTTPException(
                status_code=404,
                detail=f"classification {classification_id} not in database.",
            )
    if not (
        current_user.has_permission(EnumPermission.MANAGE_PRODUCTS)
        or classification.author_id == current_user.id
    ):
        raise HTTPException(
            status_code=403, detail="User does not have enough privilegies."
        )
    cmd = delete_cmd_class(id=classification_id)
    await bus.handle(cmd)


async def read_classification(
    classification_id: int,
    current_user: SeedUser,
    uow_repo_name: str,
    api_schema_class: type[ApiClassification],
    bus: MessageBus,
):

    uow: UnitOfWork
    async with bus.uow as uow:
        repo: CompositeRepository = getattr(uow, uow_repo_name)
        try:
            classification: Classification = await repo.get(classification_id)
        except EntityNotFoundException:
            raise HTTPException(
                status_code=404,
                detail=f"classification {classification_id} not in database.",
            )
    if not (
        current_user.has_permission(EnumPermission.MANAGE_PRODUCTS)
        or classification.author_id == current_user.id
    ):
        raise HTTPException(
            status_code=403, detail="User does not have enough privilegies."
        )
    return api_schema_class.from_domain(classification)
