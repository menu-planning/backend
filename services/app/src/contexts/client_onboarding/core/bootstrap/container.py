"""
Client Onboarding Dependency Injection Container

Configures dependencies for the client onboarding context.
"""

from dependency_injector import containers, providers
from src.contexts.client_onboarding.core.services.uow import UnitOfWork
from src.contexts.client_onboarding.services.typeform_client import create_typeform_client
from src.contexts.client_onboarding.services.webhook_manager import WebhookManager
from src.contexts.client_onboarding.services.event_publisher import create_routed_event_publisher
from src.contexts.client_onboarding.core.bootstrap.bootstrap import bootstrap
from src.db.database import async_db


class Container(containers.DeclarativeContainer):
    """Dependency injection container for client onboarding context."""
    
    wiring_config = containers.WiringConfiguration(modules=[__name__])

    # Database
    database = providers.Object(async_db)
    
    # Unit of Work
    uow = providers.Factory(
        UnitOfWork,
        session_factory=database.provided.async_session_factory,
    )
    
    # External services
    typeform_client = providers.Factory(create_typeform_client)
    
    # Event publishing
    event_publisher = providers.Factory(create_routed_event_publisher)
    
    # Business services
    webhook_manager = providers.Factory(
        WebhookManager,
        typeform_client=typeform_client
    )
    
    # Bootstrap function that creates MessageBus
    def bootstrap(self):
        """Create and configure the MessageBus for this context."""
        return bootstrap(
            uow=self.uow(),
            webhook_manager=self.webhook_manager(),
            event_publisher=self.event_publisher()
        ) 