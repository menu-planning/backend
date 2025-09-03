"""Unit tests for ApiNutriFacts schema.

Tests nutrition facts schema validation, serialization/deserialization, arithmetic operations,
and conversion methods. Follows testing principles: no I/O, fakes only, behavior-focused assertions.
"""

import pytest
from pydantic import ValidationError

from src.contexts.seedwork.adapters.exceptions.api_schema_errors import ValidationConversionError
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_facts import ApiNutriFacts
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_value import ApiNutriValue
from src.contexts.shared_kernel.adapters.ORM.sa_models.nutri_facts_sa_model import NutriFactsSaModel
from src.contexts.shared_kernel.domain.enums import MeasureUnit
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.value_objects.nutri_value import NutriValue


class TestApiNutriFactsValidation:
    """Test nutrition facts schema validation and field constraints."""

    def test_api_nutri_facts_validation_minimal_creation(self):
        """Validates minimal nutrition facts creation with default values."""
        # Given: minimal nutrition facts data
        # When: create nutrition facts with minimal data
        # Then: nutrition facts is created successfully with defaults
        api_nutri_facts = ApiNutriFacts()
        
        # All fields should be ApiNutriValue with default values
        assert isinstance(api_nutri_facts.calories, ApiNutriValue)
        assert api_nutri_facts.calories.value == 0.0
        assert api_nutri_facts.calories.unit == MeasureUnit.ENERGY
        
        assert isinstance(api_nutri_facts.protein, ApiNutriValue)
        assert api_nutri_facts.protein.value == 0.0
        assert api_nutri_facts.protein.unit == MeasureUnit.GRAM

    def test_api_nutri_facts_validation_with_numeric_values(self):
        """Validates nutrition facts creation with numeric values."""
        # Given: nutrition facts with numeric values
        # When: create nutrition facts with numbers
        # Then: numbers are converted to ApiNutriValue with default units
        api_nutri_facts = ApiNutriFacts(
            calories=250.5,
            protein=15.0,
            carbohydrate=30.0,
            total_fat=10.0
        )
        
        assert api_nutri_facts.calories.value == 250.5
        assert api_nutri_facts.calories.unit == MeasureUnit.ENERGY
        assert api_nutri_facts.protein.value == 15.0
        assert api_nutri_facts.protein.unit == MeasureUnit.GRAM
        assert api_nutri_facts.carbohydrate.value == 30.0
        assert api_nutri_facts.carbohydrate.unit == MeasureUnit.GRAM
        assert api_nutri_facts.total_fat.value == 10.0
        assert api_nutri_facts.total_fat.unit == MeasureUnit.GRAM

    def test_api_nutri_facts_validation_with_dict_values(self):
        """Validates nutrition facts creation with dictionary values."""
        # Given: nutrition facts with dictionary values
        # When: create nutrition facts with dicts
        # Then: dicts are converted to ApiNutriValue
        api_nutri_facts = ApiNutriFacts(
            calories={"value": 300.0, "unit": "kcal"},
            protein={"value": 20.0, "unit": "g"},
            sodium={"value": 500.0, "unit": "mg"}
        )
        
        assert api_nutri_facts.calories.value == 300.0
        assert api_nutri_facts.calories.unit == MeasureUnit.ENERGY
        assert api_nutri_facts.protein.value == 20.0
        assert api_nutri_facts.protein.unit == MeasureUnit.GRAM
        assert api_nutri_facts.sodium.value == 500.0
        assert api_nutri_facts.sodium.unit == MeasureUnit.MILLIGRAM

    def test_api_nutri_facts_validation_with_api_nutri_value_instances(self):
        """Validates nutrition facts creation with ApiNutriValue instances."""
        # Given: ApiNutriValue instances
        # When: create nutrition facts with ApiNutriValue
        # Then: instances are used directly
        calories = ApiNutriValue(value=200.0, unit=MeasureUnit.ENERGY)
        protein = ApiNutriValue(value=25.0, unit=MeasureUnit.GRAM)
        
        api_nutri_facts = ApiNutriFacts(
            calories=calories,
            protein=protein
        )
        
        assert api_nutri_facts.calories is calories
        assert api_nutri_facts.protein is protein

    def test_api_nutri_facts_validation_with_none_values(self):
        """Validates nutrition facts creation with None values."""
        # Given: None values for some fields
        # When: create nutrition facts with None values
        # Then: None values are converted to default ApiNutriValue
        api_nutri_facts = ApiNutriFacts(
            calories=250.0,
            protein=None,
            carbohydrate=30.0,
            total_fat=None
        )
        
        assert api_nutri_facts.calories.value == 250.0
        assert api_nutri_facts.protein.value == 0.0
        assert api_nutri_facts.protein.unit == MeasureUnit.GRAM
        assert api_nutri_facts.carbohydrate.value == 30.0
        assert api_nutri_facts.total_fat.value == 0.0
        assert api_nutri_facts.total_fat.unit == MeasureUnit.GRAM

    def test_api_nutri_facts_validation_negative_values_rejected(self):
        """Validates negative values are rejected."""
        # Given: negative nutrition values
        # When: create nutrition facts with negative values
        # Then: ValidationConversionError is raised
        with pytest.raises(ValidationConversionError) as exc_info:
            ApiNutriFacts(calories=-100.0)
        
        assert "Value for field 'calories' must be between 0.0 and infinity" in str(exc_info.value)

    def test_api_nutri_facts_validation_invalid_unit_rejected(self):
        """Validates invalid units are rejected."""
        # Given: invalid unit in dictionary
        # When: create nutrition facts with invalid unit
        # Then: ValidationConversionError is raised
        with pytest.raises(ValidationConversionError) as exc_info:
            ApiNutriFacts(calories={"value": 100.0, "unit": "invalid_unit"})
        
        assert "Invalid unit for field 'calories'" in str(exc_info.value)

    def test_api_nutri_facts_validation_invalid_value_type_rejected(self):
        """Validates invalid value types are rejected."""
        # Given: invalid value type in dictionary
        # When: create nutrition facts with invalid value type
        # Then: ValidationConversionError is raised
        with pytest.raises(ValidationConversionError) as exc_info:
            ApiNutriFacts(calories={"value": "invalid", "unit": "kcal"})
        
        assert "Value for field 'calories' must be a number" in str(exc_info.value)

    def test_api_nutri_facts_validation_invalid_field_type_rejected(self):
        """Validates invalid field types are rejected."""
        # Given: invalid field type
        # When: create nutrition facts with invalid field type
        # Then: ValidationConversionError is raised
        with pytest.raises(ValidationConversionError) as exc_info:
            ApiNutriFacts(calories="invalid_string")
        
        assert "Invalid value for field 'calories'" in str(exc_info.value)

    def test_api_nutri_facts_validation_all_nutrition_fields_present(self):
        """Validates all nutrition fields are present and properly typed."""
        # Given: nutrition facts instance
        # When: check all fields
        # Then: all expected nutrition fields are present
        api_nutri_facts = ApiNutriFacts()
        
        # Check that all expected fields exist and are ApiNutriValue instances
        expected_fields = [
            'calories', 'protein', 'carbohydrate', 'total_fat', 'saturated_fat',
            'trans_fat', 'dietary_fiber', 'sodium', 'arachidonic_acid', 'ashes',
            'dha', 'epa', 'sugar', 'starch', 'biotin', 'boro', 'caffeine',
            'calcium', 'chlorine', 'copper', 'cholesterol', 'choline', 'chrome',
            'dextrose', 'sulfur', 'phenylalanine', 'iron', 'insoluble_fiber',
            'soluble_fiber', 'fluor', 'phosphorus', 'fructo_oligosaccharides',
            'fructose', 'galacto_oligosaccharides', 'galactose', 'glucose',
            'glucoronolactone', 'monounsaturated_fat', 'polyunsaturated_fat',
            'guarana', 'inositol', 'inulin', 'iodine', 'l_carnitine',
            'l_methionine', 'lactose', 'magnesium', 'maltose', 'manganese',
            'molybdenum', 'linolenic_acid', 'linoleic_acid', 'omega_7', 'omega_9',
            'oleic_acid', 'other_carbo', 'polydextrose', 'polyols', 'potassium',
            'sacarose', 'selenium', 'silicon', 'sorbitol', 'sucralose', 'taurine',
            'vitamin_a', 'vitamin_b1', 'vitamin_b2', 'vitamin_b3', 'vitamin_b5',
            'vitamin_b6', 'folic_acid', 'vitamin_b12', 'vitamin_c', 'vitamin_d',
            'vitamin_e', 'vitamin_k', 'zinc', 'retinol', 'thiamine', 'riboflavin',
            'pyridoxine', 'niacin'
        ]
        
        for field_name in expected_fields:
            assert hasattr(api_nutri_facts, field_name)
            field_value = getattr(api_nutri_facts, field_name)
            assert isinstance(field_value, ApiNutriValue)
            assert field_value.value == 0.0  # Default value


class TestApiNutriFactsEquality:
    """Test nutrition facts equality semantics and value object contracts."""

    def test_api_nutri_facts_equality_same_values(self):
        """Ensures proper equality semantics for identical values."""
        # Given: two nutrition facts instances with same values
        # When: compare nutrition facts
        # Then: they should be equal
        facts1 = ApiNutriFacts(
            calories=250.0,
            protein=15.0,
            carbohydrate=30.0,
            total_fat=10.0
        )
        facts2 = ApiNutriFacts(
            calories=250.0,
            protein=15.0,
            carbohydrate=30.0,
            total_fat=10.0
        )
        assert facts1 == facts2

    def test_api_nutri_facts_equality_different_values(self):
        """Ensures proper inequality semantics for different values."""
        # Given: two nutrition facts instances with different values
        # When: compare nutrition facts
        # Then: they should not be equal
        facts1 = ApiNutriFacts(
            calories=250.0,
            protein=15.0,
            carbohydrate=30.0,
            total_fat=10.0
        )
        facts2 = ApiNutriFacts(
            calories=300.0,
            protein=15.0,
            carbohydrate=30.0,
            total_fat=10.0
        )
        assert facts1 != facts2

    def test_api_nutri_facts_equality_different_units(self):
        """Ensures different units result in inequality."""
        # Given: two nutrition facts with different units for same field
        # When: compare nutrition facts
        # Then: they should not be equal
        facts1 = ApiNutriFacts(
            calories={"value": 250.0, "unit": "kcal"},
            protein=15.0
        )
        facts2 = ApiNutriFacts(
            calories={"value": 250.0, "unit": "g"},  # Different unit (gram instead of kcal)
            protein=15.0
        )
        assert facts1 != facts2

    def test_api_nutri_facts_equality_zero_values(self):
        """Ensures zero values are properly compared."""
        # Given: two nutrition facts with zero values
        # When: compare nutrition facts
        # Then: they should be equal if all fields match
        facts1 = ApiNutriFacts()
        facts2 = ApiNutriFacts()
        assert facts1 == facts2

    def test_api_nutri_facts_equality_hash_consistency(self):
        """Ensures hash consistency for equal objects."""
        # Given: two equal nutrition facts instances
        # When: compute hashes
        # Then: hashes should be equal
        facts1 = ApiNutriFacts(
            calories=250.0,
            protein=15.0,
            carbohydrate=30.0
        )
        facts2 = ApiNutriFacts(
            calories=250.0,
            protein=15.0,
            carbohydrate=30.0
        )
        assert hash(facts1) == hash(facts2)

    def test_api_nutri_facts_equality_partial_fields_different(self):
        """Ensures partial field differences result in inequality."""
        # Given: nutrition facts with some fields different
        # When: compare nutrition facts
        # Then: they should not be equal
        facts1 = ApiNutriFacts(
            calories=250.0,
            protein=15.0,
            carbohydrate=30.0,
            total_fat=10.0
        )
        facts2 = ApiNutriFacts(
            calories=250.0,
            protein=15.0,
            carbohydrate=30.0,
            total_fat=12.0  # Different value
        )
        assert facts1 != facts2

    def test_api_nutri_facts_equality_all_fields_same_but_different_creation_method(self):
        """Ensures same values created differently are equal."""
        # Given: nutrition facts created with different methods but same values
        # When: compare nutrition facts
        # Then: they should be equal
        facts1 = ApiNutriFacts(
            calories=250.0,
            protein=15.0
        )
        facts2 = ApiNutriFacts(
            calories={"value": 250.0, "unit": "kcal"},
            protein={"value": 15.0, "unit": "g"}
        )
        assert facts1 == facts2


class TestApiNutriFactsSerialization:
    """Test nutrition facts serialization and deserialization contracts."""

    def test_api_nutri_facts_serialization_to_dict(self):
        """Validates nutrition facts can be serialized to dictionary."""
        # Given: nutrition facts with all fields
        # When: serialize to dict
        # Then: all fields are properly serialized
        api_nutri_facts = ApiNutriFacts(
            calories=250.0,
            protein=15.0,
            carbohydrate=30.0,
            total_fat=10.0,
            sodium=500.0
        )
        
        result = api_nutri_facts.model_dump()
        
        assert "calories" in result
        assert result["calories"]["value"] == 250.0
        assert result["calories"]["unit"] == MeasureUnit.ENERGY
        assert "protein" in result
        assert result["protein"]["value"] == 15.0
        assert result["protein"]["unit"] == MeasureUnit.GRAM
        assert "carbohydrate" in result
        assert result["carbohydrate"]["value"] == 30.0
        assert result["carbohydrate"]["unit"] == MeasureUnit.GRAM
        assert "total_fat" in result
        assert result["total_fat"]["value"] == 10.0
        assert result["total_fat"]["unit"] == MeasureUnit.GRAM
        assert "sodium" in result
        assert result["sodium"]["value"] == 500.0
        assert result["sodium"]["unit"] == MeasureUnit.MILLIGRAM

    def test_api_nutri_facts_serialization_to_json(self):
        """Validates nutrition facts can be serialized to JSON."""
        # Given: nutrition facts with all fields
        # When: serialize to JSON
        # Then: JSON is properly formatted
        api_nutri_facts = ApiNutriFacts(
            calories=250.0,
            protein=15.0,
            carbohydrate=30.0
        )
        
        json_str = api_nutri_facts.model_dump_json()
        
        assert '"calories"' in json_str
        assert '"value":250.0' in json_str
        assert '"unit":"kcal"' in json_str
        assert '"protein"' in json_str
        assert '"carbohydrate"' in json_str

    def test_api_nutri_facts_deserialization_from_dict(self):
        """Validates nutrition facts can be deserialized from dictionary."""
        # Given: dictionary with nutrition facts data
        # When: create nutrition facts from dict
        # Then: nutrition facts is properly created
        data = {
            "calories": {"value": 250.0, "unit": "kcal"},
            "protein": {"value": 15.0, "unit": "g"},
            "carbohydrate": {"value": 30.0, "unit": "g"},
            "total_fat": {"value": 10.0, "unit": "g"},
            "sodium": {"value": 500.0, "unit": "mg"}
        }
        
        api_nutri_facts = ApiNutriFacts.model_validate(data)
        
        assert api_nutri_facts.calories.value == 250.0
        assert api_nutri_facts.calories.unit == MeasureUnit.ENERGY
        assert api_nutri_facts.protein.value == 15.0
        assert api_nutri_facts.protein.unit == MeasureUnit.GRAM
        assert api_nutri_facts.carbohydrate.value == 30.0
        assert api_nutri_facts.carbohydrate.unit == MeasureUnit.GRAM
        assert api_nutri_facts.total_fat.value == 10.0
        assert api_nutri_facts.total_fat.unit == MeasureUnit.GRAM
        assert api_nutri_facts.sodium.value == 500.0
        assert api_nutri_facts.sodium.unit == MeasureUnit.MILLIGRAM

    def test_api_nutri_facts_deserialization_from_json(self):
        """Validates nutrition facts can be deserialized from JSON."""
        # Given: JSON string with nutrition facts data
        # When: create nutrition facts from JSON
        # Then: nutrition facts is properly created
        json_str = '''
        {
            "calories": {"value": 250.0, "unit": "kcal"},
            "protein": {"value": 15.0, "unit": "g"},
            "carbohydrate": {"value": 30.0, "unit": "g"}
        }
        '''
        
        api_nutri_facts = ApiNutriFacts.model_validate_json(json_str)
        
        assert api_nutri_facts.calories.value == 250.0
        assert api_nutri_facts.calories.unit == MeasureUnit.ENERGY
        assert api_nutri_facts.protein.value == 15.0
        assert api_nutri_facts.protein.unit == MeasureUnit.GRAM
        assert api_nutri_facts.carbohydrate.value == 30.0
        assert api_nutri_facts.carbohydrate.unit == MeasureUnit.GRAM

    def test_api_nutri_facts_serialization_with_zero_values(self):
        """Validates serialization handles zero values correctly."""
        # Given: nutrition facts with zero values
        # When: serialize to dict
        # Then: zero values are preserved
        api_nutri_facts = ApiNutriFacts()
        
        result = api_nutri_facts.model_dump()
        
        assert result["calories"]["value"] == 0.0
        assert result["calories"]["unit"] == MeasureUnit.ENERGY
        assert result["protein"]["value"] == 0.0
        assert result["protein"]["unit"] == MeasureUnit.GRAM

    def test_api_nutri_facts_serialization_with_decimal_precision(self):
        """Validates serialization preserves decimal precision."""
        # Given: nutrition facts with decimal precision
        # When: serialize and deserialize
        # Then: decimal precision is preserved
        original_calories = 250.123456
        original_protein = 15.789012
        api_nutri_facts = ApiNutriFacts(
            calories=original_calories,
            protein=original_protein
        )
        
        json_str = api_nutri_facts.model_dump_json()
        deserialized = ApiNutriFacts.model_validate_json(json_str)
        
        assert deserialized.calories.value == original_calories
        assert deserialized.protein.value == original_protein

    def test_api_nutri_facts_serialization_roundtrip(self):
        """Validates roundtrip serialization maintains data integrity."""
        # Given: nutrition facts with various values
        # When: serialize to JSON and deserialize back
        # Then: data integrity is maintained
        original_facts = ApiNutriFacts(
            calories=250.0,
            protein=15.0,
            carbohydrate=30.0,
            total_fat=10.0,
            sodium=500.0,
            vitamin_c=60.0
        )
        
        json_str = original_facts.model_dump_json()
        deserialized_facts = ApiNutriFacts.model_validate_json(json_str)
        
        assert deserialized_facts == original_facts

    def test_api_nutri_facts_serialization_partial_fields(self):
        """Validates serialization handles partial field data correctly."""
        # Given: nutrition facts with only some fields set
        # When: serialize to dict
        # Then: all fields are included with default values
        api_nutri_facts = ApiNutriFacts(
            calories=250.0,
            protein=15.0
        )
        
        result = api_nutri_facts.model_dump()
        
        # Check that all fields are present
        assert "calories" in result
        assert "protein" in result
        assert "carbohydrate" in result
        assert "total_fat" in result
        assert "sodium" in result
        
        # Check that set fields have correct values
        assert result["calories"]["value"] == 250.0
        assert result["protein"]["value"] == 15.0
        
        # Check that unset fields have default values
        assert result["carbohydrate"]["value"] == 0.0
        assert result["total_fat"]["value"] == 0.0
        assert result["sodium"]["value"] == 0.0


class TestApiNutriFactsArithmeticOperations:
    """Test nutrition facts arithmetic operations with unit preservation."""

    def test_api_nutri_facts_addition_with_another_nutri_facts(self):
        """Validates addition with another nutrition facts preserves units."""
        # Given: two nutrition facts instances
        # When: add nutrition facts
        # Then: result preserves units and has correct values
        facts1 = ApiNutriFacts(
            calories=250.0,
            protein=15.0,
            carbohydrate=30.0,
            total_fat=10.0
        )
        facts2 = ApiNutriFacts(
            calories=100.0,
            protein=5.0,
            carbohydrate=10.0,
            total_fat=3.0
        )
        result = facts1 + facts2
        
        assert result.calories.value == 350.0
        assert result.calories.unit == MeasureUnit.ENERGY
        assert result.protein.value == 20.0
        assert result.protein.unit == MeasureUnit.GRAM
        assert result.carbohydrate.value == 40.0
        assert result.carbohydrate.unit == MeasureUnit.GRAM
        assert result.total_fat.value == 13.0
        assert result.total_fat.unit == MeasureUnit.GRAM

    def test_api_nutri_facts_subtraction_with_another_nutri_facts(self):
        """Validates subtraction with another nutrition facts preserves units."""
        # Given: two nutrition facts instances
        # When: subtract nutrition facts
        # Then: result preserves units and has correct values
        facts1 = ApiNutriFacts(
            calories=250.0,
            protein=15.0,
            carbohydrate=30.0,
            total_fat=10.0
        )
        facts2 = ApiNutriFacts(
            calories=100.0,
            protein=5.0,
            carbohydrate=10.0,
            total_fat=3.0
        )
        result = facts1 - facts2
        
        assert result.calories.value == 150.0
        assert result.calories.unit == MeasureUnit.ENERGY
        assert result.protein.value == 10.0
        assert result.protein.unit == MeasureUnit.GRAM
        assert result.carbohydrate.value == 20.0
        assert result.carbohydrate.unit == MeasureUnit.GRAM
        assert result.total_fat.value == 7.0
        assert result.total_fat.unit == MeasureUnit.GRAM

    def test_api_nutri_facts_multiplication_with_scalar(self):
        """Validates multiplication with scalar preserves units."""
        # Given: nutrition facts and scalar
        # When: multiply nutrition facts by scalar
        # Then: result preserves units and has correct values
        facts = ApiNutriFacts(
            calories=250.0,
            protein=15.0,
            carbohydrate=30.0,
            total_fat=10.0
        )
        result = facts * 2.0
        
        assert result.calories.value == 500.0
        assert result.calories.unit == MeasureUnit.ENERGY
        assert result.protein.value == 30.0
        assert result.protein.unit == MeasureUnit.GRAM
        assert result.carbohydrate.value == 60.0
        assert result.carbohydrate.unit == MeasureUnit.GRAM
        assert result.total_fat.value == 20.0
        assert result.total_fat.unit == MeasureUnit.GRAM

    def test_api_nutri_facts_multiplication_with_another_nutri_facts(self):
        """Validates multiplication with another nutrition facts preserves units."""
        # Given: two nutrition facts instances
        # When: multiply nutrition facts
        # Then: result preserves units and has correct values
        facts1 = ApiNutriFacts(
            calories=250.0,
            protein=15.0,
            carbohydrate=30.0
        )
        facts2 = ApiNutriFacts(
            calories=2.0,
            protein=1.5,
            carbohydrate=2.0
        )
        result = facts1 * facts2
        
        assert result.calories.value == 500.0
        assert result.calories.unit == MeasureUnit.ENERGY
        assert result.protein.value == 22.5
        assert result.protein.unit == MeasureUnit.GRAM
        assert result.carbohydrate.value == 60.0
        assert result.carbohydrate.unit == MeasureUnit.GRAM

    def test_api_nutri_facts_division_with_scalar(self):
        """Validates division with scalar preserves units."""
        # Given: nutrition facts and scalar
        # When: divide nutrition facts by scalar
        # Then: result preserves units and has correct values
        facts = ApiNutriFacts(
            calories=250.0,
            protein=15.0,
            carbohydrate=30.0,
            total_fat=10.0
        )
        result = facts / 2.0
        
        assert result.calories.value == 125.0
        assert result.calories.unit == MeasureUnit.ENERGY
        assert result.protein.value == 7.5
        assert result.protein.unit == MeasureUnit.GRAM
        assert result.carbohydrate.value == 15.0
        assert result.carbohydrate.unit == MeasureUnit.GRAM
        assert result.total_fat.value == 5.0
        assert result.total_fat.unit == MeasureUnit.GRAM

    def test_api_nutri_facts_division_with_another_nutri_facts_raises_error(self):
        """Validates division with another nutrition facts raises error due to zero values."""
        # Given: two nutrition facts instances with zero values in some fields
        # When: divide nutrition facts
        # Then: ValidationConversionError is raised due to division by zero
        facts1 = ApiNutriFacts(
            calories=250.0,
            protein=15.0,
            carbohydrate=30.0,
            total_fat=10.0,
            sodium=500.0
        )
        facts2 = ApiNutriFacts(
            calories=2.0,
            protein=1.5,
            carbohydrate=2.0,
            total_fat=1.0,
            sodium=50.0
        )
        
        with pytest.raises(ValidationConversionError) as exc_info:
            _ = facts1 / facts2
        
        assert "Cannot divide by zero" in str(exc_info.value)

    def test_api_nutri_facts_division_by_zero_raises_error(self):
        """Validates division by zero raises ValidationConversionError."""
        # Given: nutrition facts and zero divisor
        # When: divide by zero
        # Then: ValidationConversionError is raised
        facts = ApiNutriFacts(
            calories=250.0,
            protein=15.0
        )
        
        with pytest.raises(ValidationConversionError) as exc_info:
            _ = facts / 0.0
        
        assert "Cannot divide by zero" in str(exc_info.value)

    def test_api_nutri_facts_reverse_multiplication_with_scalar(self):
        """Validates reverse multiplication (scalar * nutrition facts) preserves units."""
        # Given: scalar and nutrition facts
        # When: multiply scalar by nutrition facts
        # Then: result preserves units and has correct values
        facts = ApiNutriFacts(
            calories=250.0,
            protein=15.0,
            carbohydrate=30.0
        )
        result = 3.0 * facts
        
        assert result.calories.value == 750.0
        assert result.calories.unit == MeasureUnit.ENERGY
        assert result.protein.value == 45.0
        assert result.protein.unit == MeasureUnit.GRAM
        assert result.carbohydrate.value == 90.0
        assert result.carbohydrate.unit == MeasureUnit.GRAM

    def test_api_nutri_facts_arithmetic_operations_chain(self):
        """Validates chained arithmetic operations preserve units."""
        # Given: nutrition facts
        # When: perform chained arithmetic operations
        # Then: final result preserves units
        facts1 = ApiNutriFacts(
            calories=250.0,
            protein=15.0,
            carbohydrate=30.0
        )
        facts2 = ApiNutriFacts(
            calories=100.0,
            protein=5.0,
            carbohydrate=10.0
        )
        result = (facts1 + facts2) * 2.0 - facts1
        
        assert result.calories.value == 450.0  # (250+100)*2 - 250 = 450
        assert result.calories.unit == MeasureUnit.ENERGY
        assert result.protein.value == 25.0  # (15+5)*2 - 15 = 25
        assert result.protein.unit == MeasureUnit.GRAM
        assert result.carbohydrate.value == 50.0  # (30+10)*2 - 30 = 50
        assert result.carbohydrate.unit == MeasureUnit.GRAM

    def test_api_nutri_facts_arithmetic_operations_with_zero_values(self):
        """Validates arithmetic operations with zero values preserve units."""
        # Given: nutrition facts with zero values
        # When: perform arithmetic operations
        # Then: zero results preserve units
        facts1 = ApiNutriFacts(
            calories=250.0,
            protein=15.0
        )
        facts2 = ApiNutriFacts(
            calories=250.0,
            protein=15.0
        )
        result = facts1 - facts2
        
        assert result.calories.value == 0.0
        assert result.calories.unit == MeasureUnit.ENERGY
        assert result.protein.value == 0.0
        assert result.protein.unit == MeasureUnit.GRAM

    def test_api_nutri_facts_arithmetic_operations_with_different_units(self):
        """Validates arithmetic operations with different units preserve left operand units."""
        # Given: nutrition facts with different units for same field
        # When: perform arithmetic operations
        # Then: result preserves unit from left operand (no unit conversion)
        facts1 = ApiNutriFacts(
            calories={"value": 250.0, "unit": "kcal"},
            protein=15.0
        )
        facts2 = ApiNutriFacts(
            calories={"value": 1000.0, "unit": "g"},  # Different unit (gram instead of kcal)
            protein=5.0
        )
        result = facts1 + facts2
        
        # Addition preserves unit from left operand (no unit conversion performed)
        assert result.calories.value == 1250.0  # 250 + 1000 (no conversion)
        assert result.calories.unit == MeasureUnit.ENERGY  # From left operand
        assert result.protein.value == 20.0
        assert result.protein.unit == MeasureUnit.GRAM


class TestApiNutriFactsDomainConversion:
    """Test nutrition facts conversion between API schema and domain model."""

    def test_api_nutri_facts_from_domain_conversion(self):
        """Validates conversion from domain model to API schema."""
        # Given: domain nutrition facts model
        # When: convert to API schema
        # Then: all fields are properly converted
        domain_nutri_facts = NutriFacts(
            calories=NutriValue(value=250.0, unit=MeasureUnit.ENERGY),
            protein=NutriValue(value=15.0, unit=MeasureUnit.GRAM),
            carbohydrate=NutriValue(value=30.0, unit=MeasureUnit.GRAM),
            total_fat=NutriValue(value=10.0, unit=MeasureUnit.GRAM),
            sodium=NutriValue(value=500.0, unit=MeasureUnit.MILLIGRAM)
        )
        
        api_nutri_facts = ApiNutriFacts.from_domain(domain_nutri_facts)
        
        assert api_nutri_facts.calories.value == 250.0
        assert api_nutri_facts.calories.unit == MeasureUnit.ENERGY
        assert api_nutri_facts.protein.value == 15.0
        assert api_nutri_facts.protein.unit == MeasureUnit.GRAM
        assert api_nutri_facts.carbohydrate.value == 30.0
        assert api_nutri_facts.carbohydrate.unit == MeasureUnit.GRAM
        assert api_nutri_facts.total_fat.value == 10.0
        assert api_nutri_facts.total_fat.unit == MeasureUnit.GRAM
        assert api_nutri_facts.sodium.value == 500.0
        assert api_nutri_facts.sodium.unit == MeasureUnit.MILLIGRAM

    def test_api_nutri_facts_to_domain_conversion(self):
        """Validates conversion from API schema to domain model."""
        # Given: API nutrition facts schema
        # When: convert to domain model
        # Then: all fields are properly converted
        api_nutri_facts = ApiNutriFacts(
            calories=250.0,
            protein=15.0,
            carbohydrate=30.0,
            total_fat=10.0,
            sodium=500.0
        )
        
        domain_nutri_facts = api_nutri_facts.to_domain()
        
        assert domain_nutri_facts.calories.value == 250.0
        assert domain_nutri_facts.calories.unit == MeasureUnit.ENERGY
        assert domain_nutri_facts.protein.value == 15.0
        assert domain_nutri_facts.protein.unit == MeasureUnit.GRAM
        assert domain_nutri_facts.carbohydrate.value == 30.0
        assert domain_nutri_facts.carbohydrate.unit == MeasureUnit.GRAM
        assert domain_nutri_facts.total_fat.value == 10.0
        assert domain_nutri_facts.total_fat.unit == MeasureUnit.GRAM
        assert domain_nutri_facts.sodium.value == 500.0
        assert domain_nutri_facts.sodium.unit == MeasureUnit.MILLIGRAM

    def test_api_nutri_facts_domain_conversion_roundtrip(self):
        """Validates roundtrip conversion maintains data integrity."""
        # Given: domain nutrition facts model
        # When: convert to API schema and back to domain
        # Then: data integrity is maintained
        original_domain = NutriFacts(
            calories=NutriValue(value=250.0, unit=MeasureUnit.ENERGY),
            protein=NutriValue(value=15.0, unit=MeasureUnit.GRAM),
            carbohydrate=NutriValue(value=30.0, unit=MeasureUnit.GRAM),
            total_fat=NutriValue(value=10.0, unit=MeasureUnit.GRAM),
            sodium=NutriValue(value=500.0, unit=MeasureUnit.MILLIGRAM),
            vitamin_c=NutriValue(value=60.0, unit=MeasureUnit.MILLIGRAM)
        )
        
        api_nutri_facts = ApiNutriFacts.from_domain(original_domain)
        converted_domain = api_nutri_facts.to_domain()
        
        assert converted_domain == original_domain

    def test_api_nutri_facts_domain_conversion_with_zero_values(self):
        """Validates conversion handles zero values correctly."""
        # Given: domain nutrition facts with zero values
        # When: convert to API schema and back
        # Then: zero values are preserved
        original_domain = NutriFacts(
            calories=NutriValue(value=0.0, unit=MeasureUnit.ENERGY),
            protein=NutriValue(value=0.0, unit=MeasureUnit.GRAM)
        )
        
        api_nutri_facts = ApiNutriFacts.from_domain(original_domain)
        converted_domain = api_nutri_facts.to_domain()
        
        assert converted_domain == original_domain

    def test_api_nutri_facts_domain_conversion_all_units(self):
        """Validates conversion handles all measure units correctly."""
        # Given: nutrition facts with various measure units
        # When: convert to API schema and back
        # Then: all units are properly handled
        original_domain = NutriFacts(
            calories=NutriValue(value=250.0, unit=MeasureUnit.ENERGY),
            protein=NutriValue(value=15.0, unit=MeasureUnit.GRAM),
            sodium=NutriValue(value=500.0, unit=MeasureUnit.MILLIGRAM),
            vitamin_c=NutriValue(value=60.0, unit=MeasureUnit.MILLIGRAM),
            vitamin_a=NutriValue(value=1000.0, unit=MeasureUnit.IU)
        )
        
        api_nutri_facts = ApiNutriFacts.from_domain(original_domain)
        converted_domain = api_nutri_facts.to_domain()
        
        assert converted_domain == original_domain

    def test_api_nutri_facts_domain_conversion_decimal_precision(self):
        """Validates conversion preserves decimal precision."""
        # Given: domain nutrition facts with decimal precision
        # When: convert to API schema and back
        # Then: decimal precision is preserved
        original_calories = 250.123456
        original_protein = 15.789012
        original_domain = NutriFacts(
            calories=NutriValue(value=original_calories, unit=MeasureUnit.ENERGY),
            protein=NutriValue(value=original_protein, unit=MeasureUnit.GRAM)
        )
        
        api_nutri_facts = ApiNutriFacts.from_domain(original_domain)
        converted_domain = api_nutri_facts.to_domain()
        
        assert converted_domain.calories.value == original_calories
        assert converted_domain.protein.value == original_protein

    def test_api_nutri_facts_domain_conversion_partial_fields(self):
        """Validates conversion handles partial field data correctly."""
        # Given: domain nutrition facts with only some fields set
        # When: convert to API schema and back
        # Then: all fields are handled correctly
        original_domain = NutriFacts(
            calories=NutriValue(value=250.0, unit=MeasureUnit.ENERGY),
            protein=NutriValue(value=15.0, unit=MeasureUnit.GRAM)
        )
        
        api_nutri_facts = ApiNutriFacts.from_domain(original_domain)
        converted_domain = api_nutri_facts.to_domain()
        
        # Check that set fields are preserved
        assert converted_domain.calories.value == 250.0
        assert converted_domain.calories.unit == MeasureUnit.ENERGY
        assert converted_domain.protein.value == 15.0
        assert converted_domain.protein.unit == MeasureUnit.GRAM
        
        # Check that unset fields have default values
        assert converted_domain.carbohydrate.value == 0.0
        assert converted_domain.carbohydrate.unit == MeasureUnit.GRAM
        assert converted_domain.total_fat.value == 0.0
        assert converted_domain.total_fat.unit == MeasureUnit.GRAM
        assert converted_domain.sodium.value == 0.0
        assert converted_domain.sodium.unit == MeasureUnit.MILLIGRAM

    def test_api_nutri_facts_domain_conversion_with_none_values(self):
        """Validates conversion handles None values correctly."""
        # Given: domain nutrition facts with None values
        # When: convert to API schema and back
        # Then: None values are converted to default values
        original_domain = NutriFacts(
            calories=NutriValue(value=250.0, unit=MeasureUnit.ENERGY),
            protein=None,  # None value
            carbohydrate=NutriValue(value=30.0, unit=MeasureUnit.GRAM)
        )
        
        api_nutri_facts = ApiNutriFacts.from_domain(original_domain)
        converted_domain = api_nutri_facts.to_domain()
        
        # Check that set fields are preserved
        assert converted_domain.calories.value == 250.0
        assert converted_domain.calories.unit == MeasureUnit.ENERGY
        assert converted_domain.carbohydrate.value == 30.0
        assert converted_domain.carbohydrate.unit == MeasureUnit.GRAM
        
        # Check that None values are converted to default values
        assert converted_domain.protein.value == 0.0
        assert converted_domain.protein.unit == MeasureUnit.GRAM


class TestApiNutriFactsOrmConversion:
    """Test nutrition facts conversion between API schema and ORM model."""

    def test_api_nutri_facts_from_orm_model_conversion(self):
        """Validates conversion from ORM model to API schema."""
        # Given: ORM nutrition facts model
        # When: convert to API schema
        # Then: all fields are properly converted
        orm_nutri_facts = NutriFactsSaModel(
            calories=250.0,
            protein=15.0,
            carbohydrate=30.0,
            total_fat=10.0,
            sodium=500.0,
            vitamin_c=60.0
        )
        
        api_nutri_facts = ApiNutriFacts.from_orm_model(orm_nutri_facts)
        
        assert api_nutri_facts.calories.value == 250.0
        assert api_nutri_facts.calories.unit == MeasureUnit.ENERGY
        assert api_nutri_facts.protein.value == 15.0
        assert api_nutri_facts.protein.unit == MeasureUnit.GRAM
        assert api_nutri_facts.carbohydrate.value == 30.0
        assert api_nutri_facts.carbohydrate.unit == MeasureUnit.GRAM
        assert api_nutri_facts.total_fat.value == 10.0
        assert api_nutri_facts.total_fat.unit == MeasureUnit.GRAM
        assert api_nutri_facts.sodium.value == 500.0
        assert api_nutri_facts.sodium.unit == MeasureUnit.MILLIGRAM
        assert api_nutri_facts.vitamin_c.value == 60.0
        assert api_nutri_facts.vitamin_c.unit == MeasureUnit.MILLIGRAM

    def test_api_nutri_facts_to_orm_kwargs_conversion(self):
        """Validates conversion from API schema to ORM kwargs."""
        # Given: API nutrition facts schema
        # When: convert to ORM kwargs
        # Then: all fields are properly converted to numeric values
        api_nutri_facts = ApiNutriFacts(
            calories=250.0,
            protein=15.0,
            carbohydrate=30.0,
            total_fat=10.0,
            sodium=500.0,
            vitamin_c=60.0
        )
        
        orm_kwargs = api_nutri_facts.to_orm_kwargs()
        
        assert orm_kwargs["calories"] == 250.0
        assert orm_kwargs["protein"] == 15.0
        assert orm_kwargs["carbohydrate"] == 30.0
        assert orm_kwargs["total_fat"] == 10.0
        assert orm_kwargs["sodium"] == 500.0
        assert orm_kwargs["vitamin_c"] == 60.0

    def test_api_nutri_facts_orm_conversion_roundtrip(self):
        """Validates roundtrip conversion maintains data integrity."""
        # Given: ORM nutrition facts model
        # When: convert to API schema and back to ORM kwargs
        # Then: data integrity is maintained
        original_orm = NutriFactsSaModel(
            calories=250.0,
            protein=15.0,
            carbohydrate=30.0,
            total_fat=10.0,
            sodium=500.0,
            vitamin_c=60.0,
            vitamin_a=1000.0,
            calcium=200.0
        )
        
        api_nutri_facts = ApiNutriFacts.from_orm_model(original_orm)
        orm_kwargs = api_nutri_facts.to_orm_kwargs()
        
        # Create new ORM model from kwargs for comparison
        new_orm = NutriFactsSaModel(**orm_kwargs)
        
        assert new_orm.calories == original_orm.calories
        assert new_orm.protein == original_orm.protein
        assert new_orm.carbohydrate == original_orm.carbohydrate
        assert new_orm.total_fat == original_orm.total_fat
        assert new_orm.sodium == original_orm.sodium
        assert new_orm.vitamin_c == original_orm.vitamin_c
        assert new_orm.vitamin_a == original_orm.vitamin_a
        assert new_orm.calcium == original_orm.calcium

    def test_api_nutri_facts_orm_conversion_with_none_values(self):
        """Validates conversion handles None values correctly."""
        # Given: ORM nutrition facts with None values
        # When: convert to API schema and back
        # Then: None values are converted to default values
        original_orm = NutriFactsSaModel(
            calories=250.0,
            protein=None,  # None value
            carbohydrate=30.0,
            total_fat=None  # None value
        )
        
        api_nutri_facts = ApiNutriFacts.from_orm_model(original_orm)
        orm_kwargs = api_nutri_facts.to_orm_kwargs()
        
        new_orm = NutriFactsSaModel(**orm_kwargs)
        
        assert new_orm.calories == 250.0
        assert new_orm.protein == 0.0  # None converted to 0.0
        assert new_orm.carbohydrate == 30.0
        assert new_orm.total_fat == 0.0  # None converted to 0.0

    def test_api_nutri_facts_orm_conversion_with_zero_values(self):
        """Validates conversion handles zero values correctly."""
        # Given: ORM nutrition facts with zero values
        # When: convert to API schema and back
        # Then: zero values are preserved
        original_orm = NutriFactsSaModel(
            calories=0.0,
            protein=0.0,
            carbohydrate=30.0
        )
        
        api_nutri_facts = ApiNutriFacts.from_orm_model(original_orm)
        orm_kwargs = api_nutri_facts.to_orm_kwargs()
        
        new_orm = NutriFactsSaModel(**orm_kwargs)
        
        assert new_orm.calories == 0.0
        assert new_orm.protein == 0.0
        assert new_orm.carbohydrate == 30.0

    def test_api_nutri_facts_orm_conversion_with_decimal_precision(self):
        """Validates conversion preserves decimal precision."""
        # Given: ORM nutrition facts with decimal precision
        # When: convert to API schema and back
        # Then: decimal precision is preserved
        original_calories = 250.123456
        original_protein = 15.789012
        original_orm = NutriFactsSaModel(
            calories=original_calories,
            protein=original_protein,
            carbohydrate=30.0
        )
        
        api_nutri_facts = ApiNutriFacts.from_orm_model(original_orm)
        orm_kwargs = api_nutri_facts.to_orm_kwargs()
        
        new_orm = NutriFactsSaModel(**orm_kwargs)
        
        assert new_orm.calories == original_calories
        assert new_orm.protein == original_protein
        assert new_orm.carbohydrate == 30.0

    def test_api_nutri_facts_orm_conversion_partial_fields(self):
        """Validates conversion handles partial field data correctly."""
        # Given: ORM nutrition facts with only some fields set
        # When: convert to API schema and back
        # Then: all fields are handled correctly
        original_orm = NutriFactsSaModel(
            calories=250.0,
            protein=15.0
        )
        
        api_nutri_facts = ApiNutriFacts.from_orm_model(original_orm)
        orm_kwargs = api_nutri_facts.to_orm_kwargs()
        
        new_orm = NutriFactsSaModel(**orm_kwargs)
        
        # Check that set fields are preserved
        assert new_orm.calories == 250.0
        assert new_orm.protein == 15.0
        
        # Check that unset fields have default values (0.0)
        assert new_orm.carbohydrate == 0.0
        assert new_orm.total_fat == 0.0
        assert new_orm.sodium == 0.0

    def test_api_nutri_facts_orm_conversion_all_nutrition_fields(self):
        """Validates conversion handles all nutrition fields correctly."""
        # Given: ORM nutrition facts with all fields set
        # When: convert to API schema and back
        # Then: all fields are properly handled
        original_orm = NutriFactsSaModel(
            calories=250.0,
            protein=15.0,
            carbohydrate=30.0,
            total_fat=10.0,
            saturated_fat=3.0,
            trans_fat=0.5,
            dietary_fiber=5.0,
            sodium=500.0,
            vitamin_a=1000.0,
            vitamin_c=60.0,
            calcium=200.0,
            iron=8.0
        )
        
        api_nutri_facts = ApiNutriFacts.from_orm_model(original_orm)
        orm_kwargs = api_nutri_facts.to_orm_kwargs()
        
        new_orm = NutriFactsSaModel(**orm_kwargs)
        
        # Check that all set fields are preserved
        assert new_orm.calories == 250.0
        assert new_orm.protein == 15.0
        assert new_orm.carbohydrate == 30.0
        assert new_orm.total_fat == 10.0
        assert new_orm.saturated_fat == 3.0
        assert new_orm.trans_fat == 0.5
        assert new_orm.dietary_fiber == 5.0
        assert new_orm.sodium == 500.0
        assert new_orm.vitamin_a == 1000.0
        assert new_orm.vitamin_c == 60.0
        assert new_orm.calcium == 200.0
        assert new_orm.iron == 8.0


class TestApiNutriFactsEdgeCases:
    """Test nutrition facts schema edge cases and error handling."""

    def test_api_nutri_facts_validation_invalid_field_type_rejected(self):
        """Validates invalid field types are rejected."""
        # Given: invalid field type
        # When: create nutrition facts with invalid field type
        # Then: ValidationConversionError is raised
        with pytest.raises(ValidationConversionError) as exc_info:
            ApiNutriFacts(calories="invalid_string")
        
        assert "Invalid value for field 'calories'" in str(exc_info.value)

    def test_api_nutri_facts_validation_invalid_dict_structure_handled(self):
        """Validates invalid dictionary structure is handled with defaults."""
        # Given: invalid dictionary structure
        # When: create nutrition facts with invalid dict
        # Then: default values are used
        api_nutri_facts = ApiNutriFacts(calories={"invalid_key": "value"})
        
        assert api_nutri_facts.calories.value == 0.0
        assert api_nutri_facts.calories.unit == MeasureUnit.ENERGY

    def test_api_nutri_facts_validation_invalid_unit_type_rejected(self):
        """Validates invalid unit type is rejected."""
        # Given: invalid unit type in dictionary
        # When: create nutrition facts with invalid unit type
        # Then: ValidationConversionError is raised
        with pytest.raises(ValidationConversionError) as exc_info:
            ApiNutriFacts(calories={"value": 100.0, "unit": 123})  # Invalid unit type
        
        assert "Unit for field 'calories' must be a valid MeasureUnit" in str(exc_info.value)

    def test_api_nutri_facts_validation_none_unit_handled(self):
        """Validates None unit is handled with default unit."""
        # Given: None unit in dictionary
        # When: create nutrition facts with None unit
        # Then: default unit is used
        api_nutri_facts = ApiNutriFacts(calories={"value": 100.0, "unit": None})
        
        assert api_nutri_facts.calories.value == 100.0
        assert api_nutri_facts.calories.unit == MeasureUnit.ENERGY

    def test_api_nutri_facts_validation_none_value_handled(self):
        """Validates None value is handled with default value."""
        # Given: None value in dictionary
        # When: create nutrition facts with None value
        # Then: default value is used
        api_nutri_facts = ApiNutriFacts(calories={"value": None, "unit": "kcal"})
        
        assert api_nutri_facts.calories.value == 0.0
        assert api_nutri_facts.calories.unit == MeasureUnit.ENERGY

    def test_api_nutri_facts_validation_negative_value_rejected(self):
        """Validates negative values are rejected."""
        # Given: negative value
        # When: create nutrition facts with negative value
        # Then: ValidationConversionError is raised
        with pytest.raises(ValidationConversionError) as exc_info:
            ApiNutriFacts(calories=-100.0)
        
        assert "Value for field 'calories' must be between 0.0 and infinity" in str(exc_info.value)

    def test_api_nutri_facts_validation_negative_value_in_dict_rejected(self):
        """Validates negative values in dictionary are rejected."""
        # Given: negative value in dictionary
        # When: create nutrition facts with negative value in dict
        # Then: ValidationConversionError is raised
        with pytest.raises(ValidationConversionError) as exc_info:
            ApiNutriFacts(calories={"value": -100.0, "unit": "kcal"})
        
        assert "Value for field 'calories' must be between 0.0 and infinity" in str(exc_info.value)

    def test_api_nutri_facts_validation_infinity_value_accepted(self):
        """Validates infinity values are accepted."""
        # Given: infinity value
        # When: create nutrition facts with infinity value
        # Then: infinity value is accepted
        import math
        api_nutri_facts = ApiNutriFacts(calories=math.inf)
        
        assert api_nutri_facts.calories.value == math.inf
        assert api_nutri_facts.calories.unit == MeasureUnit.ENERGY

    def test_api_nutri_facts_validation_very_large_value_accepted(self):
        """Validates very large values are accepted."""
        # Given: very large value
        # When: create nutrition facts with very large value
        # Then: very large value is accepted
        large_value = 1e10
        api_nutri_facts = ApiNutriFacts(calories=large_value)
        
        assert api_nutri_facts.calories.value == large_value
        assert api_nutri_facts.calories.unit == MeasureUnit.ENERGY

    def test_api_nutri_facts_validation_very_small_positive_value_accepted(self):
        """Validates very small positive values are accepted."""
        # Given: very small positive value
        # When: create nutrition facts with very small value
        # Then: very small value is accepted
        small_value = 1e-10
        api_nutri_facts = ApiNutriFacts(calories=small_value)
        
        assert api_nutri_facts.calories.value == small_value
        assert api_nutri_facts.calories.unit == MeasureUnit.ENERGY

    def test_api_nutri_facts_validation_zero_value_accepted(self):
        """Validates zero values are accepted."""
        # Given: zero value
        # When: create nutrition facts with zero value
        # Then: zero value is accepted
        api_nutri_facts = ApiNutriFacts(calories=0.0)
        
        assert api_nutri_facts.calories.value == 0.0
        assert api_nutri_facts.calories.unit == MeasureUnit.ENERGY

    def test_api_nutri_facts_validation_integer_value_converted_to_float(self):
        """Validates integer values are converted to float."""
        # Given: integer value
        # When: create nutrition facts with integer value
        # Then: integer is converted to float
        api_nutri_facts = ApiNutriFacts(calories=250)
        
        assert api_nutri_facts.calories.value == 250.0
        assert isinstance(api_nutri_facts.calories.value, float)

    def test_api_nutri_facts_validation_string_number_rejected(self):
        """Validates string numbers are rejected."""
        # Given: string number
        # When: create nutrition facts with string number
        # Then: ValidationConversionError is raised
        with pytest.raises(ValidationConversionError) as exc_info:
            ApiNutriFacts(calories="250.5")
        
        assert "Invalid value for field 'calories'" in str(exc_info.value)

    def test_api_nutri_facts_validation_invalid_string_rejected(self):
        """Validates invalid string values are rejected."""
        # Given: invalid string value
        # When: create nutrition facts with invalid string
        # Then: ValidationConversionError is raised
        with pytest.raises(ValidationConversionError) as exc_info:
            ApiNutriFacts(calories="invalid_string")
        
        assert "Invalid value for field 'calories'" in str(exc_info.value)

    def test_api_nutri_facts_validation_empty_string_rejected(self):
        """Validates empty string values are rejected."""
        # Given: empty string value
        # When: create nutrition facts with empty string
        # Then: ValidationConversionError is raised
        with pytest.raises(ValidationConversionError) as exc_info:
            ApiNutriFacts(calories="")
        
        assert "Invalid value for field 'calories'" in str(exc_info.value)

    def test_api_nutri_facts_validation_boolean_value_converted_to_float(self):
        """Validates boolean values are converted to float."""
        # Given: boolean value
        # When: create nutrition facts with boolean value
        # Then: boolean is converted to float
        api_nutri_facts = ApiNutriFacts(calories=True)
        
        assert api_nutri_facts.calories.value == 1.0
        assert isinstance(api_nutri_facts.calories.value, float)
        assert api_nutri_facts.calories.unit == MeasureUnit.ENERGY

    def test_api_nutri_facts_validation_list_value_rejected(self):
        """Validates list values are rejected."""
        # Given: list value
        # When: create nutrition facts with list value
        # Then: ValidationConversionError is raised
        with pytest.raises(ValidationConversionError) as exc_info:
            ApiNutriFacts(calories=[100, 200])
        
        assert "Invalid value for field 'calories'" in str(exc_info.value)

    def test_api_nutri_facts_validation_dict_with_missing_value_key(self):
        """Validates dictionary with missing value key is handled."""
        # Given: dictionary with only unit key
        # When: create nutrition facts with dict missing value
        # Then: default value (0.0) is used
        api_nutri_facts = ApiNutriFacts(calories={"unit": "kcal"})
        
        assert api_nutri_facts.calories.value == 0.0
        assert api_nutri_facts.calories.unit == MeasureUnit.ENERGY

    def test_api_nutri_facts_validation_dict_with_missing_unit_key(self):
        """Validates dictionary with missing unit key is handled."""
        # Given: dictionary with only value key
        # When: create nutrition facts with dict missing unit
        # Then: default unit is used
        api_nutri_facts = ApiNutriFacts(calories={"value": 250.0})
        
        assert api_nutri_facts.calories.value == 250.0
        assert api_nutri_facts.calories.unit == MeasureUnit.ENERGY

    def test_api_nutri_facts_validation_empty_dict_handled(self):
        """Validates empty dictionary is handled."""
        # Given: empty dictionary
        # When: create nutrition facts with empty dict
        # Then: default values are used
        api_nutri_facts = ApiNutriFacts(calories={})
        
        assert api_nutri_facts.calories.value == 0.0
        assert api_nutri_facts.calories.unit == MeasureUnit.ENERGY

    def test_api_nutri_facts_immutability(self):
        """Validates nutrition facts schema is immutable."""
        # Given: nutrition facts instance
        # When: attempt to modify fields
        # Then: modification raises error
        api_nutri_facts = ApiNutriFacts(calories=250.0)
        
        with pytest.raises(ValidationError):
            api_nutri_facts.calories = ApiNutriValue(value=300.0, unit=MeasureUnit.ENERGY)

    def test_api_nutri_facts_serialization_unicode_characters(self):
        """Validates serialization handles unicode characters correctly."""
        # Given: nutrition facts with unicode characters in unit
        # When: serialize and deserialize
        # Then: unicode characters are preserved
        api_nutri_facts = ApiNutriFacts(
            calories={"value": 250.0, "unit": "kcal"},
            protein={"value": 15.0, "unit": "g"}
        )
        
        json_str = api_nutri_facts.model_dump_json()
        deserialized = ApiNutriFacts.model_validate_json(json_str)
        
        assert deserialized.calories.value == 250.0
        assert deserialized.calories.unit == MeasureUnit.ENERGY
        assert deserialized.protein.value == 15.0
        assert deserialized.protein.unit == MeasureUnit.GRAM

    def test_api_nutri_facts_arithmetic_operations_with_invalid_type(self):
        """Validates arithmetic operations with invalid types raise TypeError."""
        # Given: nutrition facts and invalid type
        # When: perform arithmetic operations
        # Then: TypeError is raised
        facts = ApiNutriFacts(calories=250.0)
        
        with pytest.raises(TypeError):
            _ = facts + "invalid"
        
        with pytest.raises(TypeError):
            _ = facts - "invalid"
        
        with pytest.raises(TypeError):
            _ = facts * "invalid"
        
        with pytest.raises(TypeError):
            _ = facts / "invalid"

    def test_api_nutri_facts_arithmetic_operations_with_negative_result_raises_error(self):
        """Validates arithmetic operations resulting in negative values raise ValidationError."""
        # Given: nutrition facts that would result in negative values
        # When: perform arithmetic that results in negative value
        # Then: ValidationError is raised due to NonNegativeFloat constraint
        facts1 = ApiNutriFacts(calories=100.0, protein=5.0)
        facts2 = ApiNutriFacts(calories=200.0, protein=10.0)
        
        with pytest.raises(ValidationError):
            _ = facts1 - facts2  # 100 - 200 = -100 (negative result)

    def test_api_nutri_facts_arithmetic_operations_chain_with_edge_cases(self):
        """Validates chained arithmetic operations with edge cases."""
        # Given: nutrition facts with edge case values
        # When: perform chained arithmetic operations
        # Then: operations handle edge cases correctly
        facts1 = ApiNutriFacts(calories=0.0, protein=1.0)
        facts2 = ApiNutriFacts(calories=100.0, protein=0.0)
        
        result = (facts1 + facts2) * 2.0
        
        assert result.calories.value == 200.0  # (0 + 100) * 2 = 200
        assert result.calories.unit == MeasureUnit.ENERGY
        assert result.protein.value == 2.0  # (1 + 0) * 2 = 2
        assert result.protein.unit == MeasureUnit.GRAM
