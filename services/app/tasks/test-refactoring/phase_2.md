# Phase 2: Meal Tests Refactoring

---
phase: 2
depends_on: [phase_1]
estimated_time: 1.5 weeks
risk_level: high
---

## Objective
Apply recipe test refactoring patterns to `test_api_meal_performance.py`, focusing on computed properties, JSON serialization, and integration test simplification.

## Prerequisites
- [ ] Phase 1 recipe tests complete
- [ ] Recipe test patterns documented
- [ ] Performance improvements validated
- [ ] **CRITICAL: Review `analysis/factory_dependencies.md` for meal test factory usage**
- [ ] **CRITICAL: Review `analysis/current_test_structure_analysis.md` for meal test classes**

# Tasks

## 2.1 Basic Meal Conversion Tests
- [ ] 2.1.1 Replace factory usage in meal conversion tests
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/test_api_meal_performance.py`
  - Purpose: Convert factory-based meal tests to explicit data
- [ ] 2.1.2 Create focused meal field validation tests
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/test_api_meal_performance.py`
  - Purpose: Test individual meal field conversions
- [ ] 2.1.3 Create explicit meal relationship tests
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/test_api_meal_performance.py`
  - Purpose: Test meal-recipe relationships with explicit data

## 2.2 Computed Properties Tests
- [ ] 2.2.1 Simplify total cooking time tests
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/test_api_meal_performance.py`
  - Purpose: Use explicit recipe data for computed time calculations
- [ ] 2.2.2 Simplify total weight calculation tests
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/test_api_meal_performance.py`
  - Purpose: Use explicit ingredient data for weight calculations
- [ ] 2.2.3 Create explicit edge case computed property tests
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/test_api_meal_performance.py`
  - Purpose: Test boundary conditions with explicit data

## 2.3 JSON Serialization & Integration
- [ ] 2.3.1 Refactor JSON serialization tests
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/test_api_meal_performance.py`
  - Purpose: Use explicit data for JSON conversion testing
- [ ] 2.3.2 Simplify integration tests
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/test_api_meal_performance.py`
  - Purpose: Break down complex integration tests into focused units
- [ ] 2.3.3 Create explicit meal-recipe integration tests
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/test_api_meal_performance.py`
  - Purpose: Test meal-recipe integration with explicit data

## 2.4 Error Handling & Edge Cases
- [ ] 2.4.1 Replace factory usage in error handling tests
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/test_api_meal_performance.py`
  - Purpose: Use explicit invalid data for error testing
- [ ] 2.4.2 Create explicit meal validation tests
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/test_api_meal_performance.py`
  - Purpose: Test meal validation with explicit boundary conditions
- [ ] 2.4.3 Create explicit meal collection tests
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/test_api_meal_performance.py`
  - Purpose: Test meal collection operations with explicit data

## Validation
- [ ] Tests: `poetry run python -m pytest tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/test_api_meal_performance.py -v`
- [ ] Coverage: `poetry run python -m pytest --cov=src/contexts/recipes_catalog/core/adapters/meal/api_schemas/root_aggregate/api_meal.py --cov-report=term-missing`
- [ ] Integration: `poetry run python -m pytest tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/ -v`
- [ ] Lint: `poetry run python -m ruff check tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/test_api_meal_performance.py`
- [ ] Factory dependency check: Verify 70% reduction in factory imports

## Success Criteria
- All meal tests pass with explicit data
- Computed property tests are reliable and fast
- JSON serialization tests use explicit data
- Integration tests are focused and maintainable
- Overall test execution time reduced by 25% 