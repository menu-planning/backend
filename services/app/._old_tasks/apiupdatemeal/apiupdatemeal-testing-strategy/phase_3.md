# Phase 3: Error Handling & Integration

---
phase: 3
estimated_time: 8 hours
---

## Objective
Implement comprehensive error handling tests and validate seamless integration with domain layer Meal.update_properties() method.

# Tasks

## 3.1 Error Handling Testing
- [x] 3.1.1 Create TestApiUpdateMealErrorHandling class
  - Files: `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_update_meal_error_handling.py`
  - Purpose: Set up error scenario testing structure
  - Reference: Error handling patterns from `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/root_aggregate/test_api_meal_validation.py`
- [x] 3.1.2 Test conversion failure scenarios
  - Files: `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_update_meal_error_handling.py`
  - Purpose: Validate graceful handling of conversion failures
  - Use: `create_systematic_error_scenarios()` from api_meal_data_factories.py
- [x] 3.1.3 Test invalid input handling
  - Files: `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_update_meal_error_handling.py`
  - Purpose: Ensure proper error messages for invalid inputs
  - Use: `create_field_validation_test_suite()` and `create_comprehensive_validation_error_scenarios()` from api_meal_data_factories.py

## 3.2 Domain Integration Testing
- [x] 3.2.1 Create TestApiUpdateMealDomainIntegration class
  - Files: `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_update_meal_domain_integration.py`
  - Purpose: Test integration with Meal.update_properties()
  - Reference: Domain integration patterns from `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/root_aggregate/test_api_meal_core.py`
- [x] 3.2.2 Test end-to-end update flow
  - Files: `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_update_meal_domain_integration.py`
  - Purpose: Validate full update pipeline works correctly
  - Use: `create_round_trip_consistency_test_scenarios()` from api_meal_data_factories.py
- [x] 3.2.3 Test all property types handling
  - Files: `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_update_meal_domain_integration.py`
  - Purpose: Ensure all property types (str, bool, list, set) work
  - Use: `create_type_conversion_test_scenarios()` from api_meal_data_factories.py

## 3.3 Business Rules Validation
- [x] 3.3.1 Test business rule preservation
  - Files: `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_update_meal_domain_integration.py`
  - Purpose: Verify domain business rules are maintained
  - Use: `create_api_meal_with_incorrect_computed_properties()` to test computed property correction
- [x] 3.3.2 Test version increment behavior
  - Files: `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_update_meal_domain_integration.py`
  - Purpose: Validate version increments on updates
  - Use: `create_api_meal()` with version tracking from api_meal_data_factories.py
- [x] 3.3.3 Test event generation verification
  - Files: `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_update_meal_domain_integration.py`
  - Purpose: Ensure domain events are properly generated
  - Reference: Event testing patterns from existing root_aggregate tests

## 3.4 Final Integration & Cleanup
- [x] 3.4.1 Run comprehensive test suite
  - Files: All test files in `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/`
  - Purpose: Validate all tests pass together
  - Use: `create_comprehensive_test_suite()` from api_meal_data_factories.py
- [x] 3.4.2 Add conftest.py if needed
  - Files: `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/conftest.py`
  - Purpose: Add shared fixtures for complex scenarios
  - Reference: Existing conftest.py at `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/root_aggregate/conftest.py`
- [x] 3.4.3 Performance validation
  - Files: All test files in `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/`
  - Purpose: Ensure tests execute within 30 seconds locally
  - Use: `create_extreme_performance_scenarios()` from api_meal_data_factories.py

## 3.5 Documentation & Final Validation
- [x] 3.5.1 Add docstrings to test classes
  - Files: All test files in `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/`
  - Purpose: Document test purpose and approach
  - Reference: Documentation patterns from `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/root_aggregate/test_api_meal_performance.py`
- [x] 3.5.2 Final coverage check
  - Files: All test files in `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/`
  - Purpose: Verify 100% coverage of target classes
  - Use: `get_test_coverage_report()` from api_meal_data_factories.py

## Key Resources to Leverage
- **Data Factories**: Use `api_meal_data_factories.py` functions:
  - `create_systematic_error_scenarios()` - Comprehensive error testing
  - `create_field_validation_test_suite()` - Field validation errors
  - `create_comprehensive_validation_error_scenarios()` - Validation error scenarios
  - `create_round_trip_consistency_test_scenarios()` - Round-trip testing
  - `create_type_conversion_test_scenarios()` - Type conversion testing
  - `create_comprehensive_test_suite()` - Full test suite
  - `create_extreme_performance_scenarios()` - Performance testing
  - `get_test_coverage_report()` - Coverage analysis

- **Existing Test Patterns**: Reference from root_aggregate tests:
  - `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/root_aggregate/test_api_meal_validation.py` - Error handling patterns
  - `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/root_aggregate/test_api_meal_core.py` - Domain integration patterns
  - `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/root_aggregate/test_api_meal_performance.py` - Performance testing patterns
  - `/tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/root_aggregate/conftest.py` - Fixture patterns

## Validation
- [ ] Tests: `poetry run python pytest /tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/ -v`
- [ ] Coverage: `poetry run python pytest /tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/ --cov`
- [ ] Performance: Test execution under 30 seconds
- [ ] All error scenarios handled gracefully
- [ ] Domain integration works seamlessly
- [ ] All systematic error scenarios from data factories pass
- [ ] Round-trip consistency validation passes
- [ ] Comprehensive test suite validation passes 