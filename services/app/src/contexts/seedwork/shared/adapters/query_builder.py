from __future__ import annotations

from typing import Generic, TypeVar, Any, TYPE_CHECKING, Union, Optional, Sequence

from sqlalchemy import Select, select, ColumnElement, nulls_last
from sqlalchemy.ext.asyncio import AsyncSession

from src.contexts.seedwork.shared.domain.entity import Entity
from src.db.base import SaBase

if TYPE_CHECKING:
    from typing import Type
    from sqlalchemy.engine import Result
    from sqlalchemy.sql.elements import UnaryExpression
    from src.contexts.seedwork.shared.adapters.filter_operators import FilterOperator
    from src.contexts.seedwork.shared.adapters.mapper import ModelMapper

# Type variables with proper bounds
E = TypeVar("E", bound=Entity)
S = TypeVar("S", bound=SaBase)


class QueryBuilder(Generic[E, S]):
    """
    A generic query builder for constructing SQLAlchemy Select statements.
    
    This class provides a fluent interface for building complex database queries
    with proper type safety for both domain entities (E) and SQLAlchemy models (S).
    
    The QueryBuilder follows the builder pattern, allowing method chaining for
    constructing complex queries while maintaining type safety throughout the
    query construction process.
    
    Type Parameters:
        E: Domain entity type, must inherit from Entity
        S: SQLAlchemy model type, must inherit from SaBase
        
    Attributes:
        _session: Async SQLAlchemy session for database operations
        _sa_model_type: The SQLAlchemy model class to query
        _starting_stmt: Optional base Select statement to build upon
        _stmt: The current Select statement being built
        _already_joined: Set of joined table names to prevent duplicates
        
    Example:
        Basic usage:
        ```python
        from src.contexts.seedwork.shared.adapters.filter_operators import EqualsOperator, GreaterThanOperator
        
        builder = QueryBuilder[Product, ProductSaModel](
            session=db_session,
            sa_model_type=ProductSaModel
        )
        
        # Build a simple query
        query = (builder
                .select()
                .where(EqualsOperator(), ProductSaModel.name, "Apple")
                .where(GreaterThanOperator(), ProductSaModel.price, 100.0)
                .build())
        
        # Execute and get results
        results = await builder.execute()
        ```
        
        Advanced usage with joins:
        ```python
        builder = QueryBuilder[Product, ProductSaModel](
            session=db_session,
            sa_model_type=ProductSaModel
        )
        
        query = (builder
                .select()
                .join(CategorySaModel, ProductSaModel.category_id == CategorySaModel.id)
                .where(InOperator(), CategorySaModel.name, ["Electronics", "Books"])
                .order_by(ProductSaModel.created_at.desc())
                .limit(50)
                .build())
        ```
    """
    
    def __init__(
        self,
        session: AsyncSession,
        sa_model_type: "Type[S]",
        starting_stmt: Optional[Select] = None
    ) -> None:
        """
        Initialize the QueryBuilder with database session and model type.
        
        Args:
            session: Async SQLAlchemy session for database operations. This session
                    will be used to execute the final query.
            sa_model_type: The SQLAlchemy model class to query. This defines the
                          primary table for the query and provides type safety.
            starting_stmt: Optional base Select statement to build upon. If provided,
                          the builder will extend this statement rather than creating
                          a new one from scratch.
                          
        Example:
            ```python
            # Basic initialization
            builder = QueryBuilder[User, UserSaModel](
                session=db_session,
                sa_model_type=UserSaModel
            )
            
            # With starting statement
            base_stmt = select(UserSaModel).where(UserSaModel.active == True)
            builder = QueryBuilder[User, UserSaModel](
                session=db_session,
                sa_model_type=UserSaModel,
                starting_stmt=base_stmt
            )
            ```
        """
        self._session: AsyncSession = session
        self._sa_model_type: "Type[S]" = sa_model_type
        self._starting_stmt: Optional[Select] = starting_stmt
        self._stmt: Optional[Select] = None
        self._already_joined: set[str] = set()
    
    def select(self) -> "QueryBuilder[E, S]":
        """
        Create or initialize the base Select statement for the query.
        
        This method establishes the foundation of the SQL query by either using
        the provided starting_stmt or creating a new Select statement from the
        SQLAlchemy model type.
        
        Returns:
            QueryBuilder[E, S]: Returns self to enable method chaining.
            
        Raises:
            ValueError: If called multiple times on the same builder instance.
            
        Example:
            ```python
            # Basic select
            builder = QueryBuilder[Product, ProductSaModel](session, ProductSaModel)
            query = builder.select().build()
            # Results in: SELECT * FROM products
            
            # With starting statement
            base_stmt = select(ProductSaModel).where(ProductSaModel.active == True)
            builder = QueryBuilder[Product, ProductSaModel](
                session, ProductSaModel, starting_stmt=base_stmt
            )
            query = builder.select().build()
            # Results in: SELECT * FROM products WHERE products.active = true
            ```
            
        Note:
            This method should be called first in the method chain, as it
            establishes the base query that other methods will modify.
        """
        if self._stmt is not None:
            raise ValueError("select() has already been called on this QueryBuilder instance")
        
        if self._starting_stmt is not None:
            # Use the provided starting statement
            self._stmt = self._starting_stmt
        else:
            # Create a new select statement from the model type
            self._stmt = select(self._sa_model_type)
        
        return self
    
    def where(
        self, 
        operator: "FilterOperator", 
        column: ColumnElement[Any], 
        value: Any
    ) -> "QueryBuilder[E, S]":
        """
        Add a WHERE clause condition to the query using a FilterOperator.
        
        This method applies a filter condition to the current Select statement
        using the Strategy pattern with FilterOperator instances. Multiple where()
        calls are combined with AND logic.
        
        Args:
            operator: A FilterOperator instance that defines how to apply the filter.
                     Examples: EqualsOperator(), GreaterThanOperator(), InOperator()
            column: The database column to filter on. Should be a SQLAlchemy
                   ColumnElement like ProductSaModel.name or CategorySaModel.id
            value: The value to compare against. Type depends on the operator
                  and column type.
                  
        Returns:
            QueryBuilder[E, S]: Returns self to enable method chaining.
            
        Raises:
            ValueError: If select() has not been called first, or if the operator
                       raises a ValueError for incompatible values.
            TypeError: If the operator raises a TypeError for incompatible types.
            
        Example:
            ```python
            from src.contexts.seedwork.shared.adapters.filter_operators import (
                EqualsOperator, GreaterThanOperator, InOperator
            )
            
            # Single condition
            builder = (QueryBuilder[Product, ProductSaModel](session, ProductSaModel)
                      .select()
                      .where(EqualsOperator(), ProductSaModel.name, "Apple"))
            
            # Multiple conditions (AND logic)
            builder = (QueryBuilder[Product, ProductSaModel](session, ProductSaModel)
                      .select()
                      .where(EqualsOperator(), ProductSaModel.category, "Electronics")
                      .where(GreaterThanOperator(), ProductSaModel.price, 100.0)
                      .where(InOperator(), ProductSaModel.tags, ["premium", "popular"]))
            
            # Results in: SELECT * FROM products 
            #            WHERE products.category = 'Electronics' 
            #              AND products.price >= 100.0 
            #              AND products.tags IN ('premium', 'popular')
            ```
            
        Note:
            The FilterOperator handles all the logic for applying the condition,
            including proper NULL handling, type coercion, and SQL generation.
            This ensures consistent behavior with the existing repository patterns.
        """
        if self._stmt is None:
            raise ValueError("select() must be called before where(). Call .select() first to initialize the query.")
        
        # Import at runtime to avoid circular imports
        from src.contexts.seedwork.shared.adapters.filter_operators import FilterOperator
        
        if not isinstance(operator, FilterOperator):
            raise TypeError(f"operator must be a FilterOperator instance, got {type(operator)}")
        
        # Apply the filter operator to the current statement
        self._stmt = operator.apply(self._stmt, column, value)
        
        return self
    
    def join(
        self,
        target: "Type[SaBase]",
        on_clause: ColumnElement[bool]
    ) -> "QueryBuilder[E, S]":
        """
        Add a JOIN clause to the query with automatic duplicate join detection.
        
        This method adds a table join to the current Select statement while
        automatically preventing duplicate joins using set-based tracking.
        The duplicate detection uses the same logic as the existing repository
        implementation to ensure compatibility.
        
        Args:
            target: The SQLAlchemy model class to join to. Must inherit from SaBase.
            on_clause: The join condition as a SQLAlchemy ColumnElement[bool].
                      Example: ProductSaModel.category_id == CategorySaModel.id
                      
        Returns:
            QueryBuilder[E, S]: Returns self to enable method chaining.
            
        Raises:
            ValueError: If select() has not been called first.
            TypeError: If target is not a SQLAlchemy model class.
            
        Example:
            ```python
            # Simple join
            builder = (QueryBuilder[Product, ProductSaModel](session, ProductSaModel)
                      .select()
                      .join(CategorySaModel, ProductSaModel.category_id == CategorySaModel.id)
                      .where(EqualsOperator(), CategorySaModel.name, "Electronics"))
            
            # Multiple joins (duplicates automatically prevented)
            builder = (QueryBuilder[Product, ProductSaModel](session, ProductSaModel)
                      .select()
                      .join(CategorySaModel, ProductSaModel.category_id == CategorySaModel.id)
                      .join(BrandSaModel, ProductSaModel.brand_id == BrandSaModel.id)
                      .join(CategorySaModel, ProductSaModel.category_id == CategorySaModel.id)  # Ignored - duplicate
                      .where(EqualsOperator(), CategorySaModel.name, "Electronics")
                      .where(EqualsOperator(), BrandSaModel.name, "Apple"))
            
            # Results in: SELECT * FROM products 
            #            JOIN categories ON products.category_id = categories.id
            #            JOIN brands ON products.brand_id = brands.id
            #            WHERE categories.name = 'Electronics' AND brands.name = 'Apple'
            ```
            
        Note:
            The duplicate detection uses string representation of the target class,
            matching the existing repository behavior: str(target) not in already_joined.
            This ensures backward compatibility with existing join logic.
        """
        if self._stmt is None:
            raise ValueError("select() must be called before join(). Call .select() first to initialize the query.")
        
        if not issubclass(target, SaBase):
            raise TypeError(f"target must be a SQLAlchemy model class inheriting from SaBase, got {type(target)}")
        
        # Use the same duplicate detection logic as existing repository
        target_key = str(target)
        
        if target_key not in self._already_joined:
            # Add the join to the statement
            self._stmt = self._stmt.join(target, on_clause)
            # Track the join to prevent duplicates
            self._already_joined.add(target_key)
        
        return self
    
    def order_by(
        self,
        column: Union[ColumnElement[Any], str],
        descending: bool = False,
        nulls_last_order: bool = True
    ) -> "QueryBuilder[E, S]":
        """
        Add an ORDER BY clause to the query with optional descending order and nulls handling.
        
        This method adds sorting to the current Select statement, with support for both
        ascending and descending order. By default, NULL values are ordered last using
        SQLAlchemy's nulls_last() function, matching the existing repository behavior.
        
        Args:
            column: The column to sort by. Can be either:
                   - A SQLAlchemy ColumnElement (e.g., ProductSaModel.name)
                   - A string column name (for convenience, though ColumnElement is preferred)
            descending: Whether to sort in descending order. Defaults to False (ascending).
            nulls_last_order: Whether to place NULL values last. Defaults to True to match
                            existing repository behavior.
                            
        Returns:
            QueryBuilder[E, S]: Returns self to enable method chaining.
            
        Raises:
            ValueError: If select() has not been called first.
            
        Example:
            ```python
            # Ascending order (default)
            builder = (QueryBuilder[Product, ProductSaModel](session, ProductSaModel)
                      .select()
                      .order_by(ProductSaModel.name))
            
            # Descending order
            builder = (QueryBuilder[Product, ProductSaModel](session, ProductSaModel)
                      .select()
                      .order_by(ProductSaModel.created_at, descending=True))
            
            # Multiple order by clauses
            builder = (QueryBuilder[Product, ProductSaModel](session, ProductSaModel)
                      .select()
                      .order_by(ProductSaModel.category)
                      .order_by(ProductSaModel.price, descending=True))
            
            # Results in: SELECT * FROM products 
            #            ORDER BY products.category ASC NULLS LAST,
            #                     products.price DESC NULLS LAST
            
            # With joins
            builder = (QueryBuilder[Product, ProductSaModel](session, ProductSaModel)
                      .select()
                      .join(CategorySaModel, ProductSaModel.category_id == CategorySaModel.id)
                      .where(EqualsOperator(), CategorySaModel.name, "Electronics")
                      .order_by(CategorySaModel.sort_order)
                      .order_by(ProductSaModel.name))
            ```
            
        Note:
            This method uses SQLAlchemy's nulls_last() function by default to ensure
            consistent ordering behavior with NULL values, matching the existing
            repository implementation. Multiple order_by() calls are cumulative,
            allowing for multi-column sorting.
        """
        if self._stmt is None:
            raise ValueError("select() must be called before order_by(). Call .select() first to initialize the query.")
        
        # Handle string column names by getting the attribute from the model
        if isinstance(column, str):
            column_element = getattr(self._sa_model_type, column)
        else:
            column_element = column
        
        # Apply descending order if requested
        if descending:
            column_element = column_element.desc()
        
        # Apply nulls_last if requested (default behavior to match existing repository)
        if nulls_last_order:
            column_element = nulls_last(column_element)
        
        # Add the ORDER BY clause
        self._stmt = self._stmt.order_by(column_element)
        
        return self
    
    def limit(self, limit_value: int) -> "QueryBuilder[E, S]":
        """
        Add a LIMIT clause to the query with proper validation.
        
        This method applies a limit to the number of results returned by the query.
        The limit must be greater than 0 to be valid, following SQL conventions
        and preventing potentially expensive unbounded queries.
        
        Args:
            limit_value: The maximum number of rows to return. Must be greater than 0.
                        
        Returns:
            QueryBuilder[E, S]: Returns self to enable method chaining.
            
        Raises:
            ValueError: If select() has not been called first, or if limit_value <= 0.
            TypeError: If limit_value is not an integer.
            
        Example:
            ```python
            # Basic limit
            builder = (QueryBuilder[Product, ProductSaModel](session, ProductSaModel)
                      .select()
                      .where(EqualsOperator(), ProductSaModel.category, "Electronics")
                      .limit(10))
            
            # With pagination (limit + offset)
            builder = (QueryBuilder[Product, ProductSaModel](session, ProductSaModel)
                      .select()
                      .order_by(ProductSaModel.name)
                      .limit(20)
                      .offset(40))  # Skip first 40, take next 20
            
            # Results in: SELECT * FROM products 
            #            WHERE products.category = 'Electronics'
            #            ORDER BY products.name ASC NULLS LAST
            #            LIMIT 20 OFFSET 40
            ```
            
        Note:
            This method should typically be used in conjunction with order_by()
            to ensure consistent results across multiple queries, especially when
            implementing pagination patterns.
        """
        if self._stmt is None:
            raise ValueError("select() must be called before limit(). Call .select() first to initialize the query.")
        
        if not isinstance(limit_value, int):
            raise TypeError(f"limit_value must be an integer, got {type(limit_value)}")
        
        if limit_value <= 0:
            raise ValueError(f"limit_value must be greater than 0, got {limit_value}")
        
        # Apply the LIMIT clause
        self._stmt = self._stmt.limit(limit_value)
        
        return self
    
    def offset(self, offset_value: int) -> "QueryBuilder[E, S]":
        """
        Add an OFFSET clause to the query with proper validation.
        
        This method applies an offset to skip a specified number of rows before
        returning results. The offset must be greater than or equal to 0, with
        0 meaning no rows are skipped.
        
        Args:
            offset_value: The number of rows to skip. Must be greater than or equal to 0.
                         A value of 0 means no offset (start from the first row).
                        
        Returns:
            QueryBuilder[E, S]: Returns self to enable method chaining.
            
        Raises:
            ValueError: If select() has not been called first, or if offset_value < 0.
            TypeError: If offset_value is not an integer.
            
        Example:
            ```python
            # Basic offset (skip first 10 rows)
            builder = (QueryBuilder[Product, ProductSaModel](session, ProductSaModel)
                      .select()
                      .order_by(ProductSaModel.created_at, descending=True)
                      .offset(10))
            
            # Pagination pattern with limit and offset
            page_size = 25
            page_number = 3  # 1-based page numbering
            offset_value = (page_number - 1) * page_size  # 50
            
            builder = (QueryBuilder[Product, ProductSaModel](session, ProductSaModel)
                      .select()
                      .where(EqualsOperator(), ProductSaModel.active, True)
                      .order_by(ProductSaModel.name)
                      .limit(page_size)
                      .offset(offset_value))
            
            # Results in: SELECT * FROM products 
            #            WHERE products.active = true
            #            ORDER BY products.name ASC NULLS LAST
            #            LIMIT 25 OFFSET 50
            
            # No offset (equivalent to not calling offset)
            builder = (QueryBuilder[Product, ProductSaModel](session, ProductSaModel)
                      .select()
                      .offset(0))  # Same as no offset
            ```
            
        Note:
            OFFSET should typically be used with ORDER BY to ensure consistent
            results across queries. Without ordering, the same offset might return
            different rows on subsequent queries. When implementing pagination,
            always combine with limit() for proper page-based navigation.
        """
        if self._stmt is None:
            raise ValueError("select() must be called before offset(). Call .select() first to initialize the query.")
        
        if not isinstance(offset_value, int):
            raise TypeError(f"offset_value must be an integer, got {type(offset_value)}")
        
        if offset_value < 0:
            raise ValueError(f"offset_value must be greater than or equal to 0, got {offset_value}")
        
        # Apply the OFFSET clause
        self._stmt = self._stmt.offset(offset_value)
        
        return self
    
    def distinct(self) -> "QueryBuilder[E, S]":
        """
        Add a DISTINCT clause to the query to eliminate duplicate rows.
        
        This method applies DISTINCT to the current Select statement, which is
        particularly useful when dealing with list-based filters or complex joins
        that might produce duplicate rows. DISTINCT ensures that each row in the
        result set is unique.
        
        Returns:
            QueryBuilder[E, S]: Returns self to enable method chaining.
            
        Raises:
            ValueError: If select() has not been called first.
            
        Example:
            ```python
            # Basic distinct query
            builder = (QueryBuilder[Product, ProductSaModel](session, ProductSaModel)
                      .select()
                      .distinct()
                      .where(EqualsOperator(), ProductSaModel.category, "Electronics"))
            
            # With joins (prevents duplicates from join operations)
            builder = (QueryBuilder[Product, ProductSaModel](session, ProductSaModel)
                      .select()
                      .distinct()
                      .join(TagSaModel, ProductSaModel.id == TagSaModel.product_id)
                      .where(InOperator(), TagSaModel.name, ["premium", "popular"]))
            
            # Results in: SELECT DISTINCT products.* FROM products 
            #            JOIN tags ON products.id = tags.product_id
            #            WHERE tags.name IN ('premium', 'popular')
            
            # With list-based filters that might create duplicates
            builder = (QueryBuilder[Product, ProductSaModel](session, ProductSaModel)
                      .select()
                      .distinct()
                      .join(CategorySaModel, ProductSaModel.category_id == CategorySaModel.id)
                      .join(TagSaModel, ProductSaModel.id == TagSaModel.product_id)
                      .where(InOperator(), CategorySaModel.name, ["Electronics", "Books"])
                      .where(InOperator(), TagSaModel.name, ["new", "featured"]))
            
            # Without distinct, this query might return the same product multiple times
            # if it has multiple matching tags or categories
            ```
            
        Note:
            DISTINCT should be used carefully as it can impact query performance,
            especially on large result sets. It's most beneficial when dealing with:
            - JOIN operations that might create cartesian products
            - List-based filters (IN operations) across multiple related tables
            - Complex queries where the same entity might match multiple conditions
            
            The distinct() method can be called at any point in the method chain
            after select(), and it will apply to the entire result set.
        """
        if self._stmt is None:
            raise ValueError("select() must be called before distinct(). Call .select() first to initialize the query.")
        
        # Apply the DISTINCT clause to the statement
        self._stmt = self._stmt.distinct()
        
        return self

    def build(self) -> Select:
        """
        Build and return the final Select statement with all applied operations.
        
        This method completes the query construction process and returns the
        finalized SQLAlchemy Select statement that can be executed against
        the database. It validates that the builder has been properly initialized
        and returns the statement with all previously applied operations
        (WHERE clauses, JOINs, ORDER BY, LIMIT, OFFSET, DISTINCT).
        
        Returns:
            Select: The final SQLAlchemy Select statement ready for execution.
            
        Raises:
            ValueError: If select() has not been called first to initialize the query.
            
        Example:
            ```python
            from src.contexts.seedwork.shared.adapters.filter_operators import EqualsOperator, InOperator
            
            # Build a complete query
            builder = QueryBuilder[Product, ProductSaModel](
                session=db_session,
                sa_model_type=ProductSaModel
            )
            
            query = (builder
                    .select()
                    .where(EqualsOperator(), ProductSaModel.active, True)
                    .join(CategorySaModel, ProductSaModel.category_id == CategorySaModel.id)
                    .where(InOperator(), CategorySaModel.name, ["Electronics", "Books"])
                    .order_by(ProductSaModel.name)
                    .limit(50)
                    .offset(0)
                    .distinct()
                    .build())
            
            # The returned Select statement can be executed
            result = await session.execute(query)
            sa_entities = result.scalars().all()
            
            # Or used as a starting statement for another QueryBuilder
            extended_builder = QueryBuilder[Product, ProductSaModel](
                session=db_session,
                sa_model_type=ProductSaModel,
                starting_stmt=query
            )
            ```
            
        Note:
            The build() method is the final step in the fluent interface chain.
            After calling build(), the QueryBuilder should not be modified further.
            The returned Select statement contains all applied filters, joins,
            sorting, pagination, and distinct operations in the order they were
            applied to the builder.
            
            The built statement is ready for execution using AsyncSession.execute()
            or can be used as a starting statement for more complex query composition.
        """
        if self._stmt is None:
            raise ValueError("select() must be called before build(). Call .select() first to initialize the query.")
        
        # Return the finalized Select statement
        return self._stmt

    async def execute(
        self,
        data_mapper: Optional["ModelMapper"] = None,
        _return_sa_instance: bool = False
    ) -> Union[list[E], list[S]]:
        """
        Execute the built query and return a list of domain entities or SA instances.
        
        This method executes the constructed Select statement against the database
        using the AsyncSession and converts the results to domain entities using
        the provided data mapper. It follows the same pattern as the existing
        SaGenericRepository.execute_stmt method.
        
        Args:
            data_mapper: Optional ModelMapper instance for converting SA entities
                        to domain entities. If not provided and _return_sa_instance
                        is False, an error will be raised.
            _return_sa_instance: If True, returns raw SQLAlchemy instances instead
                               of domain entities. Defaults to False.
                               
        Returns:
            list[E] | list[S]: List of domain entities (E) if data_mapper is provided
                              and _return_sa_instance is False, otherwise list of
                              SQLAlchemy instances (S).
                              
        Raises:
            ValueError: If select() has not been called first, or if data_mapper
                       is None and _return_sa_instance is False.
            RuntimeError: If database execution fails or mapping fails.
            
        Example:
            ```python
            from src.contexts.seedwork.shared.adapters.filter_operators import EqualsOperator
            from src.contexts.products_catalog.core.adapters.ORM.mappers.product_mapper import ProductMapper
            
            # Execute with domain entity mapping
            builder = QueryBuilder[Product, ProductSaModel](
                session=db_session,
                sa_model_type=ProductSaModel
            )
            
            products: list[Product] = await (builder
                                           .select()
                                           .where(EqualsOperator(), ProductSaModel.active, True)
                                           .limit(10)
                                           .execute(data_mapper=ProductMapper()))
            
            # Execute and return SA instances only
            sa_products: list[ProductSaModel] = await (builder
                                                     .select()
                                                     .where(EqualsOperator(), ProductSaModel.active, True)
                                                     .limit(10)
                                                     .execute(_return_sa_instance=True))
            
            # Build and execute separately
            query = builder.select().where(EqualsOperator(), ProductSaModel.active, True).build()
            products = await builder.execute(data_mapper=ProductMapper())
            ```
            
        Note:
            This method should be called after build() or as the final step in the
            method chain. It will automatically call build() if the statement hasn't
            been finalized yet.
            
            The data_mapper parameter enables the QueryBuilder to work independently
            from repositories while maintaining compatibility with the existing
            repository patterns that require domain entity conversion.
            
            Error handling follows the same patterns as SaGenericRepository to
            maintain consistency across the codebase.
        """
        if self._stmt is None:
            raise ValueError("select() must be called before execute(). Call .select() first to initialize the query.")
        
        if not _return_sa_instance and data_mapper is None:
            raise ValueError("data_mapper must be provided when _return_sa_instance is False")
        
        try:
            # Execute the query against the database
            result = await self._session.execute(self._stmt)
            sa_objs: list[S] = list(result.scalars().all())
            
            # If returning SA instances directly, no mapping needed
            if _return_sa_instance:
                return sa_objs
            
            # Convert SA instances to domain entities using the data mapper
            # At this point, we know data_mapper is not None due to the validation above
            assert data_mapper is not None, "data_mapper should not be None at this point"
            
            domain_entities: list[E] = []
            for sa_obj in sa_objs:
                domain_obj: E = data_mapper.map_sa_to_domain(sa_obj)
                domain_entities.append(domain_obj)
            
            return domain_entities
            
        except Exception as e:
            # Re-raise with context for better debugging
            raise RuntimeError(f"Query execution failed: {str(e)}") from e