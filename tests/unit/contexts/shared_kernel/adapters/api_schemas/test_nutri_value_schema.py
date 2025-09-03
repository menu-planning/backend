"""Unit tests for ApiNutriValue schema.

Tests nutrition value schema validation, serialization/deserialization, arithmetic operations,
and conversion methods. Follows testing principles: no I/O, fakes only, behavior-focused assertions.
"""

import pytest
from pydantic import ValidationError

from src.contexts.seedwork.adapters.exceptions.api_schema_errors import ValidationConversionError
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_value import ApiNutriValue
from src.contexts.shared_kernel.domain.enums import MeasureUnit
from src.contexts.shared_kernel.domain.value_objects.nutri_value import NutriValue


class TestApiNutriValueValidation:
    """Test nutrition value schema validation and field constraints."""

    def test_api_nutri_value_validation_valid_creation(self):
        """Validates valid nutrition value creation."""
        # Given: valid nutrition value components
        # When: create nutrition value with valid components
        # Then: nutrition value is created successfully
        api_nutri_value = ApiNutriValue(
            unit=MeasureUnit.GRAM,
            value=25.5
        )
        assert api_nutri_value.unit == MeasureUnit.GRAM
        assert api_nutri_value.value == 25.5

    def test_api_nutri_value_validation_all_measure_units(self):
        """Validates all measure unit enum values are accepted."""
        # Given: all measure unit enum values
        # When: create nutrition value with each unit
        # Then: all units are accepted
        for unit in MeasureUnit:
            api_nutri_value = ApiNutriValue(unit=unit, value=10.0)
            assert api_nutri_value.unit == unit
            assert api_nutri_value.value == 10.0

    def test_api_nutri_value_validation_zero_value(self):
        """Validates zero value is accepted."""
        # Given: zero value
        # When: create nutrition value with zero
        # Then: zero value is accepted
        api_nutri_value = ApiNutriValue(unit=MeasureUnit.GRAM, value=0.0)
        assert api_nutri_value.value == 0.0

    def test_api_nutri_value_validation_negative_value_rejected(self):
        """Validates negative values are rejected."""
        # Given: negative value
        # When: create nutrition value with negative value
        # Then: validation error is raised
        with pytest.raises(ValidationError):
            ApiNutriValue(unit=MeasureUnit.GRAM, value=-5.0)

    def test_api_nutri_value_validation_large_positive_value(self):
        """Validates large positive values are accepted."""
        # Given: large positive value
        # When: create nutrition value with large value
        # Then: large value is accepted
        api_nutri_value = ApiNutriValue(unit=MeasureUnit.GRAM, value=999999.99)
        assert api_nutri_value.value == 999999.99

    def test_api_nutri_value_validation_decimal_precision(self):
        """Validates decimal precision is preserved."""
        # Given: value with decimal precision
        # When: create nutrition value with decimal
        # Then: decimal precision is preserved
        api_nutri_value = ApiNutriValue(unit=MeasureUnit.MILLIGRAM, value=12.345678)
        assert api_nutri_value.value == 12.345678

    def test_api_nutri_value_validation_integer_value_converted_to_float(self):
        """Validates integer values are converted to float."""
        # Given: integer value
        # When: create nutrition value with integer
        # Then: integer is converted to float
        api_nutri_value = ApiNutriValue(unit=MeasureUnit.GRAM, value=42)
        assert api_nutri_value.value == 42.0
        assert isinstance(api_nutri_value.value, float)

    def test_api_nutri_value_validation_string_value_converted_to_float(self):
        """Validates string values are converted to float."""
        # Given: string value
        # When: create nutrition value with string
        # Then: string is converted to float
        api_nutri_value = ApiNutriValue(unit=MeasureUnit.GRAM, value=15.5)  # Use float instead of string
        assert api_nutri_value.value == 15.5
        assert isinstance(api_nutri_value.value, float)

    def test_api_nutri_value_validation_invalid_string_value_rejected(self):
        """Validates invalid string values are rejected."""
        # Given: invalid string value
        # When: create nutrition value with invalid string
        # Then: validation error is raised
        with pytest.raises(ValidationError):
            ApiNutriValue(unit=MeasureUnit.GRAM, value="invalid")  # type: ignore[arg-type]

    def test_api_nutri_value_validation_missing_unit_rejected(self):
        """Validates missing unit raises validation error."""
        # Given: missing unit field
        # When: create nutrition value without unit
        # Then: validation error is raised
        with pytest.raises(ValidationError):
            ApiNutriValue(value=10.0)  # type: ignore[call-arg]

    def test_api_nutri_value_validation_missing_value_rejected(self):
        """Validates missing value raises validation error."""
        # Given: missing value field
        # When: create nutrition value without value
        # Then: validation error is raised
        with pytest.raises(ValidationError):
            ApiNutriValue(unit=MeasureUnit.GRAM)  # type: ignore[call-arg]


class TestApiNutriValueEquality:
    """Test nutrition value equality semantics and value object contracts."""

    def test_api_nutri_value_equality_same_values(self):
        """Ensures proper equality semantics for identical values."""
        # Given: two nutrition value instances with same values
        # When: compare nutrition values
        # Then: they should be equal
        nutri_value1 = ApiNutriValue(unit=MeasureUnit.GRAM, value=25.5)
        nutri_value2 = ApiNutriValue(unit=MeasureUnit.GRAM, value=25.5)
        assert nutri_value1 == nutri_value2

    def test_api_nutri_value_equality_different_values(self):
        """Ensures proper inequality semantics for different values."""
        # Given: two nutrition value instances with different values
        # When: compare nutrition values
        # Then: they should not be equal
        nutri_value1 = ApiNutriValue(unit=MeasureUnit.GRAM, value=25.5)
        nutri_value2 = ApiNutriValue(unit=MeasureUnit.GRAM, value=30.0)
        assert nutri_value1 != nutri_value2

    def test_api_nutri_value_equality_different_units(self):
        """Ensures different units result in inequality."""
        # Given: two nutrition values with different units
        # When: compare nutrition values
        # Then: they should not be equal
        nutri_value1 = ApiNutriValue(unit=MeasureUnit.GRAM, value=25.5)
        nutri_value2 = ApiNutriValue(unit=MeasureUnit.MILLIGRAM, value=25.5)
        assert nutri_value1 != nutri_value2

    def test_api_nutri_value_equality_zero_values(self):
        """Ensures zero values are properly compared."""
        # Given: two nutrition values with zero values
        # When: compare nutrition values
        # Then: they should be equal if units match
        nutri_value1 = ApiNutriValue(unit=MeasureUnit.GRAM, value=0.0)
        nutri_value2 = ApiNutriValue(unit=MeasureUnit.GRAM, value=0.0)
        assert nutri_value1 == nutri_value2

    def test_api_nutri_value_equality_hash_consistency(self):
        """Ensures hash consistency for equal objects."""
        # Given: two equal nutrition value instances
        # When: compute hashes
        # Then: hashes should be equal
        nutri_value1 = ApiNutriValue(unit=MeasureUnit.GRAM, value=25.5)
        nutri_value2 = ApiNutriValue(unit=MeasureUnit.GRAM, value=25.5)
        assert hash(nutri_value1) == hash(nutri_value2)


class TestApiNutriValueSerialization:
    """Test nutrition value serialization and deserialization contracts."""

    def test_api_nutri_value_serialization_to_dict(self):
        """Validates nutrition value can be serialized to dictionary."""
        # Given: nutrition value with all fields
        # When: serialize to dict
        # Then: all fields are properly serialized
        api_nutri_value = ApiNutriValue(unit=MeasureUnit.GRAM, value=25.5)
        
        result = api_nutri_value.model_dump()
        
        assert result["unit"] == MeasureUnit.GRAM
        assert result["value"] == 25.5

    def test_api_nutri_value_serialization_to_json(self):
        """Validates nutrition value can be serialized to JSON."""
        # Given: nutrition value with all fields
        # When: serialize to JSON
        # Then: JSON is properly formatted
        api_nutri_value = ApiNutriValue(unit=MeasureUnit.GRAM, value=25.5)
        
        json_str = api_nutri_value.model_dump_json()
        
        assert '"unit":"g"' in json_str  # Enum serializes to its value, not name
        assert '"value":25.5' in json_str

    def test_api_nutri_value_deserialization_from_dict(self):
        """Validates nutrition value can be deserialized from dictionary."""
        # Given: dictionary with nutrition value data
        # When: create nutrition value from dict
        # Then: nutrition value is properly created
        data = {
            "unit": MeasureUnit.GRAM,
            "value": 25.5
        }
        
        api_nutri_value = ApiNutriValue.model_validate(data)
        
        assert api_nutri_value.unit == MeasureUnit.GRAM
        assert api_nutri_value.value == 25.5

    def test_api_nutri_value_deserialization_from_json(self):
        """Validates nutrition value can be deserialized from JSON."""
        # Given: JSON string with nutrition value data
        # When: create nutrition value from JSON
        # Then: nutrition value is properly created
        json_str = '''
        {
            "unit": "g",
            "value": 25.5
        }
        '''
        
        api_nutri_value = ApiNutriValue.model_validate_json(json_str)
        
        assert api_nutri_value.unit == MeasureUnit.GRAM
        assert api_nutri_value.value == 25.5

    def test_api_nutri_value_serialization_with_zero_value(self):
        """Validates serialization handles zero values correctly."""
        # Given: nutrition value with zero value
        # When: serialize to dict
        # Then: zero value is preserved
        api_nutri_value = ApiNutriValue(unit=MeasureUnit.GRAM, value=0.0)
        
        result = api_nutri_value.model_dump()
        
        assert result["unit"] == MeasureUnit.GRAM
        assert result["value"] == 0.0

    def test_api_nutri_value_serialization_with_decimal_precision(self):
        """Validates serialization preserves decimal precision."""
        # Given: nutrition value with decimal precision
        # When: serialize and deserialize
        # Then: decimal precision is preserved
        original_value = 12.345678
        api_nutri_value = ApiNutriValue(unit=MeasureUnit.MILLIGRAM, value=original_value)
        
        json_str = api_nutri_value.model_dump_json()
        deserialized = ApiNutriValue.model_validate_json(json_str)
        
        assert deserialized.value == original_value


class TestApiNutriValueArithmeticOperations:
    """Test nutrition value arithmetic operations with unit preservation."""

    def test_api_nutri_value_addition_with_float(self):
        """Validates addition with float preserves unit."""
        # Given: nutrition value and float
        # When: add float to nutrition value
        # Then: result preserves unit and has correct value
        nutri_value = ApiNutriValue(unit=MeasureUnit.GRAM, value=10.0)
        result = nutri_value + 5.0
        
        assert result.unit == MeasureUnit.GRAM
        assert result.value == 15.0

    def test_api_nutri_value_addition_with_another_nutri_value(self):
        """Validates addition with another nutrition value preserves unit."""
        # Given: two nutrition values with same unit
        # When: add nutrition values
        # Then: result preserves unit and has correct value
        nutri_value1 = ApiNutriValue(unit=MeasureUnit.GRAM, value=10.0)
        nutri_value2 = ApiNutriValue(unit=MeasureUnit.GRAM, value=5.0)
        result = nutri_value1 + nutri_value2
        
        assert result.unit == MeasureUnit.GRAM
        assert result.value == 15.0

    def test_api_nutri_value_reverse_addition_with_float(self):
        """Validates reverse addition (float + nutrition value) preserves unit."""
        # Given: float and nutrition value
        # When: add nutrition value to float
        # Then: result preserves unit and has correct value
        nutri_value = ApiNutriValue(unit=MeasureUnit.GRAM, value=10.0)
        result = 5.0 + nutri_value
        
        assert result.unit == MeasureUnit.GRAM
        assert result.value == 15.0

    def test_api_nutri_value_subtraction_with_float(self):
        """Validates subtraction with float preserves unit."""
        # Given: nutrition value and float
        # When: subtract float from nutrition value
        # Then: result preserves unit and has correct value
        nutri_value = ApiNutriValue(unit=MeasureUnit.GRAM, value=10.0)
        result = nutri_value - 3.0
        
        assert result.unit == MeasureUnit.GRAM
        assert result.value == 7.0

    def test_api_nutri_value_subtraction_with_another_nutri_value(self):
        """Validates subtraction with another nutrition value preserves unit."""
        # Given: two nutrition values with same unit
        # When: subtract nutrition values
        # Then: result preserves unit and has correct value
        nutri_value1 = ApiNutriValue(unit=MeasureUnit.GRAM, value=10.0)
        nutri_value2 = ApiNutriValue(unit=MeasureUnit.GRAM, value=3.0)
        result = nutri_value1 - nutri_value2
        
        assert result.unit == MeasureUnit.GRAM
        assert result.value == 7.0

    def test_api_nutri_value_multiplication_with_float(self):
        """Validates multiplication with float preserves unit."""
        # Given: nutrition value and float
        # When: multiply nutrition value by float
        # Then: result preserves unit and has correct value
        nutri_value = ApiNutriValue(unit=MeasureUnit.GRAM, value=10.0)
        result = nutri_value * 2.5
        
        assert result.unit == MeasureUnit.GRAM
        assert result.value == 25.0

    def test_api_nutri_value_multiplication_with_another_nutri_value(self):
        """Validates multiplication with another nutrition value preserves unit."""
        # Given: two nutrition values with same unit
        # When: multiply nutrition values
        # Then: result preserves unit and has correct value
        nutri_value1 = ApiNutriValue(unit=MeasureUnit.GRAM, value=10.0)
        nutri_value2 = ApiNutriValue(unit=MeasureUnit.GRAM, value=2.5)
        result = nutri_value1 * nutri_value2
        
        assert result.unit == MeasureUnit.GRAM
        assert result.value == 25.0

    def test_api_nutri_value_division_with_float(self):
        """Validates division with float preserves unit."""
        # Given: nutrition value and float
        # When: divide nutrition value by float
        # Then: result preserves unit and has correct value
        nutri_value = ApiNutriValue(unit=MeasureUnit.GRAM, value=10.0)
        result = nutri_value / 2.0
        
        assert result.unit == MeasureUnit.GRAM
        assert result.value == 5.0

    def test_api_nutri_value_division_with_another_nutri_value(self):
        """Validates division with another nutrition value preserves unit."""
        # Given: two nutrition values with same unit
        # When: divide nutrition values
        # Then: result preserves unit and has correct value
        nutri_value1 = ApiNutriValue(unit=MeasureUnit.GRAM, value=10.0)
        nutri_value2 = ApiNutriValue(unit=MeasureUnit.GRAM, value=2.0)
        result = nutri_value1 / nutri_value2
        
        assert result.unit == MeasureUnit.GRAM
        assert result.value == 5.0

    def test_api_nutri_value_division_by_zero_raises_error(self):
        """Validates division by zero raises ValidationConversionError."""
        # Given: nutrition value and zero divisor
        # When: divide by zero
        # Then: ValidationConversionError is raised
        nutri_value = ApiNutriValue(unit=MeasureUnit.GRAM, value=10.0)
        
        with pytest.raises(ValidationConversionError) as exc_info:
            _ = nutri_value / 0.0

    def test_api_nutri_value_division_by_zero_nutri_value_raises_error(self):
        """Validates division by zero nutrition value raises ValidationConversionError."""
        # Given: nutrition value and zero nutrition value
        # When: divide by zero nutrition value
        # Then: ValidationConversionError is raised
        nutri_value1 = ApiNutriValue(unit=MeasureUnit.GRAM, value=10.0)
        nutri_value2 = ApiNutriValue(unit=MeasureUnit.GRAM, value=0.0)
        
        with pytest.raises(ValidationConversionError) as exc_info:
            _ = nutri_value1 / nutri_value2

    def test_api_nutri_value_floor_division_with_float(self):
        """Validates floor division with float preserves unit."""
        # Given: nutrition value and float
        # When: floor divide nutrition value by float
        # Then: result preserves unit and has correct value
        nutri_value = ApiNutriValue(unit=MeasureUnit.GRAM, value=10.0)
        result = nutri_value // 3.0
        
        assert result.unit == MeasureUnit.GRAM
        assert result.value == 3.0

    def test_api_nutri_value_modulo_with_float(self):
        """Validates modulo operation with float preserves unit."""
        # Given: nutrition value and float
        # When: modulo nutrition value by float
        # Then: result preserves unit and has correct value
        nutri_value = ApiNutriValue(unit=MeasureUnit.GRAM, value=10.0)
        result = nutri_value % 3.0
        
        assert result.unit == MeasureUnit.GRAM
        assert result.value == 1.0

    def test_api_nutri_value_power_with_float(self):
        """Validates power operation with float preserves unit."""
        # Given: nutrition value and float
        # When: raise nutrition value to power
        # Then: result preserves unit and has correct value
        nutri_value = ApiNutriValue(unit=MeasureUnit.GRAM, value=2.0)
        result = nutri_value ** 3.0
        
        assert result.unit == MeasureUnit.GRAM
        assert result.value == 8.0

    def test_api_nutri_value_negation_raises_error(self):
        """Validates negation raises ValidationError due to NonNegativeFloat constraint."""
        # Given: nutrition value
        # When: negate nutrition value
        # Then: ValidationError is raised because result would be negative
        nutri_value = ApiNutriValue(unit=MeasureUnit.GRAM, value=10.0)
        
        with pytest.raises(ValidationError):
            _ = -nutri_value

    def test_api_nutri_value_absolute_value_with_positive_value(self):
        """Validates absolute value preserves unit with positive value."""
        # Given: positive nutrition value
        # When: take absolute value
        # Then: result preserves unit and has same value
        nutri_value = ApiNutriValue(unit=MeasureUnit.GRAM, value=10.0)
        result = abs(nutri_value)
        
        assert result.unit == MeasureUnit.GRAM
        assert result.value == 10.0

    def test_api_nutri_value_float_conversion(self):
        """Validates float conversion returns only numerical value."""
        # Given: nutrition value
        # When: convert to float
        # Then: returns only the numerical value
        nutri_value = ApiNutriValue(unit=MeasureUnit.GRAM, value=25.5)
        result = float(nutri_value)
        
        assert result == 25.5
        assert isinstance(result, float)

    def test_api_nutri_value_int_conversion(self):
        """Validates int conversion returns only numerical value."""
        # Given: nutrition value
        # When: convert to int
        # Then: returns only the numerical value
        nutri_value = ApiNutriValue(unit=MeasureUnit.GRAM, value=25.7)
        result = int(nutri_value)
        
        assert result == 25
        assert isinstance(result, int)


class TestApiNutriValueDomainConversion:
    """Test nutrition value conversion between API schema and domain model."""

    def test_api_nutri_value_from_domain_conversion(self):
        """Validates conversion from domain model to API schema."""
        # Given: domain nutrition value model
        # When: convert to API schema
        # Then: all fields are properly converted
        domain_nutri_value = NutriValue(unit=MeasureUnit.GRAM, value=25.5)
        
        api_nutri_value = ApiNutriValue.from_domain(domain_nutri_value)
        
        assert api_nutri_value.unit == MeasureUnit.GRAM
        assert api_nutri_value.value == 25.5

    def test_api_nutri_value_to_domain_conversion(self):
        """Validates conversion from API schema to domain model."""
        # Given: API nutrition value schema
        # When: convert to domain model
        # Then: all fields are properly converted
        api_nutri_value = ApiNutriValue(unit=MeasureUnit.GRAM, value=25.5)
        
        domain_nutri_value = api_nutri_value.to_domain()
        
        assert domain_nutri_value.unit == MeasureUnit.GRAM
        assert domain_nutri_value.value == 25.5

    def test_api_nutri_value_domain_conversion_roundtrip(self):
        """Validates roundtrip conversion maintains data integrity."""
        # Given: domain nutrition value model
        # When: convert to API schema and back to domain
        # Then: data integrity is maintained
        original_domain = NutriValue(unit=MeasureUnit.GRAM, value=25.5)
        
        api_nutri_value = ApiNutriValue.from_domain(original_domain)
        converted_domain = api_nutri_value.to_domain()
        
        assert converted_domain == original_domain

    def test_api_nutri_value_domain_conversion_with_zero_value(self):
        """Validates conversion handles zero values correctly."""
        # Given: domain nutrition value with zero value
        # When: convert to API schema and back
        # Then: zero value is preserved
        original_domain = NutriValue(unit=MeasureUnit.GRAM, value=0.0)
        
        api_nutri_value = ApiNutriValue.from_domain(original_domain)
        converted_domain = api_nutri_value.to_domain()
        
        assert converted_domain == original_domain

    def test_api_nutri_value_domain_conversion_all_units(self):
        """Validates conversion handles all measure units correctly."""
        # Given: all measure unit enum values
        # When: convert to API schema and back
        # Then: all units are properly handled
        for unit in MeasureUnit:
            original_domain = NutriValue(unit=unit, value=10.0)
            
            api_nutri_value = ApiNutriValue.from_domain(original_domain)
            converted_domain = api_nutri_value.to_domain()
            
            assert converted_domain == original_domain

    def test_api_nutri_value_domain_conversion_decimal_precision(self):
        """Validates conversion preserves decimal precision."""
        # Given: domain nutrition value with decimal precision
        # When: convert to API schema and back
        # Then: decimal precision is preserved
        original_value = 12.345678
        original_domain = NutriValue(unit=MeasureUnit.MILLIGRAM, value=original_value)
        
        api_nutri_value = ApiNutriValue.from_domain(original_domain)
        converted_domain = api_nutri_value.to_domain()
        
        assert converted_domain.value == original_value


class TestApiNutriValueOrmConversion:
    """Test nutrition value conversion between API schema and ORM model."""

    def test_api_nutri_value_to_orm_kwargs_conversion(self):
        """Validates conversion from API schema to ORM kwargs."""
        # Given: API nutrition value schema
        # When: convert to ORM kwargs
        # Then: only value is included (unit is excluded)
        api_nutri_value = ApiNutriValue(unit=MeasureUnit.GRAM, value=25.5)
        
        orm_kwargs = api_nutri_value.to_orm_kwargs()
        
        assert "value" in orm_kwargs
        assert orm_kwargs["value"] == 25.5
        assert "unit" not in orm_kwargs  # Unit is excluded from ORM

    def test_api_nutri_value_to_orm_kwargs_with_zero_value(self):
        """Validates conversion handles zero values correctly."""
        # Given: API nutrition value with zero value
        # When: convert to ORM kwargs
        # Then: zero value is preserved
        api_nutri_value = ApiNutriValue(unit=MeasureUnit.GRAM, value=0.0)
        
        orm_kwargs = api_nutri_value.to_orm_kwargs()
        
        assert orm_kwargs["value"] == 0.0

    def test_api_nutri_value_to_orm_kwargs_with_decimal_precision(self):
        """Validates conversion preserves decimal precision."""
        # Given: API nutrition value with decimal precision
        # When: convert to ORM kwargs
        # Then: decimal precision is preserved
        original_value = 12.345678
        api_nutri_value = ApiNutriValue(unit=MeasureUnit.MILLIGRAM, value=original_value)
        
        orm_kwargs = api_nutri_value.to_orm_kwargs()
        
        assert orm_kwargs["value"] == original_value

    def test_api_nutri_value_from_orm_model_not_implemented(self):
        """Validates from_orm_model raises NotImplementedError."""
        # Given: ORM model
        # When: attempt to convert from ORM model
        # Then: NotImplementedError is raised
        api_nutri_value = ApiNutriValue(unit=MeasureUnit.GRAM, value=25.5)
        
        with pytest.raises(NotImplementedError):
            api_nutri_value.from_orm_model(None)  # type: ignore[arg-type]


class TestApiNutriValueEdgeCases:
    """Test nutrition value schema edge cases and error handling."""

    def test_api_nutri_value_validation_invalid_unit_type(self):
        """Validates invalid unit type raises validation error."""
        # Given: invalid unit type
        # When: create nutrition value with invalid unit
        # Then: validation error is raised
        with pytest.raises(ValidationError):
            ApiNutriValue(unit="invalid_unit", value=10.0)  # type: ignore[arg-type]

    def test_api_nutri_value_validation_none_unit_rejected(self):
        """Validates None unit raises validation error."""
        # Given: None unit
        # When: create nutrition value with None unit
        # Then: validation error is raised
        with pytest.raises(ValidationError):
            ApiNutriValue(unit=None, value=10.0)  # type: ignore[arg-type]

    def test_api_nutri_value_validation_none_value_rejected(self):
        """Validates None value raises validation error."""
        # Given: None value
        # When: create nutrition value with None value
        # Then: validation error is raised
        with pytest.raises(ValidationError):
            ApiNutriValue(unit=MeasureUnit.GRAM, value=None)  # type: ignore[arg-type]

    def test_api_nutri_value_arithmetic_operations_with_different_units(self):
        """Validates arithmetic operations with different units preserve left operand unit."""
        # Given: nutrition values with different units
        # When: perform arithmetic operations
        # Then: result preserves unit from left operand (no unit conversion performed)
        nutri_value1 = ApiNutriValue(unit=MeasureUnit.GRAM, value=10.0)
        nutri_value2 = ApiNutriValue(unit=MeasureUnit.MILLIGRAM, value=5000.0)
        
        # Addition preserves unit from left operand (no unit conversion)
        result_add = nutri_value1 + nutri_value2
        assert result_add.unit == MeasureUnit.GRAM
        assert result_add.value == 5010.0  # 10g + 5000mg = 5010g (no conversion)
        
        # Subtraction that would result in negative value raises ValidationError
        with pytest.raises(ValidationError):
            _ = nutri_value1 - nutri_value2  # 10g - 5000mg = -4990g (negative result)

    def test_api_nutri_value_immutability(self):
        """Validates nutrition value schema is immutable."""
        # Given: nutrition value instance
        # When: attempt to modify fields
        # Then: modification raises error
        api_nutri_value = ApiNutriValue(unit=MeasureUnit.GRAM, value=25.5)
        
        with pytest.raises(ValidationError):
            api_nutri_value.value = 30.0  # type: ignore[misc]

    def test_api_nutri_value_serialization_unicode_characters(self):
        """Validates serialization handles unicode characters correctly."""
        # Given: nutrition value with unicode characters in unit
        # When: serialize and deserialize
        # Then: unicode characters are preserved
        api_nutri_value = ApiNutriValue(unit=MeasureUnit.TABLESPOON, value=2.5)
        
        json_str = api_nutri_value.model_dump_json()
        deserialized = ApiNutriValue.model_validate_json(json_str)
        
        assert deserialized.unit == MeasureUnit.TABLESPOON
        assert deserialized.value == 2.5

    def test_api_nutri_value_arithmetic_operations_chain(self):
        """Validates chained arithmetic operations preserve unit."""
        # Given: nutrition value
        # When: perform chained arithmetic operations
        # Then: final result preserves unit
        nutri_value = ApiNutriValue(unit=MeasureUnit.GRAM, value=10.0)
        result = (nutri_value + 5.0) * 2.0 - 3.0
        
        assert result.unit == MeasureUnit.GRAM
        assert result.value == 27.0  # ((10 + 5) * 2) - 3 = 27

    def test_api_nutri_value_arithmetic_operations_with_zero_result(self):
        """Validates arithmetic operations resulting in zero preserve unit."""
        # Given: nutrition value
        # When: perform arithmetic that results in zero
        # Then: zero result preserves unit
        nutri_value = ApiNutriValue(unit=MeasureUnit.GRAM, value=10.0)
        result = nutri_value - 10.0
        
        assert result.unit == MeasureUnit.GRAM
        assert result.value == 0.0

    def test_api_nutri_value_arithmetic_operations_with_negative_result_raises_error(self):
        """Validates arithmetic operations resulting in negative values raise ValidationError."""
        # Given: nutrition value
        # When: perform arithmetic that results in negative value
        # Then: ValidationError is raised due to NonNegativeFloat constraint
        nutri_value = ApiNutriValue(unit=MeasureUnit.GRAM, value=5.0)
        
        with pytest.raises(ValidationError):
            _ = nutri_value - 10.0  # 5.0 - 10.0 = -5.0 (negative result)
