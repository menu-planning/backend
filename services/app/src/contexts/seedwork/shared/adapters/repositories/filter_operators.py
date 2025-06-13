from __future__ import annotations

import abc
from typing import Any
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Generic, TypeVar

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


class LikeOperator(FilterOperator):
    """
    Filter operator for SQL LIKE pattern matching (_like postfix).
    
    Provides case-insensitive pattern matching using SQL LIKE with % wildcards.
    The operator automatically wraps the value with % wildcards for substring matching.
    
    Examples:
        ```python
        operator = LikeOperator()
        stmt = operator.apply(select(Product), Product.name, "apple")
        # Results in: WHERE LOWER(product.name) LIKE LOWER('%apple%')
        
        # For exact pattern matching, use wildcards in the value
        stmt = operator.apply(select(Product), Product.name, "apple%")
        # Results in: WHERE LOWER(product.name) LIKE LOWER('apple%')
        ```
    """
    
    def apply(self, stmt: Select, column: ColumnElement, value: Any) -> Select:
        """Apply LIKE filter to the statement with case-insensitive matching."""
        if value is None:
            raise ValueError("LikeOperator does not support None values")
        
        # Convert value to string for pattern matching
        pattern = str(value)
        
        # If pattern doesn't contain wildcards, wrap it for substring matching
        if '%' not in pattern and '_' not in pattern:
            pattern = f'%{pattern}%'
        
        # Use case-insensitive matching with LOWER()
        from sqlalchemy.sql import func
        return stmt.where(func.lower(column).like(func.lower(pattern)))


@dataclass
class FilterOperatorRegistry:
    """
    Registry for filter operators using @dataclass pattern.
    
    This replaces the hardcoded ALLOWED_POSTFIX list with a structured registry
    that provides better organization and extensibility for filter postfixes.
    
    The registry maintains both the list of allowed postfixes and the mapping
    of postfixes to their corresponding operators, providing a centralized
    location for all filter operator configuration.
    
    Examples:
        Basic usage:
        ```python
        registry = FilterOperatorRegistry()
        
        # Check if postfix is supported
        if registry.is_postfix_supported("_gte"):
            print("Greater than or equal operator supported")
        
        # Get all supported postfixes
        postfixes = registry.get_supported_postfixes()
        # Returns: ["_gte", "_lte", "_ne", "_not_in", "_is_not", "_not_exists"]
        
        # Remove postfix from filter name
        base_name = registry.remove_postfix("price_gte")
        # Returns: "price"
        ```
        
        Extension with custom operators:
        ```python
        registry = FilterOperatorRegistry()
        registry.register_postfix("_regex", RegexOperator())
        
        # Now _regex is supported
        assert registry.is_postfix_supported("_regex")
        ```
    """
    
    # Default postfixes that match existing repository ALLOWED_POSTFIX
    _default_postfixes: list[str] = field(default_factory=lambda: [
        "_gte", "_lte", "_ne", "_not_in", "_is_not", "_not_exists", "_like"
    ])
    
    # Mapping of postfixes to their operators (for future extensibility)
    _postfix_to_operator: dict[str, FilterOperator] = field(default_factory=dict)
    
    # Custom postfixes registered at runtime
    _custom_postfixes: list[str] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize the registry with default postfix-to-operator mappings."""
        # Default operator mappings (matches existing FilterOperatorFactory)
        default_mappings = {
            "_gte": GreaterThanOperator(),
            "_lte": LessThanOperator(),
            "_ne": NotEqualsOperator(),
            "_not_in": NotInOperator(),
            "_is_not": IsNotOperator(),
            "_like": LikeOperator(),
            # _not_exists doesn't have a specific operator yet, but placeholder for future
            "_not_exists": None,  # Currently handled by fallback logic
        }
        
        # Only add mappings for operators that are defined
        for postfix, operator in default_mappings.items():
            if operator is not None:
                self._postfix_to_operator[postfix] = operator
    
    def get_supported_postfixes(self) -> list[str]:
        """
        Get the complete list of supported postfixes.
        
        Returns:
            list[str]: All supported postfixes (default + custom)
            
        Example:
            ```python
            registry = FilterOperatorRegistry()
            postfixes = registry.get_supported_postfixes()
            # Returns: ["_gte", "_lte", "_ne", "_not_in", "_is_not", "_not_exists"]
            ```
        """
        return self._default_postfixes + self._custom_postfixes
    
    def is_postfix_supported(self, postfix: str) -> bool:
        """
        Check if a postfix is supported by the registry.
        
        Args:
            postfix: The postfix to check (e.g., "_gte", "_custom")
            
        Returns:
            bool: True if the postfix is supported
            
        Example:
            ```python
            registry = FilterOperatorRegistry()
            
            assert registry.is_postfix_supported("_gte")  # True
            assert not registry.is_postfix_supported("_unknown")  # False
            ```
        """
        return postfix in self.get_supported_postfixes()
    
    def register_postfix(self, postfix: str, operator: FilterOperator | None = None) -> None:
        """
        Register a custom postfix with optional operator.
        
        Args:
            postfix: The postfix to register (e.g., "_custom", "_regex")
            operator: Optional FilterOperator instance for the postfix
            
        Example:
            ```python
            registry = FilterOperatorRegistry()
            registry.register_postfix("_regex", RegexOperator())
            
            # Now _regex postfix is supported
            assert registry.is_postfix_supported("_regex")
            ```
        """
        if postfix not in self._custom_postfixes:
            self._custom_postfixes.append(postfix)
        
        if operator is not None:
            self._postfix_to_operator[postfix] = operator
    
    def get_operator_for_postfix(self, postfix: str) -> FilterOperator | None:
        """
        Get the operator associated with a postfix.
        
        Args:
            postfix: The postfix to look up
            
        Returns:
            FilterOperator | None: The operator for the postfix, or None if not found
            
        Example:
            ```python
            registry = FilterOperatorRegistry()
            operator = registry.get_operator_for_postfix("_gte")
            # Returns: GreaterThanOperator instance
            ```
        """
        return self._postfix_to_operator.get(postfix)
    
    def remove_postfix(self, filter_name: str) -> str:
        """
        Remove any supported postfix from a filter name to get the base field name.
        
        This method replaces the static remove_postfix method in SaGenericRepository
        by using the registry's list of supported postfixes.
        
        Args:
            filter_name: The filter name with potential postfix
            
        Returns:
            str: The base field name without postfix
            
        Example:
            ```python
            registry = FilterOperatorRegistry()
            
            base_name = registry.remove_postfix("price_gte")
            # Returns: "price"
            
            base_name = registry.remove_postfix("name")
            # Returns: "name" (no postfix to remove)
            
            base_name = registry.remove_postfix("complex_field_name_lte")
            # Returns: "complex_field_name"
            ```
        """
        for postfix in self.get_supported_postfixes():
            if filter_name.endswith(postfix):
                return filter_name[:-len(postfix)]
        return filter_name


# Global registry instance for convenience (replaces hardcoded ALLOWED_POSTFIX)
filter_operator_registry = FilterOperatorRegistry()


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
        self.register_operator("_like", LikeOperator())
        
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
        # Check for postfix-based operators using the registry
        for postfix in filter_operator_registry.get_supported_postfixes():
            if filter_name.endswith(postfix):
                # Get operator from registry first, fallback to our internal mapping
                registry_operator = filter_operator_registry.get_operator_for_postfix(postfix)
                if registry_operator is not None:
                    return registry_operator
                # Fallback to our internal mapping for backward compatibility
                elif postfix in self._operators:
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
        
        This now delegates to the FilterOperatorRegistry for consistency.
        
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
        return filter_operator_registry.remove_postfix(filter_name)


# Global factory instance for convenience
filter_operator_factory = FilterOperatorFactory() 