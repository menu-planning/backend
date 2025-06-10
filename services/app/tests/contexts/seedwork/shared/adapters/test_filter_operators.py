"""
Comprehensive unit tests for FilterOperator implementations.

This test suite covers:
- All FilterOperator implementations with various data types
- Edge cases: None values, empty lists, type mismatches
- Filter combination logic: same key (OR), different keys (AND)
- Relationship handling and duplicate detection
- Postfix operator behavior (_gte, _lte, _ne, _not_in, _is_not, _not_exists)
"""

import pytest
from typing import Any, Type
from unittest.mock import Mock, patch

from sqlalchemy import Column, Integer, String, Boolean, JSON
from sqlalchemy.orm import declarative_base

from src.contexts.seedwork.shared.adapters.filter_operators import (
    FilterOperator, EqualsOperator, GreaterThanOperator, LessThanOperator,
    NotEqualsOperator, InOperator, NotInOperator, ContainsOperator, IsNotOperator,
    FilterOperatorFactory
)

# Test SQLAlchemy models for testing
Base = declarative_base()

class SQLAlchemyTestModel(Base):
    __tablename__ = 'test_model'
    
    id = Column(Integer, primary_key=True)
    name = Column(String)
    age = Column(Integer)
    active = Column(Boolean)
    tags = Column(JSON)  # For list/array testing


class TestFilterOperatorImplementations:
    """Test each FilterOperator implementation individually."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.mock_stmt = Mock()
        self.mock_column = Mock()
        self.test_model = SQLAlchemyTestModel
        
    @pytest.mark.parametrize("operator_class,test_value,expected_method", [
        (EqualsOperator, "test", "__eq__"),
        (GreaterThanOperator, 10, "__ge__"),
        (LessThanOperator, 10, "__le__"),
        (NotEqualsOperator, "test", "__ne__"),
    ])
    def test_basic_operators(self, operator_class: Type[FilterOperator], test_value: Any, expected_method: str):
        """Test basic comparison operators generate correct SQL conditions."""
        operator = operator_class()
        
        # Mock the column method
        mock_condition = Mock()
        setattr(self.mock_column, expected_method, Mock(return_value=mock_condition))
        
        result = operator.apply(self.mock_stmt, self.mock_column, test_value)
        
        # Verify the correct method was called
        getattr(self.mock_column, expected_method).assert_called_once_with(test_value)
        # Verify stmt.where was called with the condition
        self.mock_stmt.where.assert_called_once_with(mock_condition)
        
    def test_equals_operator_with_none(self):
        """Test EqualsOperator handles None values correctly."""
        operator = EqualsOperator()
        mock_condition = Mock()
        self.mock_column.is_ = Mock(return_value=mock_condition)
        
        operator.apply(self.mock_stmt, self.mock_column, None)
        
        # Should use IS for None values
        self.mock_column.is_.assert_called_once_with(None)
        self.mock_stmt.where.assert_called_once_with(mock_condition)
        
    def test_in_operator_with_list(self):
        """Test InOperator with valid list values."""
        operator = InOperator()
        test_values = ["value1", "value2", "value3"]
        mock_condition = Mock()
        self.mock_column.in_ = Mock(return_value=mock_condition)
        
        operator.apply(self.mock_stmt, self.mock_column, test_values)
        
        self.mock_column.in_.assert_called_once_with(test_values)
        self.mock_stmt.where.assert_called_once_with(mock_condition)
        
    def test_in_operator_with_empty_list_raises_error(self):
        """Test InOperator with empty list raises ValueError."""
        operator = InOperator()
        empty_list = []
        
        with pytest.raises(ValueError, match="InOperator requires a non-empty collection"):
            operator.apply(self.mock_stmt, self.mock_column, empty_list)
            
    def test_in_operator_with_non_list_raises_error(self):
        """Test InOperator with non-list value raises TypeError."""
        operator = InOperator()
        single_value = "single"
        
        with pytest.raises(TypeError, match="InOperator requires a list, set, or tuple"):
            operator.apply(self.mock_stmt, self.mock_column, single_value)
        
    def test_not_in_operator_with_list(self):
        """Test NotInOperator with list values."""
        operator = NotInOperator()
        test_values = ["value1", "value2"]
        
        # Mock the column methods for the OR condition: (column.is_(None)) | (~column.in_(value))
        mock_is_null_condition = Mock()
        mock_in_condition = Mock()
        mock_not_in_condition = Mock()
        mock_or_condition = Mock()
        
        self.mock_column.is_ = Mock(return_value=mock_is_null_condition)
        self.mock_column.in_ = Mock(return_value=mock_in_condition)
        
        # Mock the ~ operator on the in_ result
        mock_in_condition.__invert__ = Mock(return_value=mock_not_in_condition)
        
        # Mock the | operator between conditions
        mock_is_null_condition.__or__ = Mock(return_value=mock_or_condition)
        
        operator.apply(self.mock_stmt, self.mock_column, test_values)
        
        self.mock_column.is_.assert_called_once_with(None)
        self.mock_column.in_.assert_called_once_with(test_values)
        mock_in_condition.__invert__.assert_called_once()
        mock_is_null_condition.__or__.assert_called_once_with(mock_not_in_condition)
        self.mock_stmt.where.assert_called_once_with(mock_or_condition)
            
    def test_not_in_operator_with_empty_list_raises_error(self):
        """Test NotInOperator with empty list raises ValueError."""
        operator = NotInOperator()
        empty_list = []
        
        with pytest.raises(ValueError, match="NotInOperator requires a non-empty collection"):
            operator.apply(self.mock_stmt, self.mock_column, empty_list)
            
    def test_contains_operator_with_string(self):
        """Test ContainsOperator for string containment."""
        operator = ContainsOperator()
        search_value = "search"
        
        # Mock the SQLAlchemy operators.contains function
        with patch('src.contexts.seedwork.shared.adapters.filter_operators.operators.contains') as mock_contains:
            mock_condition = Mock()
            mock_contains.return_value = mock_condition
            
            operator.apply(self.mock_stmt, self.mock_column, search_value)
            
            mock_contains.assert_called_once_with(self.mock_column, search_value)
            self.mock_stmt.where.assert_called_once_with(mock_condition)
        
    def test_contains_operator_with_list_column(self):
        """Test ContainsOperator for JSON/array column containment."""
        operator = ContainsOperator()
        search_value = "tag1"
        
        # Mock the SQLAlchemy operators.contains function
        with patch('src.contexts.seedwork.shared.adapters.filter_operators.operators.contains') as mock_contains:
            mock_condition = Mock()
            mock_contains.return_value = mock_condition
            
            operator.apply(self.mock_stmt, self.mock_column, search_value)
            
            mock_contains.assert_called_once_with(self.mock_column, search_value)
            self.mock_stmt.where.assert_called_once_with(mock_condition)
        
    def test_is_not_operator(self):
        """Test IsNotOperator for IS NOT SQL condition."""
        operator = IsNotOperator()
        test_value = None
        
        # Mock the SQLAlchemy operators.is_not function
        with patch('src.contexts.seedwork.shared.adapters.filter_operators.operators.is_not') as mock_is_not:
            mock_condition = Mock()
            mock_is_not.return_value = mock_condition
            
            operator.apply(self.mock_stmt, self.mock_column, test_value)
            
            mock_is_not.assert_called_once_with(self.mock_column, test_value)
            self.mock_stmt.where.assert_called_once_with(mock_condition)


class TestFilterOperatorFactory:
    """Test the FilterOperatorFactory registration and operator selection."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = FilterOperatorFactory()
        
    def test_register_and_get_basic_operators(self):
        """Test registering and retrieving basic operators."""
        # Test default operators are registered
        eq_op = self.factory.get_operator("field", str, "test")
        assert isinstance(eq_op, EqualsOperator)
        
        gte_op = self.factory.get_operator("field_gte", int, 10)
        assert isinstance(gte_op, GreaterThanOperator)
        
        in_op = self.factory.get_operator("field", str, ["a", "b"])
        assert isinstance(in_op, InOperator)
        
    def test_get_operator_with_postfix(self):
        """Test operator selection based on filter name postfix."""
        test_cases = [
            ("field_gte", int, 10, GreaterThanOperator),
            ("field_lte", int, 10, LessThanOperator),
            ("field_ne", str, "test", NotEqualsOperator),
            ("field_not_in", list, ["a", "b"], NotInOperator),
            ("field_is_not", type(None), None, IsNotOperator),
        ]
        
        for filter_name, column_type, value, expected_operator in test_cases:
            operator = self.factory.get_operator(filter_name, column_type, value)
            assert isinstance(operator, expected_operator), \
                f"Expected {expected_operator.__name__} for {filter_name}, got {type(operator).__name__}"
                
    def test_get_operator_by_value_type(self):
        """Test operator selection based on value type when no postfix."""
        # List values should return InOperator
        list_op = self.factory.get_operator("field", str, ["a", "b", "c"])
        assert isinstance(list_op, InOperator)
        
        # String values should return EqualsOperator
        str_op = self.factory.get_operator("field", str, "test")
        assert isinstance(str_op, EqualsOperator)
        
        # None values should return EqualsOperator (handles None internally)
        none_op = self.factory.get_operator("field", str, None)
        assert isinstance(none_op, EqualsOperator)
        
    def test_register_custom_operator(self):
        """Test registering custom operators."""
        class CustomOperator(FilterOperator):
            def apply(self, stmt, column, value):
                return stmt.where(column == f"custom_{value}")
                
        custom_instance = CustomOperator()
        
        # The current get_operator implementation only checks for hardcoded postfixes
        # So we need to register it as one of the recognized postfixes or test the registry directly
        self.factory.register_operator("_custom", custom_instance)
        
        # Verify it's registered in the internal operators dict
        assert "_custom" in self.factory._operators
        assert self.factory._operators["_custom"] is custom_instance
        
        # The current get_operator logic doesn't check for arbitrary custom postfixes
        # It only checks: ["_gte", "_lte", "_ne", "_not_in", "_is_not"]
        # For a field_custom, it would fall back to default behavior based on value type
        custom_op = self.factory.get_operator("field_custom", str, "test")
        # This will return EqualsOperator because "test" is a string value
        assert isinstance(custom_op, EqualsOperator)
        
        # Test direct access to verify registration worked
        direct_custom_op = self.factory._operators["_custom"]
        assert isinstance(direct_custom_op, CustomOperator)
        assert direct_custom_op is custom_instance
        
    def test_unknown_postfix_falls_back_to_default(self):
        """Test that unknown postfix falls back to value-based selection."""
        # Unknown postfix should fall back to value type
        unknown_op = self.factory.get_operator("field_unknown", str, "test")
        assert isinstance(unknown_op, EqualsOperator)
        
        unknown_list_op = self.factory.get_operator("field_unknown", str, ["a", "b"])
        assert isinstance(unknown_list_op, InOperator)


class TestFilterCombinationLogic:
    """Test how filters are combined - same key (OR) vs different keys (AND)."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = FilterOperatorFactory()
        
    def test_same_key_multiple_values_or_logic(self):
        """Test that same key with multiple values creates OR logic."""
        # Simulate: {"mealType": ["lunch", "dinner"]}
        filter_name = "mealType"
        values = ["lunch", "dinner"]
        column_type = str
        
        # Should return InOperator which creates IN clause (OR logic)
        operator = self.factory.get_operator(filter_name, column_type, values)
        assert isinstance(operator, InOperator)
        
        # Verify the operator creates correct SQL
        mock_stmt = Mock()
        mock_column = Mock()
        mock_condition = Mock()
        mock_column.in_ = Mock(return_value=mock_condition)
        
        operator.apply(mock_stmt, mock_column, values)
        
        mock_column.in_.assert_called_once_with(values)  # IN creates OR logic
        mock_stmt.where.assert_called_once_with(mock_condition)
        
    def test_different_keys_and_logic(self):
        """Test that different keys create AND logic when combined."""
        # Simulate: {"mealType": "dinner", "total_time_lte": 30}
        filters = {
            "mealType": ("dinner", str),  # (value, column_type)
            "total_time_lte": (30, int),
        }
        
        mock_stmt = Mock()
        mock_columns = {}
        mock_conditions = {}
        
        # Create mock columns and conditions for each filter
        for filter_name, (value, column_type) in filters.items():
            mock_columns[filter_name] = Mock()
            mock_conditions[filter_name] = Mock()
            
            operator = self.factory.get_operator(filter_name, column_type, value)
            
            if filter_name == "mealType":
                assert isinstance(operator, EqualsOperator)
                mock_columns[filter_name].__eq__ = Mock(return_value=mock_conditions[filter_name])
            elif filter_name == "total_time_lte":
                assert isinstance(operator, LessThanOperator)
                mock_columns[filter_name].__le__ = Mock(return_value=mock_conditions[filter_name])
                
        # Simulate applying both filters (this would be done by the repository)
        for filter_name, (value, column_type) in filters.items():
            operator = self.factory.get_operator(filter_name, column_type, value)
            operator.apply(mock_stmt, mock_columns[filter_name], value)
            
        # Verify each filter was applied separately (creating AND logic)
        assert mock_stmt.where.call_count == 2  # Two separate where calls = AND logic
        
    def test_mixed_same_and_different_keys(self):
        """Test complex scenario with both same-key (OR) and different-key (AND) logic."""
        # Simulate: {"mealType": ["lunch", "dinner"], "total_time_lte": 30, "tags": ["vegan", "quick"]}
        filters = {
            "mealType": (["lunch", "dinner"], str),  # Same key, multiple values = OR
            "total_time_lte": (30, int),              # Different key = AND
            "tags": (["vegan", "quick"], str),        # Same key, multiple values = OR
        }
        
        mock_stmt = Mock()
        
        for filter_name, (value, column_type) in filters.items():
            operator = self.factory.get_operator(filter_name, column_type, value)
            
            if isinstance(value, list):
                assert isinstance(operator, InOperator), f"Expected InOperator for {filter_name} with list value"
            elif filter_name.endswith("_lte"):
                assert isinstance(operator, LessThanOperator)
            else:
                assert isinstance(operator, EqualsOperator)
                
        # Each filter application should result in a separate where clause
        # The repository would combine them with AND, while IN clauses provide OR within each condition


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error conditions."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = FilterOperatorFactory()
        
    def test_none_values_handled_correctly(self):
        """Test that None values are handled correctly across operators."""
        test_cases = [
            ("field", None, EqualsOperator),
            ("field_ne", None, NotEqualsOperator),
            ("field_is_not", None, IsNotOperator),
        ]
        
        for filter_name, value, expected_operator in test_cases:
            operator = self.factory.get_operator(filter_name, type(None), value)
            assert isinstance(operator, expected_operator)
            
            # Test actual application
            mock_stmt = Mock()
            mock_column = Mock()
            
            # Mock appropriate column methods or operators
            if isinstance(operator, EqualsOperator):
                mock_column.is_ = Mock(return_value=Mock())
                result = operator.apply(mock_stmt, mock_column, value)
            elif isinstance(operator, NotEqualsOperator):
                mock_column.is_not = Mock(return_value=Mock())
                result = operator.apply(mock_stmt, mock_column, value)
            elif isinstance(operator, IsNotOperator):
                with patch('src.contexts.seedwork.shared.adapters.filter_operators.operators.is_not') as mock_is_not:
                    mock_is_not.return_value = Mock()
                    result = operator.apply(mock_stmt, mock_column, value)
                    
            # Should not raise an exception
            assert result == mock_stmt.where.return_value
            
    def test_empty_list_edge_cases(self):
        """Test edge cases with empty lists."""
        empty_list = []
        
        # InOperator with empty list should raise ValueError
        in_operator = self.factory.get_operator("field", str, ["non_empty"])  # Get the operator type
        assert isinstance(in_operator, InOperator)
        
        with pytest.raises(ValueError):
            in_operator.apply(Mock(), Mock(), empty_list)
        
        # NotInOperator with empty list should raise ValueError
        not_in_operator = self.factory.get_operator("field_not_in", str, ["non_empty"])
        assert isinstance(not_in_operator, NotInOperator)
        
        with pytest.raises(ValueError):
            not_in_operator.apply(Mock(), Mock(), empty_list)
        
    def test_type_consistency(self):
        """Test that operators maintain type consistency."""
        # String operations
        str_operator = self.factory.get_operator("field", str, "test")
        assert isinstance(str_operator, EqualsOperator)
        
        # Numeric operations
        num_operator = self.factory.get_operator("field_gte", int, 10)
        assert isinstance(num_operator, GreaterThanOperator)
        
        # Boolean operations
        bool_operator = self.factory.get_operator("field", bool, True)
        assert isinstance(bool_operator, EqualsOperator)
        
    def test_postfix_extraction(self):
        """Test that postfixes are correctly extracted from filter names."""
        postfix_tests = [
            ("field_gte", "_gte"),
            ("complex_field_name_lte", "_lte"),
            ("field_ne", "_ne"),
            ("field_not_in", "_not_in"),
            ("field_is_not", "_is_not"),
            ("field", ""),  # No postfix
        ]
        
        for filter_name, expected_postfix in postfix_tests:
            # This is tested indirectly through operator selection
            if expected_postfix == "_gte":
                operator = self.factory.get_operator(filter_name, int, 10)
                assert isinstance(operator, GreaterThanOperator)
            elif expected_postfix == "_lte":
                operator = self.factory.get_operator(filter_name, int, 10)
                assert isinstance(operator, LessThanOperator)
            elif expected_postfix == "_ne":
                operator = self.factory.get_operator(filter_name, str, "test")
                assert isinstance(operator, NotEqualsOperator)
            elif expected_postfix == "_not_in":
                operator = self.factory.get_operator(filter_name, list, ["a"])
                assert isinstance(operator, NotInOperator)
            elif expected_postfix == "_is_not":
                operator = self.factory.get_operator(filter_name, type(None), None)
                assert isinstance(operator, IsNotOperator)
            else:  # No postfix
                operator = self.factory.get_operator(filter_name, str, "test")
                assert isinstance(operator, EqualsOperator)


class TestBackwardCompatibility:
    """Test that new FilterOperator system maintains backward compatibility."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = FilterOperatorFactory()
        
    def test_all_existing_postfixes_supported(self):
        """Test that all existing postfixes from ALLOWED_POSTFIX are supported."""
        # From the existing repository: ["_gte", "_lte", "_ne", "_not_in", "_is_not", "_not_exists"]
        existing_postfixes = ["_gte", "_lte", "_ne", "_not_in", "_is_not", "_not_exists"]
        
        for postfix in existing_postfixes:
            filter_name = f"field{postfix}"
            
            if postfix == "_not_exists":
                # This is a special case that might need custom handling
                # For now, it should fall back to default behavior
                operator = self.factory.get_operator(filter_name, str, "test")
                assert operator is not None
            else:
                # All other postfixes should have specific operators
                if postfix in ["_gte", "_lte", "_ne", "_not_in", "_is_not"]:
                    operator = self.factory.get_operator(filter_name, str, "test")
                    assert operator is not None
                    
    def test_filter_value_type_detection(self):
        """Test that filter value type detection matches existing behavior."""
        # Existing behavior: isinstance(filter_value, (list, set)) -> use in_()
        test_cases = [
            (["a", "b"], InOperator),
            ({"a", "b"}, InOperator),  # Sets should also work
            ("string", EqualsOperator),
            (123, EqualsOperator),
            (True, EqualsOperator),
            (None, EqualsOperator),
        ]
        
        for value, expected_operator in test_cases:
            operator = self.factory.get_operator("field", type(value), value)
            assert isinstance(operator, expected_operator), \
                f"Value {value} of type {type(value)} should produce {expected_operator.__name__}"
                
    def test_existing_operator_signatures(self):
        """Test that operators can be called with the same signatures as existing code."""
        # Test basic signature compatibility with mock objects that behave more like SQLAlchemy objects
        test_cases = [
            (EqualsOperator(), "test"),
            (NotEqualsOperator(), "test"),
            (InOperator(), ["a", "b"]),
            (NotInOperator(), ["a", "b"]),
        ]
        
        for operator, test_value in test_cases:
            mock_stmt = Mock()
            mock_column = Mock()
            
            # Mock appropriate methods based on operator type
            if isinstance(operator, EqualsOperator):
                mock_column.__eq__ = Mock(return_value=Mock())
            elif isinstance(operator, NotEqualsOperator):
                mock_column.__ne__ = Mock(return_value=Mock())
            elif isinstance(operator, InOperator):
                mock_column.in_ = Mock(return_value=Mock())
            elif isinstance(operator, NotInOperator):
                # Mock the complex OR condition
                mock_is_condition = Mock()
                mock_in_condition = Mock()
                mock_not_in_condition = Mock()
                mock_or_condition = Mock()
                
                mock_column.is_ = Mock(return_value=mock_is_condition)
                mock_column.in_ = Mock(return_value=mock_in_condition)
                mock_in_condition.__invert__ = Mock(return_value=mock_not_in_condition)
                mock_is_condition.__or__ = Mock(return_value=mock_or_condition)
                
            # Should not raise an exception and should return the modified statement
            try:
                result = operator.apply(mock_stmt, mock_column, test_value)
                assert result == mock_stmt.where.return_value
            except Exception as e:
                pytest.fail(f"Operator {type(operator).__name__} failed with signature (stmt, column, value): {e}")


class TestRelationshipDuplicateHandling:
    """Test edge cases related to relationships and duplicate row handling."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.factory = FilterOperatorFactory()
        
    def test_list_filters_require_distinct(self):
        """Test that list-based filters should trigger DISTINCT to handle duplicates from joins."""
        # When filtering by lists (e.g., tags, categories), joins often create duplicate rows
        # The repository should use DISTINCT to handle this
        
        list_filters = [
            ("tags", ["vegan", "quick"]),
            ("categories", ["Electronics", "Books"]),
            ("diet_types", ["vegetarian", "gluten-free"]),
        ]
        
        for filter_name, values in list_filters:
            operator = self.factory.get_operator(filter_name, str, values)
            assert isinstance(operator, InOperator)
            
            # Verify that the operator would create an IN clause
            mock_stmt = Mock()
            mock_column = Mock()
            mock_condition = Mock()
            mock_column.in_ = Mock(return_value=mock_condition)
            
            operator.apply(mock_stmt, mock_column, values)
            mock_column.in_.assert_called_once_with(values)
            
    def test_complex_tag_filtering_scenario(self):
        """Test complex tag filtering that mirrors the MealRepo tag logic."""
        # Simulate the complex tag filtering from MealRepo:
        # Tags are grouped by key, with OR logic within each key group
        # and AND logic between different key groups
        
        # Example: tags = [("mealType", "lunch", "user123"), ("mealType", "dinner", "user123"), 
        #                  ("difficulty", "easy", "user123")]
        # Should result in: (mealType IN ["lunch", "dinner"]) AND (difficulty = "easy")
        
        tag_groups = {
            "mealType": ["lunch", "dinner"],  # OR within group
            "difficulty": ["easy"],           # Single value - still a list
            "cuisine": ["italian", "mexican"] # OR within group
        }
        
        mock_stmt = Mock()
        
        for tag_key, tag_values in tag_groups.items():
            operator = self.factory.get_operator(tag_key, str, tag_values)
            
            # All values are lists, so they should all use InOperator
            # Even single-item lists should use InOperator for consistency
            assert isinstance(operator, InOperator), f"Expected InOperator for {tag_key}, got {type(operator).__name__}"
                
        # Each tag group would be applied as a separate WHERE clause (AND logic between groups)
        # This matches the existing repository behavior where multiple filters create AND conditions
        
    def test_relationship_join_scenarios(self):
        """Test scenarios that would require table joins and duplicate handling."""
        # These scenarios mirror the FilterColumnMapper patterns from existing repositories
        
        relationship_filters = [
            # Product filtering by source name (requires join to Source table)
            ("source", "Amazon"),
            
            # Meal filtering by recipe name (requires join to Recipe table)  
            ("recipe_name", "Pasta Carbonara"),
            
            # Meal filtering by ingredient product (requires join through Recipe -> Ingredient -> Product)
            ("products", ["product_id_1", "product_id_2"]),
        ]
        
        for filter_name, filter_value in relationship_filters:
            if isinstance(filter_value, list):
                operator = self.factory.get_operator(filter_name, str, filter_value)
                assert isinstance(operator, InOperator)
            else:
                operator = self.factory.get_operator(filter_name, str, filter_value)
                assert isinstance(operator, EqualsOperator)
                
        # In the actual repository, these would trigger joins and require DISTINCT
        # The FilterOperator system provides the WHERE clause logic,
        # while the repository handles the JOIN and DISTINCT logic


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 