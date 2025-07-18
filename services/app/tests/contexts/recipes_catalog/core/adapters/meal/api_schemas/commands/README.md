# ApiCreateRecipe Test Organization

This directory contains comprehensive test suites for the `ApiCreateRecipe` command schema, organized by concern for better maintainability and clarity.

## File Structure

### Core Functionality
- **`test_api_create_recipe_core.py`** - Core functionality tests including basic recipe creation, domain conversion, and integration scenarios

### Field Validation  
- **`test_api_create_recipe_field_validation.py`** - Comprehensive field validation tests for all individual fields (name, instructions, author_id, etc.)

### Edge Cases & Error Handling
- **`test_api_create_recipe_edge_cases.py`** - Boundary values, complex scenarios, error handling, realistic scenarios, and performance tests

### Serialization
- **`test_api_create_recipe_serialization.py`** - JSON serialization/deserialization, format validation, and round-trip testing

### Legacy File (To Be Removed)
- **`test_api_create_recipe_validation.py`** - Original monolithic test file (1279 lines) that should be removed after migration

## Organization Benefits

### 🎯 **Focused Scope**
Each file handles a specific aspect:
- Core: Basic functionality and domain conversion
- Field Validation: Individual field validation logic  
- Edge Cases: Boundary conditions and error scenarios
- Serialization: JSON handling and format validation

### 📊 **Better Maintainability** 
- Smaller, more manageable files (200-400 lines each vs 1279 lines)
- Easier to locate specific test types
- Clear separation of concerns
- Reduced merge conflicts

### 🚀 **Improved Development Experience**
- Faster navigation and search
- Parallel test execution possibilities
- Clearer test failure isolation
- Better code review process

### 🏗️ **Consistent with Project Standards**
Following the same pattern as meal tests:
- `test_api_meal_core.py` (1203 lines)
- `test_api_meal_validation.py` (812 lines) 
- `test_api_meal_edge_cases.py` (894 lines)
- `test_api_meal_serialization.py` (1112 lines)
- `test_api_meal_performance.py` (902 lines)
- `test_api_meal_coverage.py` (367 lines)

## Migration Steps

1. ✅ **Created new organized files**
   - `test_api_create_recipe_core.py`
   - `test_api_create_recipe_field_validation.py` 
   - `test_api_create_recipe_edge_cases.py`
   - `test_api_create_recipe_serialization.py`

2. 🔄 **Verify tests run successfully**
   ```bash
   pytest tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_core.py -v
   pytest tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_field_validation.py -v
   pytest tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_edge_cases.py -v
   pytest tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_serialization.py -v
   ```

3. 🗑️ **Remove legacy file**
   ```bash
   rm tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/commands/test_api_create_recipe_validation.py
   ```

## Test Class Organization

### Core (`test_api_create_recipe_core.py`)
- `TestApiCreateRecipeBasics` - Basic recipe creation and validation
- `TestApiCreateRecipeDomainConversion` - Domain command conversion
- `TestApiCreateRecipeIntegration` - Integration scenarios

### Field Validation (`test_api_create_recipe_field_validation.py`)  
- `TestApiCreateRecipeNameFieldValidation` - Name field validation
- `TestApiCreateRecipeInstructionsFieldValidation` - Instructions field validation
- `TestApiCreateRecipeAuthorIdFieldValidation` - Author ID field validation
- `TestApiCreateRecipeMealIdFieldValidation` - Meal ID field validation
- `TestApiCreateRecipeOptionalFieldValidation` - Optional fields validation
- `TestApiCreateRecipeComplexFieldValidation` - Complex fields (ingredients, tags)

### Edge Cases (`test_api_create_recipe_edge_cases.py`)
- `TestApiCreateRecipeBoundaryValues` - Boundary value testing
- `TestApiCreateRecipeErrorHandling` - Error scenarios
- `TestApiCreateRecipeComplexScenarios` - Complex validation scenarios
- `TestApiCreateRecipeRealisticScenarios` - Real-world scenarios
- `TestApiCreateRecipePerformance` - Performance with large datasets

### Serialization (`test_api_create_recipe_serialization.py`)
- `TestApiCreateRecipeBasicSerialization` - Basic JSON operations
- `TestApiCreateRecipeComplexSerialization` - Complex serialization scenarios
- `TestApiCreateRecipeSerializationEdgeCases` - Edge cases in serialization
- `TestApiCreateRecipeSerializationFormat` - JSON format validation
- `TestApiCreateRecipeRoundTripSerialization` - Round-trip validation

## Helper Functions

All test files utilize the helper functions from `conftest.py`:
- `create_api_create_recipe_kwargs()` - Full recipe creation
- `create_minimal_api_create_recipe_kwargs()` - Minimal required fields
- `create_api_create_recipe_with_author_id()` - With specific author
- `create_invalid_api_create_recipe_kwargs()` - Invalid data generation
- `create_api_create_recipe_with_custom_tags()` - Custom tag scenarios
- `create_api_create_recipe_with_ingredients_and_tags()` - Complex scenarios

## Conclusion

This reorganization transforms a monolithic 1279-line test file into four focused, maintainable test suites that follow established project patterns and improve the development experience significantly. 