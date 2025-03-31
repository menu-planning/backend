from __future__ import annotations

from ast import Tuple
from collections.abc import Callable
from typing import Annotated, Any, Protocol, TypeVar

import anyio
from attrs import define, field
from sqlalchemy import Select, inspect, nulls_last, select
from sqlalchemy.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import MappedColumn
from sqlalchemy.sql.expression import ColumnOperators
from sqlalchemy.sql.functions import coalesce

from src.contexts.seedwork.shared.adapters.exceptions import (
    EntityNotFoundException, MultipleEntitiesFoundException)
from src.contexts.seedwork.shared.adapters.mapper import ModelMapper
from src.contexts.seedwork.shared.domain.entitie import Entity
from src.contexts.seedwork.shared.endpoints.exceptions import \
    BadRequestException
from src.db.base import SaBase
from src.logging.logger import logger

E = TypeVar("E", bound=Entity)  # , covariant=True)
S = TypeVar("S", bound=SaBase)  # , covariant=True)


@define
class FilterColumnMapper:
    """
    A class used to map filter keys to SQLAlchemy model columns
    and specify join operations in case the filter key is
    associated with a relationship.

    :ivar sa_model_type: The SQLAlchemy model type.
    :vartype sa_model_type: type[SaBase]
    :ivar mapping: A dictionary mapping filter keys to SQLAlchemy
                   model columns.
    :vartype mapping: Annotated[dict[str, str], "map filter key to
                      sa model column"]
    :ivar join_target_and_on_clause: A list of tuples, where each
                                     tuple contains a target and an
                                     'on' clause for a join operation.
    :vartype join_target_and_on_clause: list[Tuple]

    Example::

        from sqlalchemy import Column, Integer, String
        from sqlalchemy.ext.declarative import declarative_base

        Base = declarative_base()

        class Product(Base):
            __tablename__ = "products"

            id: Mapped[sa_field.strpk]
            diet_types: Mapped[list[DietType]] = relationship(
                secondary=products_diet_types_association, lazy="selectin"
            )

        class DietType(Base):
            __tablename__ = "diet_types"
            type: Mapped[sa_field.strpk]

        products_diet_types_association = Table(
            "products_diet_types_association",
            Base.metadata,
            Column("product_id", ForeignKey("products.id"), primary_key=True),
            Column(
                "diet_type_id", ForeignKey("diet_types.id"), primary_key=True
            ),
        )

        mapper = FilterColumnMapper()
        mapper.sa_model_type = DietType
        mapper.mapping = {'diet_types': 'type'}
        mapper.join_target_and_on_clause=[(DietType, Product.diet_types)],

    In the above example, the `mapper` can be used in the ProductRepo
    to map the `diet_types` filter key to the `type` column of the
    `DietType` model. The `join_target_and_on_clause` attribute is used
    to specify the join operation that should be performed when filtering
    by `diet_types`. In this case, the join operation is between the
    `DietType` model and the `Product.diet_types` relationship.
    """

    sa_model_type: type[SaBase]
    filter_key_to_column_name: Annotated[
        dict[str, str], "map filter key to sa model column"
    ]
    join_target_and_on_clause: list[Tuple] = field(factory=list)


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
    domain_model_type: E
    sa_model_type: S

    async def add(self, entity: E):
        """
        An asynchronous method to add an entity.

        Parameters:
        entity (E): The entity to add.
        """
        ...

    async def get(self, id: str, _return_sa_instance: bool) -> E:
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

    async def get_sa_instance(self, id: str) -> S:
        """
        An asynchronous method to get a SQLAlchemy model by id.

        Parameters:
        id (str): The id of the SQLAlchemy model.

        Returns:
        S: The SQLAlchemy model.
        """
        ...

    async def query(
        self, filter: dict[str, Any], _return_sa_instance: bool, **kwargs
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

    async def persist_all(self) -> None:
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
    _generic_repository (AsyncCompositeRepository[E, S]): The generic repository.
    """

    filter_to_column_mappers: list[FilterColumnMapper] | None = None
    sort_to_column_mapping: dict[str, str] | None = None
    _generic_repository: CompositeRepository[E, S]


@define
class Filter:
    """
    This class is used to define a filter for querying data.

    Attributes:
    columns (dict[str, str] | None): A dictionary mapping column names to
      their values. Default is None.
    skip (int | None): The number of records to skip. Default is None.
    limit (int | None): The maximum number of records to return. Default
      is None.
    sort (str | None): The column name to sort by. Default is None.
    others (dict[str, str] | None): A dictionary of other parameters.
      Default is None.
    """

    columns: dict[str, str] | None = None
    skip: int | None = None
    limit: int | None = None
    sort: str | None = None
    others: dict[str, str] | None = None


class SaGenericRepository:
    """
    This class is a generic repository for handling asynchronous database
    operations using SQLAlchemy. It provides a layer of abstraction over
    the SQLAlchemy ORM, allowing for easier and more maintainable data access.
    It should be used as the :attr:`_generic_repo` attribute of a composite
    repository implementing :class:`AsyncCompositeRepository`.

    :ivar db_session: An instance of AsyncSession from SQLAlchemy.
    :vartype db_session: AsyncSession
    :ivar data_mapper: A mapper object to convert between SQLAlchemy model
                       instances and domain model instances.
    :vartype data_mapper: Mapper
    :ivar domain_model_type: The type of the domain model.
    :vartype domain_model_type: E
    :ivar sa_model_type: The type of the SQLAlchemy model.
    :vartype sa_model_type: S
    :ivar filter_to_column_mappers: A list of FilterColumnMapper objects.
    :vartype filter_to_column_mappers: list[FilterColumnMapper] | None

    Example::

        from sqlalchemy import Column, Integer, String
        from sqlalchemy.ext.declarative import declarative_base
        from sqlalchemy.ext.asyncio import AsyncSession

        Base = declarative_base()

        class User(Base):
            __tablename__ = 'users'

            id = Column(Integer, primary_key=True)
            name = Column(String)
            fullname = Column(String)
            nickname = Column(String)

        class UserRepository(SaGenericRepository):
            db_session = AsyncSession(engine)
            data_mapper = UserDataMapper()
            domain_model_type = UserDomainModel
            sa_model_type = User
            filter_to_column_mappers = [
                FilterColumnMapper(sa_model_type=User, mapping={'name': 'name'})
            ]

        # Now you can use `UserRepository` as a generic repository for the
        `User` model.

    The class also maintains a set of 'seen' domain objects. This is used to
      keep track of which objects have been read from or written to the
      database in the current session, to help manage the session lifecycle
      and ensure data consistency.

    The ALLOWED_POSTFIX list defines postfixes that can be used in filter
      criteria to specify comparison operators, such as greater than or
      equal to (_gte), less than or equal to (_lte), not equal to (_ne),
      not in (_not_in), and is not (_is_not).
    """

    ALLOWED_POSTFIX = ["_gte", "_lte", "_ne", "_not_in", "_is_not", "_not_exists"]
    ALLOWED_FILTERS = [
        "skip",
        "limit",
        "sort",
        "created_at",
    ]

    def __init__(
        self,
        db_session: AsyncSession,
        data_mapper: type[ModelMapper],
        domain_model_type: E,
        sa_model_type: S,
        filter_to_column_mappers: list[FilterColumnMapper] | None = None,
    ):
        self._session = db_session
        self.inspector = inspect(sa_model_type)
        self.filter_to_column_mappers = filter_to_column_mappers or []
        self.data_mapper = data_mapper
        self.domain_model_type = domain_model_type
        self.sa_model_type = sa_model_type
        self.seen: set[E] = set()

    def refresh_seen(self, entity: E) -> None:
        """
        Ensure the latest version of an entity is tracked in `self.seen`.

        - If an entity with the same identity exists (determined by `==`), replace it.
        - Otherwise, add the entity.

        :param entity: The domain entity to track.
        """
        self.seen.discard(entity)
        self.seen.add(entity)


    async def add(
        self,
        domain_obj: E,
    ):
        self._session.autoflush = False
        try:
            # sa_instance = await self._merged_sa_instance(
            #     domain_obj, names_of_attr_to_populate
            # )
            sa_instance = await self.data_mapper.map_domain_to_sa(
                self._session, domain_obj
            )
            self._session.add(sa_instance)
        finally:
            self._session.autoflush = True
            await self._session.flush()
        self.refresh_seen(domain_obj)

    # async def _merge_children(
    #     self,
    #     sa_instance: S,
    # ) -> S:
    #     """
    #     Use this method to merge attributes of an SQLAlchemy instance
    #     with the database. If the instance has a relationship with
    #     another model, this method will try to merge it with an existing
    #     object first. Otherwise, trying to flush a new instance may
    #     result in an IntegrityError if the ralationship object already exists
    #     in the database with the same primary key. For this to work.

    #     """
    #     sa_mapper = inspect(self.sa_model_type)

    #     for attribute in sa_mapper.relationships.keys():
    #         # print(attribute)
    #         attribute_value = getattr(sa_instance, attribute)
    #         if isinstance(attribute_value, list):
    #             merged_list = []
    #             for i in attribute_value:
    #                 try:
    #                     merged_i = await self._session.merge(i)
    #                     merged_list.append(merged_i)
    #                 except Exception as e:
    #                     logger.error(f"Error merging {attribute}: {e}")
    #                     merged_list.append(i)
    #             setattr(sa_instance, attribute, merged_list)
    #         elif isinstance(attribute_value, set):
    #             merged_set = set()
    #             for i in attribute_value:
    #                 try:
    #                     merged_i = await self._session.merge(i)
    #                     merged_set.add(merged_i)
    #                 except Exception as e:
    #                     logger.error(f"Error merging {attribute}: {e}")
    #                     merged_set.add(i)
    #             setattr(sa_instance, attribute, merged_set)
    #         elif isinstance(attribute_value, dict):
    #             merged_dict = {}
    #             for k, v in attribute_value.items():
    #                 try:
    #                     merged_dict[k] = await self._session.merge(v)
    #                 except Exception as e:
    #                     logger.error(f"Error merging {attribute}: {e}")
    #                     merged_dict[k] = v
    #             setattr(sa_instance, attribute, merged_dict)
    #         elif isinstance(attribute_value, SaBase):
    #             try:
    #                 setattr(
    #                     sa_instance,
    #                     attribute,
    #                     await self._session.merge(attribute_value),
    #                 )
    #             except Exception as e:
    #                 logger.error(f"Error merging {attribute}: {e}")
    #     return sa_instance

    # async def _log_table_existance(self, sa_instance: S, sa_attr_name: str):
    #     try:
    #         relationship_type = utils.get_type_of_related_model(
    #             sa_instance, sa_attr_name
    #         )
    #         table_ars = relationship_type.__table_args__
    #         if isinstance(table_ars, Mapping):
    #             schema = table_ars.get("schema")
    #         else:
    #             try:
    #                 for i in table_ars:
    #                     if isinstance(i, Mapping):
    #                         schema = i.get("schema")
    #                         break
    #             except Exception as e:
    #                 schema = None
    #         table_exists = await utils.check_table_exists(
    #             self._session, relationship_type.__tablename__, schema=schema
    #         )
    #         if not table_exists:
    #             logger.error(f"Table {relationship_type.__tablename__} not found")
    #     except Exception as e:
    #         logger.error(f"Error getting related model: {e}")

    # async def _populate_relationships_ref_directly(
    #     self,
    #     domain_obj: E,
    #     sa_instance: S,
    #     names_of_attr_to_populate: set[str] | None = None,
    # ) -> S:
    #     """
    #     This method populates the relationships of an SQLAlchemy instance
    #     with the related items from the database. It is used to ensure
    #     that the relationships are properly populated when the domain model
    #     references the object directly (not by id) and these children may have
    #     children of their own, but this time referenced by id.

    #     When the domain model references the object directly and these children
    #     have relationships that are referenced by id,

    #     """
    #     if not names_of_attr_to_populate:
    #         logger.info(
    #             f"All relationships from {type(sa_instance)} being populated directly from the domain model."
    #         )
    #         return sa_instance
    #     sa_instance_inspector = inspect(sa_instance.__class__)
    #     relationships = sa_instance_inspector.relationships
    #     relationships = set(relationships.keys())
    #     names_of_attr_to_populate = set(names_of_attr_to_populate)
    #     sa_relationships_not_being_populated_here = (
    #         relationships - names_of_attr_to_populate
    #     )
    #     attrs_to_populate_not_found = names_of_attr_to_populate - relationships
    #     actual_attrs_to_populate = names_of_attr_to_populate.intersection(relationships)
    #     if attrs_to_populate_not_found:
    #         raise BadRequestException(
    #             f"Relationships {attrs_to_populate_not_found} not found on {type(sa_instance)}"
    #         )
    #     logger.info(
    #         f"Relationships {sa_relationships_not_being_populated_here} being populated directly from the domain model."
    #     )
    #     for name in actual_attrs_to_populate:
    #         if not getattr(domain_obj, name, None):
    #             raise BadRequestException(
    #                 f"Repo unable to populate relationship {name} sinci it does not exists on domain model."
    #             )
    #     for name in actual_attrs_to_populate:
    #         sa_value = getattr(sa_instance, name)
    #         domain_value = getattr(domain_obj, name)
    #         if not domain_value:
    #             continue
    #         if isinstance(domain_value, (list, set)):
    #             new_values = []
    #             for d in domain_value:
    #                 for s in sa_value:
    #                     if utils.get_entity_id(d) and utils.get_entity_id(
    #                         d
    #                     ) == utils.get_entity_id(s):
    #                         v = await self._populate_relationships_ref_by_id(d, s)
    #                         new_values.append(v)
    #                         break
    #             setattr(sa_instance, name, new_values)
    #         else:
    #             if utils.get_entity_id(domain_value) and utils.get_entity_id(
    #                 domain_value
    #             ) == utils.get_entity_id(sa_value):
    #                 v = await self._populate_relationships_ref_by_id(
    #                     domain_value, sa_value
    #                 )
    #                 setattr(sa_instance, name, v)
    #     return sa_instance

    # async def _populate_relationships_ref_by_id(
    #     self,
    #     domain_obj: E,
    #     sa_instance: S,
    # ) -> S:
    #     """
    #     This method populates the relationships of an SQLAlchemy instance
    #     with the related items from the database. It is used to ensure
    #     that the relationships are properly populated when the SQLAchemy
    #     model has a relationshiop with another model, but the domain model
    #     references only by id (does not reference the object directly).

    #     For this to work the domain model must have attributes that end with
    #     '_id' or '_ids' and the SQLAlchemy model must have a relationship
    #     with the same name as the attribute without the '_id' or '_ids' suffix.

    #     Example:
    #     domain model:
    #     class User:
    #         id: str
    #         name: str
    #         role_id: str

    #     SQLAlchemy model:
    #     class UserSaModel:
    #         __tablename__ = 'users'
    #         id: str
    #         name: str
    #         role_id: str
    #         role: Role

    #     In this case the UserSaModel has a relationship with the Role model
    #     called 'role'. The User domain model has a 'role_id' attribute that
    #     references the id of the Role model. This method will populate the
    #     'role' attribute of the UserSaModel with the Role object from the
    #     database.
    #     """
    #     sa_attr_name_to_domain_attr_name = utils.map_sa_attr_name_to_domain_attr_name(
    #         sa_instance=sa_instance,
    #         domain_obj=domain_obj,
    #         postfix_on_domain_attribute=["_id", "_ids"],
    #     )
    #     for (
    #         sa_attr_name,
    #         domain_attr_name,
    #     ) in sa_attr_name_to_domain_attr_name.items():
    #         sa_value = getattr(sa_instance, sa_attr_name)
    #         domain_value = getattr(domain_obj, domain_attr_name)
    #         relationship_type = utils.get_type_of_related_model(
    #             sa_instance, sa_attr_name
    #         )
    #         if domain_value and sa_value in (None, [], set()):
    #             await self._log_table_existance(sa_instance, sa_attr_name)
    #             # Query and set the related items
    #             if isinstance(domain_value, (list, set)):
    #                 try:
    #                     related_objs = await self._session.execute(
    #                         select(relationship_type).where(
    #                             relationship_type.id.in_(domain_value)
    #                         )
    #                     )
    #                     setattr(
    #                         sa_instance,
    #                         sa_attr_name,
    #                         related_objs.scalars().all(),
    #                     )
    #                 except Exception as e:
    #                     logger.error(f"Error populating {sa_attr_name}: {e}")
    #             elif isinstance(domain_value, str):
    #                 try:
    #                     related_obj = await self._session.get(
    #                         relationship_type, domain_value
    #                     )
    #                     setattr(sa_instance, sa_attr_name, related_obj)
    #                 except Exception as e:
    #                     logger.error(f"Error getting related model: {e}")
    #     return sa_instance

    # async def _merged_sa_instance(
    #     self,
    #     domain_obj: E,
    #     names_of_attr_to_populate: set[str] | None = None,
    # ) -> S:
    #     sa_instance = self.data_mapper.map_domain_to_sa(domain_obj)
    #     # print(f"1 {sa_instance}")
    #     sa_instance = await self._populate_relationships_ref_by_id(
    #         domain_obj, sa_instance
    #     )
    #     # print(f"2 {sa_instance}")
    #     sa_instance = await self._populate_relationships_ref_directly(
    #         domain_obj, sa_instance, names_of_attr_to_populate
    #     )
    #     # print(f"3 {sa_instance}")
    #     merged = await self._merge_children(sa_instance)
    #     # print(f"4 {merged}")
    #     print("New instances pending insertion:")
    #     for instance in self._session.new:
    #         print(instance)

    #     print("Dirty instances pending update:")
    #     for instance in self._session.dirty:
    #         print(instance)

    #     print("Deleted instances pending deletion:")
    #     for instance in self._session.deleted:
    #         print(instance)
    #     return merged

    async def get(self, id: str, _return_sa_instance: bool = False) -> E:
        table_columns = inspect(self.sa_model_type).c.keys()
        if "discarded" in table_columns:
            stmt = select(self.sa_model_type).filter_by(id=id, discarded=False)
        else:
            stmt = select(self.sa_model_type).filter_by(id=id)
        try:
            query = await self._session.execute(stmt)
            result: S = query.scalar_one()
        except NoResultFound as e:
            raise EntityNotFoundException(entity_id=id, repository=self) from e
        except MultipleResultsFound as e:
            raise MultipleEntitiesFoundException(entity_id=id, repository=self) from e
        else:
            if _return_sa_instance:
                return result
            else:
                domain_instance = self.data_mapper.map_sa_to_domain(result)
                self.refresh_seen(domain_instance)
                return domain_instance

    async def get_sa_instance(self, id: str) -> S:
        obj = await self.get(id, _return_sa_instance=True)
        return obj

    @staticmethod
    def remove_desc_prefix(word: str | None) -> str | None:
        if word.startswith("-"):
            return word[1:]
        return word

    @staticmethod
    def remove_postfix(word: str) -> str:
        for postfix in SaGenericRepository.ALLOWED_POSTFIX:
            if word.endswith(postfix):
                return word.replace(postfix, "")
        return word

    def select_filters_for_sa_model_type(
        self, filter: dict[str, Any], sa_model_type: type[SaBase]
    ) -> dict[str, Any]:
        """
        Get the filter for a specific SQLAlchemy model type.

        This method iterates over the `filter_to_column_mappers` attribute and
        checks if the SQLAlchemy model type of the mapper matches the provided
        `sa_model_type`. If a match is found, it checks if the keys in the
        provided `filter` are in the mapper's mapping. If they are, it adds
        them to the result.

        :param filter: A dictionary containing filter keys and values.
        :type filter: dict[str, Any]
        :param sa_model_type: The SQLAlchemy model type to get the filter for.
        :type sa_model_type: type[SaBase]
        :return: A dictionary containing the filter for the provided SQLAlchemy
                 model type.
        :rtype: dict[str, Any]

        Example::

            # Assume we have a User SQLAlchemy model with 'name', 'age', and
            # 'email' fields and a UserRepository that has a FilterColumnMapper
            # for the User model with a mapping {'name': 'name', 'age': 'age',
            # 'email_address': 'email'}.

            filter = {'name': 'John', 'age': 30,
                     'email_address': 'john@example.com',
                     'phone': '1234567890'}
            sa_model_type = User
            result = repository.get_filter_for_sa_model_type(filter,
                                                            sa_model_type)

            # The result will be {'name': 'John', 'age': 30,
                                'email_address': 'john@example.com'}
            # because 'name', 'age', and 'email_address' are both keys in the
            # filter and are in the FilterColumnMapper's mapping for the User
            # model. 'phone' is not in the FilterColumnMapper's
            # mapping, so it is not included in the result.

        In the above example, the `get_filter_for_sa_model_type` method is used
        to get the filter for the `User` SQLAlchemy model type. The `filter`
        dictionary contains the filter keys and values. The method returns a
        dictionary containing the filter for the `User` SQLAlchemy model type.
        """
        result = {}
        for mapper in self.filter_to_column_mappers:
            if mapper.sa_model_type is sa_model_type:
                for k in filter.keys():
                    if self.remove_postfix(k) in mapper.filter_key_to_column_name:
                        result[k] = filter[k]
                break
        return result

    def get_filter_to_column_mapper_for_sa_model_type(
        self, sa_model_type: type[SaBase]
    ) -> FilterColumnMapper | None:
        for mapper in self.filter_to_column_mappers:
            if mapper.sa_model_type is sa_model_type:
                return mapper
        return None

    async def query(
        self,
        *,
        filter: dict[str, Any] | None = None,
        starting_stmt: Select | None = None,
        sort_stmt: Callable | None = None,
        limit: int | None = None,
        already_joined: set[str] | None = None,
        sa_model: type[SaBase] | None = None,
        _return_sa_instance: bool = False,
    ) -> list[E]:
        """
        Retrieve a list of domain objects from the database based on the provided filter criteria.
        """
        already_joined = already_joined or set()
        stmt = self._build_base_statement(starting_stmt, limit)
        
        if filter:
            self._validate_filters(filter)
            stmt = self._apply_filters(stmt, filter, already_joined)
            stmt = self._apply_sorting(stmt, filter, sort_stmt, sa_model)
        # else:
        #     stmt = self.setup_skip_and_limit(stmt, {}, limit)
        
        try:
            result = await self.execute_stmt(stmt, _return_sa_instance=_return_sa_instance)
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
        return result

    def _build_base_statement(self, starting_stmt: Select | None, limit: int | None) -> Select:
        """
        Create the initial SELECT statement from the repository's model and applies the default filter.
        """
        stmt = starting_stmt if starting_stmt is not None else select(self.sa_model_type)
        # If the model has a "discarded" column, filter out discarded rows.
        if "discarded" in inspect(self.sa_model_type).c.keys():
            stmt = stmt.filter_by(discarded=False)
        stmt = self.setup_skip_and_limit(stmt, {}, limit)
        return stmt

    def _validate_filters(self, filter: dict[str, Any]) -> None:
        """
        Validates the filter keys against allowed filters and column mappers.
        """
        allowed_filters = self.ALLOWED_FILTERS.copy()
        for mapper in self.filter_to_column_mappers:
            allowed_filters.extend(mapper.filter_key_to_column_name.keys())
        for k in filter.keys():
            if self.remove_postfix(k) not in allowed_filters:
                raise BadRequestException(f"Filter not allowed: {k}")

    def _apply_filters(self, stmt: Select, filter: dict[str, Any], already_joined: set[str]) -> Select:
        """
        Applies filtering criteria by iterating through the column mappers, joining tables as needed,
        and using filter_stmt to add WHERE conditions.
        """
        for mapper in self.filter_to_column_mappers:
            sa_model_type_filter = self.select_filters_for_sa_model_type(
                filter=filter, sa_model_type=mapper.sa_model_type
            )
            if sa_model_type_filter:
                for join_target, on_clause in mapper.join_target_and_on_clause:
                    if str(join_target) not in already_joined:
                        stmt = stmt.join(join_target, on_clause)
                        already_joined.add(str(join_target))
            stmt = self.filter_stmt(
                stmt=stmt,
                filter=sa_model_type_filter,
                sa_model_type=mapper.sa_model_type,
                mapping=mapper.filter_key_to_column_name,
            )
        # Optionally, process sort filters that involve other model types.
        if "sort" in filter:
            sort_model = self.get_sa_model_type_by_filter_key(self.remove_desc_prefix(filter["sort"]))
            if sort_model and sort_model != self.sa_model_type and str(sort_model) not in already_joined:
                mapper = self.get_filter_to_column_mapper_for_sa_model_type(sort_model)
                for join_target, on_clause in mapper.join_target_and_on_clause:
                    if str(join_target) not in already_joined:
                        stmt = stmt.join(join_target, on_clause)
                        already_joined.add(str(join_target))
                stmt = self.filter_stmt(
                    stmt=stmt,
                    filter=sa_model_type_filter,
                    sa_model_type=mapper.sa_model_type,
                    mapping=mapper.filter_key_to_column_name,
                )
        logger.debug(f"Stmt after apply repo filter: {stmt}")
        return stmt

    def _apply_sorting(self, stmt: Select, filter: dict[str, Any], sort_stmt: Callable | None, sa_model: type[SaBase] | None = None,) -> Select:
        """
        Applies sorting to the statement using either the provided sort_stmt callback or
        the internal sort_stmt method.
        """
        sort_value = filter.get("sort", None)
        if sort_stmt:
            return sort_stmt(stmt=stmt, value_of_sort_query=sort_value)
        else:
            return self.sort_stmt(stmt=stmt, value_of_sort_query=sort_value, sa_model=sa_model)


    # async def query(
    #     self,
    #     *,
    #     filter: dict[str, Any] | None = None,
    #     starting_stmt: Select | None = None,
    #     sort_stmt: Callable | None = None,
    #     limit: int | None = None,
    #     already_joined: set[str] | None = None,
    #     _return_sa_instance: bool = False,
    # ) -> list[E]:
    #     """
    #     Retrieve a list of domain objects from the database based on the
    #     provided filter criteria.

    #     :param filter: A dictionary containing filter criteria for the query.
    #                    The keys should correspond to the attributes of
    #                    the domain model, and the values should specify the
    #                    desired values for those attributes. The filter can
    #                    also include special keys for pagination and sorting,
    #                    such as 'skip', 'limit', and 'sort'.
    #     :type filter: dict[str, Any] | None
    #     :param starting_stmt: An optional SQLAlchemy Select statement to start
    #                           with. If provided, the method will add the filter
    #                           criteria to this statement. If not provided, the
    #                           method will create a new Select statement based
    #                           on the SQLAlchemy model type of the repository.
    #     :type starting_stmt: Select | None
    #     :param limit: An optional limit on the number of results to return. If
    #                   not provided, a default limit is used.
    #     :type limit: int | None
    #     :param _return_sa_instance: A flag indicating whether to return the
    #                                   SQLAlchemy model instances. Default is False.
    #     :type _return_sa_instance: bool
    #     :return: A list of domain objects that match the filter criteria.
    #     :rtype: list[E]

    #     The method constructs a SQLAlchemy Select statement based on the
    #     provided filter criteria and executes it against the database.

    #     The method also handles pagination and sorting based on the 'skip',
    #     'limit', and 'sort' keys in the filter. Pagination is implemented
    #     using the offset and limit methods of the Select statement, and
    #     sorting is implemented using the order_by method of the Select
    #     statement.

    #     The method raises a BadRequestException if the filter includes keys
    #     that are not allowed. The allowed keys are defined in the
    #     'allowed_filters' list and the mapper.mapping.keys*.
    #     """
    #     if already_joined is None:
    #         already_joined = set()
    #     if starting_stmt is not None:
    #         stmt = starting_stmt
    #     else:
    #         stmt = select(self.sa_model_type)
    #     if "discarded" in inspect(self.sa_model_type).c.keys():
    #         stmt = stmt.filter_by(discarded=False)
    #     if not filter:
    #         stmt = self.setup_skip_and_limit(stmt, {}, limit)
    #     else:
    #         allowed_filters = self.ALLOWED_FILTERS.copy()
    #         # Extend the allowed filters with the keys from the filter to
    #         # column mappers.
    #         for mapper in self.filter_to_column_mappers:
    #             allowed_filters.extend(mapper.filter_key_to_column_name.keys())
    #         for k in filter.keys():
    #             if self.remove_postfix(k) not in allowed_filters:
    #                 raise BadRequestException(f"Filter not allowed: {k}")
    #         stmt = self.setup_skip_and_limit(stmt, filter, limit)
    #         # Build the query by joining tables and applying filters.
    #         for mapper in self.filter_to_column_mappers:
    #             sa_model_type_filter = self.select_filters_for_sa_model_type(
    #                 filter=filter, sa_model_type=mapper.sa_model_type
    #             )
    #             if sa_model_type_filter:
    #                 for i in mapper.join_target_and_on_clause:
    #                     join_target, on_clause = i
    #                     if str(join_target) not in already_joined:
    #                         stmt = stmt.join(join_target, on_clause)
    #                         already_joined.add(str(join_target))
    #             stmt = self.filter_stmt(
    #                 stmt=stmt,
    #                 filter=sa_model_type_filter,
    #                 sa_model_type=mapper.sa_model_type,
    #                 mapping=mapper.filter_key_to_column_name,
    #             )
    #         else:
    #             # Add sort to the query.
    #             sort_sa_model_type = ""
    #             if "sort" in filter:
    #                 sort_sa_model_type = self.get_sa_model_type_by_filter_key(
    #                     self.remove_desc_prefix(filter["sort"])
    #                 )
    #             if (
    #                 sort_sa_model_type
    #                 and sort_sa_model_type != self.sa_model_type
    #                 and str(sort_sa_model_type) not in already_joined
    #             ):
    #                 mapper = self.get_filter_to_column_mapper_for_sa_model_type(
    #                     sort_sa_model_type
    #                 )
    #                 for i in mapper.join_target_and_on_clause:
    #                     join_target, on_clause = i
    #                     if str(join_target) not in already_joined:
    #                         stmt = stmt.join(join_target, on_clause)
    #                         already_joined.add(str(join_target))
    #                 stmt = self.filter_stmt(
    #                     stmt=stmt,
    #                     filter=sa_model_type_filter,
    #                     sa_model_type=mapper.sa_model_type,
    #                     mapping=mapper.filter_key_to_column_name,
    #                 )
    #         if sort_stmt:
    #             stmt = sort_stmt(
    #                 stmt=stmt,
    #                 sort=filter.get("sort", None),
    #             )
    #         else:
    #             stmt = self.sort_stmt(
    #                 stmt=stmt,
    #                 value_of_sort_query=filter.get("sort", None),
    #             )
    #     try:
    #         result = await self.execute_stmt(
    #             stmt, _return_sa_instance=_return_sa_instance
    #         )
    #     except Exception as e:
    #         logger.error(f"Error executing query: {e}")
    #         raise
    #     return result

    def setup_skip_and_limit(
        self,
        stmt: Select,
        filter: dict[str, Any] | None,
        limit: int | None = 500,
    ) -> Select:
        skip = filter.get("skip", 0)
        limit = filter.get("limit", limit)
        if limit:
            stmt = stmt.offset(skip).limit(limit)
        else:
            stmt = stmt.offset(skip)
        return stmt

    def get_filter_key_to_column_name_for_sa_model_type(
        self, sa_model_type: type[SaBase]
    ) -> dict[str, Any] | None:
        for mapper in self.filter_to_column_mappers:
            if mapper.sa_model_type is sa_model_type:
                return mapper.filter_key_to_column_name
        return None

    def _filter_operator_selection(
        self,
        filter_name: str,
        filter_value: Any,
        sa_model_type: type[SaBase] | None = None,
    ) -> Callable[[MappedColumn, Any], ColumnOperators]:
        if not sa_model_type:
            sa_model_type = self.sa_model_type
            inspector = self.inspector
        else:
            inspector = inspect(sa_model_type)
        mapping = self.get_filter_key_to_column_name_for_sa_model_type(sa_model_type)
        column_name = mapping[self.remove_postfix(filter_name)]
        if "_gte" in filter_name:
            return ColumnOperators.__ge__
        if "_lte" in filter_name:
            return ColumnOperators.__le__
        if "_ne" in filter_name:
            return ColumnOperators.__ne__
        if "_not_in" in filter_name:
            return lambda c, v: ColumnOperators.__or__(
                ColumnOperators.__eq__(c, None),
                ColumnOperators.not_in(c, v),
            )
        if "_is_not" in filter_name:
            return ColumnOperators.is_not
        if inspector.columns[column_name].type.python_type == list:
            return ColumnOperators.contains
        if isinstance(filter_value, list):
            return ColumnOperators.in_
        if inspector.columns[column_name].type.python_type == str:
            return ColumnOperators.__eq__
        # try:
        #     iter(filter_value)
        #     return ColumnOperators.in_
        # except Exception:
        #     pass
        if inspector.columns[column_name].type.python_type == bool:
            return ColumnOperators.is_
        return ColumnOperators.__eq__

    def filter_stmt(
        self,
        stmt: Select,
        filter: dict[str, Any] | None = None,
        sa_model_type: type[SaBase] | None = None,
        mapping: dict[str, str] | None = None,
    ) -> Select:
        # TODO: check impact of removing 'distinct' from the query
        if not filter:
            return stmt
        apply_distinct = False
        for k, v in filter.items():
            stmt = stmt.where(
                self._filter_operator_selection(k, v, sa_model_type)(
                    getattr(
                        sa_model_type,
                        mapping[self.remove_postfix(k)],
                    ),
                    v,
                )
            )
            if isinstance(v, list):
                apply_distinct = True
        if apply_distinct:
            return stmt.distinct()
        return stmt

    def get_sa_model_type_by_filter_key(
        self, filter_key: str | None = None
    ) -> type[SaBase] | None:
        for mapper in self.filter_to_column_mappers:
            if filter_key in mapper.filter_key_to_column_name:
                return mapper.sa_model_type
        return None
    

    def sort_stmt(
        self,
        stmt: Select,
        value_of_sort_query: str | None = None,
        sa_model: type[SaBase] | None = None,
    ) -> Select:
        """
        Sort the query based on the provided sort criteria.
        
        If a `sa_model` is provided (for example, an alias), it will be used to
        determine the column to sort by; otherwise, self.sa_model_type is used.
        The sort criteria should be a string representing the column name.
        If the name is prefixed with a '-', the query is sorted in descending order.
        """
        if not value_of_sort_query:
            return stmt

        # Use the provided model (alias) if available.
        # sa_model_type_to_sort_by = sa_model or (
        #     self.get_sa_model_type_by_filter_key(self.remove_desc_prefix(value_of_sort_query))
        #     or self.sa_model_type
        # )
        sa_model_type_to_sort_by = (
            self.get_sa_model_type_by_filter_key(self.remove_desc_prefix(value_of_sort_query))
            or self.sa_model_type
        )
        inspector = inspect(sa_model_type_to_sort_by)
        mapping = self.get_filter_key_to_column_name_for_sa_model_type(sa_model_type_to_sort_by)
        clean_sort_name = (
            mapping.get(self.remove_desc_prefix(value_of_sort_query), None)
            or self.remove_desc_prefix(value_of_sort_query)
        )
        if clean_sort_name in inspector.columns.keys() and "source" not in value_of_sort_query:
            # sort_type = inspector.columns[clean_sort_name].type.python_type
            # alternative = None
            # if sort_type is str:
            #     alternative = ""
            # elif sort_type is float:
            #     alternative = 0.0
            # elif sort_type is int:
            #     alternative = 0
            column_attr = getattr(sa_model or sa_model_type_to_sort_by, clean_sort_name)
            if value_of_sort_query.startswith("-"):
                stmt = stmt.order_by(nulls_last(column_attr.desc()))
            else:
                stmt = stmt.order_by(nulls_last(column_attr))
            # if alternative is not None:
            #     coal = coalesce(column_attr, alternative)
            #     if value_of_sort_query.startswith("-"):
            #         stmt = stmt.order_by(nulls_last(coal.desc()))
            #     else:
            #         stmt = stmt.order_by(nulls_last(coal))
            # else:
            #     if value_of_sort_query.startswith("-"):
            #         stmt = stmt.order_by(nulls_last(column_attr.desc()))
            #     else:
            #         stmt = stmt.order_by(nulls_last(column_attr))
        return stmt


    async def execute_stmt(
        self, stmt: Select, _return_sa_instance: bool = False
    ) -> list[E]:
        sa_objs = await self._session.execute(stmt)
        sa_objs = sa_objs.scalars().all()
        if _return_sa_instance:
            return sa_objs
        result = []
        for obj in sa_objs:
            domain_obj = self.data_mapper.map_sa_to_domain(obj)
            self.refresh_seen(domain_obj)
            result.append(domain_obj)
        return result

    async def persist(
        self,
        domain_obj: E,
    ) -> None:
        assert (
            domain_obj in self.seen
        ), "Cannon persist entity which is unknown to the repo. Did you forget to call repo.add() for this entity?"
        self._session.autoflush = False
        try:
            # sa_instance = await self._merged_sa_instance(
            #     domain_obj, names_of_attr_to_populate
            # )
            if domain_obj.discarded:
                domain_obj._discarded = False
                sa_instance = await self.data_mapper.map_domain_to_sa(
                    self._session, domain_obj
                )
                sa_instance.discarded = True
            else:
                sa_instance = await self.data_mapper.map_domain_to_sa(
                    self._session, domain_obj
                )
            await self._session.merge(sa_instance)
        finally:
            self._session.autoflush = True
            await self._session.flush()
        # self.seen.discard(domain_obj)
        # self.seen.add(domain_obj)
        # sa_instance = await self._merged_sa_instance(domain_obj)
        # await self._session.merge(sa_instance)

    async def persist_all(
        self,
        # *,
        # names_of_attr_to_populate: set[str] | None = None,
    ) -> None:
        # coros = [self.persist(obj) for obj in self.seen]
        async with anyio.create_task_group() as tg:
            for obj in self.seen:
                tg.start_soon(self.persist, obj)
            # for task in coros:
            #     tg.start_soon(task)
