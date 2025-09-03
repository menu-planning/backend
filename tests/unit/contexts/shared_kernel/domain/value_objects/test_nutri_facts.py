"""Unit tests for NutriFacts value object.

Tests nutrition calculation logic, equality semantics, and value object contracts.
"""
import pytest
from typing import Any
from src.contexts.shared_kernel.domain.enums import MeasureUnit
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.value_objects.nutri_value import NutriValue


class TestNutriFactsAggregation:
    """Test nutrition calculation logic and aggregation behavior."""

    def test_nutri_facts_aggregation_happy_path(self):
        """Test basic nutrition aggregation with valid values."""
        # Given
        facts1 = NutriFacts(
            calories=NutriValue(value=100.0, unit=MeasureUnit.ENERGY),
            protein=NutriValue(value=5.0, unit=MeasureUnit.GRAM),
            sodium=NutriValue(value=200.0, unit=MeasureUnit.MILLIGRAM),
        )
        facts2 = NutriFacts(
            calories=NutriValue(value=150.0, unit=MeasureUnit.ENERGY),
            protein=NutriValue(value=8.0, unit=MeasureUnit.GRAM),
            sodium=NutriValue(value=300.0, unit=MeasureUnit.MILLIGRAM),
        )

        # When
        result = facts1 + facts2

        # Then
        assert result.calories.value == 250.0
        assert result.calories.unit == MeasureUnit.ENERGY
        assert result.protein.value == 13.0
        assert result.protein.unit == MeasureUnit.GRAM
        assert result.sodium.value == 500.0
        assert result.sodium.unit == MeasureUnit.MILLIGRAM

    def test_nutri_facts_aggregation_with_none_values(self):
        """Test aggregation when some values are None."""
        # Given
        facts1 = NutriFacts(
            calories=NutriValue(value=100.0, unit=MeasureUnit.ENERGY),
            protein=None,  # type: ignore  # This will be converted to zero value
        )
        facts2 = NutriFacts(
            calories=NutriValue(value=150.0, unit=MeasureUnit.ENERGY),
            protein=NutriValue(value=8.0, unit=MeasureUnit.GRAM),
        )

        # When
        result = facts1 + facts2

        # Then
        assert result.calories.value == 250.0
        assert result.protein.value == 8.0  # 0 + 8

    def test_nutri_facts_aggregation_with_mixed_input_types(self):
        """Test aggregation with different input types (numeric, dict, NutriValue)."""
        # Given
        facts1 = NutriFacts(
            calories=100.0,  # type: ignore  # Numeric input
            protein={"value": 5.0, "unit": MeasureUnit.GRAM},  # type: ignore  # Dict input
            sodium=NutriValue(value=200.0, unit=MeasureUnit.MILLIGRAM),  # NutriValue input
        )
        facts2 = NutriFacts(
            calories=150.0,  # type: ignore
            protein=8.0,  # type: ignore
            sodium=300.0,  # type: ignore
        )

        # When
        result = facts1 + facts2

        # Then
        assert result.calories.value == 250.0
        assert result.calories.unit == MeasureUnit.ENERGY
        assert result.protein.value == 13.0
        assert result.protein.unit == MeasureUnit.GRAM
        assert result.sodium.value == 500.0
        assert result.sodium.unit == MeasureUnit.MILLIGRAM

    def test_nutri_facts_subtraction(self):
        """Test nutrition subtraction operation."""
        # Given
        facts1 = NutriFacts(
            calories=NutriValue(value=300.0, unit=MeasureUnit.ENERGY),
            protein=NutriValue(value=15.0, unit=MeasureUnit.GRAM),
            sodium=NutriValue(value=500.0, unit=MeasureUnit.MILLIGRAM),
        )
        facts2 = NutriFacts(
            calories=NutriValue(value=100.0, unit=MeasureUnit.ENERGY),
            protein=NutriValue(value=5.0, unit=MeasureUnit.GRAM),
            sodium=NutriValue(value=200.0, unit=MeasureUnit.MILLIGRAM),
        )

        # When
        result = facts1 - facts2

        # Then
        assert result.calories.value == 200.0
        assert result.calories.unit == MeasureUnit.ENERGY
        assert result.protein.value == 10.0
        assert result.protein.unit == MeasureUnit.GRAM
        assert result.sodium.value == 300.0
        assert result.sodium.unit == MeasureUnit.MILLIGRAM

    def test_nutri_facts_aggregation_immutability(self):
        """Test that aggregation operations don't modify original instances."""
        # Given
        facts1 = NutriFacts(
            calories=NutriValue(value=100.0, unit=MeasureUnit.ENERGY),
            protein=NutriValue(value=5.0, unit=MeasureUnit.GRAM),
        )
        facts2 = NutriFacts(
            calories=NutriValue(value=150.0, unit=MeasureUnit.ENERGY),
            protein=NutriValue(value=8.0, unit=MeasureUnit.GRAM),
        )
        original_calories1 = facts1.calories.value
        original_protein1 = facts1.protein.value

        # When
        result = facts1 + facts2

        # Then
        assert facts1.calories.value == original_calories1
        assert facts1.protein.value == original_protein1
        assert result is not facts1
        assert result is not facts2


class TestNutriFactsEquality:
    """Test equality semantics and value object contracts."""

    def test_nutri_facts_equality_identical_instances(self):
        """Test equality with identical instances."""
        # Given
        facts1 = NutriFacts(
            calories=NutriValue(value=100.0, unit=MeasureUnit.ENERGY),
            protein=NutriValue(value=5.0, unit=MeasureUnit.GRAM),
            sodium=NutriValue(value=200.0, unit=MeasureUnit.MILLIGRAM),
        )
        facts2 = NutriFacts(
            calories=NutriValue(value=100.0, unit=MeasureUnit.ENERGY),
            protein=NutriValue(value=5.0, unit=MeasureUnit.GRAM),
            sodium=NutriValue(value=200.0, unit=MeasureUnit.MILLIGRAM),
        )

        # When & Then
        assert facts1 == facts2
        assert hash(facts1) == hash(facts2)

    def test_nutri_facts_equality_different_values(self):
        """Test inequality with different values."""
        # Given
        facts1 = NutriFacts(
            calories=NutriValue(value=100.0, unit=MeasureUnit.ENERGY),
            protein=NutriValue(value=5.0, unit=MeasureUnit.GRAM),
        )
        facts2 = NutriFacts(
            calories=NutriValue(value=150.0, unit=MeasureUnit.ENERGY),
            protein=NutriValue(value=8.0, unit=MeasureUnit.GRAM),
        )

        # When & Then
        assert facts1 != facts2

    def test_nutri_facts_equality_different_units(self):
        """Test inequality with different units."""
        # Given
        facts1 = NutriFacts(
            calories=NutriValue(value=100.0, unit=MeasureUnit.ENERGY),
        )
        facts2 = NutriFacts(
            calories=NutriValue(value=100.0, unit=MeasureUnit.GRAM),
        )

        # When & Then
        assert facts1 != facts2

    def test_nutri_facts_equality_with_none_values(self):
        """Test equality with None values (should be converted to zero)."""
        # Given
        facts1 = NutriFacts(
            calories=NutriValue(value=100.0, unit=MeasureUnit.ENERGY),
            protein=None,  # type: ignore  # Will be converted to zero
        )
        facts2 = NutriFacts(
            calories=NutriValue(value=100.0, unit=MeasureUnit.ENERGY),
            protein=NutriValue(value=0.0, unit=MeasureUnit.GRAM),
        )

        # When & Then
        assert facts1 == facts2

    def test_nutri_facts_equality_with_mixed_input_types(self):
        """Test equality with different input types that result in same values."""
        # Given
        facts1 = NutriFacts(
            calories=100.0,  # type: ignore  # Numeric
            protein={"value": 5.0, "unit": MeasureUnit.GRAM},  # type: ignore  # Dict
        )
        facts2 = NutriFacts(
            calories=NutriValue(value=100.0, unit=MeasureUnit.ENERGY),  # NutriValue
            protein=NutriValue(value=5.0, unit=MeasureUnit.GRAM),  # NutriValue
        )

        # When & Then
        assert facts1 == facts2

    def test_nutri_facts_equality_different_class(self):
        """Test inequality with different class instances."""
        # Given
        facts = NutriFacts(
            calories=NutriValue(value=100.0, unit=MeasureUnit.ENERGY),
        )
        other_object = "not a NutriFacts instance"

        # When & Then
        assert facts != other_object


class TestNutriFactsValueObjectContracts:
    """Test value object contracts and invariants."""

    def test_nutri_facts_immutability(self):
        """Test that NutriFacts instances are immutable."""
        # Given
        facts = NutriFacts(
            calories=NutriValue(value=100.0, unit=MeasureUnit.ENERGY),
            protein=NutriValue(value=5.0, unit=MeasureUnit.GRAM),
        )

        # When & Then - Should raise AttributeError on modification attempts
        with pytest.raises(AttributeError):
            facts.calories = NutriValue(value=200.0, unit=MeasureUnit.ENERGY)  # type: ignore

        with pytest.raises(AttributeError):
            facts.protein = NutriValue(value=10.0, unit=MeasureUnit.GRAM)  # type: ignore

    def test_nutri_facts_default_units_mapping(self):
        """Test that default units mapping is correctly applied."""
        # Given
        facts = NutriFacts(
            calories=100.0,  # type: ignore  # Should get ENERGY unit
            protein=5.0,     # type: ignore  # Should get GRAM unit
            sodium=200.0,    # type: ignore  # Should get MILLIGRAM unit
            vitamin_a=100.0, # type: ignore  # Should get IU unit
        )

        # When & Then
        assert facts.calories.unit == MeasureUnit.ENERGY
        assert facts.protein.unit == MeasureUnit.GRAM
        assert facts.sodium.unit == MeasureUnit.MILLIGRAM
        assert facts.vitamin_a.unit == MeasureUnit.IU

    def test_nutri_facts_all_nutrients_have_default_units(self):
        """Test that all nutrient fields have corresponding default units."""
        # Given
        facts = NutriFacts()

        # When & Then - All fields should have proper units from default_units mapping
        for field_name in NutriFacts.default_units:
            field_value = getattr(facts, field_name)
            expected_unit = NutriFacts.default_units[field_name]
            assert field_value.unit == expected_unit
            assert field_value.value == 0.0  # Default value

    def test_nutri_facts_arithmetic_with_non_nutri_facts(self):
        """Test arithmetic operations with non-NutriFacts instances."""
        # Given
        facts = NutriFacts(
            calories=NutriValue(value=100.0, unit=MeasureUnit.ENERGY),
        )
        other_object = "not a NutriFacts instance"

        # When & Then - Should raise TypeError for unsupported operand types
        with pytest.raises(TypeError, match="unsupported operand type"):
            facts + other_object  # type: ignore

        with pytest.raises(TypeError, match="unsupported operand type"):
            facts - other_object  # type: ignore