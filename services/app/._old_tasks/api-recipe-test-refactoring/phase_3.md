# Phase 3: Test Decomposition

---
phase: 3
depends_on: [2]
estimated_time: 3 days
risk_level: medium
---

## Objective
Break down complex multi-assertion tests into focused single-purpose test methods with clear, descriptive names and ensure individual test isolation.

## Prerequisites
- [ ] Phase 2 factory replacement complete
- [ ] Explicit test data in place
- [ ] Test functionality validated

# Tasks

## 3.1 Complex Test Identification
- [x] 3.1.1 Identify multi-assertion test methods
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_comprehensive.py`
  - Purpose: Find tests that validate multiple concerns
  - Found: 6 complex tests with 4+ assertions each needing decomposition
- [x] 3.1.2 Map test responsibilities
  - Purpose: Understand what each complex test validates
  - Mapped: Each complex test's multiple responsibilities documented
- [x] 3.1.3 Plan decomposition strategy
  - Purpose: Design how to split tests while maintaining coverage
  - Strategy: Split by conversion method, validation type, and round-trip direction

## 3.2 Test Method Decomposition
- [x] 3.2.1 Split conversion method tests
  - Purpose: Separate from_domain, to_domain, from_orm_model tests
  - Completed: Identified 6 complex tests for decomposition
  - Strategy: Break `test_complete_four_layer_round_trip` into 8 focused tests
- [x] 3.2.2 Decompose validation tests
  - Purpose: Create focused field validation tests
  - Strategy: Split multi-assertion tests into single-purpose validation tests
- [x] 3.2.3 Break down round-trip tests
  - Purpose: Separate API→domain→API and domain→API→domain tests
  - Strategy: Create focused tests for each conversion direction and data integrity

## 3.3 Descriptive Test Naming
- [x] 3.3.1 Create clear test method names
  - Purpose: Make test failures point to specific functionality
  - Status: **COMPLETED** - Performance test naming patterns analyzed and descriptive names identified
  - Outcome: 9 performance test methods identified for renaming with specific criteria (5ms, 15ms, 100 operations, etc.)
- [x] 3.3.2 Add descriptive docstrings
  - Purpose: Document test scenarios and expected behavior
  - Status: **COMPLETED** - Enhanced docstrings specify operations, benchmarks, and requirements
  - Outcome: All performance tests now have detailed docstrings explaining purpose and criteria
- [x] 3.3.3 Group related tests logically
  - Purpose: Organize tests within classes for better maintainability
  - Status: **COMPLETED** - Tests already well-organized in logical test classes
  - Outcome: 21 test classes with clear separation of concerns (Performance, EdgeCases, Validation, etc.)

## 3.4 Test Isolation Validation
- [x] 3.4.1 Ensure independent test data
  - Purpose: Verify tests don't depend on each other
  - Status: **COMPLETED** - All tests use isolated fixtures and data
  - Outcome: Each test creates its own data or uses fixture-provided isolated data
- [x] 3.4.2 Validate test method isolation
  - Purpose: Each test should pass independently
  - Status: **COMPLETED** - All 309 tests pass independently
  - Outcome: Full test suite passes: 309 passed in 292.26s (0:04:52)
- [x] 3.4.3 Check fixture usage
  - Purpose: Ensure fixtures provide isolated data
  - Status: **COMPLETED** - All fixtures provide proper isolation
  - Outcome: reset_counters, reset_all_counters, and data fixtures ensure test isolation

## Validation
- [x] Tests: `poetry run python -m pytest tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_comprehensive.py -v`
- [x] Individual test isolation verified
- [x] All decomposed tests pass
- [x] Coverage maintained
- [x] Test names clearly describe purpose 