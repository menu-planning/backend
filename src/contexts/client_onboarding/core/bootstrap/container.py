from dependency_injector import containers, providers
from src.contexts.client_onboarding.core.bootstrap.bootstrap import bootstrap
from src.contexts.client_onboarding.core.services.uow import UnitOfWork
from src.contexts.client_onboarding.core.services.webhooks.manager import (
    create_webhook_manager,
)
from src.db.database import async_db


class Container(containers.DeclarativeContainer):
    """Dependency injection container for client onboarding context.

    Provides configured instances of core services including database access,
    unit of work, webhook management, and the bootstrap function.

    Notes:
        Uses dependency-injector for service wiring and lifecycle management.
        All providers are configured as factories for proper isolation.
    """

    wiring_config = containers.WiringConfiguration(modules=[__name__])

    # Database connection provider
    database = providers.Object(async_db)

    # Unit of Work provider for transaction management
    uow = providers.Factory(
        UnitOfWork,
        session_factory=database.provided.async_session_factory,
    )

    # Webhook manager provider for external integrations
    webhook_manager = providers.Factory(create_webhook_manager)

    # Bootstrap function provider for context initialization
    bootstrap = providers.Factory(
        bootstrap,
        uow=uow,
        webhook_manager=webhook_manager,
    )
