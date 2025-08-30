# Phase 2: Core Migration

---
phase: 2
depends_on: [phase_1]
estimated_time: 40 hours
risk_level: high
---

## Objective
Migrate all standard logger usage to structured logging across all identified files while preserving functionality and correlation ID context.

## Prerequisites
- [ ] Phase 1 audit completed
- [ ] Migration report and checklist available
- [ ] High-risk files identified

# Tasks

## 2.1 Import Migration
- [ ] 2.1.1 Replace logging imports in client_onboarding context
  - Files: `src/contexts/client_onboarding/` (17 files)
  - Pattern: Replace `import logging` with `from src.logging.logger import StructlogFactory`
  - Purpose: Update import statements for structured logging
- [ ] 2.1.2 Replace logging imports in iam context
  - Files: `src/contexts/iam/` (4 files)
  - Pattern: Same as 2.1.1
  - Purpose: Update import statements
- [ ] 2.1.3 Replace logging imports in products_catalog context
  - Files: `src/contexts/products_catalog/` (6 files)
  - Pattern: Same as 2.1.1
  - Purpose: Update import statements
- [ ] 2.1.4 Replace logging imports in recipes_catalog context
  - Files: `src/contexts/recipes_catalog/` (15 files)
  - Pattern: Same as 2.1.1
  - Purpose: Update import statements
- [ ] 2.1.5 Replace logging imports in seedwork context
  - Files: `src/contexts/seedwork/` (6 files)
  - Pattern: Same as 2.1.1
  - Purpose: Update import statements
- [ ] 2.1.6 Replace logging imports in shared_kernel context
  - Files: `src/contexts/shared_kernel/` (3 files)
  - Pattern: Same as 2.1.1
  - Purpose: Update import statements

## 2.2 Logger Instantiation Migration
- [ ] 2.2.1 Update logger creation patterns
  - Pattern: Replace `logging.getLogger(__name__)` with `StructlogFactory.get_logger(__name__)`
  - Files: All files from 2.1.x tasks
  - Purpose: Use structured logger factory
- [ ] 2.2.2 Update class-based logger patterns
  - Pattern: Replace `self.logger = logging.getLogger(...)` with `self.logger = StructlogFactory.get_logger(...)`
  - Files: Repository and service classes
  - Purpose: Migrate class-level loggers

## 2.3 Log Call Migration
- [ ] 2.3.1 Convert string interpolation to structured data
  - Pattern: Replace `logger.info(f"User {user_id} action")` with `logger.info("User action", user_id=user_id)`
  - Files: All migrated files
  - Purpose: Enable structured logging benefits
- [ ] 2.3.2 Preserve correlation ID context
  - Validation: Ensure correlation_id appears in all log entries
  - Files: All migrated files
  - Purpose: Maintain traceability
- [ ] 2.3.3 Update exception logging
  - Pattern: Replace `logger.exception(...)` with `logger.error(..., exc_info=True)`
  - Files: Error handling code
  - Purpose: Maintain exception context in structured format

## 2.4 High-Risk File Migration
- [ ] 2.4.1 Migrate middleware logging files
  - Files: `src/contexts/shared_kernel/middleware/`
  - Purpose: Critical infrastructure requires careful handling
  - Validation: Test correlation ID propagation after changes
- [ ] 2.4.2 Migrate repository logging
  - Files: `src/contexts/seedwork/shared/adapters/repositories/`
  - Purpose: Database interaction logging is performance-sensitive
  - Validation: Run performance benchmarks after changes

## Validation
- [ ] Tests: `poetry run python pytest tests/ --tb=short`
- [ ] Lint: `poetry run python ruff check src/`
- [ ] Type: `poetry run python mypy src/`
- [ ] Migration check: `grep -r "logging.getLogger" src/` returns no results
- [ ] Correlation ID test: `python artifacts/test_correlation_ids.py`
- [ ] Performance benchmark: `python artifacts/benchmark_logging.py --compare`
