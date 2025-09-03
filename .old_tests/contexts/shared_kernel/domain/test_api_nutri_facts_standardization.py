"""
Behavior-focused tests for ApiNutriFacts schema standardization.

These tests validate the behavior and correctness of ApiNutriFacts schema
following the documented API schema patterns.

Focus: Test behavior and verify correctness, not implementation details.
"""

import pytest
from unittest.mock import Mock

from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_facts import ApiNutriFacts


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
        # The validator converts None values to ApiNutriValue(0.0, default_unit)
        nutri_facts = ApiNutriFacts(
            calories=None,
            protein=None,
            carbohydrate=None
        )  # type: ignore[arg-type]
        
        # Check a few key fields are converted to ApiNutriValue with 0.0 values
        assert nutri_facts.calories.value == 0.0
        assert nutri_facts.protein.value == 0.0
        assert nutri_facts.carbohydrate.value == 0.0

    def test_nutritional_value_validation_rejects_negative_values(self):
        """Test that negative nutritional values are rejected."""
        # Negative values should cause validation error
        with pytest.raises(ValueError, match="must be between 0.0 and infinity"):
            ApiNutriFacts(calories=-100.0)  # type: ignore[arg-type]

    def test_nutritional_value_validation_accepts_zero_values(self):
        """Test that zero nutritional values are accepted."""
        nutri_facts = ApiNutriFacts(
            calories=0.0,
            protein=0.0,
            carbohydrate=0.0,
            total_fat=0.0
        )  # type: ignore[arg-type]
        
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
        )  # type: ignore[arg-type]
        
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
        with pytest.raises(AttributeError):
            ApiNutriFacts.from_orm_model(None)  # type: ignore[arg-type]

    def test_to_orm_kwargs_converts_values_to_float(self):
        """Test that to_orm_kwargs extracts float values from ApiNutriValue objects."""
        nutri_facts = ApiNutriFacts(
            calories=200.0,
            protein=18.5,
            carbohydrate=25.0
        )  # type: ignore[arg-type]
        
        orm_kwargs = nutri_facts.to_orm_kwargs()
        
        # Should extract numeric values from ApiNutriValue objects
        assert orm_kwargs['calories'] == 200.0
        assert orm_kwargs['protein'] == 18.5
        assert orm_kwargs['carbohydrate'] == 25.0

    def test_comprehensive_nutritional_fields_coverage(self):
        """Test that all major nutritional fields are properly handled."""
        # Test with a comprehensive set of nutritional data
        nutri_facts = ApiNutriFacts(
            calories=500.0,
            protein=30.0,
            carbohydrate=60.0,
            total_fat=20.0,
            saturated_fat=5.0,
            dietary_fiber=8.0,
            sodium=600.0,
            calcium=200.0,
            iron=15.0,
            vitamin_c=45.0,
            vitamin_d=25.0
        )  # type: ignore[arg-type]
        
        # Verify all values are preserved correctly as ApiNutriValue objects
        assert nutri_facts.calories.value == 500.0
        assert nutri_facts.protein.value == 30.0
        assert nutri_facts.carbohydrate.value == 60.0
        assert nutri_facts.total_fat.value == 20.0
        assert nutri_facts.saturated_fat.value == 5.0
        assert nutri_facts.dietary_fiber.value == 8.0
        assert nutri_facts.sodium.value == 600.0
        assert nutri_facts.calcium.value == 200.0
        assert nutri_facts.iron.value == 15.0
        assert nutri_facts.vitamin_c.value == 45.0
        assert nutri_facts.vitamin_d.value == 25.0

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
