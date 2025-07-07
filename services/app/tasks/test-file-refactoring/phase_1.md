# Phase 1: Setup Foundation

---
phase: 1
estimated_time: 1 hour
---

## Objective
Create the shared foundation by extracting common components from the original test file into `conftest.py`. This establishes the base classes and fixtures that all split test files will use.

## Prerequisites
- [ ] Backup original `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_comprehensive.py`
- [ ] Identify current test directory structure

# Tasks

## 1.1 Create Shared Test Base
- [ ] 1.1.1 Create `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/conftest.py`
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/conftest.py`
  - Purpose: Extract BaseApiRecipeTest class from original file
- [ ] 1.1.2 Move all shared imports
  - Include: pytest, factory imports, common utilities
  - Purpose: Centralize import statements
- [ ] 1.1.3 Extract shared fixtures
  - Move: Common test data fixtures
  - Purpose: Avoid duplication across split files

## 1.2 Validate Foundation
- [ ] 1.2.1 Test imports work correctly
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/conftest.py`
  - Purpose: Ensure no import errors
- [ ] 1.2.2 Verify BaseApiRecipeTest functionality
  - Command: `python -c "from tests.contexts.recipes_catalog.core.adapters.meal.api_schemas.entities.conftest import BaseApiRecipeTest; print('Success')"`
  - Purpose: Confirm base class is properly extracted

## 1.3 Update Original File
- [ ] 1.3.1 Remove extracted components from original
  - Files: `tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_comprehensive.py`
  - Purpose: Avoid duplication and prepare for split
- [ ] 1.3.2 Update imports in original file
  - Add: `from conftest import BaseApiRecipeTest`
  - Purpose: Ensure original still works during transition

## Validation
- [ ] Tests: `pytest tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/test_api_recipe_comprehensive.py -v`
- [ ] Lint: `ruff check tests/contexts/recipes_catalog/core/adapters/meal/api_schemas/entities/conftest.py`
- [ ] Import verification: No circular imports or missing dependencies 