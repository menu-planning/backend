"""
Comprehensive behavior-focused tests for standardized shared value objects.

These tests validate the behavior and correctness of ApiProfile, ApiNutriFacts, 
and ApiNutriValue schemas following the documented API schema patterns.

Focus: Test behavior and verify correctness, not implementation details.
"""

import pytest
from datetime import date, timedelta
from unittest.mock import Mock

from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_profile import ApiProfile
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_facts import ApiNutriFacts
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_value import ApiNutriValue
from src.contexts.shared_kernel.domain.enums import MeasureUnit


class TestApiProfileStandardization:
    """Test ApiProfile schema standardization and behavior."""

    def test_profile_creation_with_valid_data(self):
        """Test that ApiProfile accepts valid profile data."""
        profile = ApiProfile(
            name="John Doe",
            birthday=date(1990, 5, 15),
            sex="male"
        )
        
        assert profile.name == "John Doe"
        assert profile.birthday == date(1990, 5, 15)
        assert profile.sex == "male"

    def test_profile_creation_with_none_values(self):
        """Test that ApiProfile validates required fields properly."""
        # All fields are required, so this should raise validation errors
        with pytest.raises(ValueError):
            profile = ApiProfile(
                name=None,  # type: ignore
                birthday=None,  # type: ignore  
                sex=None  # type: ignore
            )

    def test_name_field_validation_trims_whitespace(self):
        """Test that name field trims whitespace as expected."""
        profile = ApiProfile(
            name="  John Doe  ",
            birthday=date(1990, 1, 1),
            sex="masculino"
        )
        assert profile.name == "John Doe"

    def test_name_field_validation_handles_empty_string(self):
        """Test that empty string raises validation error for required field."""
        with pytest.raises(ValueError):
            profile = ApiProfile(
                name="   ",
                birthday=date(1990, 1, 1),
                sex="masculino"
            )

    def test_sex_field_validation_normalizes_case(self):
        """Test that sex field normalizes to lowercase."""
        profile = ApiProfile(
            name="Test User",
            birthday=date(1990, 1, 1),
            sex="MASCULINO"
        )
        assert profile.sex == "masculino"

    def test_sex_field_validation_handles_valid_options(self):
        """Test that valid sex options are accepted."""
        valid_options = ["masculino", "feminino"]
        
        for option in valid_options:
            profile = ApiProfile(
                name="Test User",
                birthday=date(1990, 1, 1),
                sex=option
            )
            assert profile.sex == option.lower()

    def test_sex_field_validation_rejects_invalid_values(self):
        """Test that invalid sex values are rejected."""
        with pytest.raises(ValueError):
            profile = ApiProfile(
                name="Test User",
                birthday=date(1990, 1, 1),
                sex="invalid_value"
            )

    def test_birthday_validation_rejects_future_date(self):
        """Test that future birthdates are rejected."""
        future_date = date.today() + timedelta(days=1)
        
        with pytest.raises(ValueError, match="Birthday cannot be in the future"):
            ApiProfile(
                name="Test User",
                birthday=future_date,
                sex="masculino"
            )

    def test_birthday_validation_rejects_unreasonably_old_date(self):
        """Test that unreasonably old birthdates are rejected."""
        old_date = date(1800, 1, 1)
        
        with pytest.raises(ValueError, match="Birthday year must be after"):
            ApiProfile(
                name="Test User",
                birthday=old_date,
                sex="masculino"
            )

    def test_birthday_validation_accepts_reasonable_dates(self):
        """Test that reasonable birthdates are accepted."""
        reasonable_dates = [
            date(1950, 1, 1),
            date(1990, 6, 15),
            date(2000, 12, 31)
        ]
        
        for birth_date in reasonable_dates:
            profile = ApiProfile(
                name="Test User",
                birthday=birth_date,
                sex="masculino"
            )
            assert profile.birthday == birth_date

    def test_from_domain_conversion_preserves_data(self):
        """Test that from_domain conversion preserves all data correctly."""
        # Create mock domain object
        domain_profile = Mock()
        domain_profile.name = "Jane Smith"
        domain_profile.birthday = date(1985, 3, 20)
        domain_profile.sex = "female"
        
        api_profile = ApiProfile.from_domain(domain_profile)
        
        assert api_profile.name == "Jane Smith"
        assert api_profile.birthday == date(1985, 3, 20)
        assert api_profile.sex == "female"

    def test_to_domain_conversion_preserves_data(self):
        """Test that to_domain conversion preserves all data correctly."""
        api_profile = ApiProfile(
            name="Bob Johnson",
            birthday=date(1975, 8, 10),
            sex="male"
        )
        
        domain_profile = api_profile.to_domain()
        
        assert domain_profile.name == "Bob Johnson"
        assert domain_profile.birthday == date(1975, 8, 10)
        assert domain_profile.sex == "male"

    def test_from_orm_model_conversion_with_valid_data(self):
        """Test from_orm_model conversion with valid ORM data."""
        orm_model = Mock()
        orm_model.name = "Alice Brown"
        orm_model.birthday = date(1992, 11, 5)
        orm_model.sex = "female"
        
        api_profile = ApiProfile.from_orm_model(orm_model)
        
        assert api_profile.name == "Alice Brown"
        assert api_profile.birthday == date(1992, 11, 5)
        assert api_profile.sex == "female"

    def test_from_orm_model_rejects_none_input(self):
        """Test that from_orm_model rejects None input."""
        with pytest.raises(ValueError, match="ORM model cannot be None"):
            ApiProfile.from_orm_model(None)

    def test_to_orm_kwargs_conversion_provides_correct_format(self):
        """Test that to_orm_kwargs provides correctly formatted data."""
        api_profile = ApiProfile(
            name="Charlie Davis",
            birthday=date(1988, 2, 14),
            sex="other"
        )
        
        orm_kwargs = api_profile.to_orm_kwargs()
        
        expected_kwargs = {
            "name": "Charlie Davis",
            "birthday": date(1988, 2, 14),
            "sex": "other"
        }
        assert orm_kwargs == expected_kwargs

    def test_round_trip_conversion_preserves_data_integrity(self):
        """Test that domain → API → domain conversion preserves data integrity."""
        # Create mock domain object
        original_domain = Mock()
        original_domain.name = "Eva White"
        original_domain.birthday = date(1993, 7, 25)
        original_domain.sex = "non_binary"
        
        # Convert to API and back
        api_profile = ApiProfile.from_domain(original_domain)
        converted_domain = api_profile.to_domain()
        
        assert converted_domain.name == original_domain.name
        assert converted_domain.birthday == original_domain.birthday
        assert converted_domain.sex == original_domain.sex


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

    def test_from_orm_model_conversion_with_enum_unit(self):
        """Test from_orm_model conversion when ORM has enum unit."""
        orm_model = Mock()
        orm_model.value = 100.0
        orm_model.unit = MeasureUnit.GRAM
        
        api_nutri_value = ApiNutriValue.from_orm_model(orm_model)
        
        # ApiNutriValue.from_orm_model should return an ApiNutriValue instance
        assert isinstance(api_nutri_value, ApiNutriValue)
        assert api_nutri_value.unit == MeasureUnit.GRAM
        assert api_nutri_value.value == 100.0

    def test_from_orm_model_conversion_with_string_unit(self):
        """Test from_orm_model conversion when ORM has string unit."""
        orm_model = Mock()
        orm_model.value = 200.0
        orm_model.unit = "g"  # string unit that should be converted
        
        api_nutri_value = ApiNutriValue.from_orm_model(orm_model)
        
        # ApiNutriValue.from_orm_model should return an ApiNutriValue instance
        assert isinstance(api_nutri_value, ApiNutriValue)
        assert api_nutri_value.unit == MeasureUnit.GRAM
        assert api_nutri_value.value == 200.0

    def test_from_orm_model_handles_invalid_unit_gracefully(self):
        """Test that from_orm_model handles invalid unit values gracefully."""
        orm_model = Mock()
        orm_model.unit = "invalid_unit"
        orm_model.value = 300.0
        
        api_nutri_value = ApiNutriValue.from_orm_model(orm_model)
        
        assert api_nutri_value.unit is None  # Invalid unit becomes None
        assert api_nutri_value.value == 300.0

    def test_from_orm_model_rejects_none_input(self):
        """Test that from_orm_model rejects None input."""
        with pytest.raises(ValueError, match="ORM model cannot be None"):
            ApiNutriValue.from_orm_model(None)

    def test_to_orm_kwargs_provides_enum_value_for_unit(self):
        """Test that to_orm_kwargs provides enum value for ORM compatibility."""
        api_nutri_value = ApiNutriValue(
            unit=MeasureUnit.MILLIGRAM,
            value=50.0
        )
        
        orm_kwargs = api_nutri_value.to_orm_kwargs()
        
        assert orm_kwargs['unit'] == MeasureUnit.MILLIGRAM.value
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


class TestApiNutriFactsStandardization:
    """Test ApiNutriFacts schema standardization and behavior."""

    def test_nutri_facts_creation_with_valid_nutritional_data(self):
        """Test that ApiNutriFacts accepts valid nutritional data."""
        # Create with defaults for all fields, then override specific ones
        base_defaults = {field: 0.0 for field in ApiNutriFacts.model_fields.keys()}
        base_defaults.update({
            'calories': 250.0,
            'protein': 15.5,
            'carbohydrate': 30.0,
            'total_fat': 10.2
        })
        
        nutri_facts = ApiNutriFacts(**base_defaults) # type: ignore
        
        assert nutri_facts.calories.value == 250.0
        assert nutri_facts.protein.value == 15.5
        assert nutri_facts.carbohydrate.value == 30.0
        assert nutri_facts.total_fat.value == 10.2

    def test_nutri_facts_creation_with_all_none_values(self):
        """Test that ApiNutriFacts handles None values by converting to defaults."""
        # Create with all fields as None, they should become default ApiNutriValue(0.0)
        base_defaults = {field: None for field in ApiNutriFacts.model_fields.keys()}
        
        nutri_facts = ApiNutriFacts(**base_defaults)
        
        # Check a few key fields are converted to ApiNutriValue with 0.0 values
        assert nutri_facts.calories.value == 0.0
        assert nutri_facts.protein.value == 0.0
        assert nutri_facts.carbohydrate.value == 0.0

    def test_nutritional_value_validation_rejects_negative_values(self):
        """Test that negative nutritional values are rejected."""
        base_defaults = {field: 0.0 for field in ApiNutriFacts.model_fields.keys()}
        base_defaults['calories'] = -100.0  # This should cause validation error
        
        with pytest.raises(ValueError):
            ApiNutriFacts(**base_defaults) # type: ignore

    def test_nutritional_value_validation_accepts_zero_values(self):
        """Test that zero nutritional values are accepted."""
        base_defaults = {field: 0.0 for field in ApiNutriFacts.model_fields.keys()}
        base_defaults.update({
            'calories': 0.0,
            'protein': 0.0,
            'carbohydrate': 0.0,
            'total_fat': 0.0
        })
        
        nutri_facts = ApiNutriFacts(**base_defaults) # type: ignore
        
        assert nutri_facts.calories.value == 0.0
        assert nutri_facts.protein.value == 0.0
        assert nutri_facts.carbohydrate.value == 0.0
        assert nutri_facts.total_fat.value == 0.0

    def test_from_domain_conversion_handles_nutri_value_objects(self):
        """Test that from_domain properly converts NutriValue objects to floats."""
        # Create mock domain object with NutriValue instances
        domain_nutri_facts = Mock()
        
        # Mock NutriValue objects
        calories_nutri_value = Mock()
        calories_nutri_value.value = 300.0
        protein_nutri_value = Mock()
        protein_nutri_value.value = 20.0
        
        # Set up domain object attributes
        domain_nutri_facts.calories = calories_nutri_value
        domain_nutri_facts.protein = protein_nutri_value
        domain_nutri_facts.carbohydrate = 45.0  # Direct float
        
        # Mock all other fields as None for simplicity
        for field_name in ApiNutriFacts.model_fields.keys():
            if not hasattr(domain_nutri_facts, field_name):
                setattr(domain_nutri_facts, field_name, None)
        
        api_nutri_facts = ApiNutriFacts.from_domain(domain_nutri_facts)
        
        assert api_nutri_facts.calories.value == 300.0  # Extracted from NutriValue
        assert api_nutri_facts.protein.value == 20.0    # Extracted from NutriValue
        assert api_nutri_facts.carbohydrate.value == 45.0  # Direct float

    def test_to_domain_conversion_preserves_float_values(self):
        """Test that to_domain conversion preserves float values correctly."""
        api_nutri_facts = ApiNutriFacts(
            calories=400.0,
            protein=25.0,
            total_fat=15.0
        )
        
        domain_nutri_facts = api_nutri_facts.to_domain()
        
        assert domain_nutri_facts.calories.value == 400.0
        assert domain_nutri_facts.protein.value == 25.0
        assert domain_nutri_facts.total_fat.value == 15.0

    def test_from_orm_model_conversion_with_valid_data(self):
        """Test from_orm_model conversion with valid ORM data."""
        orm_model = Mock()
        orm_model.calories = 350.0
        orm_model.protein = 18.5
        orm_model.carbohydrate = 40.0
        
        # Mock all other fields for complete coverage
        for field_name in ApiNutriFacts.model_fields.keys():
            if not hasattr(orm_model, field_name):
                setattr(orm_model, field_name, None)
        
        api_nutri_facts = ApiNutriFacts.from_orm_model(orm_model)
        
        assert api_nutri_facts.calories == 350.0
        assert api_nutri_facts.protein == 18.5
        assert api_nutri_facts.carbohydrate == 40.0

    def test_from_orm_model_handles_invalid_values_gracefully(self):
        """Test that from_orm_model skips invalid values gracefully."""
        orm_model = Mock()
        orm_model.calories = "invalid"  # Invalid type
        orm_model.protein = 20.0        # Valid value
        
        # Mock all other fields
        for field_name in ApiNutriFacts.model_fields.keys():
            if not hasattr(orm_model, field_name):
                setattr(orm_model, field_name, None)
        
        api_nutri_facts = ApiNutriFacts.from_orm_model(orm_model)
        
        # Invalid value should be skipped, valid value preserved
        assert not hasattr(api_nutri_facts, 'calories') or api_nutri_facts.calories is None
        assert api_nutri_facts.protein == 20.0

    def test_from_orm_model_rejects_none_input(self):
        """Test that from_orm_model rejects None input."""
        with pytest.raises((ValueError, AttributeError)):
            ApiNutriFacts.from_orm_model(None) # type: ignore

    def test_to_orm_kwargs_converts_values_to_float(self):
        """Test that to_orm_kwargs extracts float values from ApiNutriValue objects."""
        base_defaults = {field: 0.0 for field in ApiNutriFacts.model_fields.keys()}
        base_defaults.update({
            'calories': 200.0,
            'protein': 18.5,
            'carbohydrate': 25.0
        })
        
        nutri_facts = ApiNutriFacts(**base_defaults) # type: ignore
        orm_kwargs = nutri_facts.to_orm_kwargs()
        
        # Should extract numeric values from ApiNutriValue objects
        assert orm_kwargs['calories'] == 200.0
        assert orm_kwargs['protein'] == 18.5
        assert orm_kwargs['carbohydrate'] == 25.0

    def test_comprehensive_nutritional_fields_coverage(self):
        """Test that all major nutritional fields are properly handled."""
        # Test with a comprehensive set of nutritional data
        comprehensive_data = {
            'calories': 500.0,
            'protein': 30.0,
            'carbohydrate': 60.0,
            'total_fat': 20.0,
            'saturated_fat': 5.0,
            'dietary_fiber': 8.0,
            'sodium': 600.0,
            'calcium': 200.0,
            'iron': 15.0,
            'vitamin_c': 45.0,
            'vitamin_d': 25.0
        }
        
        nutri_facts = ApiNutriFacts(**comprehensive_data)
        
        # Verify all values are preserved correctly as ApiNutriValue objects
        for field_name, expected_value in comprehensive_data.items():
            actual_value = getattr(nutri_facts, field_name)
            assert actual_value.value == expected_value

    def test_round_trip_conversion_preserves_data_integrity(self):
        """Test that domain → API → domain conversion preserves data integrity."""
        # Create mock domain object
        original_domain = Mock()
        original_domain.calories = 450.0
        original_domain.protein = 28.0
        original_domain.carbohydrate = 55.0
        
        # Mock all other fields as None
        for field_name in ApiNutriFacts.model_fields.keys():
            if not hasattr(original_domain, field_name):
                setattr(original_domain, field_name, None)
        
        # Convert to API and back
        api_nutri_facts = ApiNutriFacts.from_domain(original_domain)
        converted_domain = api_nutri_facts.to_domain()
        
        assert converted_domain.calories == original_domain.calories
        assert converted_domain.protein == original_domain.protein
        assert converted_domain.carbohydrate == original_domain.carbohydrate 