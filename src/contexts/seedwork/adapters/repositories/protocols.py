from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

from src.contexts.seedwork.adapters.repositories.filter_mapper import (
    FilterColumnMapper,
)
from src.contexts.seedwork.domain.entity import Entity
from src.db.base import SaBase

if TYPE_CHECKING:
    from src.contexts.seedwork.adapters.ORM.mappers.mapper import ModelMapper
    from src.contexts.seedwork.adapters.repositories.sa_generic_repository import (
        SaGenericRepository,
    )


class BaseRepository[E: Entity, S: SaBase](Protocol):
    """Protocol for asynchronous base repository operations.

    This protocol defines the contract that all repository implementations
    must follow. It provides a clean interface for data access operations
    while maintaining type safety through generic type parameters.

    Type Parameters:
        E: Domain entity type, must inherit from Entity
        S: SQLAlchemy model type, must inherit from SaBase

    Attributes:
        filter_to_column_mappers: List of filter to column mappers for
            dynamic query building
        data_mapper: Mapper for converting between domain and ORM models
        domain_model_type: The domain model type class
        sa_model_type: The SQLAlchemy model type class

    Example:
        ```python
        from sqlalchemy import Column, Integer, String
        from sqlalchemy.ext.declarative import declarative_base

        Base = declarative_base()

        class User(Base):
            __tablename__ = 'users'
            id = Column(Integer, primary_key=True)
            name = Column(String)
            fullname = Column(String)
            nickname = Column(String)

        class UserRepository(BaseRepository[User, User]):
            filter_to_column_mappers = [
                FilterColumnMapper(sa_model_type=User, mapping={'name': 'name'})
            ]
            data_mapper = UserDataMapper()
            domain_model_type = UserDomainModel
            sa_model_type = User
        ```
    """

    filter_to_column_mappers: list[FilterColumnMapper] | None = None
    data_mapper: ModelMapper
    domain_model_type: type[E]
    sa_model_type: type[S]

    async def add(self, entity: E):
        """Add an entity to the repository.

        Args:
            entity: The domain entity to add
        """
        ...

    async def get(self, id: str, *, _return_sa_instance: bool = False) -> E:
        """Get an entity by its ID.

        Args:
            id: The unique identifier of the entity
            _return_sa_model: Flag indicating whether to return the
                SQLAlchemy model instance instead of domain entity

        Returns:
            The domain entity or SQLAlchemy model instance
        """
        ...

    async def get_sa_instance(self, id: str) -> S:
        """Get a SQLAlchemy model instance by ID.

        Args:
            id: The unique identifier of the entity

        Returns:
            The SQLAlchemy model instance
        """
        ...

    async def query(
        self, *, filters: dict[str, Any], _return_sa_instance: bool, **kwargs
    ) -> list[E]:
        """Query entities based on filter criteria.

        Args:
            filters: Dictionary of filter criteria
            _return_sa_instance: Flag indicating whether to return
                SQLAlchemy model instances instead of domain entities
            **kwargs: Additional query parameters

        Returns:
            List of domain entities or SQLAlchemy model instances
        """
        ...

    async def persist(self, domain_obj: E) -> None:
        """Persist a domain object to the repository.

        Args:
            domain_obj: The domain object to persist
        """
        ...

    async def persist_all(self, domain_entities: list[E] | None = None) -> None:
        """Persist all domain entities in the repository.

        Args:
            domain_entities: Optional list of entities to persist.
                If None, persists all entities in the repository.
        """
        ...


class CompositeRepository[E: Entity, S: SaBase](BaseRepository[E, S], Protocol):
    """Protocol for composite repository implementations.

    This protocol extends BaseRepository to provide additional functionality
    for complex repository operations. It includes filter mapping, sorting,
    and delegation to a generic repository implementation.

    Type Parameters:
        E: Domain entity type, must inherit from Entity
        S: SQLAlchemy model type, must inherit from SaBase

    Attributes:
        filter_to_column_mappers: List of filter to column mappers for
            dynamic query building
        sort_to_column_mapping: Dictionary mapping sort keys to column names
        _generic_repo: The underlying generic repository implementation
    """

    filter_to_column_mappers: list[FilterColumnMapper] | None = None

    # Forward reference using TYPE_CHECKING to avoid circular import
    _generic_repo: SaGenericRepository[E, S]
