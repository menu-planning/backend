"""Unit tests for filter operators that test them in isolation.

These tests focus on testing the filter operators directly without going through
the repository layer, ensuring we can identify issues in the filter logic itself.
"""

import pytest
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    Integer,
    MetaData,
    String,
    Table,
    create_engine,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.sql import select
from src.contexts.seedwork.adapters.repositories.filter_operators import (
    ContainsOperator,
    EqualsOperator,
    FilterOperator,
    FilterOperatorFactory,
    GreaterThanOperator,
    InOperator,
    IsNotOperator,
    LessThanOperator,
    LikeOperator,
    NotEqualsOperator,
    NotInOperator,
)


class TestFilterOperatorsUnit:
    """Unit tests for filter operators testing SQL generation directly."""

    @pytest.fixture
    def test_table(self):
        """Create a test table for SQL generation testing."""
        metadata = MetaData()
        return Table(
            "test_table",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("name", String(100)),
            Column("age", Integer),
            Column("price", Float),
            Column("active", Boolean),
            Column("tags", ARRAY(String)),  # Proper array field for contains operator
            Column("created_at", DateTime),
        )

    def test_equals_operator_string(self, test_table):
        """Test EqualsOperator with string values."""
        operator = EqualsOperator()
        stmt = select(test_table)

        # Test string equality
        result = operator.apply(stmt, test_table.c.name, "John")
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))

        assert "WHERE test_table.name = 'John'" in sql
        assert "test_table.name = 'John'" in sql

    def test_equals_operator_none(self, test_table):
        """Test EqualsOperator with None values."""
        operator = EqualsOperator()
        stmt = select(test_table)

        # Test NULL comparison
        result = operator.apply(stmt, test_table.c.name, None)
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))

        assert "WHERE test_table.name IS NULL" in sql
        assert "test_table.name IS NULL" in sql

    def test_equals_operator_boolean(self, test_table):
        """Test EqualsOperator with boolean values."""
        operator = EqualsOperator()
        stmt = select(test_table)

        # Test boolean equality
        result = operator.apply(stmt, test_table.c.active, True)
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))

        assert "WHERE test_table.active IS true" in sql
        assert "test_table.active IS true" in sql

    def test_equals_operator_false_boolean(self, test_table):
        """Test EqualsOperator with False boolean values."""
        operator = EqualsOperator()
        stmt = select(test_table)

        # Test boolean equality with False
        result = operator.apply(stmt, test_table.c.active, False)
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))

        assert "WHERE test_table.active IS false" in sql
        assert "test_table.active IS false" in sql

    def test_greater_than_operator(self, test_table):
        """Test GreaterThanOperator."""
        operator = GreaterThanOperator()
        stmt = select(test_table)

        result = operator.apply(stmt, test_table.c.age, 18)
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))

        assert "WHERE test_table.age >= 18" in sql
        assert "test_table.age >= 18" in sql

    def test_greater_than_operator_none_raises_error(self, test_table):
        """Test GreaterThanOperator raises error with None values."""
        operator = GreaterThanOperator()
        stmt = select(test_table)

        with pytest.raises(
            ValueError, match="GreaterThanOperator does not support None values"
        ):
            operator.apply(stmt, test_table.c.age, None)

    def test_less_than_operator(self, test_table):
        """Test LessThanOperator."""
        operator = LessThanOperator()
        stmt = select(test_table)

        result = operator.apply(stmt, test_table.c.age, 65)
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))

        assert "WHERE test_table.age <= 65" in sql
        assert "test_table.age <= 65" in sql

    def test_not_equals_operator(self, test_table):
        """Test NotEqualsOperator."""
        operator = NotEqualsOperator()
        stmt = select(test_table)

        # Test with string value
        result = operator.apply(stmt, test_table.c.name, "John")
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))

        assert "WHERE test_table.name != 'John'" in sql
        assert "test_table.name != 'John'" in sql

    def test_not_equals_operator_none(self, test_table):
        """Test NotEqualsOperator with None values."""
        operator = NotEqualsOperator()
        stmt = select(test_table)

        result = operator.apply(stmt, test_table.c.name, None)
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))

        assert "WHERE test_table.name IS NOT NULL" in sql
        assert "test_table.name IS NOT NULL" in sql

    def test_in_operator(self, test_table):
        """Test InOperator."""
        operator = InOperator()
        stmt = select(test_table)

        result = operator.apply(stmt, test_table.c.name, ["John", "Jane", "Bob"])
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))

        assert "WHERE test_table.name IN ('John', 'Jane', 'Bob')" in sql
        assert "test_table.name IN ('John', 'Jane', 'Bob')" in sql

    def test_in_operator_empty_list(self, test_table):
        """Test InOperator with empty list."""
        operator = InOperator()
        stmt = select(test_table)

        result = operator.apply(stmt, test_table.c.name, [])
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))

        # Empty list should generate a condition that matches nothing
        assert "WHERE test_table.name IN (NULL) AND (1 != 1)" in sql
        assert "test_table.name IN (NULL) AND (1 != 1)" in sql

    def test_in_operator_wrong_type_raises_error(self, test_table):
        """Test InOperator raises error with wrong type."""
        operator = InOperator()
        stmt = select(test_table)

        with pytest.raises(
            TypeError, match="InOperator requires a list, set, or tuple"
        ):
            operator.apply(stmt, test_table.c.name, "not_a_list")

    def test_not_in_operator(self, test_table):
        """Test NotInOperator."""
        operator = NotInOperator()
        stmt = select(test_table)

        result = operator.apply(stmt, test_table.c.name, ["John", "Jane"])
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))

        assert (
            "WHERE test_table.name IS NULL OR (test_table.name NOT IN ('John', 'Jane'))"
            in sql
        )
        assert (
            "test_table.name IS NULL OR (test_table.name NOT IN ('John', 'Jane'))"
            in sql
        )

    def test_not_in_operator_empty_list(self, test_table):
        """Test NotInOperator with empty list returns original statement."""
        operator = NotInOperator()
        stmt = select(test_table)

        result = operator.apply(stmt, test_table.c.name, [])

        # Should return the original statement unchanged
        assert result is stmt

    def test_contains_operator(self, test_table):
        """Test ContainsOperator."""
        operator = ContainsOperator()
        stmt = select(test_table)

        result = operator.apply(stmt, test_table.c.tags, "organic")
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))

        assert "WHERE test_table.tags @> ARRAY['organic']" in sql
        assert "test_table.tags @> ARRAY['organic']" in sql

    def test_contains_operator_json_generic_raises_error(self):
        """Test ContainsOperator with generic JSON type raises informative error."""
        from sqlalchemy import JSON, Column, Integer, MetaData, Table
        from sqlalchemy.sql import select

        # Create a test table with generic JSON column
        metadata = MetaData()
        test_table = Table(
            "test_table",
            metadata,
            Column("id", Integer, primary_key=True),
            Column("data", JSON),  # Generic JSON, not postgresql.JSONB
        )

        operator = ContainsOperator()
        stmt = select(test_table)

        # This should raise a NotImplementedError with informative message
        with pytest.raises(
            NotImplementedError,
            match="'contains' not supported for generic JSON type.*Use PostgreSQL-specific JSONB type",
        ):
            operator.apply(stmt, test_table.c.data, {"key": "value"})

    def test_is_not_operator(self, test_table):
        """Test IsNotOperator."""
        operator = IsNotOperator()
        stmt = select(test_table)

        result = operator.apply(stmt, test_table.c.name, "John")
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))

        assert "WHERE test_table.name IS NOT 'John'" in sql
        assert "test_table.name IS NOT 'John'" in sql

    def test_like_operator(self, test_table):
        """Test LikeOperator."""
        operator = LikeOperator()
        stmt = select(test_table)

        result = operator.apply(stmt, test_table.c.name, "john")
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))

        assert "WHERE lower(test_table.name) LIKE lower('%john%')" in sql
        assert "lower(test_table.name) LIKE lower('%john%')" in sql

    def test_like_operator_with_wildcards(self, test_table):
        """Test LikeOperator with existing wildcards."""
        operator = LikeOperator()
        stmt = select(test_table)

        result = operator.apply(stmt, test_table.c.name, "john%")
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))

        assert "WHERE lower(test_table.name) LIKE lower('john%')" in sql
        assert "lower(test_table.name) LIKE lower('john%')" in sql

    def test_like_operator_none_raises_error(self, test_table):
        """Test LikeOperator raises error with None values."""
        operator = LikeOperator()
        stmt = select(test_table)

        with pytest.raises(
            ValueError, match="LikeOperator does not support None values"
        ):
            operator.apply(stmt, test_table.c.name, None)

    def test_operator_chaining(self, test_table):
        """Test that operators can be chained together."""
        stmt = select(test_table)

        # Apply multiple filters
        stmt = EqualsOperator().apply(stmt, test_table.c.name, "John")
        stmt = GreaterThanOperator().apply(stmt, test_table.c.age, 18)
        stmt = InOperator().apply(stmt, test_table.c.tags, ["active", "verified"])

        sql = str(stmt.compile(compile_kwargs={"literal_binds": True}))

        assert "WHERE test_table.name = 'John'" in sql
        assert "test_table.age >= 18" in sql
        assert "test_table.tags IN ('active', 'verified')" in sql

    def test_operator_with_different_column_types(self, test_table):
        """Test operators with different column types."""
        # Test string column
        stmt = select(test_table)
        result = EqualsOperator().apply(stmt, test_table.c.name, "John")
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "test_table.name = 'John'" in sql

        # Test integer column
        stmt = select(test_table)
        result = EqualsOperator().apply(stmt, test_table.c.age, 25)
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "test_table.age = 25" in sql

        # Test float column
        stmt = select(test_table)
        result = EqualsOperator().apply(stmt, test_table.c.price, 19.99)
        sql = str(result.compile(compile_kwargs={"literal_binds": True}))
        assert "test_table.price = 19.99" in sql


class TestFilterOperatorFactoryUnit:
    """Unit tests for FilterOperatorFactory testing operator selection and postfix removal."""

    @pytest.mark.parametrize(
        "filter_name,column_type,value,expected_operator",
        [
            # Postfix-based operators
            ("field_gte", int, 10, GreaterThanOperator),
            ("field_lte", int, 10, LessThanOperator),
            ("field_ne", str, "test", NotEqualsOperator),
            ("field_not_in", list, ["a"], NotInOperator),
            ("field_is_not", type(None), None, IsNotOperator),
            # Value-type based operators
            ("field", str, ["a", "b"], InOperator),
            ("field", str, "test", EqualsOperator),
            ("field", bool, True, EqualsOperator),
            # Column-type based operators
            ("field", list, "search", ContainsOperator),
        ],
        ids=[
            "postfix_gte",
            "postfix_lte",
            "postfix_ne",
            "postfix_not_in",
            "postfix_is_not",
            "value_list",
            "value_string",
            "value_bool",
            "column_list",
        ],
    )
    def test_factory_creates_correct_operators(
        self, filter_name, column_type, value, expected_operator
    ):
        """Test that factory creates correct operator instances"""
        factory = FilterOperatorFactory()
        operator = factory.get_operator(filter_name, column_type, value)
        assert isinstance(operator, expected_operator)

    @pytest.mark.parametrize(
        "filter_name,expected_base",
        [
            ("field_gte", "field"),
            ("complex_field_name_lte", "complex_field_name"),
            ("field_ne", "field"),
            ("field_not_in", "field"),
            ("field_is_not", "field"),
            ("field_not_exists", "field"),
            ("field", "field"),  # No postfix
            ("name_with_underscore_gte", "name_with_underscore"),
            (
                "field_name_with_many_underscores_not_in",
                "field_name_with_many_underscores",
            ),
            ("simple_ne", "simple"),
            ("_leading_underscore_lte", "_leading_underscore"),
            ("trailing_underscore__gte", "trailing_underscore_"),
        ],
        ids=[
            "simple_gte",
            "complex_lte",
            "simple_ne",
            "simple_not_in",
            "simple_is_not",
            "not_exists",
            "no_postfix",
            "underscore_gte",
            "many_underscores",
            "simple_ne_2",
            "leading_underscore",
            "trailing_underscore",
        ],
    )
    def test_postfix_removal_logic(self, filter_name, expected_base):
        """Test postfix removal works correctly"""
        factory = FilterOperatorFactory()
        actual_base = factory.remove_postfix(filter_name)
        assert actual_base == expected_base

    def test_custom_operator_registration(self):
        """Test registering custom operators with factory"""
        factory = FilterOperatorFactory()

        # Define custom operator
        class CustomOperator(FilterOperator):
            def apply(self, stmt, column, value):
                return stmt.where(column.like(f"%{value}%"))

        # Register custom operator
        custom_op = CustomOperator()
        factory.register_operator("_custom", custom_op)

        # Verify registration
        assert "_custom" in factory._operators
        assert factory._operators["_custom"] is custom_op
        assert isinstance(factory._operators["_custom"], CustomOperator)

        # Test that custom operator can be retrieved by get_operator
        # when filter name ends with the custom postfix
        retrieved_op = factory.get_operator("field_custom", str, "test")
        # This will fallback to EqualsOperator since get_operator only checks hardcoded postfixes
        assert isinstance(retrieved_op, EqualsOperator)

        # However, we can verify the custom operator works by directly using it
        import sqlalchemy as sa
        from sqlalchemy.sql import select

        # Create a mock column and statement for testing
        test_table = sa.Table("test", sa.MetaData(), sa.Column("field", sa.String))
        stmt = select(test_table)
        column = test_table.c.field

        # Apply the custom operator directly
        result_stmt = custom_op.apply(stmt, column, "search_term")

        # Verify the operator modified the statement
        assert result_stmt is not None
        # The statement should now have a WHERE clause with LIKE
        where_clause = str(result_stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "LIKE" in where_clause
        assert "search_term" in where_clause

    @pytest.mark.parametrize(
        "filter_name,value,expected_operator",
        [
            ("field_unknown", "test", EqualsOperator),
            ("field_unknown", ["a", "b"], InOperator),
            ("field_super_custom_postfix", 42, EqualsOperator),
        ],
        ids=["unknown_string", "unknown_list", "made_up_postfix"],
    )
    def test_unknown_postfix_fallback_behavior(
        self, filter_name, value, expected_operator
    ):
        """Test that unknown postfixes fall back to value-based selection"""
        factory = FilterOperatorFactory()
        operator = factory.get_operator(filter_name, str, value)
        assert isinstance(operator, expected_operator)


class TestFilterOperatorCompatibilityUnit:
    """Unit tests for filter operator compatibility and signatures."""

    def test_operator_signatures_compatibility(self):
        """Test that operators can be called with expected signatures"""
        # Test that all operators can be instantiated and have apply method
        operators_to_test = [
            EqualsOperator(),
            GreaterThanOperator(),
            LessThanOperator(),
            NotEqualsOperator(),
            InOperator(),
            NotInOperator(),
            ContainsOperator(),
            IsNotOperator(),
            LikeOperator(),
        ]

        for operator in operators_to_test:
            # Verify apply method exists with correct signature
            assert hasattr(operator, "apply")
            assert callable(operator.apply)

            # Verify it's properly typed as FilterOperator
            assert isinstance(operator, FilterOperator)

    @pytest.mark.parametrize(
        "operator_class,column_name,value,expected_pattern",
        [
            (EqualsOperator, "name", "John", "= 'John'"),
            (EqualsOperator, "age", None, "age IS NULL"),
            (GreaterThanOperator, "age", 18, ">= 18"),
            (LessThanOperator, "age", 65, "<= 65"),
            (NotEqualsOperator, "name", "Jane", "!= 'Jane'"),
            (InOperator, "name", ["John", "Jane"], "name IN"),
            (NotInOperator, "age", [25, 30], "age NOT IN"),
            (IsNotOperator, "name", None, "name IS NOT NULL"),
        ],
        ids=[
            "equals_string",
            "equals_null",
            "gte_number",
            "lte_number",
            "ne_string",
            "in_list",
            "not_in_list",
            "is_not_null",
        ],
    )
    def test_operator_apply_methods_with_real_sql(
        self, operator_class, column_name, value, expected_pattern
    ):
        """Test operator apply methods generate correct SQL"""
        import sqlalchemy as sa
        from sqlalchemy.sql import select

        # Create a test table for SQL generation
        metadata = sa.MetaData()
        test_table = sa.Table(
            "test_table",
            metadata,
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.String),
            sa.Column("age", sa.Integer),
            sa.Column("active", sa.Boolean),
            sa.Column("tags", sa.JSON),
        )

        stmt = select(test_table)
        column = getattr(test_table.c, column_name)
        operator = operator_class()

        # Apply operator
        if isinstance(operator, InOperator) and not isinstance(
            value, list | set | tuple
        ):
            # Skip invalid test case
            pytest.skip("InOperator requires list value")

        result_stmt = operator.apply(stmt, column, value)

        # Compile to SQL string with literal binds for pattern matching
        compiled = str(result_stmt.compile(compile_kwargs={"literal_binds": True}))

        # Verify expected SQL pattern appears
        assert (
            expected_pattern in compiled or expected_pattern.upper() in compiled
        ), f"Expected '{expected_pattern}' in SQL for {operator.__class__.__name__}, got: {compiled}"
