from __future__ import annotations

import abc
from typing import Any

from sqlalchemy import Select, ColumnElement
from sqlalchemy.sql import operators
from sqlalchemy.sql.expression import ColumnOperators


class FilterOperator(abc.ABC):
    """
    Abstract base class for all filter operators used in query building.
    
    Filter operators encapsulate the logic for applying specific comparison
    operations to SQLAlchemy Select statements. Each operator implements
    the apply() method to modify a Select statement with the appropriate
    WHERE clause condition.
    
    This follows the Strategy pattern, allowing different filter operations
    to be applied uniformly while maintaining type safety and enabling
    easy extension with new operators.
    
    Examples:
        Basic operator usage:
        ```python
        # Create an equals operator
        equals_op = EqualsOperator()
        
        # Apply to a query
        stmt = select(ProductSaModel)
        filtered_stmt = equals_op.apply(stmt, ProductSaModel.name, "Apple")
        # Results in: SELECT * FROM products WHERE products.name = 'Apple'
        ```
        
        Chaining multiple operators:
        ```python
        stmt = select(ProductSaModel)
        stmt = EqualsOperator().apply(stmt, ProductSaModel.category, "Electronics")
        stmt = GreaterThanOperator().apply(stmt, ProductSaModel.price, 100.0)
        # Results in: SELECT * FROM products WHERE products.category = 'Electronics' AND products.price > 100.0
        ```
        
        Using with QueryBuilder:
        ```python
        builder = QueryBuilder[Product, ProductSaModel](session, ProductSaModel)
        query = (builder
                .select()
                .where(EqualsOperator().apply(stmt, ProductSaModel.name, "Apple"))
                .where(InOperator().apply(stmt, ProductSaModel.tags, ["organic", "fresh"]))
                .build())
        ```
    """
    
    @abc.abstractmethod
    def apply(self, stmt: Select, column: ColumnElement, value: Any) -> Select:
        """
        Apply the filter operation to a SQLAlchemy Select statement.
        
        This method takes a Select statement and modifies it by adding
        a WHERE clause condition based on the specific operator logic.
        The column parameter specifies which database column to filter on,
        and the value parameter provides the comparison value.
        
        Args:
            stmt: The SQLAlchemy Select statement to modify. This statement
                 will have a WHERE clause condition added to it.
            column: The database column to apply the filter to. This should
                   be a SQLAlchemy ColumnElement (e.g., ProductSaModel.name).
            value: The value to compare against. The type and format of this
                  value depends on the specific operator implementation.
                  
        Returns:
            Select: A new Select statement with the filter condition applied.
                   The original statement is not modified.
                   
        Raises:
            ValueError: If the value is not compatible with the operator
                       (e.g., None for operators that don't support null values).
            TypeError: If the column or value types are incompatible with
                      the operator's requirements.
                      
        Example:
            ```python
            class EqualsOperator(FilterOperator):
                def apply(self, stmt: Select, column: ColumnElement, value: Any) -> Select:
                    if value is None:
                        return stmt.where(column.is_(None))
                    return stmt.where(column == value)
            
            # Usage
            operator = EqualsOperator()
            filtered_stmt = operator.apply(
                select(ProductSaModel),
                ProductSaModel.name,
                "Apple"
            )
            ```
            
        Note:
            Implementations should handle None values appropriately,
            as database NULL comparisons require special handling in SQL.
        """
        pass


class EqualsOperator(FilterOperator):
    """
    Filter operator for equality comparisons.
    
    Handles both regular equality comparisons and NULL value comparisons
    using the appropriate SQL operators (= vs IS NULL).
    
    Examples:
        ```python
        # Regular equality
        operator = EqualsOperator()
        stmt = operator.apply(select(User), User.name, "John")
        # Results in: WHERE user.name = 'John'
        
        # NULL comparison
        stmt = operator.apply(select(User), User.middle_name, None)
        # Results in: WHERE user.middle_name IS NULL
        
        # Boolean comparison
        stmt = operator.apply(select(User), User.active, True)
        # Results in: WHERE user.active IS true
        ```
    """
    
    def apply(self, stmt: Select, column: ColumnElement, value: Any) -> Select:
        """Apply equality filter to the statement."""
        if value is None:
            return stmt.where(column.is_(None))
        elif isinstance(value, bool):
            # Use IS for boolean comparisons as per existing logic
            return stmt.where(column.is_(value))
        else:
            return stmt.where(column == value)


class GreaterThanOperator(FilterOperator):
    """
    Filter operator for greater than comparisons (_gte postfix).
    
    Examples:
        ```python
        operator = GreaterThanOperator()
        stmt = operator.apply(select(Product), Product.price, 100.0)
        # Results in: WHERE product.price >= 100.0
        ```
    """
    
    def apply(self, stmt: Select, column: ColumnElement, value: Any) -> Select:
        """Apply greater than or equal filter to the statement."""
        if value is None:
            raise ValueError("GreaterThanOperator does not support None values")
        return stmt.where(operators.ge(column, value))


class LessThanOperator(FilterOperator):
    """
    Filter operator for less than or equal comparisons (_lte postfix).
    
    Examples:
        ```python
        operator = LessThanOperator()
        stmt = operator.apply(select(Product), Product.price, 50.0)
        # Results in: WHERE product.price <= 50.0
        ```
    """
    
    def apply(self, stmt: Select, column: ColumnElement, value: Any) -> Select:
        """Apply less than or equal filter to the statement."""
        if value is None:
            raise ValueError("LessThanOperator does not support None values")
        return stmt.where(operators.le(column, value))


class NotEqualsOperator(FilterOperator):
    """
    Filter operator for not equals comparisons (_ne postfix).
    
    Uses standard SQL != behavior which excludes NULL values from results.
    
    Examples:
        ```python
        operator = NotEqualsOperator()
        stmt = operator.apply(select(User), User.status, "inactive")
        # Results in: WHERE user.status != 'inactive'
        ```
    """
    
    def apply(self, stmt: Select, column: ColumnElement, value: Any) -> Select:
        """Apply not equals filter to the statement."""
        if value is None:
            return stmt.where(column.is_not(None))
        return stmt.where(operators.ne(column, value))


class InOperator(FilterOperator):
    """
    Filter operator for IN list comparisons.
    
    Used when filtering by a list/set of values or when the column type is list.
    
    Examples:
        ```python
        operator = InOperator()
        stmt = operator.apply(select(Product), Product.category, ["Electronics", "Books"])
        # Results in: WHERE product.category IN ('Electronics', 'Books')
        ```
    """
    
    def apply(self, stmt: Select, column: ColumnElement, value: Any) -> Select:
        """Apply IN filter to the statement."""
        if not isinstance(value, (list, set, tuple)):
            raise TypeError(f"InOperator requires a list, set, or tuple, got {type(value)}")
        if not value:
            # Empty list should return a condition that matches nothing
            # This is valid SQL and allows the query to continue without error
            return stmt.where(column.in_([]))
        return stmt.where(column.in_(value))


class NotInOperator(FilterOperator):
    """
    Filter operator for NOT IN list comparisons (_not_in postfix).
    
    Handles the special case where NULL values should be included in the result,
    following the existing repository logic.
    
    Examples:
        ```python
        operator = NotInOperator()
        stmt = operator.apply(select(Product), Product.category, ["Electronics", "Books"])
        # Results in: WHERE (product.category IS NULL OR product.category NOT IN ('Electronics', 'Books'))
        ```
    """
    
    def apply(self, stmt: Select, column: ColumnElement, value: Any) -> Select:
        """Apply NOT IN filter to the statement with NULL handling."""
        if not isinstance(value, (list, set, tuple)):
            raise TypeError(f"NotInOperator requires a list, set, or tuple, got {type(value)}")
        if not value:
            # Empty list for NOT IN should return all rows (no filtering)
            return stmt
        
        # Use the same logic as existing repository: include NULL values
        return stmt.where(
            (column.is_(None)) | (~column.in_(value))
        )


class ContainsOperator(FilterOperator):
    """
    Filter operator for array/list contains operations.
    
    Used for PostgreSQL array columns or JSON array contains operations.
    
    Examples:
        ```python
        operator = ContainsOperator()
        stmt = operator.apply(select(Product), Product.tags, "organic")
        # Results in: WHERE product.tags @> ['organic'] (PostgreSQL array contains)
        ```
    """
    
    def apply(self, stmt: Select, column: ColumnElement, value: Any) -> Select:
        """Apply contains filter to the statement."""
        return stmt.where(operators.contains(column, value))


class IsNotOperator(FilterOperator):
    """
    Filter operator for IS NOT comparisons (_is_not postfix).
    
    Used primarily for NULL and boolean comparisons.
    
    Examples:
        ```python
        operator = IsNotOperator()
        stmt = operator.apply(select(User), User.deleted_at, None)
        # Results in: WHERE user.deleted_at IS NOT NULL
        ```
    """
    
    def apply(self, stmt: Select, column: ColumnElement, value: Any) -> Select:
        """Apply IS NOT filter to the statement."""
        return stmt.where(operators.is_not(column, value))


class FilterOperatorFactory:
    """
    Factory class for creating and managing filter operators.
    
    This class provides a registry of filter operators that can be looked up
    by filter name, column type, and value type. It follows the Factory pattern
    to encapsulate operator creation logic and enable easy extension.
    
    The factory automatically handles the filter postfix logic from the existing
    repository implementation (_gte, _lte, _ne, etc.) and provides fallback
    logic based on value types and column types.
    
    Examples:
        Basic usage:
        ```python
        factory = FilterOperatorFactory()
        
        # Get operator for equals
        operator = factory.get_operator("name", str, "John")
        # Returns: EqualsOperator()
        
        # Get operator for greater than
        operator = factory.get_operator("price_gte", float, 100.0)
        # Returns: GreaterThanOperator()
        
        # Get operator for list filtering
        operator = factory.get_operator("categories", list, ["Electronics", "Books"])
        # Returns: InOperator()
        ```
        
        Custom operator registration:
        ```python
        factory = FilterOperatorFactory()
        factory.register_operator("_custom", CustomOperator())
        
        operator = factory.get_operator("field_custom", str, "value")
        # Returns: CustomOperator()
        ```
    """
    
    def __init__(self):
        """Initialize the factory with default operators registered."""
        self._operators: dict[str, FilterOperator] = {}
        self._register_default_operators()
    
    def _register_default_operators(self) -> None:
        """Register all default filter operators with their postfix patterns."""
        # Postfix-based operators (match existing repository ALLOWED_POSTFIX)
        self.register_operator("_gte", GreaterThanOperator())
        self.register_operator("_lte", LessThanOperator())
        self.register_operator("_ne", NotEqualsOperator())
        self.register_operator("_not_in", NotInOperator())
        self.register_operator("_is_not", IsNotOperator())
        
        # Default operators (no postfix)
        self.register_operator("", EqualsOperator())  # Default fallback
        self.register_operator("_eq", EqualsOperator())  # Explicit equals
        self.register_operator("_in", InOperator())
        self.register_operator("_contains", ContainsOperator())
    
    def register_operator(self, filter_name: str, operator: FilterOperator) -> None:
        """
        Register a filter operator with a specific filter name pattern.
        
        Args:
            filter_name: The filter pattern to match (e.g., "_gte", "_eq", "").
                        Use empty string for default/fallback operator.
            operator: The FilterOperator instance to register.
            
        Example:
            ```python
            factory = FilterOperatorFactory()
            factory.register_operator("_custom", CustomOperator())
            ```
        """
        self._operators[filter_name] = operator
    
    def get_operator(
        self, 
        filter_name: str, 
        column_type: type, 
        value: Any
    ) -> FilterOperator:
        """
        Get the appropriate filter operator for the given filter criteria.
        
        This method implements the same logic as the existing repository's
        _filter_operator_selection method, but using the new operator classes.
        
        Args:
            filter_name: The full filter field name (e.g., "price_gte", "name")
            column_type: The Python type of the database column
            value: The filter value being applied
            
        Returns:
            FilterOperator: The appropriate operator for the filter criteria
            
        Raises:
            ValueError: If no suitable operator can be found
            
        Example:
            ```python
            factory = FilterOperatorFactory()
            
            # Postfix-based operator
            op = factory.get_operator("price_gte", float, 100.0)
            # Returns: GreaterThanOperator()
            
            # List value detection
            op = factory.get_operator("categories", str, ["Electronics", "Books"])
            # Returns: InOperator()
            
            # Column type detection
            op = factory.get_operator("tags", list, "organic")
            # Returns: ContainsOperator()
            ```
        """
        # Check for postfix-based operators first (exact match with existing logic)
        for postfix in ["_gte", "_lte", "_ne", "_not_in", "_is_not"]:
            if filter_name.endswith(postfix):
                return self._operators[postfix]
        
        # Check if value is a list/set (existing repository logic)
        if isinstance(value, (list, set)):
            return self._operators["_in"]
        
        # Check column type for special handling (existing repository logic)
        if column_type == list:
            return self._operators["_contains"]
        
        if column_type == bool:
            # Boolean values use special handling in existing repository
            return self._operators[""]  # EqualsOperator with special bool logic
        
        # Default to equals operator
        return self._operators[""]
    
    def remove_postfix(self, filter_name: str) -> str:
        """
        Remove the postfix from a filter name to get the base field name.
        
        This mirrors the existing repository's remove_postfix method.
        
        Args:
            filter_name: The filter name with potential postfix
            
        Returns:
            str: The base field name without postfix
            
        Example:
            ```python
            factory = FilterOperatorFactory()
            base_name = factory.remove_postfix("price_gte")
            # Returns: "price"
            ```
        """
        for postfix in ["_gte", "_lte", "_ne", "_not_in", "_is_not", "_not_exists"]:
            if filter_name.endswith(postfix):
                return filter_name[:-len(postfix)]
        return filter_name


# Global factory instance for convenience
filter_operator_factory = FilterOperatorFactory() 