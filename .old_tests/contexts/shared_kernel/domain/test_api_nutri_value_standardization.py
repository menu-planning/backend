"""
Behavior-focused tests for ApiNutriValue schema standardization.

These tests validate the behavior and correctness of ApiNutriValue schema
following the documented API schema patterns.

Focus: Test behavior and verify correctness, not implementation details.
"""

import pytest
from unittest.mock import Mock

from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_value import ApiNutriValue
from src.contexts.shared_kernel.domain.enums import MeasureUnit


class TestApiNutriValueStandardization:
    """Test ApiNutriValue schema standardization and behavior."""

    def test_nutri_value_creation_with_valid_data(self):
        """Test that ApiNutriValue accepts valid nutritional value data."""
        nutri_value = ApiNutriValue(
            unit=MeasureUnit.GRAM,
            value=150.5
        )
        
        assert nutri_value.unit == MeasureUnit.GRAM
        assert nutri_value.value == 150.5

    def test_nutri_value_creation_with_none_values(self):
        """Test that ApiNutriValue requires both value and unit."""
        # Both value and unit are required fields
        with pytest.raises(ValueError):
            nutri_value = ApiNutriValue(unit=None, value=None)  # type: ignore

    def test_value_validation_rejects_negative_numbers(self):
        """Test that negative nutritional values are rejected."""
        with pytest.raises(ValueError, match="Nutritional values must be non-negative"):
            ApiNutriValue(value=-10.0, unit=MeasureUnit.GRAM)

    def test_value_validation_accepts_zero_and_positive_numbers(self):
        """Test that zero and positive nutritional values are accepted."""
        valid_values = [0.0, 0.1, 1.0, 100.0, 1000.0]
        
        for value in valid_values:
            nutri_value = ApiNutriValue(value=value, unit=MeasureUnit.GRAM)
            assert nutri_value.value == value

    def test_from_domain_conversion_preserves_data(self):
        """Test that from_domain conversion preserves all data correctly."""
        domain_nutri_value = Mock()
        domain_nutri_value.unit = MeasureUnit.MILLIGRAM
        domain_nutri_value.value = 75.3
        
        api_nutri_value = ApiNutriValue.from_domain(domain_nutri_value)
        
        assert api_nutri_value.unit == MeasureUnit.MILLIGRAM
        assert api_nutri_value.value == 75.3

    def test_to_domain_conversion_handles_enum_properly(self):
        """Test that to_domain conversion handles enum conversion correctly."""
        api_nutri_value = ApiNutriValue(
            unit=MeasureUnit.KILOGRAM,
            value=2.5
        )
        
        domain_nutri_value = api_nutri_value.to_domain()
        
        assert domain_nutri_value.unit == MeasureUnit.KILOGRAM
        assert domain_nutri_value.value == 2.5

    def test_from_orm_model_not_implemented(self):
        """Test that from_orm_model raises NotImplementedError as documented."""
        orm_model = Mock()
        orm_model.value = 100.0
        orm_model.unit = MeasureUnit.GRAM
        
        # The method calls super().from_orm_model() which raises NotImplementedError
        with pytest.raises(NotImplementedError):
            ApiNutriValue.from_orm_model(orm_model)

    def test_to_orm_kwargs_excludes_unit_field(self):
        """Test that to_orm_kwargs excludes unit field as documented."""
        api_nutri_value = ApiNutriValue(
            unit=MeasureUnit.MILLIGRAM,
            value=50.0
        )
        
        orm_kwargs = api_nutri_value.to_orm_kwargs()
        
        # Unit is excluded as per the implementation
        assert 'unit' not in orm_kwargs
        assert orm_kwargs['value'] == 50.0

    def test_round_trip_conversion_preserves_data_integrity(self):
        """Test that domain → API → domain conversion preserves data integrity."""
        original_domain = Mock()
        original_domain.unit = MeasureUnit.KILOGRAM
        original_domain.value = 1.25
        
        # Convert to API and back
        api_nutri_value = ApiNutriValue.from_domain(original_domain)
        converted_domain = api_nutri_value.to_domain()
        
        assert converted_domain.unit == original_domain.unit
        assert converted_domain.value == original_domain.value


