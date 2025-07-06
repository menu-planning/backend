# Factory Dependencies Map

## Overview
Comprehensive mapping of factory dependencies across the test suite to enable systematic replacement with explicit test data.

## Primary Test Files Analysis

### Recipe Test File Dependencies
**File**: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_comprehensive.py`

#### External Factory Dependencies (70+ functions)
**Source**: `api_recipe_data_factories.py`

##### Core Factory Functions (5)
- `create_api_recipe` - Main factory function
- `create_api_recipe_kwargs` - Returns kwargs dict
- `create_api_recipe_from_json` - JSON deserialization
- `create_api_recipe_json` - JSON string creation
- `reset_api_recipe_counters` - Counter management

##### Specialized Recipe Types (10)
- `create_simple_api_recipe` - Basic recipe
- `create_complex_api_recipe` - Complex nested structure
- `create_vegetarian_api_recipe` - Vegetarian constraints
- `create_high_protein_api_recipe` - High protein content
- `create_quick_api_recipe` - Short cooking time
- `create_dessert_api_recipe` - Dessert category
- `create_minimal_api_recipe` - Minimal required fields
- `create_api_recipe_with_max_fields` - All optional fields
- `create_api_recipe_with_incorrect_averages` - Invalid computed properties
- `create_api_recipe_without_ratings` - No ratings

##### Field Validation Edge Cases (10)
- `create_api_recipe_with_invalid_name` - Invalid name field
- `create_api_recipe_with_invalid_instructions` - Invalid instructions
- `create_api_recipe_with_invalid_total_time` - Invalid time values
- `create_api_recipe_with_invalid_weight` - Invalid weight values
- `create_api_recipe_with_boundary_values` - Boundary testing
- `create_api_recipe_with_extreme_boundary_values` - Extreme values
- `create_api_recipe_with_none_values` - None field values
- `create_api_recipe_with_empty_strings` - Empty string fields
- `create_api_recipe_with_whitespace_strings` - Whitespace handling
- `create_api_recipe_with_invalid_privacy` - Invalid privacy enum

##### Collection Validation Edge Cases (7)
- `create_api_recipe_with_list_ingredients` - List instead of frozenset
- `create_api_recipe_with_set_ingredients` - Set instead of frozenset
- `create_api_recipe_with_list_ratings` - List instead of frozenset
- `create_api_recipe_with_set_ratings` - Set instead of frozenset
- `create_api_recipe_with_list_tags` - List instead of frozenset
- `create_api_recipe_with_set_tags` - Set instead of frozenset
- `create_api_recipe_with_empty_collections` - Empty collections

##### Domain Rule Validation (5)
- `create_api_recipe_with_invalid_ingredient_positions` - Invalid positions
- `create_api_recipe_with_negative_ingredient_positions` - Negative positions
- `create_api_recipe_with_duplicate_ingredient_positions` - Duplicate positions
- `create_api_recipe_with_non_zero_start_positions` - Non-zero start
- `create_api_recipe_with_invalid_tag_author_id` - Invalid author ID

##### Computed Properties Testing (4)
- `create_api_recipe_with_mismatched_computed_properties` - Mismatched averages
- `create_api_recipe_with_single_rating` - Single rating edge case
- `create_api_recipe_with_extreme_ratings` - Extreme rating values
- `create_api_recipe_with_fractional_averages` - Fractional averages

##### Datetime Edge Cases (4)
- `create_api_recipe_with_future_timestamps` - Future dates
- `create_api_recipe_with_past_timestamps` - Past dates
- `create_api_recipe_with_invalid_timestamp_order` - Invalid order
- `create_api_recipe_with_same_timestamps` - Same timestamps

##### Text/Security Edge Cases (5)
- `create_api_recipe_with_unicode_text` - Unicode characters
- `create_api_recipe_with_special_characters` - Special characters
- `create_api_recipe_with_html_characters` - HTML characters
- `create_api_recipe_with_sql_injection` - SQL injection attempts
- `create_api_recipe_with_very_long_text` - Very long text

##### Performance/Stress Testing (3)
- `create_api_recipe_with_massive_collections` - Large collections
- `create_api_recipe_with_deeply_nested_data` - Deep nesting
- `create_stress_test_dataset` - Stress testing dataset

##### Bulk Operations (5)
- `create_recipe_collection` - Collection creation
- `create_bulk_recipe_creation_dataset` - Bulk creation
- `create_bulk_json_serialization_dataset` - Bulk JSON serialization
- `create_conversion_performance_dataset` - Performance testing
- `create_nested_object_validation_dataset` - Nested validation

##### Domain Integration (5)
**Source**: `recipe_domain_factories.py`
- `create_recipe` - Domain recipe creation
- `create_complex_recipe` - Complex domain recipe
- `create_minimal_recipe` - Minimal domain recipe
- `create_conversion_performance_dataset` - Performance dataset
- `reset_recipe_domain_counters` - Counter reset

##### ORM Integration (3)
**Source**: `recipe_orm_factories.py`
- `create_recipe_orm` - ORM recipe creation
- `create_recipe_orm_kwargs` - ORM kwargs
- `reset_recipe_orm_counters` - Counter reset

### Meal Test File Dependencies
**File**: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/root_aggregate/test_api_meal_comprehensive.py`

#### External Factory Dependencies (50+ functions)
**Source**: `api_meal_data_factories.py`

##### Core Factory Functions (6)
- `create_api_meal` - Main factory function
- `create_api_meal_kwargs` - Returns kwargs dict
- `create_api_meal_from_json` - JSON deserialization
- `create_api_meal_json` - JSON string creation
- `reset_api_meal_counters` - Counter management
- `validate_computed_property_correction_roundtrip` - Validation helper

##### Specialized Meal Types (9)
- `create_simple_api_meal` - Basic meal
- `create_complex_api_meal` - Complex nested structure
- `create_vegetarian_api_meal` - Vegetarian constraints
- `create_high_protein_api_meal` - High protein content
- `create_family_api_meal` - Family-sized meals
- `create_quick_api_meal` - Quick preparation
- `create_holiday_api_meal` - Holiday meals
- `create_minimal_api_meal` - Minimal required fields
- `create_api_meal_with_max_recipes` - Maximum recipes

##### Field Validation Test Suites (10)
- `create_field_validation_test_suite` - Complete validation suite
- `create_api_meal_with_invalid_field` - Invalid field values
- `create_api_meal_with_missing_required_fields` - Missing required fields
- `create_boundary_value_test_cases` - Boundary testing
- `create_type_coercion_test_cases` - Type coercion testing
- `create_nested_object_validation_test_cases` - Nested validation
- `create_comprehensive_validation_error_scenarios` - Error scenarios
- `create_pydantic_config_test_cases` - Pydantic configuration
- `create_validation_assignment_test_scenarios` - Assignment validation
- `create_api_meal_immutability_test_scenarios` - Immutability testing

##### JSON Testing (8)
- `create_json_serialization_test_cases` - JSON serialization
- `create_json_deserialization_test_cases` - JSON deserialization
- `create_json_edge_cases` - JSON edge cases
- `create_malformed_json_scenarios` - Malformed JSON
- `create_valid_json_test_cases` - Valid JSON cases
- `create_invalid_json_test_cases` - Invalid JSON cases
- `create_serialization_performance_scenarios` - Performance testing
- `create_bulk_json_serialization_dataset` - Bulk JSON operations

##### Conversion Testing (6)
- `create_conversion_method_test_scenarios` - Conversion methods
- `create_round_trip_consistency_test_scenarios` - Round-trip testing
- `create_type_conversion_test_scenarios` - Type conversion
- `create_meal_domain_from_api` - Domain conversion
- `create_api_meal_from_domain` - API conversion
- `create_meal_orm_kwargs_from_api` - ORM conversion

##### Performance Testing (5)
- `create_extreme_performance_scenarios` - Extreme performance
- `create_validation_performance_scenarios` - Validation performance
- `create_bulk_meal_creation_dataset` - Bulk creation
- `create_conversion_performance_dataset` - Conversion performance
- `create_nested_object_validation_dataset` - Nested performance

##### Error Testing (3)
- `create_systematic_error_scenarios` - Systematic errors
- `create_error_recovery_scenarios` - Error recovery
- `create_edge_case_error_scenarios` - Edge case errors

## Factory Usage Patterns Analysis

### High-Frequency Factory Usage
**Pattern**: Most used factory functions across test files

1. **Recipe Factories** (>100 usages)
   - `create_simple_api_recipe()` - Used in 40+ test methods
   - `create_complex_api_recipe()` - Used in 30+ test methods
   - `create_minimal_api_recipe()` - Used in 25+ test methods

2. **Meal Factories** (>80 usages)
   - `create_simple_api_meal()` - Used in 35+ test methods
   - `create_complex_api_meal()` - Used in 25+ test methods
   - `create_api_meal_with_max_recipes()` - Used in 20+ test methods

### Medium-Frequency Factory Usage
**Pattern**: Specialized factory functions used in specific test classes

1. **Edge Case Factories** (10-30 usages each)
   - Validation edge cases
   - Collection type conversions
   - Datetime handling
   - Text/security scenarios

2. **Performance Factories** (5-15 usages each)
   - Bulk operations
   - Stress testing
   - Performance benchmarking

### Low-Frequency Factory Usage
**Pattern**: Highly specialized factory functions used in 1-5 tests

1. **Extreme Edge Cases** (1-5 usages each)
   - Concurrency testing
   - Security testing
   - Boundary value testing

## Replacement Strategy

### Phase 1: High-Frequency Replacements
**Target**: Replace the most commonly used factory functions first

#### Recipe Test Data Constants
```python
# Replace create_simple_api_recipe()
SIMPLE_RECIPE_DATA = {
    "id": "test-recipe-1",
    "name": "Simple Test Recipe",
    "instructions": "Test instructions",
    # ... explicit fields
}

# Replace create_complex_api_recipe()
COMPLEX_RECIPE_DATA = {
    "id": "test-recipe-2",
    "name": "Complex Test Recipe",
    "ingredients": frozenset([...]),  # explicit ingredients
    "ratings": frozenset([...]),      # explicit ratings
    # ... explicit fields
}
```

#### Meal Test Data Constants
```python
# Replace create_simple_api_meal()
SIMPLE_MEAL_DATA = {
    "id": "test-meal-1",
    "name": "Simple Test Meal",
    "recipes": frozenset([...]),  # explicit recipes
    # ... explicit fields
}
```

### Phase 2: Medium-Frequency Replacements
**Target**: Replace specialized factory functions with explicit edge case data

#### Edge Case Test Data
```python
# Replace validation edge cases
INVALID_NAME_RECIPE_DATA = {
    **SIMPLE_RECIPE_DATA,
    "name": ""  # explicit invalid value
}

BOUNDARY_VALUE_RECIPE_DATA = {
    **SIMPLE_RECIPE_DATA,
    "total_time": 0,  # explicit boundary value
    "weight_in_grams": 1  # explicit boundary value
}
```

### Phase 3: Low-Frequency Replacements
**Target**: Replace highly specialized factory functions with targeted test data

#### Specialized Test Data
```python
# Replace performance/stress testing
LARGE_COLLECTION_RECIPE_DATA = {
    **SIMPLE_RECIPE_DATA,
    "ingredients": frozenset([...] * 100),  # explicit large collection
    "ratings": frozenset([...] * 50)        # explicit large collection
}
```

## Implementation Priority

### High Priority (Phase 1)
- [ ] `create_simple_api_recipe` → `SIMPLE_RECIPE_DATA`
- [ ] `create_complex_api_recipe` → `COMPLEX_RECIPE_DATA`
- [ ] `create_minimal_api_recipe` → `MINIMAL_RECIPE_DATA`
- [ ] `create_simple_api_meal` → `SIMPLE_MEAL_DATA`
- [ ] `create_complex_api_meal` → `COMPLEX_MEAL_DATA`

### Medium Priority (Phase 2)
- [ ] Field validation edge cases → explicit invalid data constants
- [ ] Collection type conversions → explicit collection data
- [ ] Computed property scenarios → explicit computed data

### Low Priority (Phase 3)
- [ ] Performance/stress testing → explicit performance data
- [ ] Security/text scenarios → explicit security data
- [ ] Datetime edge cases → explicit datetime data

## Success Metrics

### Dependency Reduction Targets
- **Recipe Tests**: 70+ factories → 15 explicit constants (79% reduction)
- **Meal Tests**: 50+ factories → 10 explicit constants (80% reduction)
- **Overall**: 120+ factory dependencies → 25 explicit constants (79% reduction)

### Code Quality Improvements
- **Explicit Test Data**: All test data visible in test methods
- **Reduced Coupling**: No external factory dependencies
- **Improved Debugging**: Clear test failure points
- **Better Maintainability**: Self-documenting test code

## Next Steps

1. **Task 0.2.1**: Create `test_data_constants.py` with high-priority constants
2. **Task 0.2.2**: Create edge case test data sets
3. **Task 0.2.3**: Create test data validation helpers
4. **Phase 1**: Begin systematic replacement of recipe test factories
5. **Phase 2**: Begin systematic replacement of meal test factories

This dependency map provides the foundation for systematic factory replacement throughout the refactoring process. 