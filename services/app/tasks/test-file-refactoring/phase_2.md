# Phase 2: Split Implementation

---
phase: 2
estimated_time: 3 hours
---

## Objective
Split the comprehensive test file into 6 focused test files, each containing specific test classes and maintaining all original functionality.

## Prerequisites
- [ ] Phase 1 completed (conftest.py created and working)
- [ ] Original test file still passing all tests

# Tasks

## 2.1 Create Core Functionality Tests
- [ ] 2.1.1 Create `test_api_recipe_core.py` (~600 lines)
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_core.py`
  - Purpose: Extract TestApiRecipeBasics, TestApiRecipeRoundTrip, TestApiRecipeComputedProperties
- [ ] 2.1.2 Update imports in core file
  - Add: `from conftest import BaseApiRecipeTest`
  - Purpose: Use shared base class and fixtures

## 2.2 Create Validation Tests
- [ ] 2.2.1 Create `test_api_recipe_validation.py` (~600 lines)
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_validation.py`
  - Purpose: Extract TestApiRecipeErrorHandling, TestApiRecipeEdgeCases, TestApiRecipeFieldValidationEdgeCases, TestApiRecipeTagsValidationEdgeCases, TestApiRecipeFrozensetValidationEdgeCases, TestApiRecipeDomainRuleValidationEdgeCases
- [ ] 2.2.2 Update imports in validation file
  - Add: `from conftest import BaseApiRecipeTest`
  - Purpose: Use shared base class and fixtures

## 2.3 Create Performance Tests
- [ ] 2.3.1 Create `test_api_recipe_performance.py` (~1000 lines)
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_performance.py`
  - Purpose: Extract TestApiRecipePerformance, TestApiRecipeStressAndPerformance
- [ ] 2.3.2 Update imports in performance file
  - Add: `from conftest import BaseApiRecipeTest`
  - Purpose: Use shared base class and fixtures

## 2.4 Create Serialization Tests
- [ ] 2.4.1 Create `test_api_recipe_serialization.py` (~500 lines)
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_serialization.py`
  - Purpose: Extract TestApiRecipeJson, TestApiRecipeIntegration, TestApiRecipeSpecialized
- [ ] 2.4.2 Update imports in serialization file
  - Add: `from conftest import BaseApiRecipeTest`
  - Purpose: Use shared base class and fixtures

## 2.5 Create Edge Cases Tests
- [ ] 2.5.1 Create `test_api_recipe_edge_cases.py` (~400 lines)
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_edge_cases.py`
  - Purpose: Extract TestApiRecipeComputedPropertiesEdgeCases, TestApiRecipeDatetimeEdgeCases, TestApiRecipeTextAndSecurityEdgeCases, TestApiRecipeConcurrencyEdgeCases, TestApiRecipeComprehensiveValidation
- [ ] 2.5.2 Update imports in edge cases file
  - Add: `from conftest import BaseApiRecipeTest`
  - Purpose: Use shared base class and fixtures

## 2.6 Create Coverage Tests
- [ ] 2.6.1 Create `test_api_recipe_coverage.py` (~100 lines)
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_coverage.py`
  - Purpose: Extract TestApiRecipeCoverage
- [ ] 2.6.2 Update imports in coverage file
  - Add: `from conftest import BaseApiRecipeTest`
  - Purpose: Use shared base class and fixtures

## Validation
- [ ] Tests: `pytest tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_core.py -v`
- [ ] Tests: `pytest tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_validation.py -v`
- [ ] Tests: `pytest tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_performance.py -v`
- [ ] Tests: `pytest tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_serialization.py -v`
- [ ] Tests: `pytest tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_edge_cases.py -v`
- [ ] Tests: `pytest tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_coverage.py -v`
- [ ] All 6 new files should pass independently 