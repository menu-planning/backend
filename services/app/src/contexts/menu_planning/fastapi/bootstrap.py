from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.contexts.menu_planning.shared.services.uow import UnitOfWork
from src.contexts.shared_kernel.services.messagebus import MessageBus
from src.db.database import get_db_session_factory
from src.rabbitmq.aio_pika_manager import AIOPikaManager
from src.rabbitmq.connection import aio_pika_connection

from ..shared.bootstrap.boostrap import bootstrap


def get_uow(
    db_session_factory: AsyncSession = Depends(get_db_session_factory),
) -> UnitOfWork:
    return UnitOfWork(session_factory=db_session_factory)


def get_aio_pika_manager() -> AIOPikaManager:
    return AIOPikaManager(aio_pika_connection)


def fastapi_bootstrap(
    uow: UnitOfWork = Depends(get_uow),
    aio_pika_manager: AIOPikaManager = Depends(get_aio_pika_manager),
    # notifications: AsyncAbstractNotifications = None,
) -> MessageBus:
    return bootstrap(uow=uow, aio_pika_manager=aio_pika_manager)
