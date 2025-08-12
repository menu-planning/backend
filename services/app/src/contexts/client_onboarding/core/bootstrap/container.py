from dependency_injector import containers, providers

from src.contexts.client_onboarding.core.services.uow import UnitOfWork
from src.contexts.client_onboarding.core.services.webhooks.manager import (
    create_webhook_manager,
)
from src.db.database import async_db

from .bootstrap import bootstrap


class Container(containers.DeclarativeContainer):
    wiring_config = containers.WiringConfiguration(modules=[__name__])

    database = providers.Object(async_db)

    uow = providers.Factory(
        UnitOfWork,
        session_factory=database.provided.async_session_factory,
    )

    webhook_manager = providers.Factory(create_webhook_manager)

    bootstrap = providers.Factory(
        bootstrap,
        uow=uow,
        webhook_manager=webhook_manager,
    )