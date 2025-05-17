from dependency_injector import containers, providers
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.db.database import async_db

from .bootstrap import bootstrap


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(modules=[__name__])

    database = providers.Object(async_db)
    uow = providers.Factory(
        UnitOfWork,
        session_factory=database.provided.async_session_factory,
    )
    bootstrap = providers.Factory(
        bootstrap,
        uow=uow,
    )
