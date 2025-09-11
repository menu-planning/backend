"""
SQL testing utilities for robust pattern matching and AST assertions.

This module provides helper functions to make SQL test assertions more robust
and portable across different SQLAlchemy versions and database dialects.
"""

import re
from typing import Any, Union

from sqlalchemy.sql import Select
from sqlalchemy.sql.selectable import Join

# Regex patterns for common SQL constructs
IDENT = r'(?:[A-Za-z_][A-Za-z_0-9]*|"(?:[^"]|"")*")'  # quoted or bare identifier


def table_regex(name: str) -> str:
    """Generate regex pattern for table name with optional schema and quotes.

    Args:
        name: Table name to match

    Returns:
        Regex pattern that matches table with optional schema prefix and quotes
    """
    return rf'(?:{IDENT}\.)?"?{re.escape(name)}"?'


def column_regex(table: str, col: str) -> str:
    """Generate regex pattern for column reference with table qualification.

    Args:
        table: Table name
        col: Column name

    Returns:
        Regex pattern that matches table.column reference
    """
    return rf'{table_regex(table)}\s*\.\s*"?{re.escape(col)}"?'


def count_joins(select_stmt: Select) -> int:
    """Count joins in a SQLAlchemy Select statement structurally.

    Args:
        select_stmt: SQLAlchemy Select statement

    Returns:
        Number of joins in the statement
    """

    def walk(from_clause):
        if isinstance(from_clause, Join):
            return 1 + walk(from_clause.left) + walk(from_clause.right)
        return 0

    return sum(walk(fr) for fr in select_stmt.get_final_froms())


def has_postcompile_param(compiled, suffix: str) -> bool:
    """Check if compiled statement has post-compile parameter with given suffix.

    Args:
        compiled: Compiled SQLAlchemy statement
        suffix: Suffix to match in parameter names

    Returns:
        True if parameter with suffix exists
    """
    post = getattr(compiled, "post_compile_params", frozenset())
    # post_compile_params is a frozenset of BindParameter objects
    for param in post:
        if hasattr(param, "key") and suffix in str(param.key):
            return True
    return False


def get_table_names(select_stmt: Select) -> set[str]:
    """Extract table names from a SQLAlchemy Select statement.

    Args:
        select_stmt: SQLAlchemy Select statement

    Returns:
        Set of table names referenced in the statement
    """
    froms = select_stmt.get_final_froms()
    table_names = set()

    def extract_name(from_clause):
        if hasattr(from_clause, "name") and from_clause.name is not None:
            table_names.add(from_clause.name)
        elif hasattr(from_clause, "table") and from_clause.table is not None:
            table_names.add(from_clause.table.name)
        elif isinstance(from_clause, Join):
            extract_name(from_clause.left)
            extract_name(from_clause.right)

    for fr in froms:
        extract_name(fr)

    return table_names


def has_where_criteria(
    select_stmt: Select, column_name: str, operator_name: str | None = None
) -> bool:
    """Check if WHERE clause contains specific column and operator.

    Args:
        select_stmt: SQLAlchemy Select statement
        column_name: Column name to look for
        operator_name: Optional operator name to match

    Returns:
        True if criteria exists
    """
    if not hasattr(select_stmt, "_where_criteria"):
        return False

    for criteria in select_stmt._where_criteria:
        # Handle different types of criteria objects
        criteria_str = str(criteria)
        if column_name in criteria_str:
            if operator_name is None or operator_name in criteria_str:
                return True
    return False


def assert_sql_structure(sql_str: str, expected_pattern: str, **kwargs) -> None:
    """Assert SQL string matches pattern with proper flags.

    Args:
        sql_str: SQL string to test
        expected_pattern: Regex pattern to match
        **kwargs: Additional flags for re.search
    """
    flags = kwargs.get("flags", re.IGNORECASE | re.DOTALL)
    assert re.search(
        expected_pattern, sql_str, flags
    ), f"Pattern not found in SQL: {sql_str}"


def assert_join_count(select_stmt: Select, expected_count: int) -> None:
    """Assert exact number of joins in statement.

    Args:
        select_stmt: SQLAlchemy Select statement
        expected_count: Expected number of joins
    """
    actual_count = count_joins(select_stmt)
    assert (
        actual_count == expected_count
    ), f"Expected {expected_count} joins, got {actual_count}"


def assert_table_present(select_stmt: Select, table_name: str) -> None:
    """Assert table is present in FROM clause.

    Args:
        select_stmt: SQLAlchemy Select statement
        table_name: Table name to check for
    """
    table_names = get_table_names(select_stmt)
    assert table_name in table_names, f"Table {table_name} not found in {table_names}"


def assert_where_clause_count(sql_str: str, expected_count: int) -> None:
    """Assert exact number of WHERE clauses using word boundaries.

    Args:
        sql_str: SQL string to test
        expected_count: Expected number of WHERE clauses
    """
    actual_count = len(re.findall(r"\bWHERE\b", sql_str, re.IGNORECASE))
    assert (
        actual_count == expected_count
    ), f"Expected {expected_count} WHERE clauses, got {actual_count}"


def assert_join_clause_count(sql_str: str, expected_count: int) -> None:
    """Assert exact number of JOIN clauses using word boundaries.

    Args:
        sql_str: SQL string to test
        expected_count: Expected number of JOIN clauses
    """
    actual_count = len(re.findall(r"\bJOIN\b", sql_str, re.IGNORECASE))
    assert (
        actual_count == expected_count
    ), f"Expected {expected_count} JOIN clauses, got {actual_count}"
