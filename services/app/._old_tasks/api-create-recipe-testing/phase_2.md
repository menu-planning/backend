# Phase 2: Domain Conversion & Complex Fields Testing

---
phase: 2
estimated_time: 10 hours
---

## Objective
Validate to_domain() conversion method and ensure complex nested objects (ingredients, tags, nutri_facts) convert correctly to CreateRecipe domain command.

# Tasks

## 2.1 Domain Conversion Testing
- [ ] 2.1.1 Create TestApiCreateRecipeConversion class
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_conversion.py`
  - Purpose: Set up test structure for domain conversion logic
  - Reference: Follow patterns from existing test structures
  - Dependencies: Import from `api_recipe_data_factories.py`
- [ ] 2.1.2 Test basic to_domain() conversion
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_conversion.py`
  - Purpose: Verify ApiCreateRecipe.to_domain() returns valid CreateRecipe command
  - Test cases: minimal required fields, all fields populated
  - Use: `create_api_recipe()` and `create_simple_api_recipe()` from api_recipe_data_factories.py
- [ ] 2.1.3 Test CreateRecipe command structure
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_conversion.py`
  - Purpose: Validate generated command structure and field mapping
  - Test cases: field accuracy, data type preservation, command completeness
  - Use: `validate_round_trip_conversion()` from api_recipe_data_factories.py

## 2.2 Complex Fields Testing Setup
- [ ] 2.2.1 Create TestApiCreateRecipeComplexFields class
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_complex_fields.py`
  - Purpose: Focus on complex nested objects testing
  - Include: ingredients, tags, nutri_facts validation
  - Dependencies: Import from `api_recipe_data_factories.py`
- [ ] 2.2.2 Set up complex field test fixtures
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/conftest.py`
  - Purpose: Create test data for complex nested objects
  - Include: valid ingredients, various tag combinations, nutri_facts scenarios
  - Use: `create_complex_api_recipe()` and `create_api_recipe_with_deeply_nested_data()` from api_recipe_data_factories.py

## 2.3 Ingredients Field Testing
- [ ] 2.3.1 Test ingredients frozenset conversion
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_complex_fields.py`
  - Purpose: Validate ingredients list to frozenset conversion
  - Test cases: valid ingredients, empty ingredients, duplicate ingredients
  - Use: `create_api_recipe_with_list_ingredients()` and `create_api_recipe_with_empty_collections()` from api_recipe_data_factories.py
- [ ] 2.3.2 Test ingredients field validation
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_complex_fields.py`
  - Purpose: Validate individual ingredient data structure
  - Test cases: required ingredient fields, optional fields, invalid formats
  - Use: `create_api_recipe_with_invalid_ingredient_positions()` from api_recipe_data_factories.py
- [ ] 2.3.3 Test ingredients edge cases
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_complex_fields.py`
  - Purpose: Handle edge cases in ingredients processing
  - Test cases: maximum ingredient count, empty ingredient objects, malformed data
  - Use: `create_api_recipe_with_massive_collections()` from api_recipe_data_factories.py

## 2.4 Tags Field Testing
- [ ] 2.4.1 Test tags frozenset conversion
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_complex_fields.py`
  - Purpose: Validate tags list to frozenset conversion
  - Test cases: valid tags, empty tags, duplicate tags
  - Use: `create_api_recipe_with_list_tags()` and `create_api_recipe_with_empty_collections()` from api_recipe_data_factories.py
- [ ] 2.4.2 Test tags field validation
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_complex_fields.py`
  - Purpose: Validate individual tag data structure
  - Test cases: required tag fields, tag format validation, invalid tag data
  - Use: `create_api_recipe_with_invalid_tag_dict()` and `create_api_recipe_with_mixed_tag_types()` from api_recipe_data_factories.py
- [ ] 2.4.3 Test tags edge cases
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_complex_fields.py`
  - Purpose: Handle edge cases in tags processing
  - Test cases: maximum tag count, empty tag objects, special characters
  - Use: `create_api_recipe_with_invalid_tag_author_id()` from api_recipe_data_factories.py

## 2.5 Nutri_Facts Field Testing
- [ ] 2.5.1 Test nutri_facts optional object conversion
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_complex_fields.py`
  - Purpose: Validate optional nutri_facts object handling
  - Test cases: valid nutri_facts, null nutri_facts, empty nutri_facts
  - Use: `create_api_recipe_with_none_values()` and `create_complex_api_recipe()` from api_recipe_data_factories.py
- [ ] 2.5.2 Test nutri_facts field validation
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_complex_fields.py`
  - Purpose: Validate nutri_facts object structure
  - Test cases: required nutri_facts fields, data types, value ranges
  - Use: `create_api_recipe_with_deeply_nested_data()` from api_recipe_data_factories.py
- [ ] 2.5.3 Test nutri_facts edge cases
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_complex_fields.py`
  - Purpose: Handle edge cases in nutri_facts processing
  - Test cases: negative values, extreme values, missing fields
  - Use: `create_api_recipe_with_boundary_values()` from api_recipe_data_factories.py

## 2.6 Data Integrity Testing
- [ ] 2.6.1 Test data preservation during conversion
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_conversion.py`
  - Purpose: Ensure no data loss during domain conversion
  - Test cases: field completeness, data accuracy, type preservation
  - Use: `validate_round_trip_conversion()` and `validate_json_serialization()` from api_recipe_data_factories.py
- [ ] 2.6.2 Test complex object data integrity
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_complex_fields.py`
  - Purpose: Validate complex nested objects maintain integrity
  - Test cases: ingredient data preservation, tag data preservation, nutri_facts accuracy
  - Use: `create_nested_object_validation_dataset()` from api_recipe_data_factories.py
- [ ] 2.6.3 Test conversion consistency
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_conversion.py`
  - Purpose: Ensure consistent conversion behavior
  - Test cases: multiple conversion calls, various input combinations
  - Use: `REALISTIC_RECIPE_SCENARIOS` from api_recipe_data_factories.py

## Key Resources to Leverage
- **Data Factories**: Use `api_recipe_data_factories.py` functions:
  - `create_api_recipe()` - Basic recipe creation
  - `create_simple_api_recipe()` - Simple recipe scenarios
  - `create_complex_api_recipe()` - Complex nested objects
  - `create_api_recipe_with_list_*()` - Collection conversion testing
  - `create_api_recipe_with_empty_collections()` - Empty collections testing
  - `create_api_recipe_with_massive_collections()` - Performance testing
  - `create_api_recipe_with_deeply_nested_data()` - Complex nested testing
  - `create_nested_object_validation_dataset()` - Comprehensive validation

- **Conversion Testing**: Use conversion and validation utilities:
  - `validate_round_trip_conversion()` - Complete round-trip testing
  - `validate_json_serialization()` - JSON serialization testing
  - `validate_orm_conversion()` - ORM conversion testing

- **Realistic Data**: Use `REALISTIC_RECIPE_SCENARIOS` from data factories for comprehensive testing

## Validation
- [ ] Tests: `poetry run python -m pytest tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_conversion.py -v`
- [ ] Tests: `poetry run python -m pytest tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_complex_fields.py -v`
- [ ] Verify to_domain() method coverage using existing validation utilities
- [ ] All complex field conversions work correctly using existing test datasets
- [ ] Data integrity maintained across conversions using existing validation functions
- [ ] Frozenset conversions for ingredients and tags using existing collection testing

## Success Criteria
- All domain conversion tests pass
- Complex nested objects convert without data loss using existing validation
- Frozenset handling works correctly with existing collection test scenarios
- CreateRecipe command structure validated using existing conversion utilities
- No performance degradation with complex data using existing performance datasets
- Test execution under 15 seconds
- All existing conversion utilities from `api_recipe_data_factories.py` successfully integrated 