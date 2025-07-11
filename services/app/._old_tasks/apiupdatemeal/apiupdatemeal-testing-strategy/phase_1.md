# Phase 1: Core Factory Method Testing

---
phase: 1
estimated_time: 8 hours
---

## Objective
Set up test infrastructure and validate ApiUpdateMeal.from_api_meal() factory method with existing ApiMeal fixtures, ensuring conversion works for all meal configurations.

# Tasks

## 1.1 Test Infrastructure Setup
- [x] 1.1.1 Create test directory structure
  - Files: `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/`
  - Purpose: Organize test files according to existing pattern
- [x] 1.1.2 Set up imports and basic test infrastructure
  - Files: `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_update_meal_factory.py`
  - Purpose: Import required modules and set up TestApiUpdateMealFromApiMeal class
  - Dependencies: Import from `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/root_aggregate/data_factories/api_meal_data_factories.py`

## 1.2 Basic Factory Method Tests
- [x] 1.2.1 Test with simple ApiMeal fixtures
  - Files: `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_update_meal_factory.py`
  - Purpose: Verify factory method works with basic meal configurations
  - Use: `create_simple_api_meal()` from api_meal_data_factories.py
- [x] 1.2.2 Test with complex meal configurations
  - Files: `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_update_meal_factory.py`
  - Purpose: Validate conversion with multiple recipes and complex data
  - Use: `create_complex_api_meal()` and `create_api_meal_with_max_recipes()` from api_meal_data_factories.py
- [x] 1.2.3 Test field mapping accuracy
  - Files: `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_update_meal_factory.py`
  - Purpose: Ensure all ApiMeal fields correctly map to ApiUpdateMeal
  - Use: `create_api_meal_kwargs()` with various field combinations

## 1.3 Edge Cases Testing
- [x] 1.3.1 Test with empty recipes list
  - Files: `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_update_meal_factory.py`
  - Purpose: Handle edge case of meals with no recipes
  - Use: `create_api_meal_without_recipes()` from api_meal_data_factories.py
- [x] 1.3.2 Test with maximum number of recipes
  - Files: `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_update_meal_factory.py`
  - Purpose: Validate performance and correctness with large recipe sets
  - Use: `create_api_meal_with_max_recipes()` from api_meal_data_factories.py
- [x] 1.3.3 Test with complex nutritional data
  - Files: `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_update_meal_factory.py`
  - Purpose: Ensure complex nested objects are handled correctly
  - Use: `create_api_meal_with_incorrect_computed_properties()` from api_meal_data_factories.py

## 1.4 Factory Method Validation
- [x] 1.4.1 Test all existing ApiMeal fixtures
  - Files: `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_update_meal_factory.py`
  - Purpose: Comprehensive validation against existing test data
  - Use: `REALISTIC_MEAL_SCENARIOS` and `create_meal_collection()` from api_meal_data_factories.py
- [x] 1.4.2 Validate created ApiUpdateMeal instances
  - Files: `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_update_meal_factory.py`
  - Purpose: Ensure factory output is valid and complete
  - Reference: Follow validation patterns from `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/root_aggregate/test_api_meal_validation.py`

## Key Resources to Leverage
- **Data Factories**: Use `api_meal_data_factories.py` functions:
  - `create_api_meal()` - Basic meal creation
  - `create_simple_api_meal()` - Simple meal scenarios
  - `create_complex_api_meal()` - Complex meal scenarios
  - `create_api_meal_without_recipes()` - Edge case testing
  - `create_api_meal_with_max_recipes()` - Performance testing
  - `REALISTIC_MEAL_SCENARIOS` - 10 realistic meal configurations

## Validation
- [x] Tests: `poetry run python -m pytest tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_update_meal_factory.py -v`
- [x] Coverage: Verify factory method coverage
- [x] All existing ApiMeal fixtures successfully convert to ApiUpdateMeal
- [x] All 10 realistic meal scenarios from `REALISTIC_MEAL_SCENARIOS` work correctly 

**Phase 1 Status: COMPLETED ✅**
**Completion Date**: 2024-01-15
**Artifacts Generated**: 
- phase_1_completion.json
- phase_1_factory_method_testing_report.md
- Updated shared_context.json

**Next Phase**: phase_2.md ready for execution 