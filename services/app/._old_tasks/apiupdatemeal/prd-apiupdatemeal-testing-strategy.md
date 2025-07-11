# PRD: ApiUpdateMeal Testing Strategy

---
feature: apiupdatemeal-testing-strategy
complexity: standard
created: 2024-12-19
---

## Overview
**Problem**: ApiUpdateMeal class lacks comprehensive test coverage while existing ApiMeal tests are extensive and well-structured
**Solution**: Create focused test suite leveraging existing ApiMeal fixtures, emphasizing unique ApiUpdateMeal functionality
**Value**: Ensures API reliability for meal updates and prevents regressions in critical conversion logic

## Goals & Scope
### Goals
1. Validate ApiUpdateMeal factory method (`from_api_meal()`) with existing fixtures
2. Ensure proper domain command creation via `to_domain()` methods
3. Verify `exclude_unset=True` logic in `ApiAttributesToUpdateOnMeal`
4. Validate seamless integration with `Meal.update_properties()` method
5. Establish comprehensive error handling for conversion failures

### Out of Scope
1. Comprehensive field validation (covered by existing ApiMeal tests)
2. Direct construction testing (minimal, error cases only)
3. Performance benchmarking or load testing
4. CI/CD pipeline integration (not available)

## User Stories
### Story 1: Factory Method Validation
**As a** developer **I want** to verify `from_api_meal()` works with all existing ApiMeal fixtures **So that** I can trust the conversion process
- [ ] All ApiMeal test fixtures successfully convert to ApiUpdateMeal
- [ ] Field mapping is accurate and complete
- [ ] Edge cases (empty recipes, max recipes, complex meals) are handled

### Story 2: Domain Command Creation
**As a** developer **I want** to ensure `to_domain()` creates valid UpdateMeal commands **So that** the domain layer receives properly formatted data
- [ ] `ApiUpdateMeal.to_domain()` returns valid UpdateMeal command
- [ ] `ApiAttributesToUpdateOnMeal.to_domain()` respects `exclude_unset=True`
- [ ] Only modified fields are included in updates dictionary

### Story 3: Domain Integration
**As a** developer **I want** to verify updates work with `Meal.update_properties()` **So that** the full update flow functions correctly
- [ ] Generated updates dictionary works with domain method
- [ ] All property types are handled correctly
- [ ] Business rules and validation are preserved

## Technical Requirements
### Architecture
- Test classes organized by functionality area
- Integration with existing ApiMeal test infrastructure
- Reuse of comprehensive ApiMeal fixtures and data factories
- Isolation of ApiUpdateMeal-specific logic testing

### Data Requirements
- Access to existing ApiMeal test fixtures in `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/root_aggregate/`
- Test data covering edge cases: empty recipes, maximum recipes, complex nutritional data
- Error scenario data for validation testing

### Integration Points
- Existing ApiMeal test suite and fixtures
- Domain layer `Meal.update_properties()` method
- Pydantic validation system
- UpdateMeal command structure

## Functional Requirements
1. **Factory Method Testing**: `from_api_meal()` must work with all existing ApiMeal fixtures
2. **Conversion Logic Testing**: `to_domain()` methods must create valid domain objects
3. **Exclude Unset Logic**: Only explicitly set fields should be included in updates
4. **Error Handling**: Conversion failures must be properly caught and reported
5. **Domain Integration**: Updates must work seamlessly with `Meal.update_properties()`

## Quality Requirements
- **Test Coverage**: 100% coverage of ApiUpdateMeal and ApiAttributesToUpdateOnMeal methods
- **Integration**: All existing ApiMeal fixtures must work with new tests
- **Maintainability**: Tests must be easy to understand and modify
- **Performance**: Tests should execute quickly in local environment

## Testing Approach
### Core Test Classes Structure
```python
class TestApiUpdateMealFromApiMeal:
    # Primary tests using existing ApiMeal fixtures
    # Test factory method with various meal configurations
    
class TestApiUpdateMealConversion:
    # Test to_domain() conversion logic
    # Validate UpdateMeal command creation
    
class TestApiAttributesToUpdateOnMealExcludeUnset:
    # Test exclude_unset=True behavior specifically
    # Verify only set fields are included
    
class TestApiUpdateMealErrorHandling:
    # Test exception scenarios and error messages
    # Validate graceful failure handling

class TestApiUpdateMealDomainIntegration:
    # Test integration with Meal.update_properties()
    # Validate end-to-end update flow
```

### Testing Strategy
- **Unit Tests**: Focus on individual method behavior
- **Integration Tests**: Verify interaction with existing fixtures
- **Error Scenario Tests**: Validate exception handling
- **Domain Integration Tests**: Ensure compatibility with domain layer

## Implementation Phases
### Phase 1: Core Factory Method Testing
- [ ] Set up test infrastructure and imports
- [ ] Implement `TestApiUpdateMealFromApiMeal` class
- [ ] Test with basic ApiMeal fixtures
- [ ] Test with complex meal configurations
- [ ] Test with edge cases (empty recipes, max recipes)

### Phase 2: Conversion Logic Validation
- [ ] Implement `TestApiUpdateMealConversion` class
- [ ] Test `ApiUpdateMeal.to_domain()` method
- [ ] Test `ApiAttributesToUpdateOnMeal.to_domain()` method
- [ ] Validate exclude_unset behavior
- [ ] Test UpdateMeal command structure

### Phase 3: Error Handling & Integration
- [ ] Implement `TestApiUpdateMealErrorHandling` class
- [ ] Test conversion failure scenarios
- [ ] Test invalid input handling
- [ ] Implement `TestApiUpdateMealDomainIntegration` class
- [ ] Test with `Meal.update_properties()` method

## Success Metrics
- All existing ApiMeal fixtures work with ApiUpdateMeal factory method
- 100% test coverage of ApiUpdateMeal and ApiAttributesToUpdateOnMeal classes
- Zero test failures in integration with domain layer
- Clear error messages for all failure scenarios
- Tests execute in under 30 seconds locally

## Risks & Mitigation
- **Risk**: Existing ApiMeal fixtures may not cover all edge cases
  **Mitigation**: Review fixture coverage and add specific test cases for ApiUpdateMeal
- **Risk**: Domain integration may reveal unexpected validation issues
  **Mitigation**: Test with actual domain objects and validate business rules
- **Risk**: Exclude_unset logic may be complex to test thoroughly
  **Mitigation**: Create specific test scenarios with partial field updates

## Dependencies
- Existing ApiMeal test fixtures and data factories
- Access to domain layer Meal class and methods
- Pydantic testing utilities
- Current test infrastructure and patterns

## Key Test Scenarios
### Factory Method Edge Cases
- Empty recipes list
- Maximum number of recipes
- Complex nutritional data
- All optional fields None vs unset
- Nested object validation

### Conversion Logic Edge Cases
- Partial field updates
- None vs unset field handling
- Complex nested object conversion
- UUID field validation
- Frozen set handling

### Domain Integration Scenarios
- All property types (str, bool, list, set, etc.)
- Business rule validation
- Version increment behavior
- Event generation verification
- Cache invalidation testing

## File Structure
```
tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/
├── test_api_update_meal_factory.py
├── test_api_update_meal_conversion.py
├── test_api_update_meal_exclude_unset.py
├── test_api_update_meal_error_handling.py
├── test_api_update_meal_domain_integration.py
└── conftest.py  # Additional fixtures if needed
``` 