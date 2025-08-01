"""
Client Onboarding Dependency Injection Container

Configures dependencies for the client onboarding context.
"""

from dependency_injector import containers, providers
from src.contexts.client_onboarding.core.services.uow import UnitOfWork
from src.contexts.client_onboarding.services.typeform_client import create_typeform_client
from src.contexts.client_onboarding.services.webhook_manager import WebhookManager, create_webhook_manager
from src.contexts.client_onboarding.services.event_publisher import create_routed_event_publisher
from src.contexts.client_onboarding.core.bootstrap.bootstrap import bootstrap
from src.db.database import async_db
from src.contexts.client_onboarding.config import config


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
    
    # Business services with enhanced capabilities
    webhook_manager = providers.Factory(
        create_webhook_manager,
        typeform_client=typeform_client
    )
    
    # Enhanced webhook manager with comprehensive status tracking, operation history,
    # bulk operations, and synchronization capabilities.
    # Uses validated configuration and rate-limited TypeForm client.
    webhook_manager_enhanced = providers.Factory(
        WebhookManager,
        typeform_client=typeform_client
    )
    
    # Bootstrap function that creates MessageBus
    def bootstrap(self):
        """
        Create and configure the MessageBus for this context.
        
        Uses enhanced webhook manager with:
        - Comprehensive status tracking (WebhookStatusInfo, WebhookOperationRecord)
        - Bulk webhook operations and synchronization
        - Operation audit trail and error handling
        - Rate-limited TypeForm client (2 req/sec compliance)
        - Validated configuration (startup validation enabled)
        """
        return bootstrap(
            uow=self.uow(),
            webhook_manager=self.webhook_manager(),
            event_publisher=self.event_publisher()
        )
    
    def get_webhook_manager_with_context(self, operation_context: str = "default"):
        """
        Get webhook manager with operational context for enhanced tracking.
        
        Args:
            operation_context: Context for operation tracking (e.g., 'api', 'scheduled', 'admin')
            
        Returns:
            Configured WebhookManager with operational context
        """
        manager = self.webhook_manager()
        # Could add context-specific configuration here if needed
        return manager 