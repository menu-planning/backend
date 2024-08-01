from typing import Annotated

from fastapi import Depends, HTTPException
from src.contexts.iam.fastapi.bootstrap import fastapi_bootstrap
from src.contexts.iam.shared.domain.entities.user import User
from src.contexts.iam.shared.services.uow import UnitOfWork
from src.contexts.seedwork.fastapi.deps import current_user_id
from src.contexts.seedwork.shared.adapters.exceptions import (
    EntityNotFoundException,
    MultipleEntitiesFoundException,
)
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.logging.logger import logger


async def current_active_user(
    current_user_id: Annotated[str, Depends(current_user_id)],
    bus: Annotated[MessageBus, Depends(fastapi_bootstrap)],
) -> User:
    try:
        uow: UnitOfWork
        async with bus.uow as uow:
            user = await uow.users.get(id=current_user_id)
        return user
    except EntityNotFoundException:
        logger.error(f"User not found in database: {current_user_id}")
        raise HTTPException(status_code=404, detail="User not in database.")
    except MultipleEntitiesFoundException:
        logger.error(f"Multiple users found in database: {current_user_id}")
        raise HTTPException(status_code=500, detail="Multiple users found in database.")
    except Exception as e:
        logger.error(f"Error: {e}")
        raise HTTPException(status_code=500, detail="Internal server error.")
