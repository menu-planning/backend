# PRD: API Create Recipe Testing Strategy

---
feature: api-create-recipe-testing
complexity: standard
created: 2024-12-19
---

## Overview
**Problem**: ApiCreateRecipe class lacks comprehensive test coverage, creating risk for recipe creation failures and data corruption
**Solution**: Create focused test suite covering all ApiCreateRecipe functionality, validation logic, and domain conversion
**Value**: Ensures API reliability for recipe creation, prevents regressions, and maintains data integrity

## Goals & Scope
### Goals
1. Validate ApiCreateRecipe field validation with comprehensive test scenarios
2. Ensure proper domain command creation via `to_domain()` method
3. Verify error handling for invalid inputs and conversion failures
4. Test integration with CreateRecipe domain command structure
5. Establish 100% test coverage for all ApiCreateRecipe functionality

### Out of Scope
1. API endpoint testing (controller layer)
2. Database integration testing
3. Performance benchmarking or load testing
4. UI/frontend integration testing
5. Other recipe API classes (focus only on ApiCreateRecipe)

## User Stories
### Story 1: Field Validation Testing
**As a** developer **I want** to verify all ApiCreateRecipe fields validate correctly **So that** invalid recipe data is rejected before domain processing
- [ ] Required fields (name, instructions, author_id, meal_id, ingredients, tags) validation
- [ ] Optional fields (description, utensils, total_time, notes, privacy, nutri_facts, weight_in_grams, image_url) handling
- [ ] Data type validation for each field
- [ ] Edge cases (empty strings, null values, invalid formats)

### Story 2: Domain Command Creation
**As a** developer **I want** to ensure `to_domain()` creates valid CreateRecipe commands **So that** the domain layer receives properly formatted data
- [ ] `ApiCreateRecipe.to_domain()` returns valid CreateRecipe command
- [ ] All field mappings are accurate and complete
- [ ] Complex nested objects (ingredients, tags, nutri_facts) convert correctly
- [ ] Privacy enum handling with default fallback

### Story 3: Error Handling Validation
**As a** developer **I want** to verify error handling for invalid inputs **So that** conversion failures are properly reported
- [ ] ValueError raised for conversion failures with descriptive messages
- [ ] Invalid UUID format handling
- [ ] Malformed ingredient and tag data handling
- [ ] Edge cases for optional field conversion

## Technical Requirements
### Architecture
- Test classes organized by functionality area
- Comprehensive test data fixtures for various recipe scenarios
- Integration with existing test infrastructure patterns
- Isolation of ApiCreateRecipe-specific logic testing

### Data Requirements
- Test fixtures covering all field combinations
- Edge case data: empty ingredients, maximum field lengths, invalid formats
- Valid domain object examples for comparison
- Error scenario data for validation testing

### Integration Points
- CreateRecipe domain command structure
- Pydantic validation system
- Recipe field validation classes (RecipeNameRequired, etc.)
- Privacy enum and default value handling

## Functional Requirements
1. **Field Validation Testing**: All ApiCreateRecipe fields must validate according to their type definitions
2. **Domain Conversion Testing**: `to_domain()` method must create valid CreateRecipe commands
3. **Error Handling Testing**: Conversion failures must be properly caught and reported
4. **Data Integrity Testing**: Complex nested objects must convert without data loss
5. **Default Value Testing**: Optional fields and privacy defaults must work correctly

## Quality Requirements
- **Test Coverage**: 100% coverage of ApiCreateRecipe class methods
- **Data Coverage**: Test scenarios covering all field combinations
- **Error Coverage**: All exception scenarios tested with clear error messages
- **Maintainability**: Tests must be easy to understand and modify
- **Performance**: Tests should execute quickly in local environment

## Testing Approach
### Core Test Classes Structure
```python
class TestApiCreateRecipeValidation:
    # Test field validation for all required and optional fields
    # Test data type validation and constraints
    
class TestApiCreateRecipeConversion:
    # Test to_domain() conversion logic
    # Validate CreateRecipe command creation
    
class TestApiCreateRecipeErrorHandling:
    # Test exception scenarios and error messages
    # Validate graceful failure handling
    
class TestApiCreateRecipeComplexFields:
    # Test complex nested objects (ingredients, tags, nutri_facts)
    # Validate frozenset handling and conversions
    
class TestApiCreateRecipeIntegration:
    # Test integration with CreateRecipe domain command
    # Validate end-to-end creation flow
```

### Testing Strategy
- **Unit Tests**: Focus on individual method and field validation
- **Integration Tests**: Verify domain command creation and compatibility
- **Error Scenario Tests**: Validate exception handling and error messages
- **Data Integrity Tests**: Ensure no data loss during conversion

## Implementation Phases
### Phase 1: Core Field Validation
- [ ] Set up test infrastructure and imports
- [ ] Implement `TestApiCreateRecipeValidation` class
- [ ] Test required fields validation (name, instructions, author_id, meal_id)
- [ ] Test optional fields validation and defaults
- [ ] Test data type constraints and edge cases

### Phase 2: Domain Conversion & Complex Fields
- [ ] Implement `TestApiCreateRecipeConversion` class
- [ ] Test `to_domain()` method functionality
- [ ] Implement `TestApiCreateRecipeComplexFields` class
- [ ] Test ingredients frozenset conversion
- [ ] Test tags frozenset conversion
- [ ] Test nutri_facts optional object conversion

### Phase 3: Error Handling & Integration
- [ ] Implement `TestApiCreateRecipeErrorHandling` class
- [ ] Test conversion failure scenarios
- [ ] Test invalid input handling with descriptive errors
- [ ] Implement `TestApiCreateRecipeIntegration` class
- [ ] Test CreateRecipe command structure validation

## Success Metrics
- 100% test coverage of ApiCreateRecipe class
- All field validation scenarios tested and passing
- Zero test failures in domain integration
- Clear error messages for all failure scenarios
- Tests execute in under 30 seconds locally

## Risks & Mitigation
- **Risk**: Complex nested objects may have edge cases not covered
  **Mitigation**: Create comprehensive test fixtures covering all ingredient and tag combinations
- **Risk**: Field validation may be inconsistent across different field types
  **Mitigation**: Systematic testing of each field type with consistent validation patterns
- **Risk**: Domain integration may reveal unexpected validation issues
  **Mitigation**: Test with actual CreateRecipe domain objects and validate business rules

## Dependencies
- Existing recipe field validation classes
- CreateRecipe domain command class
- Pydantic testing utilities
- Current test infrastructure and patterns

## Key Test Scenarios
### Field Validation Edge Cases
- Empty required fields
- Maximum field length validation
- Invalid UUID formats
- Malformed ingredient and tag data
- Privacy enum validation

### Domain Conversion Edge Cases
- All required fields only
- All optional fields populated
- Mixed field scenarios
- Complex nested object validation
- Default value assignment

### Error Handling Scenarios
- ValueError for conversion failures
- Invalid data type handling
- Malformed nested object handling
- Descriptive error message validation

## File Structure
```
tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/
├── test_api_create_recipe_validation.py
├── test_api_create_recipe_conversion.py
├── test_api_create_recipe_error_handling.py
├── test_api_create_recipe_complex_fields.py
├── test_api_create_recipe_integration.py
└── conftest.py  # Test fixtures and utilities
``` 