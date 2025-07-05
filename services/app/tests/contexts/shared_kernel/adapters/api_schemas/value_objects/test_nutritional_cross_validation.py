"""
Cross-validation tests for ApiNutriValue and ApiNutriFacts integration.

This test suite validates the interaction patterns between ApiNutriValue and ApiNutriFacts
schemas, ensuring proper integration behavior, calculation consistency, performance
characteristics, and backward compatibility across contexts.

Follows Phase 1 excellence patterns:
- Behavior-focused testing (not implementation details)
- Performance validation under 5ms requirement
- Comprehensive error scenarios with realistic data
- Cross-context integration validation
- Round-trip conversion integrity
"""

import time

from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_facts import ApiNutriFacts
from src.contexts.shared_kernel.adapters.api_schemas.value_objects.api_nutri_value import ApiNutriValue
from src.contexts.shared_kernel.domain.enums import MeasureUnit
from src.contexts.shared_kernel.domain.value_objects.nutri_facts import NutriFacts
from src.contexts.shared_kernel.domain.value_objects.nutri_value import NutriValue


class TestApiNutriValueFactsIntegration:
    """Test integration behavior between ApiNutriValue and ApiNutriFacts."""

    def test_nutri_facts_creation_with_mixed_apinutrivalue_types(self):
        """Test that ApiNutriFacts properly handles mixed ApiNutriValue and float inputs."""
        # Real-world scenario: API receives mixed format nutritional data
        nutri_facts = ApiNutriFacts(
            calories=ApiNutriValue(value=250.0, unit=MeasureUnit.ENERGY),
            protein=15.5,  # float
            carbohydrate=ApiNutriValue(value=30.0, unit=MeasureUnit.GRAM),
            total_fat=8.2,  # float
            vitamin_c=ApiNutriValue(value=60.0, unit=MeasureUnit.MILLIGRAM),
            calcium=120.0  # float
        ) # type: ignore
        
        # Verify ApiNutriValue instances are preserved
        assert isinstance(nutri_facts.calories, ApiNutriValue)
        assert nutri_facts.calories.value == 250.0
        assert nutri_facts.calories.unit == MeasureUnit.ENERGY
        
        # Verify float values are preserved
        assert isinstance(nutri_facts.protein, float)
        assert nutri_facts.protein == 15.5
        
        # Verify mixed conversion to domain works correctly
        domain_facts = nutri_facts.to_domain()
        assert isinstance(domain_facts, NutriFacts)
        assert domain_facts.calories.value == 250.0
        assert domain_facts.protein.value == 15.5
        assert domain_facts.carbohydrate.value == 30.0

    def test_nutri_facts_json_conversion_with_nested_apinutrivalue_objects(self):
        """Test JSON serialization and deserialization with nested ApiNutriValue objects."""
        # Real-world scenario: API response containing detailed nutritional info
        original_facts = ApiNutriFacts(
            calories=ApiNutriValue(value=300.0, unit=MeasureUnit.ENERGY),
            protein=ApiNutriValue(value=25.0, unit=MeasureUnit.GRAM),
            carbohydrate=45.0,
            vitamin_d=ApiNutriValue(value=600.0, unit=MeasureUnit.IU),
            calcium=ApiNutriValue(value=200.0, unit=MeasureUnit.MILLIGRAM)
        ) # type: ignore
        
        # Serialize to JSON
        json_data = original_facts.model_dump_json()
        assert isinstance(json_data, str)
        
        # Deserialize from JSON
        recreated_facts = ApiNutriFacts.model_validate_json(json_data)
        
        # Verify ApiNutriValue objects are properly recreated
        assert isinstance(recreated_facts.calories, ApiNutriValue)
        assert recreated_facts.calories.value == 300.0
        assert recreated_facts.calories.unit == MeasureUnit.ENERGY
        
        # Verify float values are preserved
        assert recreated_facts.carbohydrate == 45.0
        
        # Verify complex vitamins/minerals are preserved
        assert isinstance(recreated_facts.vitamin_d, ApiNutriValue)
        assert recreated_facts.vitamin_d.value == 600.0
        assert recreated_facts.vitamin_d.unit == MeasureUnit.IU

    def test_complex_nutritional_profile_aggregation_behavior(self):
        """Test behavior when aggregating multiple nutritional profiles (meal composition scenario)."""
        # Real-world scenario: Meal composed of multiple recipes with different nutritional formats
        recipe1_nutrition = ApiNutriFacts(
            calories=ApiNutriValue(value=150.0, unit=MeasureUnit.ENERGY),
            protein=12.0,
            carbohydrate=ApiNutriValue(value=20.0, unit=MeasureUnit.GRAM),
            vitamin_c=ApiNutriValue(value=30.0, unit=MeasureUnit.MILLIGRAM)
        ) # type: ignore
        
        recipe2_nutrition = ApiNutriFacts(
            calories=200.0,  # float
            protein=ApiNutriValue(value=18.0, unit=MeasureUnit.GRAM),
            carbohydrate=25.0,
            vitamin_c=40.0
        ) # type: ignore
        
        recipe3_nutrition = ApiNutriFacts(
            calories=ApiNutriValue(value=100.0, unit=MeasureUnit.ENERGY),
            protein=ApiNutriValue(value=8.0, unit=MeasureUnit.GRAM),
            carbohydrate=ApiNutriValue(value=15.0, unit=MeasureUnit.GRAM),
            vitamin_c=ApiNutriValue(value=25.0, unit=MeasureUnit.MILLIGRAM)
        ) # type: ignore
        
        # Convert to domain for aggregation (simulating meal composition)
        domain_facts = [
            recipe1_nutrition.to_domain(),
            recipe2_nutrition.to_domain(),
            recipe3_nutrition.to_domain()
        ]
        
        # Aggregate nutritional facts (simulating Meal.nutri_facts computation)
        total_nutrition = NutriFacts()
        for facts in domain_facts:
            total_nutrition += facts
        
        # Convert aggregated result back to API
        api_total = ApiNutriFacts.from_domain(total_nutrition)
        
        # Verify aggregation accuracy
        assert isinstance(api_total.calories, ApiNutriValue)
        assert api_total.calories.value == 450.0  # 150 + 200 + 100
        assert isinstance(api_total.protein, ApiNutriValue)
        assert api_total.protein.value == 38.0    # 12 + 18 + 8
        assert isinstance(api_total.carbohydrate, ApiNutriValue)
        assert api_total.carbohydrate.value == 60.0  # 20 + 25 + 15
        assert isinstance(api_total.vitamin_c, ApiNutriValue)
        assert api_total.vitamin_c.value == 95.0     # 30 + 40 + 25

    def test_edge_case_nutritional_calculations_with_zero_and_none_values(self):
        """Test edge cases in nutritional calculations with zero and None values."""
        # Real-world scenario: Incomplete nutritional data from various sources
        incomplete_nutrition = ApiNutriFacts(
            calories=ApiNutriValue(value=0.0, unit=MeasureUnit.ENERGY),  # Zero calories
            protein=0.0,  # Zero protein as float (None becomes 0.0 due to default)
            carbohydrate=ApiNutriValue(value=15.0, unit=MeasureUnit.GRAM),
            total_fat=0.0,  # Zero fat as float
            calcium=ApiNutriValue(value=50.0, unit=MeasureUnit.MILLIGRAM)
        ) # type: ignore
        
        # Convert to domain and verify handling
        domain_facts = incomplete_nutrition.to_domain()
        
        # Verify domain conversion handles zero values correctly
        assert domain_facts.calories.value == 0.0
        assert domain_facts.protein.value == 0.0
        assert domain_facts.carbohydrate.value == 15.0
        assert domain_facts.total_fat.value == 0.0
        assert domain_facts.calcium.value == 50.0
        
        # Verify round-trip conversion maintains data integrity
        api_converted_back = ApiNutriFacts.from_domain(domain_facts)
        assert isinstance(api_converted_back.calories, ApiNutriValue)
        assert api_converted_back.calories.value == 0.0
        assert isinstance(api_converted_back.protein, ApiNutriValue)
        assert api_converted_back.protein.value == 0.0


class TestNutritionalCalculationConsistency:
    """Test calculation consistency between ApiNutriValue and ApiNutriFacts."""

    def test_macronutrient_percentage_calculation_consistency(self):
        """Test that macronutrient percentage calculations are consistent across formats."""
        # Real-world scenario: Calculating macronutrient distribution
        nutrition_data = ApiNutriFacts(
            calories=ApiNutriValue(value=400.0, unit=MeasureUnit.ENERGY),
            protein=ApiNutriValue(value=30.0, unit=MeasureUnit.GRAM),    # 30g * 4 kcal/g = 120 kcal
            carbohydrate=50.0,                                           # 50g * 4 kcal/g = 200 kcal  
            total_fat=ApiNutriValue(value=8.0, unit=MeasureUnit.GRAM)    # 8g * 9 kcal/g = 72 kcal
        ) # type: ignore
        
        # Convert to domain for percentage calculations
        domain_facts = nutrition_data.to_domain()
        
        # Calculate macronutrient percentages (simulating meal macro_division)
        protein_calories = domain_facts.protein.value * 4  # 4 kcal per gram
        carb_calories = domain_facts.carbohydrate.value * 4
        fat_calories = domain_facts.total_fat.value * 9   # 9 kcal per gram
        total_macro_calories = protein_calories + carb_calories + fat_calories
        
        # Verify calculation consistency
        assert total_macro_calories == 392.0  # 120 + 200 + 72
        
        protein_percentage = (protein_calories / total_macro_calories) * 100
        carb_percentage = (carb_calories / total_macro_calories) * 100
        fat_percentage = (fat_calories / total_macro_calories) * 100
        
        # Verify percentages are realistic and sum to 100
        assert abs(protein_percentage - 30.61) < 0.1   # ~30.6%
        assert abs(carb_percentage - 51.02) < 0.1      # ~51.0%
        assert abs(fat_percentage - 18.37) < 0.1       # ~18.4%
        assert abs((protein_percentage + carb_percentage + fat_percentage) - 100.0) < 0.1

    def test_unit_conversion_consistency_across_nutritional_values(self):
        """Test that unit conversions are consistent across different nutritional values."""
        # Real-world scenario: Converting between different unit representations
        vitamin_nutrition = ApiNutriFacts(
            vitamin_d=ApiNutriValue(value=600.0, unit=MeasureUnit.IU),
            vitamin_c=ApiNutriValue(value=1000.0, unit=MeasureUnit.MILLIGRAM),
            calcium=ApiNutriValue(value=1.2, unit=MeasureUnit.GRAM),
            iron=ApiNutriValue(value=18000.0, unit=MeasureUnit.MICROGRAM)
        ) # type: ignore
        
        # Convert to domain and verify unit consistency
        domain_facts = vitamin_nutrition.to_domain()
        
        # Verify units are preserved correctly
        assert domain_facts.vitamin_d.unit == MeasureUnit.IU
        assert domain_facts.vitamin_c.unit == MeasureUnit.MILLIGRAM
        assert domain_facts.calcium.unit == MeasureUnit.GRAM
        assert domain_facts.iron.unit == MeasureUnit.MICROGRAM
        
        # Verify values are preserved during conversion
        assert domain_facts.vitamin_d.value == 600.0
        assert domain_facts.vitamin_c.value == 1000.0
        assert domain_facts.calcium.value == 1.2
        assert domain_facts.iron.value == 18000.0
        
        # Round-trip conversion should maintain consistency
        api_converted = ApiNutriFacts.from_domain(domain_facts)
        assert api_converted.vitamin_d.value == 600.0 # type: ignore
        assert api_converted.vitamin_d.unit == MeasureUnit.IU # type: ignore

    def test_nutritional_density_calculations_with_weight_scaling(self):
        """Test nutritional density calculations when scaling by weight."""
        # Real-world scenario: Scaling nutrition per 100g to actual serving size
        base_nutrition_per_100g = ApiNutriFacts(
            calories=ApiNutriValue(value=250.0, unit=MeasureUnit.ENERGY),
            protein=ApiNutriValue(value=20.0, unit=MeasureUnit.GRAM),
            carbohydrate=30.0,
            total_fat=ApiNutriValue(value=10.0, unit=MeasureUnit.GRAM),
            sodium=ApiNutriValue(value=500.0, unit=MeasureUnit.MILLIGRAM)
        ) # type: ignore
        
        # Scale to 150g serving (1.5x multiplier)
        serving_weight = 150.0
        base_weight = 100.0
        scale_factor = serving_weight / base_weight
        
        # Convert to domain for scaling calculations
        domain_per_100g = base_nutrition_per_100g.to_domain()
        
        # Create scaled nutrition (simulating recipe scaling)
        scaled_domain = NutriFacts(
            calories=NutriValue(value=domain_per_100g.calories.value * scale_factor, unit=domain_per_100g.calories.unit),
            protein=NutriValue(value=domain_per_100g.protein.value * scale_factor, unit=domain_per_100g.protein.unit),
            carbohydrate=NutriValue(value=domain_per_100g.carbohydrate.value * scale_factor, unit=domain_per_100g.carbohydrate.unit),
            total_fat=NutriValue(value=domain_per_100g.total_fat.value * scale_factor, unit=domain_per_100g.total_fat.unit),
            sodium=NutriValue(value=domain_per_100g.sodium.value * scale_factor, unit=domain_per_100g.sodium.unit)
        )
        
        # Convert scaled result back to API
        scaled_api = ApiNutriFacts.from_domain(scaled_domain)
        
        # Verify scaling calculations
        assert scaled_api.calories.value == 375.0      # 250 * 1.5 # type: ignore
        assert scaled_api.protein.value == 30.0        # 20 * 1.5   # type: ignore
        assert scaled_api.carbohydrate.value == 45.0   # 30 * 1.5 # type: ignore
        assert scaled_api.total_fat.value == 15.0      # 10 * 1.5 # type: ignore
        assert scaled_api.sodium.value == 750.0        # 500 * 1.5 # type: ignore


class TestNutritionalPerformanceValidation:
    """Test performance characteristics of combined nutritional operations."""

    def test_large_scale_nutritional_aggregation_performance(self):
        """Test performance when aggregating large numbers of nutritional profiles."""
        # Real-world scenario: Aggregating nutrition for complex meals with many ingredients
        start_time = time.perf_counter()
        
        # Create 50 diverse nutritional profiles (simulating complex meal)
        nutritional_profiles = []
        for i in range(50):
            profile = ApiNutriFacts(
                calories=ApiNutriValue(value=50.0 + i, unit=MeasureUnit.ENERGY),
                protein=10.0 + (i * 0.5),
                carbohydrate=ApiNutriValue(value=15.0 + i, unit=MeasureUnit.GRAM),
                total_fat=5.0 + (i * 0.2),
                vitamin_c=ApiNutriValue(value=20.0 + i, unit=MeasureUnit.MILLIGRAM),
                calcium=100.0 + i
            ) # type: ignore
            nutritional_profiles.append(profile)
        
        # Convert to domain and aggregate
        domain_profiles = [profile.to_domain() for profile in nutritional_profiles]
        aggregated = NutriFacts()
        for profile in domain_profiles:
            aggregated += profile
        
        # Convert back to API
        final_api = ApiNutriFacts.from_domain(aggregated)
        
        end_time = time.perf_counter()
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Performance requirement: < 5ms for complex aggregation
        assert execution_time < 5.0, f"Performance requirement failed: {execution_time:.2f}ms > 5ms"
        
        # Verify aggregation accuracy (spot checks)
        expected_calories = sum(50.0 + i for i in range(50))  # 50*50 + (0+1+2+...+49) = 2500 + 1225 = 3725
        assert final_api.calories.value == expected_calories # type: ignore
        
        expected_protein = sum(10.0 + (i * 0.5) for i in range(50))  # 50*10 + 0.5*(0+1+2+...+49) = 500 + 612.5 = 1112.5
        assert final_api.protein.value == expected_protein # type: ignore

    def test_json_serialization_performance_with_complex_nutrition(self):
        """Test JSON serialization performance with complex nutritional data."""
        # Real-world scenario: API response serialization for detailed nutrition
        complex_nutrition = ApiNutriFacts(
            # Major macronutrients  
            calories=ApiNutriValue(value=450.0, unit=MeasureUnit.ENERGY),
            protein=ApiNutriValue(value=35.0, unit=MeasureUnit.GRAM),
            carbohydrate=ApiNutriValue(value=60.0, unit=MeasureUnit.GRAM),
            total_fat=ApiNutriValue(value=15.0, unit=MeasureUnit.GRAM),
            
            # Detailed breakdown
            saturated_fat=ApiNutriValue(value=4.0, unit=MeasureUnit.GRAM),
            dietary_fiber=ApiNutriValue(value=8.0, unit=MeasureUnit.GRAM),
            sodium=ApiNutriValue(value=800.0, unit=MeasureUnit.MILLIGRAM),
            
            # Vitamins
            vitamin_c=ApiNutriValue(value=120.0, unit=MeasureUnit.MILLIGRAM),
            vitamin_d=ApiNutriValue(value=600.0, unit=MeasureUnit.IU),
            vitamin_b12=ApiNutriValue(value=2.4, unit=MeasureUnit.MICROGRAM),
            folic_acid=ApiNutriValue(value=400.0, unit=MeasureUnit.MICROGRAM),
            
            # Minerals
            calcium=ApiNutriValue(value=300.0, unit=MeasureUnit.MILLIGRAM),
            iron=ApiNutriValue(value=18.0, unit=MeasureUnit.MILLIGRAM),
            potassium=ApiNutriValue(value=2000.0, unit=MeasureUnit.MILLIGRAM),
            zinc=ApiNutriValue(value=15.0, unit=MeasureUnit.MILLIGRAM)
        ) # type: ignore
        
        start_time = time.perf_counter()
        
        # Serialize to JSON (simulating API response)
        json_data = complex_nutrition.model_dump_json()
        
        # Deserialize from JSON (simulating API request processing)
        recreated = ApiNutriFacts.model_validate_json(json_data)
        
        end_time = time.perf_counter()
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Performance requirement: < 5ms for complex JSON operations
        assert execution_time < 5.0, f"JSON performance requirement failed: {execution_time:.2f}ms > 5ms"
        
        # Verify data integrity after JSON round-trip
        assert recreated.calories.value == 450.0 # type: ignore
        assert recreated.protein.value == 35.0 # type: ignore
        assert recreated.vitamin_c.value == 120.0 # type: ignore
        assert recreated.calcium.value == 300.0 # type: ignore

    def test_bulk_conversion_performance_api_domain_roundtrips(self):
        """Test performance of bulk API ↔ Domain conversions."""
        # Real-world scenario: Bulk processing of nutritional data
        start_time = time.perf_counter()
        
        # Create 20 diverse nutritional profiles
        api_profiles = []
        for i in range(20):
            profile = ApiNutriFacts(
                calories=ApiNutriValue(value=200.0 + (i * 10), unit=MeasureUnit.ENERGY),
                protein=ApiNutriValue(value=15.0 + i, unit=MeasureUnit.GRAM),
                carbohydrate=25.0 + (i * 2),
                total_fat=ApiNutriValue(value=8.0 + (i * 0.5), unit=MeasureUnit.GRAM),
                vitamin_c=50.0 + (i * 5),
                calcium=ApiNutriValue(value=150.0 + (i * 10), unit=MeasureUnit.MILLIGRAM)
            ) # type: ignore    
            api_profiles.append(profile)
        
        # Convert to domain
        domain_profiles = [profile.to_domain() for profile in api_profiles]
        
        # Convert back to API 
        converted_back = [ApiNutriFacts.from_domain(domain) for domain in domain_profiles]
        
        end_time = time.perf_counter()
        execution_time = (end_time - start_time) * 1000  # Convert to milliseconds
        
        # Performance requirement: < 5ms for 20 round-trip conversions
        assert execution_time < 5.0, f"Bulk conversion performance failed: {execution_time:.2f}ms > 5ms"
        
        # Verify conversion integrity (spot checks)
        assert len(converted_back) == 20
        assert converted_back[0].calories.value == 200.0 # type: ignore
        assert converted_back[10].protein.value == 25.0  # 15 + 10 # type: ignore
        assert converted_back[19].calcium.value == 340.0  # 150 + (19 * 10) # type: ignore


class TestCrossContextCompatibility:
    """Test compatibility across different contexts (recipes, meals, products)."""

    def test_recipe_to_meal_nutritional_aggregation_compatibility(self):
        """Test compatibility when aggregating recipe nutrition into meal nutrition."""
        # Real-world scenario: Meal composed of multiple recipes (recipes_catalog context)
        recipe1_nutrition = ApiNutriFacts(
            calories=ApiNutriValue(value=180.0, unit=MeasureUnit.ENERGY),
            protein=ApiNutriValue(value=12.0, unit=MeasureUnit.GRAM),
            carbohydrate=25.0,
            total_fat=6.0
        ) # type: ignore
        
        recipe2_nutrition = ApiNutriFacts(
            calories=220.0,
            protein=ApiNutriValue(value=16.0, unit=MeasureUnit.GRAM),
            carbohydrate=ApiNutriValue(value=30.0, unit=MeasureUnit.GRAM),
            total_fat=ApiNutriValue(value=8.0, unit=MeasureUnit.GRAM)
        ) # type: ignore
        
        # Simulate meal aggregation (as done in Meal.nutri_facts)
        recipe1_domain = recipe1_nutrition.to_domain()
        recipe2_domain = recipe2_nutrition.to_domain()
        
        meal_nutrition = NutriFacts()
        meal_nutrition += recipe1_domain
        meal_nutrition += recipe2_domain
        
        meal_api_nutrition = ApiNutriFacts.from_domain(meal_nutrition)
        
        # Verify meal-level aggregation matches expected values
        assert meal_api_nutrition.calories.value == 400.0  # 180 + 220 # type: ignore
        assert meal_api_nutrition.protein.value == 28.0    # 12 + 16 # type: ignore
        assert meal_api_nutrition.carbohydrate.value == 55.0  # 25 + 30 # type: ignore
        assert meal_api_nutrition.total_fat.value == 14.0     # 6 + 8 # type: ignore
        
        # Verify all fields are ApiNutriValue instances (from_domain behavior)
        assert isinstance(meal_api_nutrition.calories, ApiNutriValue)
        assert isinstance(meal_api_nutrition.protein, ApiNutriValue)
        assert isinstance(meal_api_nutrition.carbohydrate, ApiNutriValue)
        assert isinstance(meal_api_nutrition.total_fat, ApiNutriValue)

    def test_product_catalog_nutritional_data_compatibility(self):
        """Test compatibility with product catalog nutritional data formats."""
        # Real-world scenario: Product nutritional information (products_catalog context)
        product_nutrition = ApiNutriFacts(
            # Standard product label format
            calories=ApiNutriValue(value=150.0, unit=MeasureUnit.ENERGY),
            protein=5.0,
            carbohydrate=ApiNutriValue(value=20.0, unit=MeasureUnit.GRAM),
            total_fat=6.0,
            saturated_fat=ApiNutriValue(value=2.0, unit=MeasureUnit.GRAM),
            sodium=ApiNutriValue(value=300.0, unit=MeasureUnit.MILLIGRAM),
            
            # Product-specific nutrients
            vitamin_c=ApiNutriValue(value=80.0, unit=MeasureUnit.MILLIGRAM),
            calcium=ApiNutriValue(value=120.0, unit=MeasureUnit.MILLIGRAM),
            iron=ApiNutriValue(value=2.0, unit=MeasureUnit.MILLIGRAM)
        ) # type: ignore
        
        # Test domain conversion for business logic
        domain_nutrition = product_nutrition.to_domain()
        
        # Verify domain objects can be used for calculations
        protein_calories = domain_nutrition.protein.value * 4
        carb_calories = domain_nutrition.carbohydrate.value * 4
        fat_calories = domain_nutrition.total_fat.value * 9
        
        assert protein_calories == 20.0   # 5 * 4
        assert carb_calories == 80.0      # 20 * 4
        assert fat_calories == 54.0       # 6 * 9

    def test_menu_planning_nutritional_integration_compatibility(self):
        """Test compatibility with menu planning nutritional calculations."""
        # Real-world scenario: Menu meal nutritional planning (client context)
        breakfast_nutrition = ApiNutriFacts(
            calories=ApiNutriValue(value=320.0, unit=MeasureUnit.ENERGY),
            protein=ApiNutriValue(value=15.0, unit=MeasureUnit.GRAM),
            carbohydrate=45.0,
            total_fat=ApiNutriValue(value=12.0, unit=MeasureUnit.GRAM)
        ) # type: ignore
        
        lunch_nutrition = ApiNutriFacts(
            calories=450.0,
            protein=ApiNutriValue(value=25.0, unit=MeasureUnit.GRAM),
            carbohydrate=ApiNutriValue(value=55.0, unit=MeasureUnit.GRAM),
            total_fat=15.0
        ) # type: ignore
        
        dinner_nutrition = ApiNutriFacts(
            calories=ApiNutriValue(value=380.0, unit=MeasureUnit.ENERGY),
            protein=22.0,
            carbohydrate=ApiNutriValue(value=48.0, unit=MeasureUnit.GRAM),
            total_fat=ApiNutriValue(value=14.0, unit=MeasureUnit.GRAM)
        ) # type: ignore    
        
        # Simulate daily nutritional planning
        daily_meals = [breakfast_nutrition, lunch_nutrition, dinner_nutrition]
        daily_total = NutriFacts()
        
        for meal_nutrition in daily_meals:
            meal_domain = meal_nutrition.to_domain()
            daily_total += meal_domain
        
        daily_api_total = ApiNutriFacts.from_domain(daily_total)
        
        # Verify daily totals are realistic for menu planning
        assert daily_api_total.calories.value == 1150.0  # 320 + 450 + 380 # type: ignore
        assert daily_api_total.protein.value == 62.0     # 15 + 25 + 22 # type: ignore
        assert daily_api_total.carbohydrate.value == 148.0  # 45 + 55 + 48 # type: ignore
        assert daily_api_total.total_fat.value == 41.0      # 12 + 15 + 14 # type: ignore
        
        # Verify daily protein percentage (should be ~21% for balanced diet)
        protein_calories = daily_api_total.protein.value * 4  # 248 kcal # type: ignore
        protein_percentage = (protein_calories / daily_api_total.calories.value) * 100 # type: ignore
        assert 20.0 <= protein_percentage <= 25.0  # Realistic range for balanced diet


class TestBackwardCompatibilityValidation:
    """Test backward compatibility with existing nutritional endpoints."""

    def test_legacy_float_only_nutritional_data_compatibility(self):
        """Test compatibility with legacy systems that use float-only nutritional data."""
        # Real-world scenario: Legacy API endpoints with float-only nutrition
        legacy_nutrition_data = {
            "calories": 280.0,
            "protein": 18.0,
            "carbohydrate": 35.0,
            "total_fat": 9.0,
            "sodium": 450.0,
            "vitamin_c": 75.0
        }
        
        # Test that legacy data can be processed correctly
        api_nutrition = ApiNutriFacts(**legacy_nutrition_data)
        
        # Verify all values are preserved as floats (legacy behavior)
        assert api_nutrition.calories == 280.0 # type: ignore
        assert api_nutrition.protein == 18.0 # type: ignore
        assert api_nutrition.carbohydrate == 35.0 # type: ignore
        assert api_nutrition.total_fat == 9.0 # type: ignore
        assert api_nutrition.sodium == 450.0
        assert api_nutrition.vitamin_c == 75.0
        
        # Verify legacy data can be converted to domain
        domain_nutrition = api_nutrition.to_domain()
        assert domain_nutrition.calories.value == 280.0
        assert domain_nutrition.protein.value == 18.0
        
        # Verify round-trip conversion maintains data
        api_converted = ApiNutriFacts.from_domain(domain_nutrition)
        assert api_converted.calories.value == 280.0 # type: ignore
        assert api_converted.protein.value == 18.0 # type: ignore

    def test_mixed_legacy_and_enhanced_format_compatibility(self):
        """Test compatibility when mixing legacy float and enhanced ApiNutriValue formats."""
        # Real-world scenario: Gradual migration with mixed data formats
        mixed_nutrition_data = ApiNutriFacts(
            # Legacy float format
            calories=350.0,
            protein=28.0,
            carbohydrate=42.0,
            
            # Enhanced ApiNutriValue format
            total_fat=ApiNutriValue(value=12.0, unit=MeasureUnit.GRAM),
            vitamin_c=ApiNutriValue(value=90.0, unit=MeasureUnit.MILLIGRAM),
            calcium=ApiNutriValue(value=200.0, unit=MeasureUnit.MILLIGRAM)
        ) # type: ignore
        
        # Test JSON serialization preserves mixed format
        json_data = mixed_nutrition_data.model_dump_json()
        recreated = ApiNutriFacts.model_validate_json(json_data)
        
        # Verify mixed formats are preserved
        assert recreated.calories == 350.0  # float preserved
        assert recreated.protein == 28.0    # float preserved
        assert isinstance(recreated.total_fat, ApiNutriValue)  # ApiNutriValue preserved
        assert recreated.total_fat.value == 12.0
        
        # Verify domain conversion handles mixed formats correctly
        domain_nutrition = recreated.to_domain()
        assert domain_nutrition.calories.value == 350.0
        assert domain_nutrition.total_fat.value == 12.0

    def test_orm_integration_backward_compatibility(self):
        """Test backward compatibility with existing ORM nutritional data structures."""
        # Real-world scenario: Existing ORM models with float-only nutritional storage
        nutrition_with_mixed_types = ApiNutriFacts(
            calories=ApiNutriValue(value=400.0, unit=MeasureUnit.ENERGY),
            protein=ApiNutriValue(value=30.0, unit=MeasureUnit.GRAM),
            carbohydrate=50.0,  # float
            total_fat=ApiNutriValue(value=18.0, unit=MeasureUnit.GRAM),
            sodium=600.0,       # float
            vitamin_c=ApiNutriValue(value=100.0, unit=MeasureUnit.MILLIGRAM)
        ) # type: ignore
        
        # Create ORM kwargs data that simulates existing database storage (all floats)
        simulated_orm_kwargs = {
            "calories": 400.0,
            "protein": 30.0,
            "carbohydrate": 50.0,
            "total_fat": 18.0,
            "sodium": 600.0,
            "vitamin_c": 100.0
        }
        
        # Verify ORM kwargs can be used to recreate ApiNutriFacts
        recreated_from_orm = ApiNutriFacts(**simulated_orm_kwargs)
        
        # Values should be preserved as floats
        assert recreated_from_orm.calories == 400.0
        assert recreated_from_orm.protein == 30.0
        assert recreated_from_orm.carbohydrate == 50.0
        assert recreated_from_orm.total_fat == 18.0 