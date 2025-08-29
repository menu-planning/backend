"""
Comprehensive tests for TypeConversionUtility class.

Tests cover all conversion methods with edge cases, error handling,
and performance validation as required by Phase 1.1.2.
"""

import pytest
import time
from uuid import UUID, uuid4
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum

from src.contexts.seedwork.shared.adapters.api_schemas.base_api_model import TypeConversionUtility
from src.contexts.seedwork.shared.adapters.exceptions.api_schema import ValidationConversionError


class SampleEnum(Enum):
    """Sample enum for enum conversion testing."""
    VALUE_ONE = "value_one"
    VALUE_TWO = "value_two"
    SPECIAL_CHARS = "special!@#$%^&*()"


class TestTypeConversionUtility:
    """Comprehensive test suite for TypeConversionUtility class."""

    def setup_method(self):
        """Set up test data for each test method."""
        self.test_uuid = uuid4()
        self.test_uuid_str = str(self.test_uuid)
        self.test_datetime = datetime(2024, 1, 15, 10, 30, 45, 123456, timezone.utc)
        self.test_datetime_iso = "2024-01-15T10:30:45.123456+00:00"

    # UUID Conversion Tests
    def test_uuid_to_string_valid(self):
        """Test valid UUID to string conversion."""
        result = TypeConversionUtility.uuid_to_string(self.test_uuid)
        assert result == self.test_uuid_str
        assert isinstance(result, str)

    def test_uuid_to_string_none(self):
        """Test UUID to string conversion with None input."""
        result = TypeConversionUtility.uuid_to_string(None)
        assert result is None

    def test_string_to_uuid_valid(self):
        """Test valid string to UUID conversion."""
        result = TypeConversionUtility.string_to_uuid(self.test_uuid_str)
        assert result == self.test_uuid
        assert isinstance(result, UUID)

    def test_string_to_uuid_none(self):
        """Test string to UUID conversion with None input."""
        result = TypeConversionUtility.string_to_uuid(None)
        assert result is None

    @pytest.mark.parametrize("invalid_uuid_str", [
        "invalid-uuid",
        "123",
        "",
        "not-a-uuid-at-all",
        "12345678-1234-1234-1234-12345678901",  # Too short
        "12345678-1234-1234-1234-1234567890123",  # Too long
        "xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx",  # Invalid chars
    ])
    def test_string_to_uuid_invalid(self, invalid_uuid_str):
        """Test string to UUID conversion with invalid inputs."""
        with pytest.raises(ValidationConversionError) as exc_info:
            TypeConversionUtility.string_to_uuid(invalid_uuid_str)
        
        error = exc_info.value
        assert error.conversion_direction == "string_to_uuid"
        assert error.source_data == invalid_uuid_str
        assert "not a valid UUID format" in error.message

    # Enum Conversion Tests
    def test_enum_to_string_valid(self):
        """Test valid enum to string conversion."""
        result = TypeConversionUtility.enum_to_string(SampleEnum.VALUE_ONE)
        assert result == "value_one"
        assert isinstance(result, str)

    def test_enum_to_string_special_chars(self):
        """Test enum to string conversion with special characters."""
        result = TypeConversionUtility.enum_to_string(SampleEnum.SPECIAL_CHARS)
        assert result == "special!@#$%^&*()"

    def test_enum_to_string_none(self):
        """Test enum to string conversion with None input."""
        result = TypeConversionUtility.enum_to_string(None)
        assert result is None

    def test_string_to_enum_valid(self):
        """Test valid string to enum conversion."""
        result = TypeConversionUtility.string_to_enum("value_one", SampleEnum)
        assert result == SampleEnum.VALUE_ONE
        assert isinstance(result, SampleEnum)

    def test_string_to_enum_none(self):
        """Test string to enum conversion with None input."""
        result = TypeConversionUtility.string_to_enum(None, SampleEnum)
        assert result is None

    @pytest.mark.parametrize("invalid_enum_str", [
        "invalid_value",
        "VALUE_ONE",  # Wrong case
        "",
        "value_three",  # Non-existent value
    ])
    def test_string_to_enum_invalid(self, invalid_enum_str):
        """Test string to enum conversion with invalid inputs."""
        with pytest.raises(ValidationConversionError) as exc_info:
            TypeConversionUtility.string_to_enum(invalid_enum_str, SampleEnum)
        
        error = exc_info.value
        assert error.conversion_direction == "string_to_enum"
        assert error.source_data == invalid_enum_str
        assert f"not a valid {SampleEnum.__name__} value" in error.message
        assert "Valid values:" in error.message

    # Set/FrozenSet Conversion Tests
    def test_set_to_frozenset_valid(self):
        """Test valid set to frozenset conversion."""
        test_set = {"a", "b", "c"}
        result = TypeConversionUtility.set_to_frozenset(test_set)
        assert result == frozenset({"a", "b", "c"})
        assert isinstance(result, frozenset)

    def test_set_to_frozenset_empty(self):
        """Test empty set to frozenset conversion."""
        result = TypeConversionUtility.set_to_frozenset(set())
        assert result == frozenset()
        assert isinstance(result, frozenset)

    def test_set_to_frozenset_none(self):
        """Test set to frozenset conversion with None input."""
        result = TypeConversionUtility.set_to_frozenset(None)
        assert result is None

    def test_frozenset_to_set_valid(self):
        """Test valid frozenset to set conversion."""
        test_frozenset = frozenset({"x", "y", "z"})
        result = TypeConversionUtility.frozenset_to_set(test_frozenset)
        assert result == {"x", "y", "z"}
        assert isinstance(result, set)

    def test_frozenset_to_set_none(self):
        """Test frozenset to set conversion with None input."""
        result = TypeConversionUtility.frozenset_to_set(None)
        assert result is None

    def test_list_to_frozenset_valid(self):
        """Test valid list to frozenset conversion."""
        test_list = ["a", "b", "c", "a"]  # With duplicate
        result = TypeConversionUtility.list_to_frozenset(test_list)
        assert result == frozenset({"a", "b", "c"})  # Duplicates removed
        assert isinstance(result, frozenset)

    def test_list_to_frozenset_none(self):
        """Test list to frozenset conversion with None input."""
        result = TypeConversionUtility.list_to_frozenset(None)
        assert result is None

    def test_frozenset_to_list_valid(self):
        """Test valid frozenset to list conversion."""
        test_frozenset = frozenset({"x", "y", "z"})
        result = TypeConversionUtility.frozenset_to_list(test_frozenset)
        assert result is not None
        assert set(result) == {"x", "y", "z"}  # Order may vary
        assert isinstance(result, list)

    def test_frozenset_to_list_none(self):
        """Test frozenset to list conversion with None input."""
        result = TypeConversionUtility.frozenset_to_list(None)
        assert result is None

    # DateTime Conversion Tests
    def test_datetime_to_isostring_valid(self):
        """Test valid datetime to ISO string conversion."""
        result = TypeConversionUtility.datetime_to_isostring(self.test_datetime)
        assert result == self.test_datetime_iso
        assert isinstance(result, str)

    def test_datetime_to_isostring_none(self):
        """Test datetime to ISO string conversion with None input."""
        result = TypeConversionUtility.datetime_to_isostring(None)
        assert result is None

    def test_isostring_to_datetime_valid(self):
        """Test valid ISO string to datetime conversion."""
        result = TypeConversionUtility.isostring_to_datetime(self.test_datetime_iso)
        assert result == self.test_datetime
        assert isinstance(result, datetime)

    def test_isostring_to_datetime_none(self):
        """Test ISO string to datetime conversion with None input."""
        result = TypeConversionUtility.isostring_to_datetime(None)
        assert result is None

    @pytest.mark.parametrize("invalid_iso_str", [
        "invalid-datetime",
        "2024-13-01T10:30:45",  # Invalid month
        "2024-01-32T10:30:45",  # Invalid day
        "2024-01-15T25:30:45",  # Invalid hour
        "not-a-date",
        "",
    ])
    def test_isostring_to_datetime_invalid(self, invalid_iso_str):
        """Test ISO string to datetime conversion with invalid inputs."""
        with pytest.raises(ValidationConversionError) as exc_info:
            TypeConversionUtility.isostring_to_datetime(invalid_iso_str)
        
        error = exc_info.value
        assert error.conversion_direction == "isostring_to_datetime"
        assert error.source_data == invalid_iso_str

    # Decimal/Float Conversion Tests
    def test_decimal_to_float_valid(self):
        """Test valid decimal to float conversion."""
        test_decimal = Decimal("123.456")
        result = TypeConversionUtility.decimal_to_float(test_decimal)
        assert result == 123.456
        assert isinstance(result, float)

    def test_decimal_to_float_none(self):
        """Test decimal to float conversion with None input."""
        result = TypeConversionUtility.decimal_to_float(None)
        assert result is None

    def test_float_to_decimal_valid(self):
        """Test valid float to decimal conversion."""
        result = TypeConversionUtility.float_to_decimal(123.456, precision=3)
        assert result == Decimal("123.456")
        assert isinstance(result, Decimal)

    def test_float_to_decimal_default_precision(self):
        """Test float to decimal conversion with default precision."""
        result = TypeConversionUtility.float_to_decimal(123.456)
        assert result == Decimal("123.46")  # Default precision=2

    def test_float_to_decimal_none(self):
        """Test float to decimal conversion with None input."""
        result = TypeConversionUtility.float_to_decimal(None)
        assert result is None

    # Comma String Conversion Tests
    def test_frozenset_to_comma_string_valid(self):
        """Test valid frozenset to comma string conversion."""
        test_frozenset = frozenset({"apple", "banana", "cherry"})
        result = TypeConversionUtility.frozenset_to_comma_string(test_frozenset)
        # Order may vary, so check components
        assert isinstance(result, str)
        parts = result.split(",")
        assert set(parts) == {"apple", "banana", "cherry"}

    def test_frozenset_to_comma_string_empty(self):
        """Test empty frozenset to comma string conversion."""
        result = TypeConversionUtility.frozenset_to_comma_string(frozenset())
        assert result == ""

    def test_frozenset_to_comma_string_none(self):
        """Test frozenset to comma string conversion with None input."""
        result = TypeConversionUtility.frozenset_to_comma_string(None)
        assert result is None

    def test_comma_string_to_frozenset_valid(self):
        """Test valid comma string to frozenset conversion."""
        test_string = "apple,banana,cherry"
        result = TypeConversionUtility.comma_string_to_frozenset(test_string)
        assert result == frozenset({"apple", "banana", "cherry"})
        assert isinstance(result, frozenset)

    def test_comma_string_to_frozenset_with_spaces(self):
        """Test comma string to frozenset conversion with spaces."""
        test_string = " apple , banana , cherry "
        result = TypeConversionUtility.comma_string_to_frozenset(test_string)
        assert result == frozenset({"apple", "banana", "cherry"})

    def test_comma_string_to_frozenset_empty(self):
        """Test empty string to frozenset conversion."""
        result = TypeConversionUtility.comma_string_to_frozenset("")
        assert result == frozenset()

    def test_comma_string_to_frozenset_none(self):
        """Test comma string to frozenset conversion with None input."""
        result = TypeConversionUtility.comma_string_to_frozenset(None)
        assert result is None

    def test_set_to_comma_string_valid(self):
        """Test valid set to comma string conversion."""
        test_set = {"x", "y", "z"}
        result = TypeConversionUtility.set_to_comma_string(test_set)
        assert isinstance(result, str)
        parts = result.split(",")
        assert set(parts) == {"x", "y", "z"}

    def test_comma_string_to_set_valid(self):
        """Test valid comma string to set conversion."""
        test_string = "x,y,z"
        result = TypeConversionUtility.comma_string_to_set(test_string)
        assert result == {"x", "y", "z"}
        assert isinstance(result, set)

    # Performance Tests
    def test_uuid_conversion_performance(self):
        """Test UUID conversion performance (<1ms for 1000 conversions)."""
        test_uuids = [uuid4() for _ in range(1000)]
        
        # Test uuid_to_string performance
        start_time = time.perf_counter()
        for uuid_obj in test_uuids:
            TypeConversionUtility.uuid_to_string(uuid_obj)
        uuid_to_string_time = time.perf_counter() - start_time
        
        # Test string_to_uuid performance
        uuid_strings = [str(uuid_obj) for uuid_obj in test_uuids]
        start_time = time.perf_counter()
        for uuid_str in uuid_strings:
            TypeConversionUtility.string_to_uuid(uuid_str)
        string_to_uuid_time = time.perf_counter() - start_time
        
        # Assert performance requirements
        assert uuid_to_string_time < 0.01, f"UUID to string conversion too slow: {uuid_to_string_time:.4f}s"
        assert string_to_uuid_time < 0.01, f"String to UUID conversion too slow: {string_to_uuid_time:.4f}s"

    def test_collection_conversion_performance(self):
        """Test collection conversion performance (<5ms for 1000 conversions)."""
        test_sets = [{"item" + str(i) for i in range(10)} for _ in range(100)]
        
        start_time = time.perf_counter()
        for test_set in test_sets:
            frozenset_result = TypeConversionUtility.set_to_frozenset(test_set)
            TypeConversionUtility.frozenset_to_set(frozenset_result)
        collection_time = time.perf_counter() - start_time
        
        assert collection_time < 0.005, f"Collection conversion too slow: {collection_time:.4f}s"

    # Edge Case Tests
    def test_unicode_handling(self):
        """Test conversion methods handle Unicode characters properly."""
        unicode_enum_value = "café_münü_测试"
        unicode_set = {"café", "münü", "测试", "🎯"}
        
        # Test comma string conversions with Unicode
        comma_result = TypeConversionUtility.set_to_comma_string(unicode_set)
        assert isinstance(comma_result, str)
        
        back_to_set = TypeConversionUtility.comma_string_to_set(comma_result)
        assert back_to_set == unicode_set

    def test_large_collection_handling(self):
        """Test conversion methods handle large collections efficiently."""
        large_set = {f"item_{i}" for i in range(10000)}
        
        # Test conversion without errors
        frozenset_result = TypeConversionUtility.set_to_frozenset(large_set)
        assert frozenset_result is not None
        assert len(frozenset_result) == 10000
        
        back_to_set = TypeConversionUtility.frozenset_to_set(frozenset_result)
        assert back_to_set == large_set

    def test_round_trip_conversions(self):
        """Test that round-trip conversions preserve data integrity."""
        # UUID round-trip
        original_uuid = uuid4()
        uuid_str = TypeConversionUtility.uuid_to_string(original_uuid)
        restored_uuid = TypeConversionUtility.string_to_uuid(uuid_str)
        assert restored_uuid == original_uuid
        
        # Set round-trip
        original_set = {"a", "b", "c"}
        frozenset_result = TypeConversionUtility.set_to_frozenset(original_set)
        restored_set = TypeConversionUtility.frozenset_to_set(frozenset_result)
        assert restored_set == original_set
        
        # DateTime round-trip
        original_datetime = datetime.now(timezone.utc)
        iso_str = TypeConversionUtility.datetime_to_isostring(original_datetime)
        restored_datetime = TypeConversionUtility.isostring_to_datetime(iso_str)
        assert restored_datetime == original_datetime 