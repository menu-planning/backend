from __future__ import annotations

from collections.abc import Callable
from typing import Annotated, Any, Generic, Protocol, TypeVar

import anyio
from attrs import define, field
from sqlalchemy import ColumnElement, Select, inspect, nulls_last, select
from sqlalchemy.exc import MultipleResultsFound, NoResultFound
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import InstrumentedAttribute, MappedColumn
from sqlalchemy.sql import operators
from sqlalchemy.sql.expression import ColumnOperators
from sqlalchemy.sql.functions import coalesce
from src.contexts.seedwork.adapters.ORM.mappers.mapper import ModelMapper
from src.contexts.seedwork.adapters.repositories.filter_operators import (
    FilterOperatorFactory,
)
from src.contexts.seedwork.adapters.repositories.repository_exceptions import (
    EntityNotFoundError,
    FilterValidationError,
    MultipleEntitiesFoundError,
)
from src.contexts.seedwork.domain.entity import Entity
from src.db.base import SaBase, SerializerMixin
from src.logging.logger import structlog_logger

logger = structlog_logger("sa_generic_repository")

E = TypeVar("E", bound=Entity)  # , covariant=True)
S = TypeVar("S", bound=SaBase)  # , covariant=True)


@define
class FilterColumnMapper(Generic[E, S]):
    """
    A class used to map filter keys to SQLAlchemy model columns
    and specify join operations in case the filter key is
    associated with a relationship.

    :ivar sa_model_type: The SQLAlchemy model type.
    :vartype sa_model_type: Type[S]
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

    sa_model_type: type[S]
    filter_key_to_column_name: Annotated[
        dict[str, str], "map filter key to sa model column"
    ]
    join_target_and_on_clause: (
        list[tuple[type[SaBase], InstrumentedAttribute]] | None
    ) = field(factory=list)


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
        self, filters: dict[str, Any], _return_sa_instance: bool, **kwargs
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
    _generic_repository (AsyncCompositeRepository[E, S]): The generic repository.
    """

    filter_to_column_mappers: list[FilterColumnMapper] | None = None
    # sort_to_column_mapping: dict[str, str] | None = None
    _generic_repo: SaGenericRepository[E, S]


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


class SaGenericRepository(Generic[E, S]):
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
        domain_model_type: type[E],
        sa_model_type: type[S],
        filter_to_column_mappers: list[FilterColumnMapper] | None = None,
    ):
        self._session = db_session
        self.data_mapper = data_mapper
        self.domain_model_type = domain_model_type
        self.sa_model_type = sa_model_type
        self.filter_to_column_mappers = filter_to_column_mappers or []
        self.inspector = inspect(sa_model_type)
        self.seen: set[E] = set()
        # Initialize FilterOperatorFactory for new operator pattern
        self._filter_operator_factory = FilterOperatorFactory()

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
            sa_instance = await self.data_mapper.map_domain_to_sa(
                self._session, domain_obj
            )
            self._session.add(sa_instance)
        finally:
            self._session.autoflush = True
            await self._session.flush()
        self.refresh_seen(domain_obj)

    async def get(self, id: str, _return_sa_instance: bool = False) -> E | S:
        table_columns = inspect(self.sa_model_type).c.keys()  # type: ignore
        if "discarded" in table_columns:
            stmt = select(self.sa_model_type).filter_by(id=id, discarded=False)  # type: ignore
        else:
            stmt = select(self.sa_model_type).filter_by(id=id)  # type: ignore
        try:
            query = await self._session.execute(stmt)
            result: S = query.scalar_one()
        except NoResultFound as e:
            raise EntityNotFoundError(id=id, repository=self) from e
        except MultipleResultsFound as e:
            raise MultipleEntitiesFoundError(id=id, repository=self) from e
        else:
            if _return_sa_instance:
                return result
            else:
                domain_instance = self.data_mapper.map_sa_to_domain(result)
                self.refresh_seen(domain_instance)
                return domain_instance

    async def get_sa_instance(self, id: str) -> S:
        obj = await self.get(id, _return_sa_instance=True)
        return obj  # type: ignore

    @staticmethod
    def remove_desc_prefix(word: str) -> str:
        if word and word.startswith("-"):
            return word[1:]
        return word

    @staticmethod
    def remove_postfix(word: str) -> str:
        for postfix in SaGenericRepository.ALLOWED_POSTFIX:
            if word.endswith(postfix):
                return word.replace(postfix, "")
        return word

    def get_filters_for_sa_model_type(
        self, filters: dict[str, Any], sa_model_type: type[S]
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
        :type sa_model_type: Type[S]
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
                for k in filters:
                    if self.remove_postfix(k) in mapper.filter_key_to_column_name:
                        result[k] = filters[k]
                break
        return result

    def get_filter_to_column_mapper_for_sa_model_type(
        self, sa_model_type: type[S]
    ) -> FilterColumnMapper | None:
        for mapper in self.filter_to_column_mappers:
            if mapper.sa_model_type is sa_model_type:
                return mapper
        return None

    def _build_base_statement(
        self, starting_stmt: Select | None, limit: int | None
    ) -> Select:
        """
        Create the initial SELECT statement from the repository's model and applies the default filter.
        """
        logger.debug(f"Building base statement for {self.sa_model_type}")
        stmt = (
            starting_stmt if starting_stmt is not None else select(self.sa_model_type)
        )
        # If the model has a "discarded" column, filter out discarded rows.
        if "discarded" in inspect(self.sa_model_type).c.keys():  # type: ignore
            stmt = stmt.filter_by(discarded=False)
        stmt = self.setup_skip_and_limit(stmt, {}, limit)
        return stmt

    def _validate_filters(self, filters: dict[str, Any]) -> None:
        """
        Validates the filter keys against allowed filters and column mappers.
        """
        logger.debug("Validating filters")
        allowed_filters = self.ALLOWED_FILTERS.copy()
        for mapper in self.filter_to_column_mappers:
            allowed_filters.extend(mapper.filter_key_to_column_name.keys())
        for k in filters:
            if self.remove_postfix(k) not in allowed_filters:
                raise FilterValidationError(f"Filter not allowed: {k}", repository=self)

    def _apply_filters(
        self, stmt: Select, filters: dict[str, Any], already_joined: set[str]
    ) -> Select:
        """
        Applies filtering criteria by iterating through the column mappers, joining tables as needed,
        and using FilterOperator pattern to add WHERE conditions.
        """
        distinct = False
        for mapper in self.filter_to_column_mappers:
            logger.debug(
                f"Applying filters for {mapper.sa_model_type}. Filter: {filters}"
            )
            sa_model_type_filter = self.get_filters_for_sa_model_type(
                filters=filters, sa_model_type=mapper.sa_model_type
            )
            logger.debug(f"Filter for {mapper.sa_model_type}: {sa_model_type_filter}")
            if sa_model_type_filter and mapper.join_target_and_on_clause:
                for join_target, on_clause in mapper.join_target_and_on_clause:
                    if str(join_target) not in already_joined:
                        stmt = stmt.join(join_target, on_clause)
                        already_joined.add(str(join_target))
                # logger.debug(f"Joining {join_target} on {on_clause}")
                distinct = True

            # Use new FilterOperator pattern for filter application
            stmt = self._apply_filters_with_operator_factory(
                stmt=stmt,
                filters=sa_model_type_filter,
                sa_model_type=mapper.sa_model_type,
                mapping=mapper.filter_key_to_column_name,
                distinct=distinct,
            )

        if "sort" in filters:
            logger.debug(f"Applying sorting for {filters['sort']}")
            sort_model = self.get_sa_model_type_by_filter_key(
                self.remove_desc_prefix(filters["sort"])
            )
            logger.debug(f"Sort model: {sort_model}")
            if (
                sort_model
                and sort_model != self.sa_model_type
                and str(sort_model) not in already_joined
            ):
                mapper = self.get_filter_to_column_mapper_for_sa_model_type(sort_model)
                if mapper:
                    if mapper.join_target_and_on_clause:
                        for join_target, on_clause in mapper.join_target_and_on_clause:
                            if str(join_target) not in already_joined:
                                stmt = stmt.join(join_target, on_clause)
                                already_joined.add(str(join_target))
                        distinct = True
                    stmt = self._apply_filters_with_operator_factory(
                        stmt=stmt,
                        filters=sa_model_type_filter,
                        sa_model_type=mapper.sa_model_type,
                        mapping=mapper.filter_key_to_column_name,
                        distinct=distinct,
                    )
        logger.debug("Filters applied")
        return stmt

    def _apply_filters_with_operator_factory(
        self,
        stmt: Select,
        filters: dict[str, Any] | None,
        sa_model_type: type[S],
        mapping: dict[str, str],
        distinct: bool = False,
    ) -> Select:
        """
        Apply filters using the FilterOperator pattern with FilterOperatorFactory.

        This method replaces the complex logic in filter_stmt by using the
        FilterOperatorFactory to get appropriate operators and apply them.
        """
        if not filters:
            return stmt

        apply_distinct = distinct
        for filter_key, filter_value in filters.items():
            try:
                # Get column type for operator selection
                column_name = mapping[self.remove_postfix(filter_key)]
                inspector = inspect(sa_model_type)
                column_type = inspector.columns[column_name].type.python_type

                # Use FilterOperatorFactory to get the appropriate operator
                operator = self._filter_operator_factory.get_operator(
                    filter_name=filter_key, column_type=column_type, value=filter_value
                )

                # Get the SQLAlchemy column
                column = getattr(sa_model_type, column_name)

                # Apply the operator
                stmt = operator.apply(stmt, column, filter_value)

                # Check if distinct is needed for list values
                if isinstance(filter_value, list):
                    apply_distinct = True

            except KeyError as e:
                raise FilterValidationError(
                    f"Filter key {filter_key} not found in mapping for {sa_model_type.__name__}: {e}",
                    repository=self,
                )
            except Exception as e:
                logger.error(f"Error applying filter {filter_key}={filter_value}: {e}")
                raise FilterValidationError(
                    f"Invalid filter {filter_key}: {e}", repository=self
                )

        if apply_distinct:
            return stmt.distinct()
        return stmt

    def _apply_sorting(
        self,
        stmt: Select,
        filters: dict[str, Any],
        sort_stmt: Callable | None,
        sa_model: type[S] | None = None,
    ) -> Select:
        """
        Applies sorting to the statement using either the provided sort_stmt callback or
        the internal sort_stmt method.
        """
        sort_value = filters.get("sort")
        if sort_stmt:
            logger.debug("Applying custom sort statement")
            return sort_stmt(stmt=stmt, value_of_sort_query=sort_value)
        else:
            return self.sort_stmt(
                stmt=stmt, value_of_sort_query=sort_value, sa_model=sa_model
            )

    def setup_skip_and_limit(
        self,
        stmt: Select,
        filters: dict[str, Any] | None,
        limit: int | None = 500,
    ) -> Select:
        skip = filters.get("skip", 0) if filters else 0
        limit = filters.get("limit", limit) if filters else limit
        if limit:
            stmt = stmt.offset(skip).limit(limit)
        else:
            stmt = stmt.offset(skip)
        return stmt

    def get_filter_key_to_column_name_for_sa_model_type(
        self, sa_model_type: type[S]
    ) -> dict[str, Any] | None:
        for mapper in self.filter_to_column_mappers:
            if mapper.sa_model_type is sa_model_type:
                return mapper.filter_key_to_column_name
        return None

    def _filter_operator_selection(
        self,
        filter_name: str,
        filter_value: Any,
        sa_model_type: type[S] | None = None,
    ) -> Callable[[ColumnElement, Any], ColumnElement[bool]]:
        if not sa_model_type:
            sa_model_type = self.sa_model_type
            inspector = self.inspector
        else:
            inspector = inspect(sa_model_type)
        mapping = self.get_filter_key_to_column_name_for_sa_model_type(sa_model_type)
        if not mapping:
            raise FilterValidationError(
                f"Filter key {filter_name} not found in any filter column mapper.",
                repository=self,
            )
        column_name = mapping[self.remove_postfix(filter_name)]
        if "_gte" in filter_name:
            return operators.ge
        if "_lte" in filter_name:
            return operators.le
        if "_ne" in filter_name:
            return operators.ne
        if "_not_in" in filter_name:
            return lambda c, v: ColumnOperators.__or__(
                ColumnOperators.__eq__(c, None),
                ColumnOperators.not_in(c, v),
            )  # type: ignore
        if "_is_not" in filter_name:
            return operators.is_not

        # FIRST check the filter value
        if isinstance(filter_value, (list, set)):
            return lambda c, v: c.in_(v)

        # THEN check the column type
        if inspector.columns[column_name].type.python_type == list:
            return operators.contains
        if inspector.columns[column_name].type.python_type == str:
            return operators.eq
        if inspector.columns[column_name].type.python_type == bool:
            return lambda c, v: c.is_(v)

        return operators.eq

    def filter_stmt(
        self,
        stmt: Select,
        sa_model_type: type[S],
        mapping: dict[str, str],
        filters: dict[str, Any] | None = None,
        distinct: bool = False,
    ) -> Select:
        # TODO: check impact of removing 'distinct' from the query
        if not filters:
            return stmt
        apply_distinct = distinct
        for k, v in filters.items():
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
    ) -> type[S] | None:
        for mapper in self.filter_to_column_mappers:
            if filter_key in mapper.filter_key_to_column_name:
                return mapper.sa_model_type
        return None

    def sort_stmt(
        self,
        stmt: Select,
        value_of_sort_query: str | None = None,
        sa_model: type[S] | None = None,
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

        sa_model_type_to_sort_by = (
            self.get_sa_model_type_by_filter_key(
                self.remove_desc_prefix(value_of_sort_query)
            )
            or self.sa_model_type
        )
        inspector = inspect(sa_model_type_to_sort_by)
        mapping = self.get_filter_key_to_column_name_for_sa_model_type(
            sa_model_type_to_sort_by
        )
        if mapping and mapping.get(self.remove_desc_prefix(value_of_sort_query), None):
            clean_sort_name = mapping.get(
                self.remove_desc_prefix(value_of_sort_query), None
            )
        else:
            clean_sort_name = self.remove_desc_prefix(value_of_sort_query)
        if (
            clean_sort_name in inspector.columns.keys()
            and "source" not in value_of_sort_query
        ):
            column_attr = getattr(sa_model or sa_model_type_to_sort_by, clean_sort_name)
            if value_of_sort_query.startswith("-"):
                stmt = stmt.order_by(nulls_last(column_attr.desc()))
            else:
                stmt = stmt.order_by(nulls_last(column_attr))
        return stmt

    async def execute_stmt(
        self, stmt: Select, _return_sa_instance: bool = False
    ) -> Any:
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
            if domain_obj.discarded:
                domain_obj._discarded = False
                sa_instance = await self.data_mapper.map_domain_to_sa(
                    self._session, domain_obj
                )
                sa_instance.discarded = True  # type: ignore
            else:
                sa_instance = await self.data_mapper.map_domain_to_sa(
                    self._session, domain_obj
                )
            await self._session.merge(sa_instance)
        finally:
            self._session.autoflush = True
            await self._session.flush()

    async def persist_all(self, domain_entities: list[E] | None = None) -> None:
        if not domain_entities:
            return
        for i in domain_entities:
            assert (
                i in self.seen
            ), "Cannon persist entity which is unknown to the repo. Did you forget to call repo.add() for this entity?"
        self._session.autoflush = False
        sa_instances = []

        async def prepare_sa_instance(obj: E):
            if obj.discarded:
                obj._discarded = False
                sa_instance = await self.data_mapper.map_domain_to_sa(
                    self._session, obj
                )
                sa_instance.discarded = True  # type: ignore
            else:
                sa_instance = await self.data_mapper.map_domain_to_sa(
                    self._session, obj
                )
            sa_instances.append(sa_instance)

        async with anyio.create_task_group() as tg:
            for obj in domain_entities:
                tg.start_soon(prepare_sa_instance, obj)

        for sa_instance in sa_instances:
            await self._session.merge(sa_instance)

        self._session.autoflush = True
        await self._session.flush()

    async def query(
        self,
        *,
        filters: dict[str, Any] | None = None,
        starting_stmt: Select | None = None,
        sort_stmt: Callable | None = None,
        limit: int | None = None,
        already_joined: set[str] | None = None,
        sa_model: type[S] | None = None,
        _return_sa_instance: bool = False,
    ) -> list[E]:
        """
        Retrieve a list of domain objects from the database based on the provided filter criteria.
        """
        try:
            stmt = self._build_query(
                filters=filters,
                starting_stmt=starting_stmt,
                sort_stmt=sort_stmt,
                limit=limit,
                already_joined=already_joined,
                sa_model=sa_model,
            )
            result = await self.execute_stmt(
                stmt, _return_sa_instance=_return_sa_instance
            )
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
        return result

    def _build_query(
        self,
        *,
        filters: dict[str, Any] | None = None,
        starting_stmt: Select | None = None,
        sort_stmt: Callable | None = None,
        limit: int | None = None,
        already_joined: set[str] | None = None,
        sa_model: type[S] | None = None,
    ) -> Select:
        """
        Build the complete SQL query statement from the provided parameters.

        This method orchestrates the query building process by:
        1. Building the base SELECT statement
        2. Validating and applying filters
        3. Applying sorting
        4. Managing joins to prevent duplicates

        Args:
            filter: Dictionary of filter criteria
            starting_stmt: Optional pre-built SELECT statement to start from
            sort_stmt: Optional custom sorting function
            limit: Maximum number of results to return
            already_joined: Set of already joined table names to prevent duplicates
            sa_model: SQLAlchemy model type for sorting context

        Returns:
            Complete SQLAlchemy Select statement ready for execution
        """
        already_joined = already_joined or set()
        stmt = self._build_base_statement(starting_stmt, limit)

        if filters:
            self._validate_filters(filters)
            stmt = self._apply_filters(stmt, filters, already_joined)
            stmt = self._apply_sorting(stmt, filters, sort_stmt, sa_model)

        return stmt
