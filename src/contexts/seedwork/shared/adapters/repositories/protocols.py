from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

from src.contexts.seedwork.shared.adapters.repositories.filter_mapper import (
    E,
    FilterColumnMapper,
    S,
)

if TYPE_CHECKING:
    from src.contexts.seedwork.shared.adapters.ORM.mappers.mapper import ModelMapper
    from src.contexts.seedwork.shared.adapters.repositories.sa_generic_repository import (  # noqa: E501
        SaGenericRepository,
    )


class BaseRepository(Protocol[E, S]):
    """
    A protocol for an asynchronous base repository.

    :ivar filter_to_column_mappers: A list of filter to column mappers.
    :vartype filter_to_column_mappers: list[FilterColumnMapper] | None
    :ivar data_mapper: A data mapper.
    :vartype data_mapper: Mapper
    :ivar domain_model_type: The domain model type.
    :vartype domain_model_type: E
    :ivar sa_model_type: The SQLAlchemy model type.
    :vartype sa_model_type: S

    Example::

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

    In the above example, the `UserRepository` class is an implementation of
    the `BaseRepository` protocol for the `User` SQLAlchemy model. The
    `filter_to_column_mappers` attribute is used to map filter keys to
    SQLAlchemy model columns and specify join operations in case the filter
    key is associated with a relationship. The `data_mapper` attribute is
    used to map data between the domain model and the SQLAlchemy model. The
    `domain_model_type` and `sa_model_type` attributes specify the types of
    the domain model and the SQLAlchemy model, respectively.
    """

    filter_to_column_mappers: list[FilterColumnMapper] | None = None
    data_mapper: ModelMapper
    domain_model_type: type[E]
    sa_model_type: type[S]

    async def add(self, entity: E):
        """
        An asynchronous method to add an entity.

        Parameters:
        entity (E): The entity to add.
        """
        ...

    async def get(self, entity_id: str, *, _return_sa_instance: bool = False) -> E:
        """
        An asynchronous method to get an entity by id.

        Parameters:
        id (str): The id of the entity.
        _return_sa_model (bool): A flag indicating whether to return the
          SQLAlchemy model.

        Returns:
        E: The entity.
        """
        ...

    async def get_sa_instance(self, entity_id: str) -> S:
        """
        An asynchronous method to get a SQLAlchemy model by id.

        Parameters:
        id (str): The id of the SQLAlchemy model.

        Returns:
        S: The SQLAlchemy model.
        """
        ...

    async def query(
        self, *, filters: dict[str, Any], _return_sa_instance: bool, **kwargs
    ) -> list[E]:
        """
        An asynchronous method to list entities based on a filter.

        Parameters:
        filter (dict[str, Any]): The filter.

        Returns:
        list[E]: A list of entities.
        """
        ...

    async def persist(self, domain_obj: E) -> None:
        """
        An asynchronous method to persist a domain object.

        Parameters:
        domain_obj (E): The domain object to persist.
        """
        ...

    async def persist_all(self, domain_entities: list[E] | None = None) -> None:
        """
        An asynchronous method to persist all domain objects.
        """
        ...


class CompositeRepository(BaseRepository[E, S], Protocol):
    """
    This class is a protocol for an asynchronous composite repository.

    Attributes:
    filter_to_column_mappers (list[FilterColumnMapper] | None): A list
      of filter to column mappers.
    sort_to_column_mapping (dict[str, str] | None): A dictionary mapping
      sort keys to columns.
    _generic_repository (SaGenericRepository[E, S]): The generic repository.
    """

    filter_to_column_mappers: list[FilterColumnMapper] | None = None

    # Forward reference using TYPE_CHECKING to avoid circular import
    _generic_repo: SaGenericRepository[E, S]
