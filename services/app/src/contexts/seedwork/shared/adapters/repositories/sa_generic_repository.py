from __future__ import annotations

from collections.abc import Callable
from typing import Any, Generic, Type, Optional
import time
import warnings

import anyio
from sqlalchemy import ColumnElement, Select, inspect, nulls_last, select
from sqlalchemy.exc import MultipleResultsFound, NoResultFound, SQLAlchemyError, DatabaseError, IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import ColumnOperators
from sqlalchemy.sql import operators

from src.contexts.seedwork.shared.adapters.exceptions import (
    EntityNotFoundException, MultipleEntitiesFoundException)
from src.contexts.seedwork.shared.adapters.ORM.mappers.mapper import ModelMapper
from src.contexts.seedwork.shared.adapters.repositories.filter_operators import filter_operator_factory, filter_operator_registry
from src.contexts.seedwork.shared.adapters.repositories.join_manager import JoinManager
from src.contexts.seedwork.shared.adapters.repositories.filter_mapper import FilterColumnMapper, E, S
from src.contexts.seedwork.shared.adapters.repositories.repository_exceptions import (
    RepositoryQueryException, FilterValidationException, JoinException, EntityMappingException
)
from src.contexts.seedwork.shared.adapters.repositories.repository_logger import RepositoryLogger
from src.contexts.seedwork.shared.endpoints.exceptions import BadRequestException
from src.logging.logger import logger
from src.contexts.seedwork.shared.adapters.filter_validator import FilterValidator
from src.contexts.seedwork.shared.adapters.repositories.query_builder import QueryBuilder


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

    The filter postfixes are now managed by FilterOperatorRegistry instead of
      a hardcoded ALLOWED_POSTFIX list, providing better extensibility and
      organization for comparison operators like _gte, _lte, _ne, _not_in, _is_not.
    """

    # Legacy ALLOWED_POSTFIX removed - now handled by FilterOperatorRegistry
    # ALLOWED_POSTFIX = ["_gte", "_lte", "_ne", "_not_in", "_is_not", "_not_exists"]
    ALLOWED_FILTERS = [
        "skip",
        "limit",
        "sort",
        "created_at",
    ]

    def __init__(
        self,
        db_session: AsyncSession,
        data_mapper: Type[ModelMapper],
        domain_model_type: Type[E],
        sa_model_type: Type[S],
        filter_to_column_mappers: list[FilterColumnMapper] | None = None,
        cache_backend: Any = None,  # Optional cache backend for future use
        repository_logger: Optional[RepositoryLogger] = None,
    ):
        self._session = db_session
        self.data_mapper = data_mapper
        self.domain_model_type = domain_model_type
        self.sa_model_type = sa_model_type
        self.filter_to_column_mappers = filter_to_column_mappers or []
        self.inspector = inspect(sa_model_type)
        self.seen: set[E] = set()
        self.cache_backend = cache_backend  # Placeholder for future caching layer
        
        # Initialize structured logger for this repository instance
        if repository_logger is None:
            self._repo_logger = RepositoryLogger.create_logger(f"{self.sa_model_type.__name__}Repository")
        else:
            self._repo_logger = repository_logger
            
        self._repo_logger.logger.debug(
            "Repository initialized",
            domain_model=self.domain_model_type.__name__,
            sa_model=self.sa_model_type.__name__,
            mapper_count=len(self.filter_to_column_mappers)
        )

        # Initialize FilterValidator based on provided column mappers
        try:
            self._filter_validator = FilterValidator.from_mappers(
                self.filter_to_column_mappers,
                special_allowed=self.ALLOWED_FILTERS,
                sa_model_type=self.sa_model_type,
            )
        except Exception as e:
            # Fallback to a validator with no type information if mappers are misconfigured
            self._filter_validator = FilterValidator({}, special_allowed=self.ALLOWED_FILTERS, sa_model_type=self.sa_model_type)
            logger.warning(
                "Failed to initialize FilterValidator from mappers. Falling back to empty validator. Error: %s",
                str(e),
            )

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
        *,
        ttl: int = 300,
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
        self._invalidate_cache_for_entity(domain_obj, ttl=ttl)

    async def get(self, id: str, _return_sa_instance: bool = False, _return_discarded: bool = False) -> E | S:
        table_columns = inspect(self.sa_model_type).c.keys() # type: ignore
        if "discarded" in table_columns:
            if _return_discarded:
                stmt = select(self.sa_model_type).filter_by(id=id) # type: ignore
            else:
                stmt = select(self.sa_model_type).filter_by(id=id, discarded=False) # type: ignore
        else:
            stmt = select(self.sa_model_type).filter_by(id=id) # type: ignore
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

    async def get_sa_instance(self, id: str, _return_discarded: bool = False) -> S:
        obj = await self.get(id, _return_sa_instance=True, _return_discarded=_return_discarded)
        return obj # type: ignore

    @staticmethod
    def remove_desc_prefix(word: str) -> str:
        if word and word.startswith("-"):
            return word[1:]
        return word

    @staticmethod
    def remove_postfix(word: str) -> str:
        # Use FilterOperatorRegistry instead of hardcoded ALLOWED_POSTFIX
        return filter_operator_registry.remove_postfix(word)

    def get_filters_for_sa_model_type(
        self, filter: dict[str, Any], sa_model_type: Type[S]
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
                for k in filter.keys():
                    if self.remove_postfix(k) in mapper.filter_key_to_column_name:
                        result[k] = filter[k]
                break
        return result

    def get_filter_to_column_mapper_for_sa_model_type(
        self, sa_model_type: Type[S]
    ) -> FilterColumnMapper | None:
        for mapper in self.filter_to_column_mappers:
            if mapper.sa_model_type is sa_model_type:
                return mapper
        return None

    def _build_base_statement(self, starting_stmt: Select | None, limit: int | None) -> Select:
        """
        Create the initial SELECT statement from the repository's model.
        Note: Discarded filtering is now handled in FilterValidator rather than here.
        """
        self._repo_logger.log_sql_construction(
            step="build_base",
            sql_fragment=f"SELECT {self.sa_model_type.__tablename__}.*",
            parameters={"starting_stmt_provided": starting_stmt is not None, "limit": limit}
        )
        
        stmt = starting_stmt if starting_stmt is not None else select(self.sa_model_type)
        stmt = self.setup_skip_and_limit(stmt, {}, limit)
        
        self._repo_logger.log_sql_construction(
            step="build_base_complete",
            sql_fragment="Base statement with limits",
            parameters={"starting_stmt_provided": starting_stmt is not None}
        )
        
        return stmt

    def _validate_filters(self, filter: dict[str, Any]) -> dict[str, Any]:
        """
        Validate filter dict using centralized FilterValidator.
        Returns the processed filter dictionary (potentially with automatic discarded handling).
        """

        # Early exit if no filters provided
        if not filter:
            filter = {}

        # Log start of validation
        self._repo_logger.debug_filter_operation(
            "Starting filter validation",
            filter_count=len(filter),
            filter_keys=list(filter.keys()),
        )

        # Performance warning for large filter sets
        if len(filter) > 10:
            self._repo_logger.warn_performance_issue(
                "large_filter_set",
                f"Filter contains {len(filter)} conditions which may impact performance",
                filter_count=len(filter),
                filter_keys=list(filter.keys()),
            )

        # Delegate validation logic to FilterValidator and get processed filter
        try:
            processed_filter = self._filter_validator.validate(filter, repository=self)
        except FilterValidationException as exc:
            # Provide additional logging context before re-raising
            self._repo_logger.debug_filter_operation(
                "Filter validation failed via FilterValidator",
                invalid_filters=exc.invalid_filters,
                suggested_filters=exc.suggested_filters,
            )
            raise

        # Log successful validation summary
        self._repo_logger.debug_filter_operation(
            "Filter validation completed successfully",
            original_filters=len(filter),
            processed_filters=len(processed_filter),
            special_filters=len([
                k for k in processed_filter.keys() if self.remove_postfix(k) in self.ALLOWED_FILTERS
            ]),
            mapped_filters=len([
                k for k in processed_filter.keys() if self.remove_postfix(k) in self._filter_validator.allowed_keys_types
            ]),
        )
        
        return processed_filter

    def _apply_filters(self, stmt: Select, filter: dict[str, Any], already_joined: set[str]) -> Select:
        """
        Applies filtering criteria by iterating through the column mappers, joining tables as needed,
        and using FilterOperator pattern to add WHERE conditions.
        
        Refactored to use JoinManager for handling table joins with enhanced error handling.
        
        Raises:
            JoinException: When join operations fail
            RepositoryQueryException: When filter application fails
        """
        start_time = time.perf_counter()
        
        self._repo_logger.debug_filter_operation(
            "Starting filter application",
            filter_count=len(filter),
            mapper_count=len(self.filter_to_column_mappers),
            already_joined_count=len(already_joined)
        )
        
        try:
            # Create JoinManager with existing joins
            join_manager = JoinManager.create_with_existing_joins(already_joined)
            distinct = False
            joins_performed = 0
            filters_applied = 0
            
            for i, mapper in enumerate(self.filter_to_column_mappers):
                mapper_start_time = time.perf_counter()
                
                self._repo_logger.debug_filter_operation(
                    "Processing mapper",
                    mapper_index=i,
                    sa_model=mapper.sa_model_type.__name__,
                    filter_keys=list(mapper.filter_key_to_column_name.keys())
                )
                
                sa_model_type_filter = self.get_filters_for_sa_model_type(
                    filter=filter, sa_model_type=mapper.sa_model_type
                )
                
                if sa_model_type_filter:
                    self._repo_logger.debug_filter_operation(
                        "Filters found for mapper",
                        sa_model=mapper.sa_model_type.__name__,
                        applicable_filters=sa_model_type_filter
                    )
                    
                    # Use JoinManager to handle joins if filter requires them
                    if mapper.join_target_and_on_clause:
                        join_start_time = time.perf_counter()
                        try:
                            stmt, requires_distinct = join_manager.handle_joins(stmt, mapper.join_target_and_on_clause)
                            join_time = time.perf_counter() - join_start_time
                            
                            # Log join operations
                            for join_target, join_condition in mapper.join_target_and_on_clause:
                                self._repo_logger.log_join(
                                    join_target=join_target.__name__,
                                    join_condition=str(join_condition),
                                    join_type="inner"
                                )
                                joins_performed += 1
                            
                            if requires_distinct:
                                distinct = True
                                self._repo_logger.debug_join_operation(
                                    "Join requires DISTINCT",
                                    join_target=mapper.sa_model_type.__name__,
                                    join_time=join_time
                                )
                                
                        except Exception as e:
                            self._repo_logger.debug_join_operation(
                                "Join operation failed",
                                sa_model=mapper.sa_model_type.__name__,
                                join_path=str(mapper.join_target_and_on_clause),
                                error=str(e)
                            )
                            raise JoinException(
                                message=f"Failed to join tables for {mapper.sa_model_type.__name__}",
                                repository=self,
                                join_path=str(mapper.join_target_and_on_clause),
                                relationship_error=str(e)
                            ) from e
                    
                    # Apply filters for this mapper
                    filter_start_time = time.perf_counter()
                    try:
                        stmt = self._apply_filters_with_operator_factory(
                            stmt=stmt,
                            filter=sa_model_type_filter,
                            sa_model_type=mapper.sa_model_type,
                            mapping=mapper.filter_key_to_column_name,
                            distinct=distinct,
                        )
                        filter_time = time.perf_counter() - filter_start_time
                        filters_applied += len(sa_model_type_filter)
                        
                        self._repo_logger.debug_filter_operation(
                            "Filters applied successfully",
                            sa_model=mapper.sa_model_type.__name__,
                            filter_count=len(sa_model_type_filter),
                            filter_time=filter_time
                        )
                        
                    except Exception as e:
                        self._repo_logger.debug_filter_operation(
                            "Filter application failed",
                            sa_model=mapper.sa_model_type.__name__,
                            filters=sa_model_type_filter,
                            error=str(e)
                        )
                        raise RepositoryQueryException(
                            message=f"Failed to apply filters for {mapper.sa_model_type.__name__}",
                            repository=self,
                            filter_values=sa_model_type_filter
                        ) from e
                
                mapper_time = time.perf_counter() - mapper_start_time
                self._repo_logger.debug_performance_detail(
                    "Mapper processing completed",
                    mapper_index=i,
                    sa_model=mapper.sa_model_type.__name__,
                    processing_time=mapper_time
                )
            
            # Handle sorting joins using JoinManager
            if "sort" in filter:
                sort_start_time = time.perf_counter()
                sort_field = filter["sort"]
                
                self._repo_logger.debug_join_operation(
                    "Processing sort joins",
                    sort_field=sort_field
                )
                
                sort_model = self.get_sa_model_type_by_filter_key(self.remove_desc_prefix(sort_field))
                
                if sort_model and sort_model != self.sa_model_type and join_manager.is_join_needed(sort_model):
                    mapper = self.get_filter_to_column_mapper_for_sa_model_type(sort_model)
                    if mapper and mapper.join_target_and_on_clause:
                        try:
                            stmt, requires_distinct = join_manager.handle_joins(stmt, mapper.join_target_and_on_clause)
                            sort_time = time.perf_counter() - sort_start_time
                            
                            # Log sort joins
                            for join_target, join_condition in mapper.join_target_and_on_clause:
                                self._repo_logger.log_join(
                                    join_target=join_target.__name__,
                                    join_condition=str(join_condition),
                                    join_type="inner (for sorting)"
                                )
                                joins_performed += 1
                            
                            if requires_distinct:
                                distinct = True
                                
                            self._repo_logger.debug_join_operation(
                                "Sort joins completed",
                                sort_field=sort_field,
                                sort_model=sort_model.__name__,
                                sort_time=sort_time
                            )
                            
                        except Exception as e:
                            self._repo_logger.debug_join_operation(
                                "Sort join operation failed",
                                sort_field=sort_field,
                                sort_model=sort_model.__name__,
                                error=str(e)
                            )
                            raise JoinException(
                                message=f"Failed to join tables for sorting by {sort_field}",
                                repository=self,
                                join_path=str(mapper.join_target_and_on_clause),
                                relationship_error=str(e)
                            ) from e
            
            # Update the already_joined set with new joins from JoinManager
            new_joins = join_manager.get_tracked_joins() - already_joined
            already_joined.update(join_manager.get_tracked_joins())
            
            total_time = time.perf_counter() - start_time
            
            # Performance monitoring and warnings
            self._repo_logger.log_performance(
                query_time=total_time,
                result_count=filters_applied,
                memory_usage=self._repo_logger.get_memory_usage()
            )
            
            # Warn about complex joins
            if joins_performed > 3:
                self._repo_logger.warn_performance_issue(
                    "complex_joins",
                    f"Query uses {joins_performed} table joins which may impact performance",
                    join_count=joins_performed,
                    total_time=total_time
                )
            
            self._repo_logger.debug_filter_operation(
                "Filter application completed",
                total_time=total_time,
                filters_applied=filters_applied,
                joins_performed=joins_performed,
                new_joins_count=len(new_joins),
                requires_distinct=distinct
            )
            
            return stmt
            
        except (JoinException, RepositoryQueryException):
            # Re-raise our custom exceptions as-is
            raise
        except Exception as e:
            total_time = time.perf_counter() - start_time
            self._repo_logger.debug_filter_operation(
                "Unexpected error during filter application",
                error=str(e),
                error_type=type(e).__name__,
                total_time=total_time
            )
            # Catch any other unexpected errors during filter application
            raise RepositoryQueryException(
                message=f"Unexpected error during filter application",
                repository=self,
                filter_values=filter
            ) from e

    def _apply_filters_with_operator_factory(
        self,
        stmt: Select,
        filter: dict[str, Any] | None,
        sa_model_type: Type[S],
        mapping: dict[str, str],
        distinct: bool = False,
    ) -> Select:
        """
        Apply filters using the FilterOperator pattern with FilterOperatorFactory.
        
        This method replaces the complex logic in filter_stmt by using the 
        FilterOperatorFactory to get appropriate operators and apply them.
        """
        warnings.warn(
            "'_apply_filters_with_operator_factory' is an internal method and may be removed or changed in a future version. "
            "Prefer using 'filter_stmt' or the high-level 'query' interface instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        if not filter:
            return stmt
        
        filter_start_time = time.perf_counter()
        
        self._repo_logger.debug_filter_operation(
            "Starting filter application with operator factory",
            sa_model=sa_model_type.__name__,
            filter_count=len(filter),
            mapping_count=len(mapping),
            distinct_required=distinct
        )
        
        # Import the global factory instance
        from src.contexts.seedwork.shared.adapters.repositories.filter_operators import filter_operator_factory
        
        apply_distinct = distinct
        successful_filters = 0
        
        for filter_key, filter_value in filter.items():
            filter_operation_start = time.perf_counter()
            
            try:
                # Get the base column name (without postfix)
                base_column_name = self.remove_postfix(filter_key)
                column_name = mapping[base_column_name]
                
                self._repo_logger.debug_filter_operation(
                    "Processing individual filter",
                    filter_key=filter_key,
                    base_column=base_column_name,
                    mapped_column=column_name,
                    filter_value=filter_value,
                    value_type=type(filter_value).__name__
                )
                
                # Get column type for operator selection (more robust approach)
                column_type = str  # Default fallback
                try:
                    inspector = inspect(sa_model_type)
                    column_info = inspector.columns[column_name]
                    # Try to get python_type, fallback to generic type if needed
                    try:
                        column_type = column_info.type.python_type
                        self._repo_logger.debug_filter_operation(
                            "Column type detected",
                            filter_key=filter_key,
                            column_name=column_name,
                            column_type=column_type.__name__
                        )
                    except (NotImplementedError, AttributeError):
                        # Fallback for complex column types
                        column_type = str
                        self._repo_logger.debug_filter_operation(
                            "Using fallback column type",
                            filter_key=filter_key,
                            column_name=column_name,
                            fallback_type="str"
                        )
                except Exception as e:
                    # Ultimate fallback
                    column_type = str
                    self._repo_logger.debug_filter_operation(
                        "Column type detection failed, using str fallback",
                        filter_key=filter_key,
                        column_name=column_name,
                        error=str(e)
                    )
                
                # Use FilterOperatorFactory to get the appropriate operator
                operator_selection_start = time.perf_counter()
                operator = filter_operator_factory.get_operator(
                    filter_name=filter_key,
                    column_type=column_type,
                    value=filter_value
                )
                operator_selection_time = time.perf_counter() - operator_selection_start
                
                self._repo_logger.debug_filter_operation(
                    "Filter operator selected",
                    filter_key=filter_key,
                    operator_type=type(operator).__name__,
                    column_type=column_type.__name__,
                    selection_time=operator_selection_time
                )
                
                # Get the SQLAlchemy column
                column = getattr(sa_model_type, column_name)
                
                # Apply the operator
                operator_apply_start = time.perf_counter()
                stmt = operator.apply(stmt, column, filter_value)
                operator_apply_time = time.perf_counter() - operator_apply_start
                
                # Log the applied filter
                self._repo_logger.log_filter(
                    filter_key=filter_key,
                    filter_value=filter_value,
                    filter_type=type(operator).__name__,
                    column_name=column_name
                )
                
                # Check if distinct is needed for list values
                if isinstance(filter_value, list):
                    apply_distinct = True
                    self._repo_logger.debug_filter_operation(
                        "DISTINCT required due to list filter",
                        filter_key=filter_key,
                        list_size=len(filter_value)
                    )
                
                successful_filters += 1
                filter_operation_time = time.perf_counter() - filter_operation_start
                
                self._repo_logger.debug_filter_operation(
                    "Filter applied successfully",
                    filter_key=filter_key,
                    operator_type=type(operator).__name__,
                    operation_time=filter_operation_time,
                    operator_apply_time=operator_apply_time
                )
                    
            except KeyError as e:
                filter_operation_time = time.perf_counter() - filter_operation_start
                self._repo_logger.debug_filter_operation(
                    "Filter mapping error",
                    filter_key=filter_key,
                    base_column=base_column_name,
                    available_mappings=list(mapping.keys()),
                    operation_time=filter_operation_time,
                    error=str(e)
                )
                raise FilterValidationException(
                    message=f"Filter key '{filter_key}' not found in column mapping for {sa_model_type.__name__}",
                    repository=self,
                    invalid_filters=[filter_key],
                    suggested_filters=list(mapping.keys())[:5]  # Suggest available mapping keys
                ) from e
            except Exception as e:
                filter_operation_time = time.perf_counter() - filter_operation_start
                self._repo_logger.debug_filter_operation(
                    "Filter application error",
                    filter_key=filter_key,
                    filter_value=filter_value,
                    value_type=type(filter_value).__name__,
                    operation_time=filter_operation_time,
                    error=str(e),
                    error_type=type(e).__name__
                )
                raise RepositoryQueryException(
                    message=f"Failed to apply filter '{filter_key}' with value '{filter_value}': {str(e)}",
                    repository=self,
                    filter_values={filter_key: filter_value}
                ) from e
        
        total_filter_time = time.perf_counter() - filter_start_time
        
        # Apply DISTINCT if needed
        if apply_distinct:
            stmt = stmt.distinct()
            self._repo_logger.log_sql_construction(
                step="distinct",
                sql_fragment="SELECT DISTINCT",
                parameters={"reason": "list_filters_require_distinct"}
            )
        
        self._repo_logger.debug_filter_operation(
            "Filter factory application completed",
            sa_model=sa_model_type.__name__,
            total_filters=len(filter),
            successful_filters=successful_filters,
            distinct_applied=apply_distinct,
            total_time=total_filter_time
        )
        
        return stmt

    def _apply_sorting(self, stmt: Select, filter: dict[str, Any], sort_stmt: Callable | None, sa_model: Type[S] | None = None,) -> Select:
        """
        Applies sorting to the statement using either the provided sort_stmt callback or
        the internal sort_stmt method.
        """
        sort_value = filter.get("sort", None)
        if sort_stmt:
            self._repo_logger.debug_query_step("sort", "Applying custom sort statement", sort_value=sort_value)
            return sort_stmt(stmt=stmt, value_of_sort_query=sort_value)
        else:
            return self.sort_stmt(stmt=stmt, value_of_sort_query=sort_value, sa_model=sa_model)


    def setup_skip_and_limit(
        self,
        stmt: Select,
        filter: dict[str, Any] | None,
        limit: int | None = 500,
    ) -> Select:
        skip = filter.get("skip", 0) if filter else 0
        limit = filter.get("limit", limit) if filter else limit
        if limit:
            stmt = stmt.offset(skip).limit(limit)
        else:
            stmt = stmt.offset(skip)
        return stmt

    def get_filter_key_to_column_name_for_sa_model_type(
        self, sa_model_type: Type[S]
    ) -> dict[str, Any] | None:
        for mapper in self.filter_to_column_mappers:
            if mapper.sa_model_type is sa_model_type:
                return mapper.filter_key_to_column_name
        return None

    def _filter_operator_selection(
        self,
        filter_name: str,
        filter_value: Any,
        sa_model_type: Type[S] | None = None,
    ) -> Callable[[ColumnElement, Any], ColumnElement[bool]]:
        """
        Select the appropriate filter operator for the given filter criteria.
        
        This method has been refactored to use FilterOperatorFactory while maintaining
        backward compatibility with the existing Callable return type.
        
        Args:
            filter_name: The filter field name (may include postfix like _gte, _lte)
            filter_value: The value to filter by
            sa_model_type: The SQLAlchemy model type (optional)
            
        Returns:
            Callable: A function that takes (column, value) and returns a ColumnElement condition
        """
        warnings.warn(
            "'_filter_operator_selection' is deprecated and will be removed in a future version. "
            "Use 'FilterOperatorFactory.get_operator' directly instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        if not sa_model_type:
            sa_model_type = self.sa_model_type
            inspector = self.inspector
        else:
            inspector = inspect(sa_model_type)
            
        # Get the column mapping to validate the filter key exists
        mapping = self.get_filter_key_to_column_name_for_sa_model_type(sa_model_type)
        if not mapping:
            raise BadRequestException(
                f"Filter key {filter_name} not found in any filter column mapper."
            )
            
        # Get the base column name (without postfix)
        base_filter_name = filter_operator_factory.remove_postfix(filter_name)
        column_name = mapping[base_filter_name]
        
        # Determine the column type for the factory
        try:
            column_type = inspector.columns[column_name].type.python_type
        except (KeyError, AttributeError):
            # Fallback to generic type if column inspection fails
            column_type = type(filter_value) if filter_value is not None else str
        
        # Get the operator from the factory
        operator = filter_operator_factory.get_operator(filter_name, column_type, filter_value)
        
        # Return a callable that wraps the operator.apply method to maintain backward compatibility
        def operator_wrapper(column: ColumnElement, value: Any) -> ColumnElement[bool]:
            """
            Wrapper function to maintain backward compatibility.
            
            The existing code expects a callable that takes (column, value) and returns
            a ColumnElement[bool]. The new FilterOperator.apply method takes (stmt, column, value)
            and returns a Select statement. This wrapper extracts the WHERE condition
            from the modified statement.
            """
            # For simple cases, we can directly call the operator methods we know
            # This maintains the exact same behavior as the original implementation
            if hasattr(operator, '__class__'):
                operator_name = operator.__class__.__name__
                
                if operator_name == 'EqualsOperator':
                    if value is None:
                        return column.is_(None)  # type: ignore
                    elif isinstance(value, bool):
                        return column.is_(value)  # type: ignore
                    else:
                        return column.__eq__(value)  # type: ignore
                
                elif operator_name == 'GreaterThanOperator':
                    return operators.ge(column, value)  # type: ignore
                
                elif operator_name == 'LessThanOperator':
                    return operators.le(column, value)  # type: ignore
                
                elif operator_name == 'NotEqualsOperator':
                    if value is None:
                        return column.is_not(None)  # type: ignore
                    return operators.ne(column, value)  # type: ignore
                
                elif operator_name == 'InOperator':
                    return column.in_(value)  # type: ignore
                
                elif operator_name == 'NotInOperator':
                    # Maintain exact same logic as original implementation
                    return ColumnOperators.__or__(  # type: ignore
                        ColumnOperators.__eq__(column, None),
                        ColumnOperators.not_in(column, value),
                    )
                
                elif operator_name == 'ContainsOperator':
                    return operators.contains(column, value)  # type: ignore
                
                elif operator_name == 'IsNotOperator':
                    return operators.is_not(column, value)  # type: ignore
            
            # Ultimate fallback to equals
            return column.__eq__(value)  # type: ignore
        
        return operator_wrapper


    def filter_stmt(
        self,
        stmt: Select,
        sa_model_type: Type[S],
        mapping: dict[str, str],
        filter: dict[str, Any] | None = None,
        distinct: bool = False,
    ) -> Select:
        """
        Apply filter conditions to a SQLAlchemy Select statement.
        
        This method has been simplified to use FilterOperator.apply() pattern directly,
        delegating filter logic to the appropriate FilterOperator instances.
        
        Args:
            stmt: The base SQLAlchemy Select statement
            sa_model_type: The SQLAlchemy model type
            mapping: Dictionary mapping filter keys to column names
            filter: Dictionary of filter criteria (key-value pairs)
            distinct: Whether to apply DISTINCT to the query
            
        Returns:
            Select: Modified Select statement with filter conditions applied
        """
        if not filter:
            return stmt
            
        apply_distinct = distinct
        
        # Get inspector for column type detection
        if sa_model_type == self.sa_model_type:
            inspector = self.inspector
        else:
            inspector = inspect(sa_model_type)
        
        for filter_key, filter_value in filter.items():
            # Get the base column name (without postfix)
            base_filter_name = filter_operator_factory.remove_postfix(filter_key)
            column_name = mapping[base_filter_name]
            
            # Get the column attribute from the SQLAlchemy model
            column = getattr(sa_model_type, column_name)
            
            # Determine the column type for the operator factory
            try:
                column_type = inspector.columns[column_name].type.python_type
            except (KeyError, AttributeError):
                # Fallback to generic type if column inspection fails
                column_type = type(filter_value) if filter_value is not None else str
            
            # Get the appropriate FilterOperator from the factory
            operator = filter_operator_factory.get_operator(filter_key, column_type, filter_value)
            
            # Apply the filter using the operator's apply method
            stmt = operator.apply(stmt, column, filter_value)
            
            # Track when to apply DISTINCT (for list-based filters)
            if isinstance(filter_value, list):
                apply_distinct = True
        
        # Apply DISTINCT if needed
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
        sa_model: Type[S] | None = None,
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
            self.get_sa_model_type_by_filter_key(self.remove_desc_prefix(value_of_sort_query))
            or self.sa_model_type
        )
        inspector = inspect(sa_model_type_to_sort_by)
        mapping = self.get_filter_key_to_column_name_for_sa_model_type(sa_model_type_to_sort_by)
        if mapping and mapping.get(self.remove_desc_prefix(value_of_sort_query), None):
            clean_sort_name = (
                mapping.get(self.remove_desc_prefix(value_of_sort_query), None)
            )
        else:
            clean_sort_name = self.remove_desc_prefix(value_of_sort_query)
        if clean_sort_name in inspector.columns.keys() and "source" not in value_of_sort_query:
            column_attr = getattr(sa_model or sa_model_type_to_sort_by, clean_sort_name)
            if value_of_sort_query.startswith("-"):
                stmt = stmt.order_by(nulls_last(column_attr.desc()))
            else:
                stmt = stmt.order_by(nulls_last(column_attr))
        return stmt


    async def execute_stmt(
        self, stmt: Select, _return_sa_instance: bool = False
    ) -> Any:
        """
        Execute a SQLAlchemy Select statement and return domain entities or SA instances.
        
        Enhanced with comprehensive structured logging for execution tracking and performance monitoring.
        
        Raises:
            RepositoryQueryException: When database execution fails
            EntityMappingException: When domain mapping fails
        """
        start_time = time.perf_counter()
        correlation_id = f"exec_{int(start_time * 1000)}"
        
        self._repo_logger.debug_query_step(
            "execution_start",
            "Starting statement execution",
            correlation_id=correlation_id,
            return_sa_instance=_return_sa_instance,
            sa_model=self.sa_model_type.__name__
        )
        
        # Try to get SQL string for logging (best effort)
        sql_query = None
        try:
            sql_query = str(stmt.compile(compile_kwargs={"literal_binds": True}))
            self._repo_logger.log_sql_construction(
                step="final_sql",
                sql_fragment=sql_query[:500] + "..." if len(sql_query) > 500 else sql_query,
                parameters={"full_sql_length": len(sql_query)}
            )
        except Exception as e:
            sql_query = str(stmt)  # Fallback to basic string representation
            self._repo_logger.debug_query_step(
                "sql_compilation",
                "Could not compile SQL with literal binds",
                correlation_id=correlation_id,
                error=str(e),
                fallback_sql_length=len(sql_query)
            )
        
        try:
            # Execute the SQL query
            execution_start_time = time.perf_counter()
            
            try:
                # Utilize QueryBuilder for statement execution to ensure consistency with the
                # new query-building pattern introduced in Phase 1. The builder is initialised
                # with the pre-constructed `stmt` and executed in SA-instance mode so that the
                # existing mapping and logging logic below remains unchanged.
                qb = QueryBuilder(
                    session=self._session,
                    sa_model_type=self.sa_model_type,
                    starting_stmt=stmt,
                )
                qb.select()  # prime builder with starting statement
                try:
                    with anyio.fail_after(30.0):
                        sa_objs = await qb.execute(_return_sa_instance=True)
                except TimeoutError:
                    execution_time = time.perf_counter() - execution_start_time
                    self._repo_logger.debug_query_step(
                        "sql_execution_timeout",
                        "SQL execution timed out after 30 seconds",
                        correlation_id=correlation_id,
                        execution_time=execution_time,
                        sql_query=sql_query
                    )
                    raise RepositoryQueryException(
                        message="Database query execution timed out after 30 seconds",
                        repository=self,
                        sql_query=sql_query,
                        execution_time=execution_time,
                        correlation_id=correlation_id
                    )
                execution_time = time.perf_counter() - execution_start_time
                
                self._repo_logger.debug_query_step(
                    "sql_execution",
                    "SQL execution completed",
                    correlation_id=correlation_id,
                    execution_time=execution_time,
                    result_count=len(sa_objs),
                    sa_model=self.sa_model_type.__name__
                )
                
                # Log performance metrics
                self._repo_logger.log_performance(
                    query_time=execution_time,
                    result_count=len(sa_objs),
                    memory_usage=self._repo_logger.get_memory_usage(),
                    sql_query=sql_query
                )
                
            except (SQLAlchemyError, DatabaseError) as e:
                execution_time = time.perf_counter() - execution_start_time
                
                self._repo_logger.debug_query_step(
                    "sql_execution_error",
                    "SQL execution failed",
                    correlation_id=correlation_id,
                    execution_time=execution_time,
                    error=str(e),
                    error_type=type(e).__name__,
                    sql_query=sql_query
                )
                
                raise RepositoryQueryException(
                    message=f"Database query execution failed: {str(e)}",
                    repository=self,
                    sql_query=sql_query,
                    execution_time=execution_time,
                    correlation_id=correlation_id
                ) from e
            
            # Return SA instances directly if requested
            if _return_sa_instance:
                total_time = time.perf_counter() - start_time
                
                self._repo_logger.debug_query_step(
                    "execution_complete",
                    "Statement execution completed (SA instances)",
                    correlation_id=correlation_id,
                    total_time=total_time,
                    result_count=len(sa_objs),
                    result_type="sa_instances"
                )
                
                return sa_objs
            
            # Convert SA instances to domain entities
            mapping_start_time = time.perf_counter()
            result = []
            mapping_errors = 0
            
            self._repo_logger.debug_query_step(
                "domain_mapping_start",
                "Starting domain entity mapping",
                correlation_id=correlation_id,
                sa_instances_count=len(sa_objs),
                domain_model=self.domain_model_type.__name__
            )
            
            for i, obj in enumerate(sa_objs):
                entity_mapping_start = time.perf_counter()
                
                try:
                    domain_obj = self.data_mapper.map_sa_to_domain(obj)
                    self.refresh_seen(domain_obj)
                    result.append(domain_obj)
                    
                    entity_mapping_time = time.perf_counter() - entity_mapping_start
                    
                    # Log individual mapping for debugging (only for first few items)
                    if i < 5:  # Log details for first 5 mappings
                        self._repo_logger.debug_performance_detail(
                            "Entity mapped successfully",
                            correlation_id=correlation_id,
                            entity_index=i,
                            entity_id=getattr(domain_obj, 'id', 'unknown'),
                            mapping_time=entity_mapping_time
                        )
                        
                except Exception as e:
                    mapping_errors += 1
                    entity_mapping_time = time.perf_counter() - entity_mapping_start
                    
                    self._repo_logger.debug_query_step(
                        "entity_mapping_error",
                        "Entity mapping failed",
                        correlation_id=correlation_id,
                        entity_index=i,
                        sa_instance_type=type(obj).__name__,
                        mapping_time=entity_mapping_time,
                        error=str(e),
                        error_type=type(e).__name__
                    )
                    
                    raise EntityMappingException(
                        message=f"Failed to map SA instance to domain entity at index {i}",
                        repository=self,
                        sa_obj=obj,
                        mapping_direction="sa_to_domain",
                        correlation_id=correlation_id
                    ) from e
            
            mapping_time = time.perf_counter() - mapping_start_time
            total_time = time.perf_counter() - start_time
            
            # Log mapping completion summary
            self._repo_logger.debug_query_step(
                "domain_mapping_complete",
                "Domain entity mapping completed",
                correlation_id=correlation_id,
                mapped_entities=len(result),
                mapping_errors=mapping_errors,
                mapping_time=mapping_time,
                avg_mapping_time=mapping_time / len(sa_objs) if sa_objs else 0
            )
            
            # Performance warning for slow mapping
            if mapping_time > 1.0:
                self._repo_logger.warn_performance_issue(
                    "slow_mapping",
                    f"Domain mapping took {mapping_time:.2f} seconds for {len(sa_objs)} entities",
                    correlation_id=correlation_id,
                    mapping_time=mapping_time,
                    entity_count=len(sa_objs)
                )
            
            # Final execution summary
            self._repo_logger.debug_query_step(
                "execution_complete",
                "Statement execution completed successfully",
                correlation_id=correlation_id,
                total_time=total_time,
                execution_time=execution_time,
                mapping_time=mapping_time,
                result_count=len(result),
                result_type="domain_entities",
                seen_entities_count=len(self.seen)
            )
            
            return result
            
        except (RepositoryQueryException, EntityMappingException):
            # Re-raise our custom exceptions as-is
            raise
        except Exception as e:
            # Catch any other unexpected errors
            total_time = time.perf_counter() - start_time
            
            self._repo_logger.debug_query_step(
                "execution_error",
                "Unexpected error during statement execution",
                correlation_id=correlation_id,
                total_time=total_time,
                error=str(e),
                error_type=type(e).__name__,
                sql_query=sql_query
            )
            
            raise RepositoryQueryException(
                message=f"Unexpected error during statement execution: {str(e)}",
                repository=self,
                execution_time=total_time,
                correlation_id=correlation_id
            ) from e

    async def persist(
        self,
        domain_obj: E,
        *,
        ttl: int = 300,  # Optional TTL for future cache invalidation use
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
                sa_instance.discarded = True # type: ignore
            else:
                sa_instance = await self.data_mapper.map_domain_to_sa(
                    self._session, domain_obj
                )
            await self._session.merge(sa_instance)
        finally:
            self._session.autoflush = True
            await self._session.flush()
        self._invalidate_cache_for_entity(domain_obj, ttl=ttl)

    async def persist_all(self, domain_entities: list[E] | None = None, *, ttl: int = 300) -> None:
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
                sa_instance = await self.data_mapper.map_domain_to_sa(self._session, obj)
                sa_instance.discarded = True # type: ignore
            else:
                sa_instance = await self.data_mapper.map_domain_to_sa(self._session, obj)
            sa_instances.append(sa_instance)

        async with anyio.create_task_group() as tg:
            for obj in domain_entities:
                tg.start_soon(prepare_sa_instance, obj)

        for sa_instance in sa_instances:
            await self._session.merge(sa_instance)

        self._session.autoflush = True
        await self._session.flush()
        for entity in domain_entities:
            self._invalidate_cache_for_entity(entity, ttl=ttl)

    def _invalidate_cache_for_entity(self, entity: E, ttl: int = 300) -> None:
        """
        Placeholder for cache invalidation logic. Does nothing by default.
        In the future, this should remove or update cache entries affected by this entity.
        The ttl parameter is provided for future use (e.g., to delay or schedule invalidation).
        """
        # TODO: Implement cache invalidation using self.cache_backend
        pass

    async def query(
        self,
        *,
        filter: dict[str, Any] | None = None,
        starting_stmt: Select | None = None,
        sort_stmt: Callable | None = None,
        limit: int | None = None,
        already_joined: set[str] | None = None,
        sa_model: Type[S] | None = None,
        _return_sa_instance: bool = False,
    ) -> list[E]:
        """
        Retrieve a list of domain objects from the database based on the provided filter criteria.
        
        This method provides comprehensive error handling and timing for query operations.
        Enhanced with structured logging using RepositoryLogger throughout the entire pipeline.
        
        Args:
            filter: Dictionary of filter criteria
            starting_stmt: Optional pre-built SELECT statement
            sort_stmt: Optional custom sorting function
            limit: Maximum number of results to return
            already_joined: Set of already joined tables
            sa_model: SQLAlchemy model type for sorting context
            _return_sa_instance: Whether to return SA instances instead of domain entities
            
        Returns:
            List of domain entities or SA instances
            
        Raises:
            FilterValidationException: When invalid filters are provided
            JoinException: When join operations fail
            RepositoryQueryException: When query building or execution fails
            EntityMappingException: When entity mapping fails
        """
        # --- Caching Hook: Attempt to retrieve from cache before query execution ---
        cache_key = self._build_cache_key(
            filter=filter,
            starting_stmt=starting_stmt,
            sort_stmt=sort_stmt,
            limit=limit,
            already_joined=already_joined,
            sa_model=sa_model,
            _return_sa_instance=_return_sa_instance,
        )
        cached_result = self._get_from_cache(cache_key)
        if cached_result is not None:
            self._repo_logger.debug_query_step(
                "cache_hit",
                "Query result returned from cache",
                cache_key=cache_key
            )
            return cached_result
        # Use RepositoryLogger's track_query context manager for comprehensive tracking
        async with self._repo_logger.track_query(
            "repository_query",
            domain_model=self.domain_model_type.__name__,
            sa_model=self.sa_model_type.__name__,
            filter_count=len(filter) if filter else 0,
            has_starting_stmt=starting_stmt is not None,
            has_custom_sort=sort_stmt is not None,
            limit=limit,
            return_sa_instance=_return_sa_instance
        ) as context:
            
            try:
                # Log query parameters
                self._repo_logger.debug_query_step(
                    "query_start",
                    "Query operation started",
                    filter=filter,
                    limit=limit,
                    already_joined_count=len(already_joined) if already_joined else 0,
                    custom_sort_provided=sort_stmt is not None
                )
                
                # Build the query with comprehensive error handling
                query_build_start = time.perf_counter()
                
                try:
                    stmt = self._build_query(
                        filter=filter,
                        starting_stmt=starting_stmt,
                        sort_stmt=sort_stmt,
                        limit=limit,
                        already_joined=already_joined,
                        sa_model=sa_model,
                    )
                    
                    query_build_time = time.perf_counter() - query_build_start
                    context["query_build_time"] = query_build_time
                    
                    self._repo_logger.debug_query_step(
                        "query_build",
                        "Query built successfully",
                        query_build_time=query_build_time
                    )
                    
                except (FilterValidationException, JoinException) as e:
                    # These already have good context, just add correlation_id from logger
                    if hasattr(e, 'add_context'):
                        e.add_context("correlation_id", self._repo_logger.correlation_id)
                        e.add_context("query_build_time", time.perf_counter() - query_build_start)
                    context["error_type"] = type(e).__name__
                    context["error_during"] = "query_building"
                    raise
                except Exception as e:
                    build_time = time.perf_counter() - query_build_start
                    context["error_type"] = type(e).__name__
                    context["error_during"] = "query_building"
                    context["query_build_time"] = build_time
                    
                    self._repo_logger.debug_query_step(
                        "query_build_error",
                        "Query building failed with unexpected error",
                        error=str(e),
                        error_type=type(e).__name__,
                        query_build_time=build_time
                    )
                    
                    raise RepositoryQueryException(
                        message=f"Query building failed: {str(e)}",
                        repository=self,
                        filter_values=filter or {},
                        execution_time=build_time,
                        correlation_id=self._repo_logger.correlation_id
                    ) from e
                
                # Execute the query with error handling
                query_execution_start = time.perf_counter()
                
                try:
                    result = await self.execute_stmt(stmt, _return_sa_instance=_return_sa_instance)
                    # --- Caching Hook: Store result in cache after successful query ---
                    self._set_cache(self._build_cache_key(
                        filter=filter,
                        starting_stmt=starting_stmt,
                        sort_stmt=sort_stmt,
                        limit=limit,
                        already_joined=already_joined,
                        sa_model=sa_model,
                        _return_sa_instance=_return_sa_instance,
                    ), result)
                    query_execution_time = time.perf_counter() - query_execution_start
                    context["query_execution_time"] = query_execution_time
                    context["result_count"] = len(result)
                    context["result_type"] = "sa_instances" if _return_sa_instance else "domain_entities"
                    self._repo_logger.debug_query_step(
                        "query_complete",
                        "Query execution completed successfully",
                        query_execution_time=query_execution_time,
                        result_count=len(result),
                        result_type=context["result_type"]
                    )
                    return result
                    
                except RepositoryQueryException as e:
                    # Add correlation context to query execution errors
                    if hasattr(e, 'add_context'):
                        e.add_context("correlation_id", self._repo_logger.correlation_id)
                        e.add_context("total_query_time", time.perf_counter() - query_build_start)
                        if not e.filter_values:
                            e.filter_values = filter or {}
                    context["error_type"] = type(e).__name__
                    context["error_during"] = "query_execution"
                    raise
                except EntityMappingException as e:
                    # Add correlation context to mapping errors
                    if hasattr(e, 'add_context'):
                        e.add_context("correlation_id", self._repo_logger.correlation_id)
                        e.add_context("total_query_time", time.perf_counter() - query_build_start)
                    context["error_type"] = type(e).__name__
                    context["error_during"] = "entity_mapping"
                    raise
                except Exception as e:
                    execution_time = time.perf_counter() - query_execution_start
                    total_time = time.perf_counter() - query_build_start
                    context["error_type"] = type(e).__name__
                    context["error_during"] = "query_execution"
                    context["query_execution_time"] = execution_time
                    
                    self._repo_logger.debug_query_step(
                        "query_execution_error",
                        "Query execution failed with unexpected error",
                        error=str(e),
                        error_type=type(e).__name__,
                        query_execution_time=execution_time,
                        total_time=total_time
                    )
                    
                    raise RepositoryQueryException(
                        message=f"Query execution failed unexpectedly: {str(e)}",
                        repository=self,
                        filter_values=filter or {},
                        execution_time=total_time,
                        correlation_id=self._repo_logger.correlation_id
                    ) from e
                    
            except (FilterValidationException, JoinException, RepositoryQueryException, EntityMappingException):
                # Re-raise our custom exceptions as-is (they already have proper context)
                raise
            except Exception as e:
                # Final catch-all for truly unexpected errors
                context["error_type"] = type(e).__name__
                context["error_during"] = "unknown"
                
                self._repo_logger.debug_query_step(
                    "query_unexpected_error",
                    "Unexpected error in query method",
                    error=str(e),
                    error_type=type(e).__name__
                )
                
                raise RepositoryQueryException(
                    message=f"Unexpected repository error: {str(e)}",
                    repository=self,
                    filter_values=filter or {},
                    execution_time=time.perf_counter() - query_build_start,
                    correlation_id=self._repo_logger.correlation_id
                ) from e

    def _build_query(
        self,
        *,
        filter: dict[str, Any] | None = None,
        starting_stmt: Select | None = None,
        sort_stmt: Callable | None = None,
        limit: int | None = None,
        already_joined: set[str] | None = None,
        sa_model: Type[S] | None = None,
    ) -> Select:
        """
        Build the complete SQL query statement from the provided parameters.
        
        This method orchestrates the query building process by:
        1. Building the base SELECT statement
        2. Validating and applying filters (with automatic discarded handling)
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
        warnings.warn(
            "'_build_query' is an internal helper and its signature may change without notice. "
            "External code should call the public 'query' method instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        already_joined = already_joined or set()
        stmt = self._build_base_statement(starting_stmt, limit)
        
        # Always validate filters (even if None) to handle automatic discarded filtering
        processed_filter = self._validate_filters(filter or {})
        
        if processed_filter:
            stmt = self._apply_filters(stmt, processed_filter, already_joined)
            stmt = self._apply_sorting(stmt, processed_filter, sort_stmt, sa_model)
        
        return stmt 

    def _build_cache_key(
        self,
        filter: dict[str, Any] | None = None,
        starting_stmt: Select | None = None,
        sort_stmt: Callable | None = None,
        limit: int | None = None,
        already_joined: set[str] | None = None,
        sa_model: Type[S] | None = None,
        _return_sa_instance: bool = False,
    ) -> str:
        """
        Build a cache key based on query parameters. This is a simple stringification for demonstration.
        In production, use a more robust and collision-resistant approach.
        """
        # TODO: Replace with a more robust cache key builder as needed
        key_parts = [
            str(filter),
            str(starting_stmt),
            str(sort_stmt),
            str(limit),
            str(already_joined),
            str(sa_model),
            str(_return_sa_instance),
        ]
        return "|".join(key_parts)

    def _get_from_cache(self, cache_key: str) -> Any:
        """
        Placeholder for cache retrieval logic. Returns None by default.
        In the future, this should query the cache_backend for the given key.
        """
        # TODO: Implement cache lookup using self.cache_backend
        return None

    def _set_cache(self, cache_key: str, value: Any, ttl: int = 300) -> None:
        """
        Placeholder for cache set logic. Does nothing by default.
        In the future, this should store the value in cache_backend with the given key and TTL.
        """
        # TODO: Implement cache set using self.cache_backend
        pass 