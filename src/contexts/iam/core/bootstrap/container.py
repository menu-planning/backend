"""Dependency injection container for IAM context wiring.

Exposes providers for database access, unit-of-work instances, and a fully
bootstrapped message bus with IAM handlers registered.
"""

from dependency_injector import containers, providers
from src.contexts.iam.core.services.uow import UnitOfWork
from src.db.fastapi_database import fastapi_db

from .bootstrap import bootstrap


class Container(containers.DeclarativeContainer):
    """Dependency injection container for IAM components.
    
    Provides dependency injection configuration for IAM context services.
    Manages database connections, unit-of-work instances, and message bus
    configuration with proper dependency wiring.
    
    Attributes:
        database: Provider of the async database resource.
        uow: Factory provider creating `UnitOfWork` instances bound to the DB.
        bootstrap: Factory provider producing a configured `MessageBus`.
        
    Notes:
        Uses dependency-injector framework for declarative container configuration.
        All providers are configured for automatic wiring in IAM modules.
    """
    wiring_config = containers.WiringConfiguration(modules=[__name__])

    database = providers.Object(fastapi_db)
    uow_factory = providers.Factory(
        UnitOfWork, session_factory=database.provided.async_session_factory
    )
    bootstrap = providers.Factory(
        bootstrap,
        uow_factory=uow_factory.provider,
    )
    bus_factory = bootstrap
