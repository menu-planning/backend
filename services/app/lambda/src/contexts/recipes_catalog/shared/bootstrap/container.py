from dependency_injector import containers, providers
from src.contexts.recipes_catalog.shared.services.uow import UnitOfWork
from src.db.database import async_db
from src.rabbitmq.aio_pika_manager import AIOPikaManager
from src.rabbitmq.connection import aio_pika_connection

from .bootstrap import bootstrap


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(modules=[__name__])

    database = providers.Object(async_db)
    connection_maker = providers.Object(aio_pika_connection)
    aio_pika_manager = providers.Singleton(AIOPikaManager, connection_maker)
    uow = providers.Factory(
        UnitOfWork,
        session_factory=database.provided.async_session_factory,
    )
    bootstrap = providers.Factory(
        bootstrap,
        uow=uow,
        aio_pika_manager=aio_pika_manager,
    )
