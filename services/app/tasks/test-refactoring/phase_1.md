# Phase 1: Recipe Tests Refactoring

---
phase: 1
depends_on: [phase_0]
estimated_time: 2 weeks
risk_level: high
---

## Objective
Refactor `test_api_recipe_comprehensive.py` to use explicit test data, break down complex tests into focused single-purpose tests, and eliminate factory dependencies.

## Prerequisites
- [ ] Phase 0 infrastructure complete
- [ ] Test data constants validated
- [ ] Performance helpers tested
- [ ] **CRITICAL: Review `analysis/factory_dependencies.md` for factory replacement targets**
- [ ] **CRITICAL: Review `analysis/current_test_structure_analysis.md` for test class breakdown**

# Tasks

## 1.1 Basic Conversion Tests
- [ ] 1.1.1 Replace factory usage in to_domain tests
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_comprehensive.py`
  - Purpose: Convert factory-based tests to explicit data tests
- [ ] 1.1.2 Replace factory usage in from_domain tests
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_comprehensive.py`
  - Purpose: Use explicit test data for domain→API conversion
- [ ] 1.1.3 Create focused field validation tests
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_comprehensive.py`
  - Purpose: Test individual field conversions with explicit data

## 1.2 Round-trip Tests Breakdown
- [ ] 1.2.1 Break down complex round-trip tests
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_comprehensive.py`
  - Purpose: Separate ID preservation, field preservation, and collection preservation
- [ ] 1.2.2 Create focused ingredient preservation tests
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_comprehensive.py`
  - Purpose: Test ingredient collection round-trip with explicit data
- [ ] 1.2.3 Create focused rating preservation tests
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_comprehensive.py`
  - Purpose: Test rating collection round-trip with explicit data
- [ ] 1.2.4 Create focused tag preservation tests
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_comprehensive.py`
  - Purpose: Test tag collection round-trip with explicit data

## 1.3 Error Handling Tests
- [ ] 1.3.1 Replace factory usage in validation error tests
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_comprehensive.py`
  - Purpose: Use explicit invalid data for error testing
- [ ] 1.3.2 Create explicit boundary condition tests
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_comprehensive.py`
  - Purpose: Test edge cases with explicit boundary values
- [ ] 1.3.3 Create explicit null/empty value tests
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_comprehensive.py`
  - Purpose: Test error handling with explicit null scenarios

## 1.4 JSON Serialization Tests
- [ ] 1.4.1 Simplify JSON serialization tests
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_comprehensive.py`
  - Purpose: Use explicit data for JSON conversion testing
- [ ] 1.4.2 Create explicit JSON edge case tests
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_comprehensive.py`
  - Purpose: Test JSON handling with explicit edge cases

## Validation
- [ ] Tests: `poetry run python -m pytest tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_comprehensive.py -v`
- [ ] Coverage: `poetry run python -m pytest --cov=src/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/api_recipe.py --cov-report=term-missing`
- [ ] Performance: `poetry run python -m pytest tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_comprehensive.py::TestApiRecipePerformance -v`
- [ ] Lint: `poetry run python -m ruff check tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_comprehensive.py`
- [ ] Factory dependency check: Verify 70% reduction in factory imports

## Success Criteria
- All recipe tests pass with explicit data
- 70% reduction in factory method usage
- Test execution time reduced by 20%
- Zero regression in test coverage
- All performance tests stable across environments 