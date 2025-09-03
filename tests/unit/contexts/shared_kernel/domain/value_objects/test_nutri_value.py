"""Unit tests for NutriValue value object.

Tests value object invariants, equality semantics, and arithmetic operations.
Focuses on business behavior without I/O dependencies.
"""

import pytest

from src.contexts.shared_kernel.domain.enums import MeasureUnit
from src.contexts.shared_kernel.domain.value_objects.nutri_value import NutriValue


class TestNutriValueValidation:
    """Test value object invariants and constraints."""

    def test_creates_valid_nutri_value_with_positive_value(self) -> None:
        """Test creating NutriValue with valid positive value."""
        # Given
        unit = MeasureUnit.GRAM
        value = 25.5

        # When
        nutri_value = NutriValue(unit=unit, value=value)

        # Then
        assert nutri_value.unit == unit
        assert nutri_value.value == value

    def test_creates_valid_nutri_value_with_zero_value(self) -> None:
        """Test creating NutriValue with zero value."""
        # Given
        unit = MeasureUnit.MILLIGRAM
        value = 0.0

        # When
        nutri_value = NutriValue(unit=unit, value=value)

        # Then
        assert nutri_value.unit == unit
        assert nutri_value.value == value

    def test_creates_valid_nutri_value_with_negative_value(self) -> None:
        """Test creating NutriValue with negative value (valid for nutrition)."""
        # Given
        unit = MeasureUnit.PERCENT
        value = -5.0

        # When
        nutri_value = NutriValue(unit=unit, value=value)

        # Then
        assert nutri_value.unit == unit
        assert nutri_value.value == value

    def test_creates_valid_nutri_value_with_all_measure_units(self) -> None:
        """Test creating NutriValue with all available measure units."""
        # Given
        units = [
            MeasureUnit.UNIT,
            MeasureUnit.KILOGRAM,
            MeasureUnit.GRAM,
            MeasureUnit.MILLIGRAM,
            MeasureUnit.MICROGRAM,
            MeasureUnit.LITER,
            MeasureUnit.MILLILITER,
            MeasureUnit.PERCENT,
            MeasureUnit.ENERGY,
            MeasureUnit.IU,
            MeasureUnit.TABLESPOON,
            MeasureUnit.TEASPOON,
            MeasureUnit.CUP,
            MeasureUnit.PINCH,
            MeasureUnit.HANDFUL,
            MeasureUnit.SLICE,
            MeasureUnit.PIECE,
        ]

        # When/Then
        for unit in units:
            nutri_value = NutriValue(unit=unit, value=10.0)
            assert nutri_value.unit == unit
            assert nutri_value.value == 10.0

    def test_creates_valid_nutri_value_with_float_precision(self) -> None:
        """Test creating NutriValue with various float precisions."""
        # Given
        unit = MeasureUnit.GRAM
        test_values = [1.0, 1.5, 0.1, 0.01, 0.001, 123.456789]

        # When/Then
        for value in test_values:
            nutri_value = NutriValue(unit=unit, value=value)
            assert nutri_value.value == value

    def test_nutri_value_is_immutable(self) -> None:
        """Test that NutriValue is immutable after creation."""
        # Given
        nutri_value = NutriValue(unit=MeasureUnit.GRAM, value=25.0)

        # When/Then
        with pytest.raises(AttributeError):
            nutri_value.value = 30.0  # type: ignore

        with pytest.raises(AttributeError):
            nutri_value.unit = MeasureUnit.KILOGRAM  # type: ignore


class TestNutriValueEquality:
    """Test value object contracts and equality semantics."""

    def test_equality_with_same_unit_and_value(self) -> None:
        """Test equality when unit and value are identical."""
        # Given
        unit = MeasureUnit.GRAM
        value = 25.5

        # When
        nutri_value1 = NutriValue(unit=unit, value=value)
        nutri_value2 = NutriValue(unit=unit, value=value)

        # Then
        assert nutri_value1 == nutri_value2
        assert hash(nutri_value1) == hash(nutri_value2)

    def test_inequality_with_different_units(self) -> None:
        """Test inequality when units differ but values are same."""
        # Given
        value = 25.5

        # When
        nutri_value1 = NutriValue(unit=MeasureUnit.GRAM, value=value)
        nutri_value2 = NutriValue(unit=MeasureUnit.MILLIGRAM, value=value)

        # Then
        assert nutri_value1 != nutri_value2

    def test_inequality_with_different_values(self) -> None:
        """Test inequality when values differ but units are same."""
        # Given
        unit = MeasureUnit.GRAM

        # When
        nutri_value1 = NutriValue(unit=unit, value=25.5)
        nutri_value2 = NutriValue(unit=unit, value=30.0)

        # Then
        assert nutri_value1 != nutri_value2

    def test_inequality_with_different_units_and_values(self) -> None:
        """Test inequality when both units and values differ."""
        # When
        nutri_value1 = NutriValue(unit=MeasureUnit.GRAM, value=25.5)
        nutri_value2 = NutriValue(unit=MeasureUnit.KILOGRAM, value=0.0255)

        # Then
        assert nutri_value1 != nutri_value2

    def test_equality_with_zero_values(self) -> None:
        """Test equality with zero values."""
        # Given
        unit = MeasureUnit.GRAM

        # When
        nutri_value1 = NutriValue(unit=unit, value=0.0)
        nutri_value2 = NutriValue(unit=unit, value=0.0)

        # Then
        assert nutri_value1 == nutri_value2

    def test_equality_with_negative_values(self) -> None:
        """Test equality with negative values."""
        # Given
        unit = MeasureUnit.PERCENT
        value = -5.0

        # When
        nutri_value1 = NutriValue(unit=unit, value=value)
        nutri_value2 = NutriValue(unit=unit, value=value)

        # Then
        assert nutri_value1 == nutri_value2

    def test_equality_consistency_with_hash(self) -> None:
        """Test that equal objects have equal hashes."""
        # Given
        unit = MeasureUnit.GRAM
        value = 25.5

        # When
        nutri_value1 = NutriValue(unit=unit, value=value)
        nutri_value2 = NutriValue(unit=unit, value=value)

        # Then
        assert nutri_value1 == nutri_value2
        assert hash(nutri_value1) == hash(nutri_value2)

    def test_inequality_with_non_nutri_value(self) -> None:
        """Test inequality with non-NutriValue objects."""
        # Given
        nutri_value = NutriValue(unit=MeasureUnit.GRAM, value=25.5)

        # When/Then
        assert nutri_value != "not a nutri value"
        assert nutri_value != 25.5
        assert nutri_value != None  # noqa: E711
        assert nutri_value != MeasureUnit.GRAM


class TestNutriValueArithmetic:
    """Test arithmetic operations on NutriValue."""

    def test_addition_with_same_units(self) -> None:
        """Test addition of NutriValues with same units."""
        # Given
        unit = MeasureUnit.GRAM
        nutri_value1 = NutriValue(unit=unit, value=25.0)
        nutri_value2 = NutriValue(unit=unit, value=15.0)

        # When
        result = nutri_value1 + nutri_value2

        # Then
        assert result.unit == unit
        assert result.value == 40.0

    def test_addition_with_different_units(self) -> None:
        """Test addition of NutriValues with different units."""
        # Given
        nutri_value1 = NutriValue(unit=MeasureUnit.GRAM, value=25.0)
        nutri_value2 = NutriValue(unit=MeasureUnit.MILLIGRAM, value=15.0)

        # When
        result = nutri_value1 + nutri_value2

        # Then
        # Should use the first unit as fallback
        assert result.unit == MeasureUnit.GRAM
        assert result.value == 40.0

    def test_addition_with_none(self) -> None:
        """Test addition with None returns original value."""
        # Given
        nutri_value = NutriValue(unit=MeasureUnit.GRAM, value=25.0)

        # When
        result = nutri_value + None

        # Then
        assert result == nutri_value

    def test_subtraction_with_same_units(self) -> None:
        """Test subtraction of NutriValues with same units."""
        # Given
        unit = MeasureUnit.GRAM
        nutri_value1 = NutriValue(unit=unit, value=25.0)
        nutri_value2 = NutriValue(unit=unit, value=15.0)

        # When
        result = nutri_value1 - nutri_value2

        # Then
        assert result.unit == unit
        assert result.value == 10.0

    def test_subtraction_with_different_units(self) -> None:
        """Test subtraction of NutriValues with different units."""
        # Given
        nutri_value1 = NutriValue(unit=MeasureUnit.GRAM, value=25.0)
        nutri_value2 = NutriValue(unit=MeasureUnit.MILLIGRAM, value=15.0)

        # When
        result = nutri_value1 - nutri_value2

        # Then
        # Should use the first unit as fallback
        assert result.unit == MeasureUnit.GRAM
        assert result.value == 10.0

    def test_subtraction_with_none(self) -> None:
        """Test subtraction with None returns original value."""
        # Given
        nutri_value = NutriValue(unit=MeasureUnit.GRAM, value=25.0)

        # When
        result = nutri_value - None

        # Then
        assert result == nutri_value

    def test_multiplication_with_float(self) -> None:
        """Test multiplication with float scalar."""
        # Given
        nutri_value = NutriValue(unit=MeasureUnit.GRAM, value=25.0)
        multiplier = 2.5

        # When
        result = nutri_value * multiplier

        # Then
        assert result.unit == MeasureUnit.GRAM
        assert result.value == 62.5

    def test_multiplication_with_zero(self) -> None:
        """Test multiplication with zero."""
        # Given
        nutri_value = NutriValue(unit=MeasureUnit.GRAM, value=25.0)

        # When
        result = nutri_value * 0.0

        # Then
        assert result.unit == MeasureUnit.GRAM
        assert result.value == 0.0

    def test_multiplication_with_negative_scalar(self) -> None:
        """Test multiplication with negative scalar."""
        # Given
        nutri_value = NutriValue(unit=MeasureUnit.GRAM, value=25.0)

        # When
        result = nutri_value * -1.0

        # Then
        assert result.unit == MeasureUnit.GRAM
        assert result.value == -25.0

    def test_multiplication_with_non_float_returns_not_implemented(self) -> None:
        """Test multiplication with non-float returns NotImplemented."""
        # Given
        nutri_value = NutriValue(unit=MeasureUnit.GRAM, value=25.0)

        # When
        result = nutri_value.__mul__("not a float")  # type: ignore

        # Then
        assert result is NotImplemented

    def test_arithmetic_operations_preserve_immutability(self) -> None:
        """Test that arithmetic operations preserve immutability."""
        # Given
        nutri_value1 = NutriValue(unit=MeasureUnit.GRAM, value=25.0)
        nutri_value2 = NutriValue(unit=MeasureUnit.GRAM, value=15.0)

        # When
        result = nutri_value1 + nutri_value2

        # Then
        # Original values should be unchanged
        assert nutri_value1.value == 25.0
        assert nutri_value2.value == 15.0
        # Result should be a new instance
        assert result is not nutri_value1
        assert result is not nutri_value2


class TestNutriValueEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_very_large_values(self) -> None:
        """Test NutriValue with very large values."""
        # Given
        unit = MeasureUnit.GRAM
        large_value = 999999.999

        # When
        nutri_value = NutriValue(unit=unit, value=large_value)

        # Then
        assert nutri_value.value == large_value

    def test_very_small_values(self) -> None:
        """Test NutriValue with very small values."""
        # Given
        unit = MeasureUnit.MICROGRAM
        small_value = 0.000001

        # When
        nutri_value = NutriValue(unit=unit, value=small_value)

        # Then
        assert nutri_value.value == small_value

    def test_float_precision_handling(self) -> None:
        """Test handling of float precision in arithmetic."""
        # Given
        unit = MeasureUnit.GRAM
        nutri_value1 = NutriValue(unit=unit, value=0.1)
        nutri_value2 = NutriValue(unit=unit, value=0.2)

        # When
        result = nutri_value1 + nutri_value2

        # Then
        # Should handle float precision correctly
        assert abs(result.value - 0.3) < 1e-10

    def test_arithmetic_with_extreme_values(self) -> None:
        """Test arithmetic operations with extreme values."""
        # Given
        unit = MeasureUnit.GRAM
        nutri_value1 = NutriValue(unit=unit, value=1e6)
        nutri_value2 = NutriValue(unit=unit, value=1e-6)

        # When
        result_add = nutri_value1 + nutri_value2
        result_sub = nutri_value1 - nutri_value2
        result_mul = nutri_value1 * 0.5

        # Then
        assert result_add.value == 1000000.000001
        assert result_sub.value == 999999.999999
        assert result_mul.value == 500000.0

    def test_unit_compatibility_fallback_behavior(self) -> None:
        """Test unit compatibility fallback behavior in arithmetic."""
        # Given
        nutri_value1 = NutriValue(unit=MeasureUnit.GRAM, value=25.0)
        nutri_value2 = NutriValue(unit=MeasureUnit.KILOGRAM, value=0.025)

        # When
        result = nutri_value1 + nutri_value2

        # Then
        # Should use first unit as fallback
        assert result.unit == MeasureUnit.GRAM
        assert result.value == 25.025  # 25.0 + 0.025 (no unit conversion, just adds values)

    def test_arithmetic_chain_operations(self) -> None:
        """Test chaining multiple arithmetic operations."""
        # Given
        base_value = NutriValue(unit=MeasureUnit.GRAM, value=100.0)
        add_value = NutriValue(unit=MeasureUnit.GRAM, value=50.0)
        subtract_value = NutriValue(unit=MeasureUnit.GRAM, value=25.0)

        # When
        result = (base_value + add_value - subtract_value) * 2.0

        # Then
        assert result.unit == MeasureUnit.GRAM
        assert result.value == 250.0  # (100 + 50 - 25) * 2
