from typing import Annotated

from fastapi import APIRouter, Depends, status
from src.contexts.iam.fastapi.bootstrap import fastapi_bootstrap
from src.contexts.iam.shared.adapters.api_schemas.commands.create_user import (
    ApiCreateUser,
)
from src.contexts.iam.shared.domain.entities.user import User
from src.contexts.seedwork.fastapi.deps import current_user_id
from src.contexts.seedwork.shared.endpoints.decorators import timeout_after
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger

router = APIRouter()


@router.post("/users", status_code=status.HTTP_201_CREATED)
@timeout_after()
async def create(
    cmd_data: ApiCreateUser,
    current_user_id: Annotated[User, Depends(current_user_id)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
):
    """
    Create a new user.
    """
    logger.info(f"Creating user with id {cmd_data.user_id}")
    cmd = cmd_data.to_domain()
    await bus.handle(cmd)
