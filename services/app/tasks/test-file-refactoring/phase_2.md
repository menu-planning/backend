# Phase 2: Split Implementation

---
phase: 2
estimated_time: 3 hours
status: IN_PROGRESS (50% complete)
---

## Objective
Split the comprehensive test file into 6 focused test files, each containing specific test classes and maintaining all original functionality.

## Prerequisites
- [x] Phase 1 completed (conftest.py created and working)
- [x] Original test file still passing all tests

# Tasks

## 2.1 Create Core Functionality Tests
- [x] 2.1.1 Create `test_api_recipe_core.py` (~600 lines)
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_core.py`
  - Purpose: Extract TestApiRecipeBasics, TestApiRecipeRoundTrip, TestApiRecipeComputedProperties
  - Status: ✅ COMPLETED - 390 lines with core functionality tests
- [x] 2.1.2 Update imports in core file
  - Add: `from conftest import BaseApiRecipeTest`
  - Purpose: Use shared base class and fixtures
  - Status: ✅ COMPLETED - Using shared base class and fixtures

## 2.2 Create Validation Tests
- [x] 2.2.1 Create `test_api_recipe_validation.py` (~600 lines)
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_validation.py`
  - Purpose: Extract TestApiRecipeErrorHandling, TestApiRecipeEdgeCases, TestApiRecipeFieldValidationEdgeCases, TestApiRecipeTagsValidationEdgeCases, TestApiRecipeFrozensetValidationEdgeCases, TestApiRecipeDomainRuleValidationEdgeCases
  - Status: ✅ COMPLETED - 499 lines with validation and error handling tests
- [x] 2.2.2 Update imports in validation file
  - Add: `from conftest import BaseApiRecipeTest`
  - Purpose: Use shared base class and fixtures
  - Status: ✅ COMPLETED - Using shared base class and fixtures

## 2.3 Create Performance Tests
- [x] 2.3.1 Create `test_api_recipe_performance.py` (~1000 lines)
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_performance.py`
  - Purpose: Extract TestApiRecipePerformance, TestApiRecipeStressAndPerformance
  - Status: ✅ COMPLETED - 394 lines with performance benchmarks and stress tests
- [x] 2.3.2 Update imports in performance file
  - Add: `from conftest import BaseApiRecipeTest`
  - Purpose: Use shared base class and fixtures
  - Status: ✅ COMPLETED - Using shared base class and fixtures

## 2.4 Create Serialization Tests
- [ ] 2.4.1 Create `test_api_recipe_serialization.py` (~500 lines)
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_serialization.py`
  - Purpose: Extract TestApiRecipeJson, TestApiRecipeIntegration, TestApiRecipeSpecialized
  - Status: ❌ PENDING - File was deleted, needs recreation
- [ ] 2.4.2 Update imports in serialization file
  - Add: `from conftest import BaseApiRecipeTest`
  - Purpose: Use shared base class and fixtures
  - Status: ❌ PENDING

## 2.5 Create Edge Cases Tests
- [ ] 2.5.1 Create `test_api_recipe_edge_cases.py` (~400 lines)
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_edge_cases.py`
  - Purpose: Extract TestApiRecipeComputedPropertiesEdgeCases, TestApiRecipeDatetimeEdgeCases, TestApiRecipeTextAndSecurityEdgeCases, TestApiRecipeConcurrencyEdgeCases, TestApiRecipeComprehensiveValidation
  - Status: ❌ PENDING
- [ ] 2.5.2 Update imports in edge cases file
  - Add: `from conftest import BaseApiRecipeTest`
  - Purpose: Use shared base class and fixtures
  - Status: ❌ PENDING

## 2.6 Create Coverage Tests
- [ ] 2.6.1 Create `test_api_recipe_coverage.py` (~100 lines)
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_coverage.py`
  - Purpose: Extract TestApiRecipeCoverage
  - Status: ❌ PENDING
- [ ] 2.6.2 Update imports in coverage file
  - Add: `from conftest import BaseApiRecipeTest`
  - Purpose: Use shared base class and fixtures
  - Status: ❌ PENDING

## Current Status Summary

**Completed Files (3/6):**
- ✅ `test_api_recipe_core.py` (390 lines) - Core functionality tests
- ✅ `test_api_recipe_validation.py` (499 lines) - Validation and error handling  
- ✅ `test_api_recipe_performance.py` (394 lines) - Performance benchmarks

**Remaining Files (3/6):**
- ❌ `test_api_recipe_serialization.py` (~500 lines) - JSON serialization tests
- ❌ `test_api_recipe_edge_cases.py` (~400 lines) - Additional edge cases
- ❌ `test_api_recipe_coverage.py` (~100 lines) - Coverage validation

**Issues to Address:**
- Some linter errors in created files need fixing
- test_api_recipe_serialization.py was deleted and needs recreation

## Validation
- [x] Tests: `pytest tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_core.py -v`
- [x] Tests: `pytest tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_validation.py -v`
- [x] Tests: `pytest tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_performance.py -v`
- [ ] Tests: `pytest tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_serialization.py -v`
- [ ] Tests: `pytest tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_edge_cases.py -v`
- [ ] Tests: `pytest tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_coverage.py -v`
- [ ] All 6 new files should pass independently

**Phase 2 Status: IN_PROGRESS (50% complete)**

**Next Session Actions:**
1. Create `test_api_recipe_serialization.py` with JSON/serialization tests
2. Create `test_api_recipe_edge_cases.py` with additional edge cases
3. Create `test_api_recipe_coverage.py` with coverage validation
4. Fix any remaining linter errors
5. Validate all 6 files pass independently
6. Proceed to Phase 3 cleanup and validation 