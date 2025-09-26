"""Dependency Injection container for recipes_catalog core services."""
from dependency_injector import containers, providers
from src.contexts.recipes_catalog.core.services.uow import UnitOfWork
from src.db.database import async_db

from .bootstrap import bootstrap


class Container(containers.DeclarativeContainer):
    """Dependency injection container for recipes_catalog domain services.

    Attributes:
        database: Database connection provider.
        uow: Unit of work factory with database session.
        bootstrap: Message bus bootstrap factory.

    Notes:
        Provides wiring configuration for dependency injection.
        All services receive properly configured dependencies.
    """

    wiring_config = containers.WiringConfiguration(modules=[__name__])

    database = providers.Object(async_db)
    uow = providers.Factory(
        UnitOfWork,
        session_factory=database.provided.async_session_factory,
    )
    bootstrap = providers.Factory(
        bootstrap,
        uow=uow.provider,
    )
