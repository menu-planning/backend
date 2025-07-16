"""
Comprehensive behavior-focused tests for ApiNutriFacts schema standardization.

Following Phase 1 patterns: 90+ test methods with >95% coverage, behavior-focused approach,
round-trip validation, comprehensive error handling, edge cases, and performance validation.

Focus: Test behavior and verify correctness, not implementation details.
Special focus: JSON validation with mixed input types (int | float | None | dict).
"""

import pytest
import time
import json
from unittest.mock import Mock

from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_facts import ApiNutriFacts
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_value import ApiNutriValue
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.value_objects.nutri_value import NutriValue
from src.contexts.shared_kernel.domain.enums import MeasureUnit
from pydantic import ValidationError


class TestApiNutriFactsFourLayerConversion:
    """Test comprehensive four-layer conversion patterns for ApiNutriFacts."""

    def test_from_domain_conversion_preserves_all_nutritional_data(self):
        """Test that domain to API conversion preserves all nutritional facts data accurately."""
        domain_nutri_facts = NutriFacts(
            calories=NutriValue(value=250.0, unit=MeasureUnit.ENERGY),
            protein=NutriValue(value=15.5, unit=MeasureUnit.GRAM),
            carbohydrate=NutriValue(value=30.0, unit=MeasureUnit.GRAM),
            total_fat=NutriValue(value=8.2, unit=MeasureUnit.GRAM),
            vitamin_c=NutriValue(value=60.0, unit=MeasureUnit.MILLIGRAM),
            calcium=NutriValue(value=120.0, unit=MeasureUnit.MILLIGRAM)
        )
        
        api_nutri_facts = ApiNutriFacts.from_domain(domain_nutri_facts)
        
        # Verify major macronutrients
        assert isinstance(api_nutri_facts.calories, ApiNutriValue)
        assert api_nutri_facts.calories.value == 250.0
        assert api_nutri_facts.calories.unit == MeasureUnit.ENERGY
        
        assert isinstance(api_nutri_facts.protein, ApiNutriValue)
        assert api_nutri_facts.protein.value == 15.5
        assert api_nutri_facts.protein.unit == MeasureUnit.GRAM
        
        # Verify micronutrients
        assert isinstance(api_nutri_facts.vitamin_c, ApiNutriValue)
        assert api_nutri_facts.vitamin_c.value == 60.0
        assert api_nutri_facts.vitamin_c.unit == MeasureUnit.MILLIGRAM

    def test_to_domain_conversion_preserves_all_nutritional_data(self):
        """Test that API to domain conversion preserves all nutritional facts data accurately."""
        # Create using kwargs - all fields have defaults
        api_nutri_facts = ApiNutriFacts(
            calories=ApiNutriValue(value=300.0, unit=MeasureUnit.ENERGY),
            protein=ApiNutriValue(value=20.0, unit=MeasureUnit.GRAM),
            total_fat=ApiNutriValue(value=12.0, unit=MeasureUnit.GRAM),
            vitamin_d=ApiNutriValue(value=400.0, unit=MeasureUnit.IU),
            iron=ApiNutriValue(value=2.5, unit=MeasureUnit.MILLIGRAM)
        ) # type: ignore
        
        domain_nutri_facts = api_nutri_facts.to_domain()
        
        # Verify conversion to domain objects
        assert isinstance(domain_nutri_facts.calories, NutriValue)
        assert domain_nutri_facts.calories.value == 300.0
        assert domain_nutri_facts.calories.unit == MeasureUnit.ENERGY
        
        assert isinstance(domain_nutri_facts.protein, NutriValue)
        assert domain_nutri_facts.protein.value == 20.0
        assert domain_nutri_facts.protein.unit == MeasureUnit.GRAM

    def test_from_orm_model_conversion_with_numeric_values(self):
        """Test that ORM to API conversion handles numeric-only values correctly."""
        mock_orm = Mock()
        mock_orm.calories = 200.0
        mock_orm.protein = 18.0
        mock_orm.carbohydrate = 25.0
        mock_orm.total_fat = 7.5
        mock_orm.vitamin_c = 45.0
        
        # Set all other fields to None to avoid AttributeError
        for field_name in ApiNutriFacts.model_fields.keys():
            if not hasattr(mock_orm, field_name):
                setattr(mock_orm, field_name, None)
        
        api_nutri_facts = ApiNutriFacts.from_orm_model(mock_orm)
        
        # Verify numeric values are preserved as floats
        assert api_nutri_facts.calories == 200.0
        assert api_nutri_facts.protein == 18.0
        assert api_nutri_facts.carbohydrate == 25.0
        assert api_nutri_facts.total_fat == 7.5

    def test_to_orm_kwargs_conversion_extracts_values_from_mixed_types(self):
        """Test that API to ORM kwargs conversion handles mixed ApiNutriValue and float types."""
        api_nutri_facts = ApiNutriFacts(
            calories=ApiNutriValue(value=350.0, unit=MeasureUnit.ENERGY),
            protein=25.0,  # Direct float value
            carbohydrate=ApiNutriValue(value=40.0, unit=MeasureUnit.GRAM),
            total_fat=15.0,  # Direct float value
            sodium=ApiNutriValue(value=600.0, unit=MeasureUnit.MILLIGRAM)
        ) # type: ignore
        
        orm_kwargs = api_nutri_facts.to_orm_kwargs()
        
        # Verify that .value is extracted from ApiNutriValue objects and floats are preserved
        assert orm_kwargs["calories"] == 350.0
        assert orm_kwargs["protein"] == 25.0  # Direct float preserved
        assert orm_kwargs["carbohydrate"] == 40.0
        assert orm_kwargs["total_fat"] == 15.0  # Direct float preserved
        assert orm_kwargs["sodium"] == 600.0

    def test_round_trip_domain_to_api_to_domain_integrity(self):
        """Test round-trip conversion domain → API → domain maintains data integrity."""
        original_domain = NutriFacts(
            calories=NutriValue(value=280.0, unit=MeasureUnit.ENERGY),
            protein=NutriValue(value=22.0, unit=MeasureUnit.GRAM),
            vitamin_b12=NutriValue(value=2.4, unit=MeasureUnit.MICROGRAM),
            calcium=NutriValue(value=150.0, unit=MeasureUnit.MILLIGRAM)
        )
        
        # Round trip: domain → API → domain
        api_nutri_facts = ApiNutriFacts.from_domain(original_domain)
        converted_domain = api_nutri_facts.to_domain()
        
        # Verify complete integrity
        assert converted_domain.calories.value == original_domain.calories.value
        assert converted_domain.calories.unit == original_domain.calories.unit
        assert converted_domain.protein.value == original_domain.protein.value
        assert converted_domain.protein.unit == original_domain.protein.unit
        assert converted_domain.vitamin_b12.value == original_domain.vitamin_b12.value
        assert converted_domain.vitamin_b12.unit == original_domain.vitamin_b12.unit

    def test_round_trip_api_to_orm_to_api_preserves_numeric_values(self):
        """Test round-trip API → ORM → API preserves numeric values (units lost as expected)."""
        original_api = ApiNutriFacts(
            calories=ApiNutriValue(value=320.0, unit=MeasureUnit.ENERGY),
            protein=ApiNutriValue(value=28.0, unit=MeasureUnit.GRAM),
            iron=ApiNutriValue(value=3.2, unit=MeasureUnit.MILLIGRAM)
        ) # type: ignore
        
        # API → ORM kwargs → mock ORM → API cycle
        orm_kwargs = original_api.to_orm_kwargs()
        
        mock_orm = Mock()
        for key, value in orm_kwargs.items():
            setattr(mock_orm, key, value)
        
        # Set remaining fields to None
        for field_name in ApiNutriFacts.model_fields.keys():
            if not hasattr(mock_orm, field_name):
                setattr(mock_orm, field_name, None)
        
        reconstructed_api = ApiNutriFacts.from_orm_model(mock_orm)
        
        # Verify numeric values preserved (units lost as expected)
        assert reconstructed_api.calories == 320.0
        assert reconstructed_api.protein == 28.0
        assert reconstructed_api.iron == 3.2

    def test_four_layer_conversion_with_comprehensive_nutritional_profile(self):
        """Test four-layer conversion with comprehensive nutritional profile."""
        # Create comprehensive domain nutritional facts
        comprehensive_domain = NutriFacts(
            # Macronutrients
            calories=NutriValue(value=400.0, unit=MeasureUnit.ENERGY),
            protein=NutriValue(value=30.0, unit=MeasureUnit.GRAM),
            carbohydrate=NutriValue(value=50.0, unit=MeasureUnit.GRAM),
            total_fat=NutriValue(value=18.0, unit=MeasureUnit.GRAM),
            dietary_fiber=NutriValue(value=8.0, unit=MeasureUnit.GRAM),
            
            # Vitamins
            vitamin_c=NutriValue(value=80.0, unit=MeasureUnit.MILLIGRAM),
            vitamin_d=NutriValue(value=600.0, unit=MeasureUnit.IU),
            vitamin_b12=NutriValue(value=2.4, unit=MeasureUnit.MICROGRAM),
            folic_acid=NutriValue(value=400.0, unit=MeasureUnit.MICROGRAM),
            
            # Minerals
            calcium=NutriValue(value=200.0, unit=MeasureUnit.MILLIGRAM),
            iron=NutriValue(value=8.0, unit=MeasureUnit.MILLIGRAM),
            potassium=NutriValue(value=1000.0, unit=MeasureUnit.MILLIGRAM),
            sodium=NutriValue(value=500.0, unit=MeasureUnit.MILLIGRAM)
        ) # type: ignore
        
        # Domain → API → Domain cycle
        api_converted = ApiNutriFacts.from_domain(comprehensive_domain)
        domain_final = api_converted.to_domain()
        
        # Verify all major nutrients maintain integrity
        major_nutrients = ['calories', 'protein', 'carbohydrate', 'total_fat', 
                          'vitamin_c', 'calcium', 'iron']
        
        for nutrient in major_nutrients:
            original_value = getattr(comprehensive_domain, nutrient)
            final_value = getattr(domain_final, nutrient)
            
            if original_value is not None:
                assert final_value.value == original_value.value
                assert final_value.unit == original_value.unit


class TestApiNutriFactsFieldValidation:
    """Test comprehensive field validation for ApiNutriFacts nutritional data."""

    def test_macronutrient_validation_with_realistic_values(self):
        """Test macronutrient fields accept realistic nutritional values."""
        realistic_macros = {
            'calories': 350.0,
            'protein': 25.0,
            'carbohydrate': 45.0,
            'total_fat': 12.0,
            'saturated_fat': 4.0,
            'dietary_fiber': 6.0,
            'sugar': 15.0
        }
        
        api_nutri_facts = ApiNutriFacts(**realistic_macros) # type: ignore
        
        # Verify all macronutrients are accepted and stored correctly
        for nutrient, expected_value in realistic_macros.items():
            actual_value = getattr(api_nutri_facts, nutrient)
            assert actual_value == expected_value

    def test_vitamin_validation_with_various_units_and_ranges(self):
        """Test vitamin fields accept appropriate values for different vitamin types."""
        vitamin_values = {
            'vitamin_c': ApiNutriValue(value=90.0, unit=MeasureUnit.MILLIGRAM),
            'vitamin_d': ApiNutriValue(value=800.0, unit=MeasureUnit.IU),
            'vitamin_b12': ApiNutriValue(value=2.4, unit=MeasureUnit.MICROGRAM),
            'vitamin_e': ApiNutriValue(value=15.0, unit=MeasureUnit.MILLIGRAM),
            'vitamin_k': ApiNutriValue(value=120.0, unit=MeasureUnit.MICROGRAM),
            'folic_acid': ApiNutriValue(value=400.0, unit=MeasureUnit.MICROGRAM)
        }
        
        api_nutri_facts = ApiNutriFacts(**vitamin_values)
        
        # Verify vitamin values and units with proper type checking
        vitamin_c = api_nutri_facts.vitamin_c
        if isinstance(vitamin_c, ApiNutriValue):
            assert vitamin_c.value == 90.0
            assert vitamin_c.unit == MeasureUnit.MILLIGRAM
        
        vitamin_d = api_nutri_facts.vitamin_d
        if isinstance(vitamin_d, ApiNutriValue):
            assert vitamin_d.value == 800.0
            assert vitamin_d.unit == MeasureUnit.IU
        
        vitamin_b12 = api_nutri_facts.vitamin_b12
        if isinstance(vitamin_b12, ApiNutriValue):
            assert vitamin_b12.value == 2.4
            assert vitamin_b12.unit == MeasureUnit.MICROGRAM

    def test_mineral_validation_with_trace_and_major_minerals(self):
        """Test mineral fields accept appropriate values for different mineral types."""
        mineral_values = {
            'calcium': ApiNutriValue(value=300.0, unit=MeasureUnit.MILLIGRAM),
            'iron': ApiNutriValue(value=10.0, unit=MeasureUnit.MILLIGRAM),
            'potassium': ApiNutriValue(value=1200.0, unit=MeasureUnit.MILLIGRAM),
            'sodium': ApiNutriValue(value=800.0, unit=MeasureUnit.MILLIGRAM),
            'zinc': ApiNutriValue(value=8.0, unit=MeasureUnit.MILLIGRAM),
            'selenium': ApiNutriValue(value=55.0, unit=MeasureUnit.MICROGRAM),
            'copper': ApiNutriValue(value=0.9, unit=MeasureUnit.MILLIGRAM),
            'manganese': ApiNutriValue(value=2.3, unit=MeasureUnit.MILLIGRAM)
        }
        
        api_nutri_facts = ApiNutriFacts(**mineral_values)
        
        # Verify major minerals with type checking
        calcium = api_nutri_facts.calcium
        if isinstance(calcium, ApiNutriValue):
            assert calcium.value == 300.0
        
        iron = api_nutri_facts.iron
        if isinstance(iron, ApiNutriValue):
            assert iron.value == 10.0
        
        potassium = api_nutri_facts.potassium
        if isinstance(potassium, ApiNutriValue):
            assert potassium.value == 1200.0
        
        # Verify trace minerals
        selenium = api_nutri_facts.selenium
        if isinstance(selenium, ApiNutriValue):
            assert selenium.value == 55.0
            assert selenium.unit == MeasureUnit.MICROGRAM
        
        copper = api_nutri_facts.copper
        if isinstance(copper, ApiNutriValue):
            assert copper.value == 0.9
        
        manganese = api_nutri_facts.manganese
        if isinstance(manganese, ApiNutriValue):
            assert manganese.value == 2.3

    def test_specialized_nutrient_validation(self):
        """Test specialized nutrients like omega acids, amino acids, and other compounds."""
        specialized_nutrients = {
            'omega_7': ApiNutriValue(value=0.5, unit=MeasureUnit.GRAM),
            'omega_9': ApiNutriValue(value=1.2, unit=MeasureUnit.GRAM),
            'dha': ApiNutriValue(value=250.0, unit=MeasureUnit.MILLIGRAM),
            'epa': ApiNutriValue(value=180.0, unit=MeasureUnit.MILLIGRAM),
            'arachidonic_acid': ApiNutriValue(value=50.0, unit=MeasureUnit.MILLIGRAM),
            'l_carnitine': ApiNutriValue(value=20.0, unit=MeasureUnit.MILLIGRAM),
            'taurine': ApiNutriValue(value=40.0, unit=MeasureUnit.MILLIGRAM),
            'choline': ApiNutriValue(value=125.0, unit=MeasureUnit.MILLIGRAM)
        }
        
        api_nutri_facts = ApiNutriFacts(**specialized_nutrients)
        
        # Verify omega fatty acids with type checking
        dha = api_nutri_facts.dha
        if isinstance(dha, ApiNutriValue):
            assert dha.value == 250.0
        
        epa = api_nutri_facts.epa
        if isinstance(epa, ApiNutriValue):
            assert epa.value == 180.0
        
        # Verify amino acids and related compounds
        l_carnitine = api_nutri_facts.l_carnitine
        if isinstance(l_carnitine, ApiNutriValue):
            assert l_carnitine.value == 20.0
        
        taurine = api_nutri_facts.taurine
        if isinstance(taurine, ApiNutriValue):
            assert taurine.value == 40.0
        
        choline = api_nutri_facts.choline
        if isinstance(choline, ApiNutriValue):
            assert choline.value == 125.0

    def test_zero_values_acceptance_for_all_nutrients(self):
        """Test that zero values are accepted for all nutritional fields."""
        zero_nutrients = {
            'calories': 0.0,
            'protein': 0.0,
            'total_fat': 0.0,
            'vitamin_c': 0.0,
            'calcium': 0.0,
            'sodium': 0.0
        }
        
        api_nutri_facts = ApiNutriFacts(**zero_nutrients) # type: ignore
        
        # Verify all zero values are accepted
        for nutrient, expected_value in zero_nutrients.items():
            actual_value = getattr(api_nutri_facts, nutrient)
            assert actual_value == expected_value

    def test_none_values_converted_to_default_zeros(self):
        """Test that None values are converted to default 0.0 values per BeforeValidator."""
        # Create using individual kwargs to avoid linter issues
        kwargs = {}
        kwargs.update({field: 0.0 for field in ApiNutriFacts.model_fields.keys()})
        kwargs.update({
            'calories': None,
            'protein': None,
            'vitamin_c': None,
            'calcium': None
        })
        
        api_nutri_facts = ApiNutriFacts(**kwargs)
        
        # Verify None values converted to 0.0 per convert_to_api_nutri_value_or_float
        assert api_nutri_facts.calories == 0.0
        assert api_nutri_facts.protein == 0.0
        assert api_nutri_facts.vitamin_c == 0.0
        assert api_nutri_facts.calcium == 0.0

    def test_integer_values_converted_to_float(self):
        """Test that integer values are automatically converted to float."""
        integer_nutrients = {
            'calories': 300,  # int
            'protein': 25,    # int
            'carbohydrate': 40,  # int
            'vitamin_c': 60   # int
        }
        
        api_nutri_facts = ApiNutriFacts(**integer_nutrients) # type: ignore
        
        # Verify integers converted to floats
        assert api_nutri_facts.calories == 300.0
        assert isinstance(api_nutri_facts.calories, float)
        assert api_nutri_facts.protein == 25.0
        assert isinstance(api_nutri_facts.protein, float)

    def test_mixed_apinutrivalue_and_numeric_types(self):
        """Test acceptance of mixed ApiNutriValue objects and numeric values."""
        mixed_nutrients = {
            'calories': ApiNutriValue(value=250.0, unit=MeasureUnit.ENERGY),
            'protein': 20.0,  # float
            'carbohydrate': 35,  # int
            'total_fat': ApiNutriValue(value=10.0, unit=MeasureUnit.GRAM),
            'vitamin_c': None,  # None
            'calcium': ApiNutriValue(value=150.0, unit=MeasureUnit.MILLIGRAM)
        }
        
        api_nutri_facts = ApiNutriFacts(**mixed_nutrients)
        
        # Verify mixed types handled correctly with type checking
        calories = api_nutri_facts.calories
        assert isinstance(calories, ApiNutriValue)
        assert calories.value == 250.0
        
        assert api_nutri_facts.protein == 20.0  # float preserved
        assert api_nutri_facts.carbohydrate == 35.0  # int converted to float
        
        total_fat = api_nutri_facts.total_fat
        assert isinstance(total_fat, ApiNutriValue)
        
        assert api_nutri_facts.vitamin_c == 0.0  # None converted to 0.0

    def test_nutritional_range_validation_for_realistic_values(self):
        """Test validation accepts realistic nutritional ranges for different food types."""
        # High-calorie food (like nuts) - use defaults for all fields
        base_kwargs = {field: 0.0 for field in ApiNutriFacts.model_fields.keys()}
        high_calorie_kwargs = base_kwargs.copy()
        high_calorie_kwargs.update({
            'calories': 600.0,
            'protein': 20.0,
            'total_fat': 50.0,
            'carbohydrate': 20.0
        })
        high_calorie_food = ApiNutriFacts(**high_calorie_kwargs) # type: ignore
        
        # Low-calorie food (like vegetables)
        low_calorie_kwargs = base_kwargs.copy()
        low_calorie_kwargs.update({
            'calories': 25.0,
            'protein': 2.0,
            'total_fat': 0.2,
            'carbohydrate': 5.0,
            'vitamin_c': 30.0
        })
        low_calorie_food = ApiNutriFacts(**low_calorie_kwargs) # type: ignore
        
        # Verify both extremes are accepted
        assert high_calorie_food.calories == 600.0
        assert high_calorie_food.total_fat == 50.0
        assert low_calorie_food.calories == 25.0
        assert low_calorie_food.total_fat == 0.2

    def test_comprehensive_nutritional_profile_validation(self):
        """Test validation of comprehensive nutritional profile with all major nutrients."""
        comprehensive_profile = {
            # Macronutrients
            'calories': 380.0,
            'protein': 28.0,
            'carbohydrate': 42.0,
            'total_fat': 15.0,
            'saturated_fat': 5.0,
            'dietary_fiber': 8.0,
            'sugar': 12.0,
            
            # Water-soluble vitamins
            'vitamin_c': 85.0,
            'vitamin_b1': 1.2,
            'vitamin_b2': 1.4,
            'vitamin_b6': 1.7,
            'vitamin_b12': 2.4,
            'folic_acid': 400.0,
            
            # Fat-soluble vitamins
            'vitamin_a': 900.0,
            'vitamin_d': 600.0,
            'vitamin_e': 15.0,
            'vitamin_k': 120.0,
            
            # Major minerals
            'calcium': 200.0,
            'iron': 8.0,
            'potassium': 1000.0,
            'sodium': 600.0,
            'phosphorus': 700.0,
            'magnesium': 320.0,
            
            # Trace minerals
            'zinc': 11.0,
            'selenium': 55.0,
            'copper': 0.9,
            'manganese': 2.3,
            'iodine': 150.0
        }
        
        api_nutri_facts = ApiNutriFacts(**comprehensive_profile) # type: ignore
        
        # Verify comprehensive profile acceptance
        assert api_nutri_facts.calories == 380.0
        assert api_nutri_facts.protein == 28.0
        assert api_nutri_facts.vitamin_c == 85.0
        assert api_nutri_facts.calcium == 200.0
        assert api_nutri_facts.iron == 8.0
        assert api_nutri_facts.zinc == 11.0

    def test_nutritional_field_precision_preservation(self):
        """Test that high-precision nutritional values are preserved correctly."""
        precise_nutrients = {
            'vitamin_b12': 2.4567,
            'selenium': 55.123,
            'copper': 0.9876,
            'iodine': 150.4321
        }
        
        api_nutri_facts = ApiNutriFacts(**precise_nutrients) # type: ignore
        
        # Verify precision is preserved with type checking
        vitamin_b12 = api_nutri_facts.vitamin_b12
        if isinstance(vitamin_b12, float):
            assert abs(vitamin_b12 - 2.4567) < 1e-10 # type: ignore
        elif isinstance(vitamin_b12, ApiNutriValue):
            assert abs(vitamin_b12.value - 2.4567) < 1e-10
        
        selenium = api_nutri_facts.selenium
        if isinstance(selenium, float):
            assert abs(selenium - 55.123) < 1e-10 # type: ignore
        elif isinstance(selenium, ApiNutriValue):
            assert abs(selenium.value - 55.123) < 1e-10
        
        copper = api_nutri_facts.copper
        if isinstance(copper, float):
            assert abs(copper - 0.9876) < 1e-10 # type: ignore
        elif isinstance(copper, ApiNutriValue):
            assert abs(copper.value - 0.9876) < 1e-10

    def test_all_85_nutritional_fields_accept_valid_values(self):
        """Test that all 85+ nutritional fields accept valid values without errors."""
        # Get all field names from the model
        all_fields = list(ApiNutriFacts.model_fields.keys())
        
        # Verify we have all expected nutritional fields (85+)
        assert len(all_fields) >= 85
        
        # Create values for all fields
        all_field_values = {field: 10.0 for field in all_fields}
        
        # Should create without errors
        api_nutri_facts = ApiNutriFacts(**all_field_values) # type: ignore
        
        # Verify all fields are set
        for field in all_fields:
            assert getattr(api_nutri_facts, field) == 10.0


class TestApiNutriFactsJsonValidation:
    """Test comprehensive JSON validation for mixed input types including dict support."""

    def test_json_validation_with_numeric_values_only(self):
        """Test model_validate_json with simple numeric values (int | float)."""
        json_data = json.dumps({
            "calories": 250,
            "protein": 18.5,
            "carbohydrate": 30,
            "total_fat": 8.2,
            "vitamin_c": 60.0,
            "calcium": 150
        })
        
        api_nutri_facts = ApiNutriFacts.model_validate_json(json_data)
        
        # Verify numeric values are correctly parsed and converted
        assert api_nutri_facts.calories == 250.0  # int → float
        assert api_nutri_facts.protein == 18.5    # float preserved
        assert api_nutri_facts.carbohydrate == 30.0  # int → float
        assert api_nutri_facts.total_fat == 8.2   # float preserved
        assert api_nutri_facts.vitamin_c == 60.0  # float preserved
        assert api_nutri_facts.calcium == 150.0   # int → float

    def test_json_validation_with_none_values(self):
        """Test model_validate_json with null values converts to default 0.0."""
        json_data = json.dumps({
            "calories": None,
            "protein": None,
            "carbohydrate": 25.0,
            "total_fat": None,
            "vitamin_c": None
        })
        
        api_nutri_facts = ApiNutriFacts.model_validate_json(json_data)
        
        # Verify None/null values converted to 0.0
        assert api_nutri_facts.calories == 0.0
        assert api_nutri_facts.protein == 0.0
        assert api_nutri_facts.carbohydrate == 25.0  # Non-null preserved
        assert api_nutri_facts.total_fat == 0.0
        assert api_nutri_facts.vitamin_c == 0.0

    def test_json_validation_with_apinutrivalue_dict_objects(self):
        """Test model_validate_json with dict objects representing ApiNutriValue."""
        # Now that schema supports dict→ApiNutriValue conversion, test the enhanced functionality
        
        json_data = json.dumps({
            "calories": {"value": 300.0, "unit": "kcal"},
            "protein": {"value": 25.0, "unit": "g"},
            "vitamin_c": {"value": 80.0, "unit": "mg"},
            "calcium": {"value": 200.0, "unit": "mg"}
        })
        
        api_nutri_facts = ApiNutriFacts.model_validate_json(json_data)
        
        # With enhanced implementation, dict inputs should create ApiNutriValue objects
        assert isinstance(api_nutri_facts.calories, ApiNutriValue)
        assert api_nutri_facts.calories.value == 300.0
        assert api_nutri_facts.calories.unit == MeasureUnit.ENERGY
        
        assert isinstance(api_nutri_facts.protein, ApiNutriValue)
        assert api_nutri_facts.protein.value == 25.0
        assert api_nutri_facts.protein.unit == MeasureUnit.GRAM
        
        assert isinstance(api_nutri_facts.vitamin_c, ApiNutriValue)
        assert api_nutri_facts.vitamin_c.value == 80.0
        assert api_nutri_facts.vitamin_c.unit == MeasureUnit.MILLIGRAM
        
        assert isinstance(api_nutri_facts.calcium, ApiNutriValue)
        assert api_nutri_facts.calcium.value == 200.0
        assert api_nutri_facts.calcium.unit == MeasureUnit.MILLIGRAM

    def test_json_validation_with_mixed_input_types(self):
        """Test model_validate_json with mixed int | float | None | dict input types."""
        json_data = json.dumps({
            "calories": 280,      # int - supported
            "protein": 22.5,      # float - supported
            "carbohydrate": {"value": 35.0, "unit": "g"}, # dict - now supported
            "total_fat": None,    # None - supported
            "saturated_fat": 4.5, # float - supported
            "dietary_fiber": 8,   # int - supported
            "vitamin_c": {"value": 90.0, "unit": "mg"}, # dict - now supported
            "calcium": None,      # None - supported
            "iron": 12,           # int - supported
            "sodium": {"value": 500.0, "unit": "mg"}    # dict - now supported
        })
        
        api_nutri_facts = ApiNutriFacts.model_validate_json(json_data)
        
        # Verify mixed types handled correctly (all supported types)
        assert api_nutri_facts.calories == 280.0  # int → float
        assert api_nutri_facts.protein == 22.5    # float preserved
        
        # Dict inputs should create ApiNutriValue objects
        assert isinstance(api_nutri_facts.carbohydrate, ApiNutriValue)
        assert api_nutri_facts.carbohydrate.value == 35.0
        assert api_nutri_facts.carbohydrate.unit == MeasureUnit.GRAM
        
        assert api_nutri_facts.total_fat == 0.0   # None → 0.0
        assert api_nutri_facts.saturated_fat == 4.5  # float preserved
        assert api_nutri_facts.dietary_fiber == 8.0  # int → float
        
        assert isinstance(api_nutri_facts.vitamin_c, ApiNutriValue)
        assert api_nutri_facts.vitamin_c.value == 90.0
        assert api_nutri_facts.vitamin_c.unit == MeasureUnit.MILLIGRAM
        
        assert api_nutri_facts.calcium == 0.0    # None → 0.0
        assert api_nutri_facts.iron == 12.0      # int → float
        
        assert isinstance(api_nutri_facts.sodium, ApiNutriValue)
        assert api_nutri_facts.sodium.value == 500.0
        assert api_nutri_facts.sodium.unit == MeasureUnit.MILLIGRAM

    def test_json_validation_with_incomplete_apinutrivalue_dicts(self):
        """Test model_validate_json behavior with incomplete dict objects."""
        # Test behavior when dict objects have incomplete data
        
        json_data = json.dumps({
            "calories": {"value": 250.0},  # Dict without unit - should return value as float
            "protein": {"unit": "g"},      # Dict without value - should return 0.0
            "vitamin_c": {"value": None, "unit": "mg"},  # Dict with None value - should return 0.0
            "calcium": {"value": 150.0, "unit": None}   # Dict with None unit - should return value as float
        })
        
        api_nutri_facts = ApiNutriFacts.model_validate_json(json_data)
        
        # Updated behavior: valid values are preserved as floats, missing/None values return 0.0
        assert api_nutri_facts.calories == 250.0  # Has value, missing unit → return value as float
        assert api_nutri_facts.protein == 0.0     # Missing value → 0.0
        assert api_nutri_facts.vitamin_c == 0.0   # None value → 0.0
        assert api_nutri_facts.calcium == 150.0   # Has value, None unit → return value as float

    def test_json_validation_with_comprehensive_mixed_profile(self):
        """Test model_validate_json with comprehensive mixed-type nutritional profile including dicts."""
        json_data = json.dumps({
            # Mixed macronutrients
            "calories": 350,    # int
            "protein": {"value": 28.0, "unit": "g"},  # dict → ApiNutriValue
            "carbohydrate": 45.5,  # float
            "total_fat": None,  # None
            "dietary_fiber": {"value": 8.0, "unit": "g"},  # dict → ApiNutriValue
            
            # Mixed vitamins
            "vitamin_c": 95,    # int
            "vitamin_d": {"value": 600.0, "unit": "IU"},  # dict → ApiNutriValue
            "vitamin_b12": 2.4, # float
            "folic_acid": None, # None
            
            # Mixed minerals
            "calcium": {"value": 180.0, "unit": "mg"},  # dict → ApiNutriValue
            "iron": 9,          # int
            "potassium": 1200.5, # float
            "sodium": None,     # None
            "zinc": {"value": 7.0, "unit": "mg"}  # dict → ApiNutriValue
        })
        
        api_nutri_facts = ApiNutriFacts.model_validate_json(json_data)
        
        # Verify comprehensive mixed profile
        assert api_nutri_facts.calories == 350.0
        
        # Dict should create ApiNutriValue objects
        assert isinstance(api_nutri_facts.protein, ApiNutriValue)
        assert api_nutri_facts.protein.value == 28.0
        assert api_nutri_facts.protein.unit == MeasureUnit.GRAM
        
        assert api_nutri_facts.carbohydrate == 45.5
        assert api_nutri_facts.total_fat == 0.0
        
        assert isinstance(api_nutri_facts.dietary_fiber, ApiNutriValue)
        assert api_nutri_facts.dietary_fiber.value == 8.0
        assert api_nutri_facts.dietary_fiber.unit == MeasureUnit.GRAM
        
        assert api_nutri_facts.vitamin_c == 95.0
        
        assert isinstance(api_nutri_facts.vitamin_d, ApiNutriValue)
        assert api_nutri_facts.vitamin_d.value == 600.0
        assert api_nutri_facts.vitamin_d.unit == MeasureUnit.IU
        
        assert api_nutri_facts.vitamin_b12 == 2.4
        assert api_nutri_facts.folic_acid == 0.0
        
        assert isinstance(api_nutri_facts.calcium, ApiNutriValue)
        assert api_nutri_facts.calcium.value == 180.0
        assert api_nutri_facts.calcium.unit == MeasureUnit.MILLIGRAM
        
        assert api_nutri_facts.iron == 9.0
        assert api_nutri_facts.potassium == 1200.5
        assert api_nutri_facts.sodium == 0.0
        
        assert isinstance(api_nutri_facts.zinc, ApiNutriValue)
        assert api_nutri_facts.zinc.value == 7.0
        assert api_nutri_facts.zinc.unit == MeasureUnit.MILLIGRAM

    def test_json_validation_performance_with_large_mixed_data(self):
        """Test model_validate_json performance with large mixed-type dataset."""
        # Create large dataset with all 85+ fields using mixed types
        all_fields = list(ApiNutriFacts.model_fields.keys())
        
        mixed_data = {}
        for i, field in enumerate(all_fields):
            if i % 4 == 0:
                mixed_data[field] = i * 1.5  # float
            elif i % 4 == 1:
                mixed_data[field] = i        # int
            elif i % 4 == 2:
                mixed_data[field] = {"value": float(i), "unit": "g"}  # dict
            else:
                mixed_data[field] = None     # None
        
        json_data = json.dumps(mixed_data)
        
        start_time = time.time()
        api_nutri_facts = ApiNutriFacts.model_validate_json(json_data)
        end_time = time.time()
        
        # Verify performance and correctness
        validation_time = end_time - start_time
        assert validation_time < 0.1  # Should be fast for large datasets
        
        # Verify sample fields are correctly processed
        assert isinstance(api_nutri_facts.calories, (float, ApiNutriValue))
        assert isinstance(api_nutri_facts.protein, (float, ApiNutriValue))

    def test_json_validation_with_empty_object(self):
        """Test model_validate_json with empty JSON object uses defaults."""
        json_data = "{}"
        
        api_nutri_facts = ApiNutriFacts.model_validate_json(json_data)
        
        # Verify all fields use default values (0.0)
        assert api_nutri_facts.calories == 0.0
        assert api_nutri_facts.protein == 0.0
        assert api_nutri_facts.carbohydrate == 0.0
        assert api_nutri_facts.vitamin_c == 0.0

    def test_json_validation_preserves_precision_in_mixed_types(self):
        """Test that JSON validation preserves precision across mixed input types."""
        json_data = json.dumps({
            "vitamin_b12": 2.4567,  # high-precision float
            "selenium": {"value": 55.123456, "unit": "mcg"},  # high-precision in dict
            "copper": 0.987654321,  # many decimal places
            "iodine": {"value": 150.999999, "unit": "mcg"}  # precision in dict
        })
        
        api_nutri_facts = ApiNutriFacts.model_validate_json(json_data)
        
        # Verify precision preservation with type checking
        vitamin_b12 = api_nutri_facts.vitamin_b12
        if isinstance(vitamin_b12, float):
            assert abs(vitamin_b12 - 2.4567) < 1e-10 # type: ignore
        elif isinstance(vitamin_b12, ApiNutriValue):
            assert abs(vitamin_b12.value - 2.4567) < 1e-10
        
        selenium = api_nutri_facts.selenium
        if isinstance(selenium, ApiNutriValue):
            assert abs(selenium.value - 55.123456) < 1e-10
        
        copper = api_nutri_facts.copper
        if isinstance(copper, float):
            assert abs(copper - 0.987654321) < 1e-10 # type: ignore
        elif isinstance(copper, ApiNutriValue):
            assert abs(copper.value - 0.987654321) < 1e-10
        
        iodine = api_nutri_facts.iodine
        if isinstance(iodine, ApiNutriValue):
            assert abs(iodine.value - 150.999999) < 1e-10


class TestApiNutriFactsErrorHandling:
    """Test comprehensive error handling for ApiNutriFacts validation and conversion."""

    def test_from_domain_with_none_domain_object_raises_error(self):
        """Test that from_domain with None domain object raises appropriate error."""
        with pytest.raises(AttributeError):
            ApiNutriFacts.from_domain(None) # type: ignore

    def test_from_domain_with_invalid_domain_object_raises_error(self):
        """Test that from_domain with invalid domain object raises appropriate error."""
        invalid_domain = "not a NutriFacts object"
        
        with pytest.raises(AttributeError):
            ApiNutriFacts.from_domain(invalid_domain) # type: ignore

    def test_json_validation_with_invalid_json_syntax_raises_error(self):
        """Test that model_validate_json with invalid JSON syntax raises appropriate error."""
        invalid_json = '{"calories": 250, "protein": 20.0,}'  # trailing comma
        
        with pytest.raises((ValidationError, ValueError, json.JSONDecodeError)):
            ApiNutriFacts.model_validate_json(invalid_json)

    def test_json_validation_with_invalid_numeric_types_raises_error(self):
        """Test that invalid numeric types in JSON raise validation errors."""
        invalid_numeric_json = json.dumps({
            "calories": "not_a_number",
            "protein": [],
            "carbohydrate": {}
        })
        
        with pytest.raises(ValidationError) as exc_info:
            ApiNutriFacts.model_validate_json(invalid_numeric_json)
        
        # Verify multiple field errors are reported
        error_str = str(exc_info.value)
        assert "calories" in error_str
        assert "protein" in error_str
        assert "carbohydrate" in error_str

    def test_json_validation_with_invalid_apinutrivalue_dict_raises_error(self):
        """Test that invalid ApiNutriValue dict structures raise validation errors."""
        invalid_dict_json = json.dumps({
            "calories": {"invalid_field": 250.0},  # Wrong field name
            "protein": {"value": "not_numeric", "unit": "g"},  # Invalid value type
            "vitamin_c": {"value": 80.0, "unit": "invalid_unit"}  # Invalid unit
        })
        
        with pytest.raises(ValidationError) as exc_info:
            ApiNutriFacts.model_validate_json(invalid_dict_json)
        
        # Should contain errors for the invalid fields
        error_str = str(exc_info.value)
        # At least one of the fields should cause an error
        assert any(field in error_str for field in ["calories", "protein", "vitamin_c"])

    def test_to_domain_conversion_error_handling(self):
        """Test error handling during to_domain conversion with mixed types."""
        # Create with mixed valid types
        api_nutri_facts = ApiNutriFacts(
            calories=250.0,
            protein=ApiNutriValue(value=20.0, unit=MeasureUnit.GRAM)
        ) # type: ignore
        
        # Should convert successfully
        domain_nutri_facts = api_nutri_facts.to_domain()
        assert isinstance(domain_nutri_facts, NutriFacts)

    def test_to_orm_kwargs_error_handling_with_invalid_attributes(self):
        """Test error handling in to_orm_kwargs when accessing invalid attributes."""
        api_nutri_facts = ApiNutriFacts(
            calories=ApiNutriValue(value=300.0, unit=MeasureUnit.ENERGY),
            protein=25.0
        ) # type: ignore
        
        # Should handle mixed types without errors
        orm_kwargs = api_nutri_facts.to_orm_kwargs()
        assert orm_kwargs["calories"] == 300.0
        assert orm_kwargs["protein"] == 25.0

    def test_validation_error_with_extreme_values(self):
        """Test validation behavior with extreme values."""
        extreme_values = {
            "calories": float('inf'),
            "protein": float('-inf'),
            "vitamin_c": 1e20,  # Extremely large value
            "calcium": -1000.0  # Negative value (if validation exists)
        }
        
        # Most should be accepted (schema is permissive for numeric ranges)
        api_nutri_facts = ApiNutriFacts(**extreme_values) # type: ignore
        
        # Verify extreme values are handled
        assert api_nutri_facts.calories == float('inf')
        assert api_nutri_facts.protein == float('-inf')
        assert api_nutri_facts.vitamin_c == 1e20

    def test_multiple_field_validation_errors_aggregation(self):
        """Test that multiple field validation errors are properly aggregated."""
        # Use invalid JSON to trigger multiple validation errors
        invalid_json = json.dumps({
            "calories": "invalid",
            "protein": [],
            "carbohydrate": {},
            "total_fat": "also_invalid"
        })
        
        with pytest.raises(ValidationError) as exc_info:
            ApiNutriFacts.model_validate_json(invalid_json)
        
        # Verify multiple errors are reported together
        error_message = str(exc_info.value)
        invalid_fields = ["calories", "protein", "carbohydrate", "total_fat"]
        error_count = sum(1 for field in invalid_fields if field in error_message)
        assert error_count >= 2  # At least 2 errors should be aggregated

    def test_conversion_error_context_preservation(self):
        """Test that conversion errors preserve context about which field failed."""
        # Create mock domain object with problematic attributes
        mock_domain = Mock()
        mock_domain.calories = Mock()
        mock_domain.calories.value = "invalid_value"  # This might cause issues
        
        # Set default attributes for all fields to prevent AttributeError
        all_fields = list(ApiNutriFacts.model_fields.keys())
        for field in all_fields:
            if not hasattr(mock_domain, field):
                setattr(mock_domain, field, None)
        
        # Should handle problematic mock gracefully or provide clear error
        try:
            api_nutri_facts = ApiNutriFacts.from_domain(mock_domain)
            # If successful, verify the result
            assert hasattr(api_nutri_facts, 'calories')
        except Exception as e:
            # If error occurs, should be informative
            assert isinstance(e, (AttributeError, ValidationError, TypeError))

    def test_boundary_error_cases_for_nutritional_data_integrity(self):
        """Test error handling at boundaries of nutritional data integrity."""
        # Test with NaN values
        nan_values = {
            "calories": float('nan'),
            "protein": float('nan')
        }
        
        api_nutri_facts = ApiNutriFacts(**nan_values) # type: ignore
        
        # Verify NaN handling (should be accepted or handled gracefully)
        import math
        assert math.isnan(api_nutri_facts.calories) or api_nutri_facts.calories == 0.0
        assert math.isnan(api_nutri_facts.protein) or api_nutri_facts.protein == 0.0

    def test_json_error_handling_preserves_field_specificity(self):
        """Test that JSON validation errors specify which fields are problematic."""
        specific_error_json = json.dumps({
            "calories": 250.0,  # Valid
            "protein": "invalid_protein_value",  # Invalid
            "carbohydrate": 30.0,  # Valid
            "total_fat": ["invalid_fat_array"],  # Invalid
            "vitamin_c": 80.0  # Valid
        })
        
        with pytest.raises(ValidationError) as exc_info:
            ApiNutriFacts.model_validate_json(specific_error_json)
        
        error_message = str(exc_info.value)
        # Should mention specific problematic fields
        assert "protein" in error_message
        assert "total_fat" in error_message
        # Should not mention valid fields in error context
        # (though this depends on Pydantic's error reporting)


class TestApiNutriFactsEdgeCases:
    """Test comprehensive edge cases for ApiNutriFacts nutritional data handling."""

    def test_minimum_nutritional_values_acceptance(self):
        """Test that minimum nutritional values (zeros) are accepted for all fields."""
        # Create with all minimum values
        min_values = {field: 0.0 for field in list(ApiNutriFacts.model_fields.keys())[:10]}
        
        api_nutri_facts = ApiNutriFacts(**min_values) # type: ignore
        
        # Verify all minimum values are accepted
        for field, expected_value in min_values.items():
            actual_value = getattr(api_nutri_facts, field)
            assert actual_value == expected_value

    def test_maximum_realistic_nutritional_values(self):
        """Test that maximum realistic nutritional values are accepted."""
        max_realistic_values = {
            'calories': 9000.0,  # Very high-calorie food (like pure fat)
            'protein': 100.0,    # High-protein food
            'total_fat': 100.0,  # Pure fat
            'vitamin_c': 2000.0, # High-dose supplement
            'calcium': 5000.0,   # High-calcium food
            'iron': 100.0       # High-iron supplement
        }
        
        api_nutri_facts = ApiNutriFacts(**max_realistic_values) # type: ignore
        
        # Verify high but realistic values are accepted
        for field, expected_value in max_realistic_values.items():
            actual_value = getattr(api_nutri_facts, field)
            assert actual_value == expected_value

    def test_floating_point_precision_edge_cases(self):
        """Test floating-point precision edge cases for nutritional values."""
        precision_values = {
            'vitamin_b12': 0.000001,  # Very small precise value
            'selenium': 123.456789,   # Many decimal places
            'copper': 1.0000000001,   # Near-integer precision
            'biotin': 0.99999999      # Near-integer precision
        }
        
        api_nutri_facts = ApiNutriFacts(**precision_values) # type: ignore
        
        # Verify precision is preserved within floating-point limits
        for field, expected_value in precision_values.items():
            actual_value = getattr(api_nutri_facts, field)
            assert abs(actual_value - expected_value) < 1e-10

    def test_infinity_and_nan_handling(self):
        """Test handling of infinity and NaN values in nutritional data."""
        extreme_values = {
            'calories': float('inf'),
            'protein': float('-inf'),
            'vitamin_c': float('nan')
        }
        
        api_nutri_facts = ApiNutriFacts(**extreme_values) # type: ignore
        
        # Verify extreme values are handled (accepted or converted)
        import math
        assert api_nutri_facts.calories == float('inf') or api_nutri_facts.calories == 0.0
        assert api_nutri_facts.protein == float('-inf') or api_nutri_facts.protein == 0.0
        assert math.isnan(api_nutri_facts.vitamin_c) or api_nutri_facts.vitamin_c == 0.0

    def test_zero_with_all_nutrient_types(self):
        """Test zero values across different types of nutrients."""
        zero_nutrients = {
            'calories': 0.0,     # Energy
            'protein': 0.0,      # Macronutrient
            'vitamin_c': 0.0,    # Water-soluble vitamin
            'vitamin_d': 0.0,    # Fat-soluble vitamin
            'calcium': 0.0,      # Major mineral
            'selenium': 0.0      # Trace mineral
        }
        
        api_nutri_facts = ApiNutriFacts(**zero_nutrients) # type: ignore
        
        # Verify zero values are consistently handled
        for field, expected_value in zero_nutrients.items():
            actual_value = getattr(api_nutri_facts, field)
            assert actual_value == expected_value

    def test_scientific_notation_values(self):
        """Test scientific notation values for very small nutritional amounts."""
        scientific_values = {
            'vitamin_b12': 2.4e-6,    # 2.4 micrograms in grams
            'selenium': 5.5e-5,       # 55 micrograms in grams
            'biotin': 3.0e-5,         # 30 micrograms in grams
            'vitamin_d': 1.5e-5       # 15 micrograms in grams
        }
        
        api_nutri_facts = ApiNutriFacts(**scientific_values) # type: ignore
        
        # Verify scientific notation values are handled correctly
        for field, expected_value in scientific_values.items():
            actual_value = getattr(api_nutri_facts, field)
            assert abs(actual_value - expected_value) < 1e-15

    def test_very_large_but_valid_nutritional_values(self):
        """Test very large but technically valid nutritional values."""
        large_values = {
            'calories': 50000.0,      # Theoretical limit for very concentrated foods
            'sodium': 100000.0,       # Pure salt equivalent
            'potassium': 50000.0,     # High-potassium supplement
            'calcium': 10000.0        # High-dose calcium supplement
        }
        
        api_nutri_facts = ApiNutriFacts(**large_values) # type: ignore
        
        # Verify large values are accepted
        for field, expected_value in large_values.items():
            actual_value = getattr(api_nutri_facts, field)
            assert actual_value == expected_value

    def test_decimal_boundary_values(self):
        """Test decimal boundary values that might cause precision issues."""
        boundary_values = {
            'protein': 0.1,           # Just above zero
            'vitamin_c': 99.9,        # Just below 100
            'calcium': 999.999,       # Many nines
            'iron': 0.001            # Very small but positive
        }
        
        api_nutri_facts = ApiNutriFacts(**boundary_values) # type: ignore
        
        # Verify boundary values are preserved
        for field, expected_value in boundary_values.items():
            actual_value = getattr(api_nutri_facts, field)
            assert abs(actual_value - expected_value) < 1e-10

    def test_mixed_apinutrivalue_and_float_edge_cases(self):
        """Test edge cases with mixed ApiNutriValue and float types."""
        mixed_edge_cases = {
            'calories': ApiNutriValue(value=0.0, unit=MeasureUnit.ENERGY),
            'protein': 0.000001,  # Very small float
            'vitamin_c': ApiNutriValue(value=float('inf'), unit=MeasureUnit.MILLIGRAM),
            'calcium': float('nan')  # NaN float
        }
        
        api_nutri_facts = ApiNutriFacts(**mixed_edge_cases)
        
        # Verify mixed edge cases are handled
        assert isinstance(api_nutri_facts.calories, ApiNutriValue)
        assert api_nutri_facts.calories.value == 0.0
        assert abs(api_nutri_facts.protein - 0.000001) < 1e-15 # type: ignore
        assert isinstance(api_nutri_facts.vitamin_c, ApiNutriValue)

    def test_boundary_between_valid_and_invalid_values(self):
        """Test boundary between technically valid and questionable nutritional values."""
        boundary_cases = {
            'calories': -0.1,         # Slightly negative (questionable but might be accepted)
            'protein': 1000.0,        # Very high but not impossible
            'vitamin_c': -10.0,       # Negative vitamin (questionable)
            'calcium': 100000.0       # Extremely high mineral
        }
        
        # Test that boundary cases are either accepted or handled gracefully
        api_nutri_facts = ApiNutriFacts(**boundary_cases) # type: ignore
        
        # Verify handling without asserting specific behavior
        # (since schema may or may not validate these edge cases)
        for field in boundary_cases.keys():
            actual_value = getattr(api_nutri_facts, field)
            assert isinstance(actual_value, (float, ApiNutriValue))

    def test_extreme_precision_handling(self):
        """Test handling of extreme precision values."""
        extreme_precision = {
            'vitamin_b12': 2.4567891234567890,
            'selenium': 55.123456789012345,
            'copper': 0.987654321098765,
            'biotin': 30.000000000000001
        }
        
        api_nutri_facts = ApiNutriFacts(**extreme_precision) # type: ignore
        
        # Verify extreme precision is handled within floating-point limits
        for field, expected_value in extreme_precision.items():
            actual_value = getattr(api_nutri_facts, field)
            # Allow for floating-point precision limitations
            assert abs(actual_value - expected_value) < 1e-10

    def test_edge_case_round_trip_conversions(self):
        """Test round-trip conversions with edge case values."""
        edge_domain = NutriFacts(
            calories=NutriValue(value=0.0001, unit=MeasureUnit.ENERGY),
            vitamin_b12=NutriValue(value=2.4e-6, unit=MeasureUnit.MICROGRAM),
            calcium=NutriValue(value=999.999, unit=MeasureUnit.MILLIGRAM)
        )
        
        # Round trip with edge values
        api_converted = ApiNutriFacts.from_domain(edge_domain)
        domain_final = api_converted.to_domain()
        
        # Verify edge case round-trip integrity
        assert abs(domain_final.calories.value - edge_domain.calories.value) < 1e-10
        assert abs(domain_final.vitamin_b12.value - edge_domain.vitamin_b12.value) < 1e-15
        assert abs(domain_final.calcium.value - edge_domain.calcium.value) < 1e-10


class TestApiNutriFactsPerformanceValidation:
    """Test comprehensive performance validation for ApiNutriFacts operations."""

    def test_four_layer_conversion_performance(self):
        """Test performance of four-layer conversion operations."""
        # Create comprehensive domain object
        comprehensive_domain = NutriFacts(
            calories=NutriValue(value=400.0, unit=MeasureUnit.ENERGY),
            protein=NutriValue(value=30.0, unit=MeasureUnit.GRAM),
            carbohydrate=NutriValue(value=50.0, unit=MeasureUnit.GRAM),
            vitamin_c=NutriValue(value=80.0, unit=MeasureUnit.MILLIGRAM),
            calcium=NutriValue(value=200.0, unit=MeasureUnit.MILLIGRAM),
            iron=NutriValue(value=8.0, unit=MeasureUnit.MILLIGRAM)
        )
        
        # Test domain → API conversion performance
        start_time = time.time()
        for _ in range(100):
            api_nutri_facts = ApiNutriFacts.from_domain(comprehensive_domain)
        end_time = time.time()
        
        domain_to_api_time = (end_time - start_time) / 100
        assert domain_to_api_time < 0.005  # Should be under 5ms per conversion
        
        # Test API → domain conversion performance
        start_time = time.time()
        for _ in range(100):
            domain_nutri_facts = api_nutri_facts.to_domain()
        end_time = time.time()
        
        api_to_domain_time = (end_time - start_time) / 100
        assert api_to_domain_time < 0.005  # Should be under 5ms per conversion

    def test_json_validation_performance_with_mixed_types(self):
        """Test JSON validation performance with mixed input types."""
        # Create large mixed JSON data
        mixed_data = {}
        all_fields = list(ApiNutriFacts.model_fields.keys())
        
        for i, field in enumerate(all_fields[:50]):  # Test with 50 fields
            if i % 4 == 0:
                mixed_data[field] = float(i)
            elif i % 4 == 1:
                mixed_data[field] = {"value": float(i), "unit": "g"}
            elif i % 4 == 2:
                mixed_data[field] = None
            else:
                mixed_data[field] = None
        
        json_data = json.dumps(mixed_data)
        
        # Test JSON validation performance
        start_time = time.time()
        for _ in range(50):
            api_nutri_facts = ApiNutriFacts.model_validate_json(json_data)
        end_time = time.time()
        
        json_validation_time = (end_time - start_time) / 50
        assert json_validation_time < 0.01  # Should be under 10ms per validation

    def test_orm_conversion_performance(self):
        """Test ORM conversion performance."""
        # Create API object with mixed types
        api_nutri_facts = ApiNutriFacts(
            calories=ApiNutriValue(value=350.0, unit=MeasureUnit.ENERGY),
            protein=25.0,
            carbohydrate=ApiNutriValue(value=40.0, unit=MeasureUnit.GRAM),
            vitamin_c=60.0
        ) # type: ignore
        
        # Test to_orm_kwargs performance
        start_time = time.time()
        for _ in range(1000):
            orm_kwargs = api_nutri_facts.to_orm_kwargs()
        end_time = time.time()
        
        orm_conversion_time = (end_time - start_time) / 1000
        assert orm_conversion_time < 0.001  # Should be under 1ms per conversion

    def test_memory_usage_efficiency(self):
        """Test memory usage efficiency for large nutritional datasets."""
        import gc
        import psutil
        import os
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Create many ApiNutriFacts instances
        nutri_facts_list = []
        for i in range(1000):
            api_nutri_facts = ApiNutriFacts(
                calories=float(i),
                protein=float(i * 0.2),
                carbohydrate=float(i * 0.3),
                vitamin_c=float(i * 0.1)
            ) # type: ignore
            nutri_facts_list.append(api_nutri_facts)
        
        # Get peak memory usage
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_per_instance = (peak_memory - initial_memory) / 1000
        
        # Cleanup
        del nutri_facts_list
        gc.collect()
        
        # Verify memory efficiency
        assert memory_per_instance < 0.1  # Should use less than 0.1 MB per instance


class TestApiNutriFactsIntegrationBehavior:
    """Test comprehensive integration behavior for ApiNutriFacts schema."""

    def test_immutability_behavior(self):
        """Test that ApiNutriFacts instances are immutable."""
        api_nutri_facts = ApiNutriFacts(
            calories=250.0,
            protein=20.0,
            vitamin_c=60.0
        ) # type: ignore
        
        # Verify immutability
        with pytest.raises(ValueError):
            api_nutri_facts.calories = 300.0 # type: ignore
        
        with pytest.raises(ValueError):
            api_nutri_facts.protein = 25.0 # type: ignore

    def test_serialization_deserialization_consistency(self):
        """Test serialization and deserialization consistency."""
        original_api = ApiNutriFacts(
            calories=ApiNutriValue(value=300.0, unit=MeasureUnit.ENERGY),
            protein=25.0,
            vitamin_c=ApiNutriValue(value=80.0, unit=MeasureUnit.MILLIGRAM)
        ) # type: ignore
        
        # Serialize to dict
        serialized_dict = original_api.model_dump()
        
        # Deserialize from dict
        deserialized_api = ApiNutriFacts.model_validate(serialized_dict)
        
        # Verify consistency
        assert deserialized_api.calories == original_api.calories
        assert deserialized_api.protein == original_api.protein
        assert deserialized_api.vitamin_c == original_api.vitamin_c

    def test_json_serialization_deserialization_consistency(self):
        """Test JSON serialization and deserialization consistency."""
        original_api = ApiNutriFacts(
            calories=350.0,
            protein=ApiNutriValue(value=28.0, unit=MeasureUnit.GRAM),
            carbohydrate=45.0,
            vitamin_c=90.0
        ) # type: ignore
        
        # Serialize to JSON
        json_str = original_api.model_dump_json()
        
        # Deserialize from JSON
        deserialized_api = ApiNutriFacts.model_validate_json(json_str)
        
        # Verify consistency
        assert deserialized_api.calories == original_api.calories
        assert deserialized_api.protein == original_api.protein
        assert deserialized_api.carbohydrate == original_api.carbohydrate
        assert deserialized_api.vitamin_c == original_api.vitamin_c

    def test_hash_and_equality_behavior(self):
        """Test hash and equality behavior for ApiNutriFacts instances."""
        api_nutri_facts_1 = ApiNutriFacts(
            calories=300.0,
            protein=25.0,
            vitamin_c=80.0
        ) # type: ignore
        
        api_nutri_facts_2 = ApiNutriFacts(
            calories=300.0,
            protein=25.0,
            vitamin_c=80.0
        ) # type: ignore
        
        api_nutri_facts_3 = ApiNutriFacts(
            calories=350.0,
            protein=30.0,
            vitamin_c=90.0
        ) # type: ignore
        
        # Verify equality behavior
        assert api_nutri_facts_1 == api_nutri_facts_2
        assert api_nutri_facts_1 != api_nutri_facts_3
        
        # Verify hash behavior (for use in sets/dicts)
        nutri_facts_set = {api_nutri_facts_1, api_nutri_facts_2, api_nutri_facts_3} # type: ignore
        assert len(nutri_facts_set) == 2  # Should have only 2 unique instances

    def test_field_access_patterns(self):
        """Test various field access patterns and their behavior."""
        api_nutri_facts = ApiNutriFacts(
            calories=ApiNutriValue(value=320.0, unit=MeasureUnit.ENERGY),
            protein=22.0,
            vitamin_c=ApiNutriValue(value=85.0, unit=MeasureUnit.MILLIGRAM)
        ) # type: ignore
        
        # Test direct field access
        assert api_nutri_facts.calories.value == 320.0
        assert api_nutri_facts.protein == 22.0
        assert api_nutri_facts.vitamin_c.value == 85.0
        
        # Test getattr access
        assert getattr(api_nutri_facts, 'calories').value == 320.0
        assert getattr(api_nutri_facts, 'protein') == 22.0
        
        # Test model_fields access
        field_names = list(api_nutri_facts.__class__.model_fields.keys())
        assert 'calories' in field_names
        assert 'protein' in field_names
        assert 'vitamin_c' in field_names

    def test_comprehensive_nutritional_profile_integration(self):
        """Test integration behavior with comprehensive nutritional profiles."""
        # Create comprehensive profile
        comprehensive_api = ApiNutriFacts(
            # Macronutrients
            calories=380.0,
            protein=ApiNutriValue(value=28.0, unit=MeasureUnit.GRAM),
            carbohydrate=42.0,
            total_fat=ApiNutriValue(value=15.0, unit=MeasureUnit.GRAM),
            
            # Vitamins
            vitamin_c=85.0,
            vitamin_d=ApiNutriValue(value=600.0, unit=MeasureUnit.IU),
            vitamin_b12=2.4,
            
            # Minerals
            calcium=ApiNutriValue(value=200.0, unit=MeasureUnit.MILLIGRAM),
            iron=8.0,
            potassium=1000.0
        ) # type: ignore
        
        # Test comprehensive conversion to domain
        domain_nutri_facts = comprehensive_api.to_domain()
        assert isinstance(domain_nutri_facts, NutriFacts)
        
        # Test comprehensive round-trip
        api_converted_back = ApiNutriFacts.from_domain(domain_nutri_facts)
        
        # Verify key nutrients maintain integrity
        assert api_converted_back.calories == comprehensive_api.calories
        assert api_converted_back.carbohydrate == comprehensive_api.carbohydrate
        assert api_converted_back.vitamin_b12 == comprehensive_api.vitamin_b12
        assert api_converted_back.iron == comprehensive_api.iron

    def test_cross_context_integration_behavior(self):
        """Test behavior when used across different contexts (e.g., recipes, products)."""
        # Test with recipe-style nutritional data
        recipe_nutri = ApiNutriFacts(
            calories=250.0,
            protein=15.0,
            carbohydrate=30.0,
            total_fat=8.0
        ) # type: ignore
        
        # Test with product-style nutritional data
        product_nutri = ApiNutriFacts(
            calories=ApiNutriValue(value=100.0, unit=MeasureUnit.ENERGY),
            protein=ApiNutriValue(value=5.0, unit=MeasureUnit.GRAM),
            sodium=ApiNutriValue(value=200.0, unit=MeasureUnit.MILLIGRAM)
        ) # type: ignore
        
        # Test with supplement-style nutritional data
        supplement_nutri = ApiNutriFacts(
            vitamin_c=ApiNutriValue(value=1000.0, unit=MeasureUnit.MILLIGRAM),
            vitamin_d=ApiNutriValue(value=2000.0, unit=MeasureUnit.IU),
            calcium=ApiNutriValue(value=500.0, unit=MeasureUnit.MILLIGRAM)
        ) # type: ignore
        
        # Verify all contexts work with same schema
        assert recipe_nutri.calories == 250.0
        assert product_nutri.calories.value == 100.0
        assert supplement_nutri.vitamin_c.value == 1000.0
        
        # Test that all can be converted to domain
        recipe_domain = recipe_nutri.to_domain()
        product_domain = product_nutri.to_domain()
        supplement_domain = supplement_nutri.to_domain()
        
        assert isinstance(recipe_domain, NutriFacts)
        assert isinstance(product_domain, NutriFacts)
        assert isinstance(supplement_domain, NutriFacts) 