# Phase 2: Factory Method Replacement

---
phase: 2
depends_on: [1]
estimated_time: 3 days
risk_level: medium
---

## Objective
Replace complex factory method calls with explicit test data creation while preserving simple factory usage where beneficial and maintaining test functionality.

## Prerequisites
- [ ] Phase 1 analysis complete
- [ ] Factory usage patterns documented
- [ ] Test coverage baseline established

# Tasks

## 2.1 Simple Factory Replacement
- [ ] 2.1.1 Replace basic recipe creation factories
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_comprehensive.py`
  - Purpose: Convert simple factory calls to explicit data
- [ ] 2.1.2 Create explicit test data for basic scenarios
  - Purpose: Make test data visible and understandable
- [ ] 2.1.3 Validate basic test functionality
  - Purpose: Ensure no functionality loss

## 2.2 Complex Factory Replacement
- [ ] 2.2.1 Replace complex recipe creation factories
  - Purpose: Convert complex factory calls with explicit ingredient/rating data
- [ ] 2.2.2 Create explicit nested object data
  - Purpose: Make ingredient, rating, and tag data explicit
- [ ] 2.2.3 Replace collection factory methods
  - Purpose: Convert recipe collection factories to explicit lists

## 2.3 Domain Factory Integration
- [ ] 2.3.1 Replace domain factory calls where appropriate
  - Purpose: Create explicit domain objects for round-trip tests
- [ ] 2.3.2 Maintain domain factory usage for ORM tests
  - Purpose: Keep useful factory methods for complex ORM object creation
- [ ] 2.3.3 Update fixture dependencies
  - Purpose: Ensure fixtures work with new explicit data

## 2.4 Test Data Validation
- [ ] 2.4.1 Run tests after each factory replacement
  - Purpose: Validate functionality preservation
- [ ] 2.4.2 Update test documentation
  - Purpose: Ensure test purposes are clear with explicit data
- [ ] 2.4.3 Verify test data variety
  - Purpose: Ensure edge cases and typical scenarios are covered

## Validation
- [ ] Tests: `poetry run python -m pytest tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_comprehensive.py -v`
- [ ] Coverage: `poetry run python -m pytest tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_comprehensive.py --cov=src --cov-report=html`
- [ ] All factory replacements tested
- [ ] No test functionality lost 