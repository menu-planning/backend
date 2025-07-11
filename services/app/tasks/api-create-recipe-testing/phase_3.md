# Phase 3: Error Handling & Integration Testing

---
phase: 3
estimated_time: 8 hours
---

## Objective
Validate error handling for invalid inputs and conversion failures, and ensure seamless integration with CreateRecipe domain command structure.

# Tasks

## 3.1 Error Handling Testing Setup
- [ ] 3.1.1 Create TestApiCreateRecipeErrorHandling class
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_error_handling.py`
  - Purpose: Set up test structure for error handling validation
  - Include: ValueError scenarios, conversion failures, invalid input handling
  - Dependencies: Import from `api_recipe_data_factories.py`
- [ ] 3.1.2 Set up error scenario test fixtures
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/conftest.py`
  - Purpose: Create test data for error scenarios
  - Include: invalid field values, malformed data, edge case failures
  - Use: `create_comprehensive_validation_test_cases()` from api_recipe_data_factories.py

## 3.2 Field Validation Error Testing
- [ ] 3.2.1 Test required field validation errors
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_error_handling.py`
  - Purpose: Validate error messages for missing required fields
  - Test cases: missing name, missing instructions, missing author_id, missing meal_id
  - Use: `create_api_recipe_with_invalid_name()` and `create_api_recipe_with_invalid_instructions()` from api_recipe_data_factories.py
- [ ] 3.2.2 Test UUID format validation errors
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_error_handling.py`
  - Purpose: Validate error handling for invalid UUID formats
  - Test cases: invalid author_id UUID, invalid meal_id UUID, malformed UUIDs
  - Use: `create_api_recipe_kwargs()` with invalid UUID scenarios from api_recipe_data_factories.py
- [ ] 3.2.3 Test field type validation errors
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_error_handling.py`
  - Purpose: Validate error handling for wrong field types
  - Test cases: string fields with numbers, numeric fields with strings, type mismatches
  - Use: `create_api_recipe_with_invalid_total_time()` and `create_api_recipe_with_invalid_weight()` from api_recipe_data_factories.py

## 3.3 Complex Field Error Testing
- [ ] 3.3.1 Test ingredients validation errors
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_error_handling.py`
  - Purpose: Validate error handling for malformed ingredients
  - Test cases: invalid ingredient structure, missing ingredient fields, malformed ingredient data
  - Use: `create_api_recipe_with_invalid_ingredient_positions()` and `create_api_recipe_with_negative_ingredient_positions()` from api_recipe_data_factories.py
- [ ] 3.3.2 Test tags validation errors
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_error_handling.py`
  - Purpose: Validate error handling for malformed tags
  - Test cases: invalid tag structure, missing tag fields, malformed tag data
  - Use: `create_api_recipe_with_invalid_tag_dict()` and `create_api_recipe_with_invalid_tag_types()` from api_recipe_data_factories.py
- [ ] 3.3.3 Test nutri_facts validation errors
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_error_handling.py`
  - Purpose: Validate error handling for malformed nutri_facts
  - Test cases: invalid nutri_facts structure, negative values, missing fields
  - Use: `create_api_recipe_with_boundary_values()` and `create_api_recipe_with_extreme_boundary_values()` from api_recipe_data_factories.py

## 3.4 Conversion Error Testing
- [ ] 3.4.1 Test to_domain() conversion failures
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_error_handling.py`
  - Purpose: Validate error handling during domain conversion
  - Test cases: conversion failures, ValueError scenarios, descriptive error messages
  - Use: `validate_round_trip_conversion()` with invalid data from api_recipe_data_factories.py
- [ ] 3.4.2 Test frozenset conversion errors
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_error_handling.py`
  - Purpose: Validate error handling for frozenset conversion failures
  - Test cases: ingredients frozenset errors, tags frozenset errors, unhashable type errors
  - Use: `create_api_recipe_with_invalid_tag_types()` from api_recipe_data_factories.py
- [ ] 3.4.3 Test privacy enum conversion errors
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_error_handling.py`
  - Purpose: Validate error handling for privacy enum conversion
  - Test cases: invalid enum values, enum conversion failures, default fallback testing
  - Use: `create_api_recipe_with_invalid_privacy()` from api_recipe_data_factories.py

## 3.5 Integration Testing Setup
- [ ] 3.5.1 Create TestApiCreateRecipeIntegration class
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_integration.py`
  - Purpose: Set up test structure for integration validation
  - Include: CreateRecipe command testing, end-to-end validation
  - Dependencies: Import from `api_recipe_data_factories.py`
- [ ] 3.5.2 Test CreateRecipe command integration
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_integration.py`
  - Purpose: Validate integration with CreateRecipe domain command
  - Test cases: command creation, field mapping, business rule validation
  - Use: `create_recipe_collection()` from api_recipe_data_factories.py

## 3.6 End-to-End Integration Testing
- [ ] 3.6.1 Test complete recipe creation flow
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_integration.py`
  - Purpose: Validate end-to-end recipe creation process
  - Test cases: full recipe creation, complex recipe scenarios, minimal recipe scenarios
  - Use: `REALISTIC_RECIPE_SCENARIOS` and `create_test_recipe_dataset()` from api_recipe_data_factories.py
- [ ] 3.6.2 Test domain command structure validation
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_integration.py`
  - Purpose: Ensure generated commands meet domain requirements
  - Test cases: command structure, field completeness, business rule compliance
  - Use: `validate_round_trip_conversion()` and `validate_orm_conversion()` from api_recipe_data_factories.py
- [ ] 3.6.3 Test integration with existing domain logic
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_integration.py`
  - Purpose: Validate compatibility with existing domain layer
  - Test cases: domain layer integration, business rule validation, edge case handling
  - Use: `create_recipe_domain_from_api()` and `create_api_recipe_from_domain()` from api_recipe_data_factories.py

## 3.7 Error Message Quality Testing
- [ ] 3.7.1 Test error message descriptiveness
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_error_handling.py`
  - Purpose: Ensure error messages are clear and helpful
  - Test cases: field-specific errors, clear error descriptions, actionable error messages
  - Use: `create_comprehensive_validation_test_cases()` from api_recipe_data_factories.py
- [ ] 3.7.2 Test error message consistency
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_error_handling.py`
  - Purpose: Validate consistent error message format
  - Test cases: error message structure, consistent terminology, error categorization
  - Use: `create_api_recipe_with_unicode_text()` and `create_api_recipe_with_special_characters()` from api_recipe_data_factories.py
- [ ] 3.7.3 Test error context information
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_error_handling.py`
  - Purpose: Ensure error messages include relevant context
  - Test cases: field names in errors, problematic values, suggested fixes
  - Use: `create_api_recipe_with_html_characters()` and `create_api_recipe_with_sql_injection()` from api_recipe_data_factories.py

## Key Resources to Leverage
- **Error Scenario Generators**: Use `api_recipe_data_factories.py` functions:
  - `create_comprehensive_validation_test_cases()` - Complete validation scenarios
  - `create_api_recipe_with_invalid_*()` - Invalid field testing
  - `create_api_recipe_with_boundary_values()` - Boundary testing
  - `create_api_recipe_with_extreme_boundary_values()` - Extreme value testing
  - `create_api_recipe_with_unicode_text()` - Unicode testing
  - `create_api_recipe_with_special_characters()` - Special character testing
  - `create_api_recipe_with_html_characters()` - HTML/XSS testing
  - `create_api_recipe_with_sql_injection()` - SQL injection testing

- **Integration Testing**: Use integration and validation utilities:
  - `validate_round_trip_conversion()` - Complete round-trip testing
  - `validate_orm_conversion()` - ORM conversion testing
  - `validate_json_serialization()` - JSON serialization testing
  - `create_recipe_domain_from_api()` - Domain conversion testing
  - `create_api_recipe_from_domain()` - Reverse domain conversion

- **Realistic Test Data**: Use comprehensive test datasets:
  - `REALISTIC_RECIPE_SCENARIOS` - 5 realistic recipe scenarios
  - `create_test_recipe_dataset()` - Performance testing dataset
  - `create_recipe_collection()` - Collection testing
  - `create_stress_test_dataset()` - Stress testing scenarios

## Validation
- [ ] Tests: `poetry run python -m pytest tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_error_handling.py -v`
- [ ] Tests: `poetry run python -m pytest tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_integration.py -v`
- [ ] Tests: `poetry run python -m pytest tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/ -v`
- [ ] Verify all error scenarios are handled gracefully using existing error scenario generators
- [ ] All error messages are descriptive and helpful using existing validation utilities
- [ ] Integration with CreateRecipe domain command works correctly using existing conversion utilities
- [ ] 100% test coverage achieved using comprehensive test datasets

## Success Criteria
- All error handling tests pass
- Error messages are descriptive and actionable using existing validation
- Integration with domain layer is seamless using existing conversion utilities
- No unhandled exceptions in error scenarios using comprehensive error datasets
- CreateRecipe command structure validated using existing domain conversion testing
- Complete test coverage of ApiCreateRecipe class using existing comprehensive test scenarios
- All tests execute in under 30 seconds total
- All existing error handling and integration utilities from `api_recipe_data_factories.py` successfully integrated

## Final Validation
- [ ] Full test suite execution: `poetry run python -m pytest tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/ -v --cov`
- [ ] Coverage report generation and 100% coverage verification using existing coverage utilities
- [ ] Performance validation (all tests under 30 seconds) using existing performance datasets
- [ ] Integration validation with existing test infrastructure using existing validation patterns 