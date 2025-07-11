# Phase 2: Conversion Logic Validation

---
phase: 2
estimated_time: 10 hours
---

## Objective
Validate to_domain() conversion methods and ensure exclude_unset=True logic works correctly for partial updates.

# Tasks

## 2.1 ApiUpdateMeal to_domain() Testing
- [x] 2.1.1 Create TestApiUpdateMealConversion class
  - Files: `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_update_meal_conversion.py`
  - Purpose: Set up test structure for conversion logic
  - Reference: Follow patterns from `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/root_aggregate/test_api_meal_core.py`
- [x] 2.1.2 Test basic UpdateMeal command creation
  - Files: `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_update_meal_conversion.py`
  - Purpose: Verify ApiUpdateMeal.to_domain() returns valid UpdateMeal
  - Use: `create_api_meal()` from api_meal_data_factories.py
- [x] 2.1.3 Test with various meal configurations
  - Files: `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_update_meal_conversion.py`
  - Purpose: Validate conversion across different meal types
  - Use: `REALISTIC_MEAL_SCENARIOS` and meal type variants from api_meal_data_factories.py

## 2.2 ApiAttributesToUpdateOnMeal Testing
- [x] 2.2.1 Create TestApiAttributesToUpdateOnMealExcludeUnset class
  - Files: `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_update_meal_exclude_unset.py`
  - Purpose: Focus on exclude_unset behavior testing
  - Reference: Validation patterns from `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/root_aggregate/test_api_meal_validation.py`
- [x] 2.2.2 Test partial field updates
  - Files: `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_update_meal_exclude_unset.py`
  - Purpose: Verify only set fields are included in updates
  - Use: `create_boundary_value_test_cases()` from api_meal_data_factories.py
- [x] 2.2.3 Test None vs unset field handling
  - Files: `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_update_meal_exclude_unset.py`
  - Purpose: Distinguish between explicitly set None and unset fields
  - Use: `create_minimal_api_meal()` vs `create_api_meal()` from api_meal_data_factories.py

## 2.3 Conversion Logic Edge Cases
- [x] 2.3.1 Test with empty/minimal updates
  - Files: `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_update_meal_conversion.py`
  - Purpose: Handle edge cases with minimal data
  - Use: `create_minimal_api_meal()` from api_meal_data_factories.py
- [x] 2.3.2 Test complex nested object conversion
  - Files: `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_update_meal_conversion.py`
  - Purpose: Validate nested objects convert correctly
  - Use: `create_complex_api_meal()` and `create_api_meal_with_max_recipes()` from api_meal_data_factories.py
- [x] 2.3.3 Test UUID field validation
  - Files: `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_update_meal_conversion.py`
  - Purpose: Ensure UUID fields are handled properly
  - Use: `create_type_conversion_test_scenarios()` from api_meal_data_factories.py

## 2.4 UpdateMeal Command Structure Validation
- [x] 2.4.1 Validate command structure consistency
  - Files: `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_update_meal_conversion.py`
  - Purpose: Ensure generated commands match expected structure
  - Use: `create_conversion_method_test_scenarios()` from api_meal_data_factories.py
- [x] 2.4.2 Test command field types
  - Files: `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_update_meal_conversion.py`
  - Purpose: Verify all field types are correctly converted
  - Use: `create_type_conversion_test_scenarios()` from api_meal_data_factories.py
- [x] 2.4.3 Test frozen set handling
  - Files: `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_update_meal_conversion.py`
  - Purpose: Validate frozen set conversion for recipe IDs
  - Use: Collection conversion scenarios from api_meal_data_factories.py

## Key Resources to Leverage
- **Data Factories**: Use `api_meal_data_factories.py` functions:
  - `create_api_meal()` - Basic meal creation
  - `create_minimal_api_meal()` - Minimal field testing
  - `create_complex_api_meal()` - Complex nested objects
  - `create_boundary_value_test_cases()` - Boundary testing
  - `create_type_conversion_test_scenarios()` - Type conversion testing
  - `create_conversion_method_test_scenarios()` - Conversion testing

- **Existing Test Patterns**: Reference from root_aggregate tests:
  - `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/root_aggregate/test_api_meal_core.py` - Core testing patterns
  - `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/root_aggregate/test_api_meal_validation.py` - Validation patterns

## Validation
- [x] Tests: `poetry run python pytest /tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_update_meal_conversion.py -v`
- [x] Tests: `poetry run python pytest /tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_update_meal_exclude_unset.py -v`
- [x] Verify exclude_unset logic works correctly
- [x] All conversion methods produce valid domain objects
- [x] All boundary value test cases pass
- [x] All type conversion scenarios work correctly

## Completion Summary

### ✅ Completed Tasks (12/12)
- **2.1.1-2.1.3**: ApiUpdateMeal to_domain() Testing ✅
- **2.2.1-2.2.3**: ApiAttributesToUpdateOnMeal Testing ✅
- **2.3.1-2.3.3**: Conversion Logic Edge Cases ✅
- **2.4.1-2.4.3**: UpdateMeal Command Structure Validation ✅

### 📊 Test Coverage Achieved
- **Total Tests Created**: 43 tests (23 in conversion + 20 in exclude_unset)
- **Success Rate**: 100% (43/43 passing)
- **Execution Time**: ~30 seconds total
- **Coverage Areas**:
  - Basic and complex conversion logic
  - Edge cases (minimal data, large collections, UUID validation)
  - Command structure validation and consistency
  - Frozen set handling and type conversions
  - Exclude_unset behavior testing
  - Comprehensive field type validation

### 🚧 Pending Tasks (0/12)
All Phase 2 tasks completed successfully.

## Phase 2 Complete ✅

**Phase Status**: COMPLETED
**Completion Date**: 2024-01-15
**Total Test Count**: 43 tests
**Test Success Rate**: 100%
**All Tasks Validated**: ✅

Ready to proceed to Phase 3. 