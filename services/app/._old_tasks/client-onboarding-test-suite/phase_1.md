# Phase 1: Core Foundation

---
phase: 1
estimated_time: 5-7 days
---

## Objective
Establish test directory structure mirroring recipes_catalog patterns, extend existing counter management, create basic data factories, and implement comprehensive unit tests for domain entities, commands, and events.

# Tasks

## 1.1 Test Directory Structure
- [x] 1.1.1 Create test directory structure
  - Files: `tests/contexts/client_onboarding/` (directory structure)
  - Purpose: Mirror recipes_catalog test organization
- [x] 1.1.2 Set up context-specific conftest.py
  - Files: `tests/contexts/client_onboarding/conftest.py`
  - Purpose: Context-specific fixtures that complement main `tests/conftest.py`
- [x] 1.1.3 Create __init__.py files for proper imports
  - Files: `tests/contexts/client_onboarding/core/__init__.py` and subdirectories
  - Purpose: Enable clean import structure

## 1.2 Extend Existing Infrastructure
- [x] 1.2.1 Add client_onboarding counters to counter_manager
  - Files: `tests/utils/counter_manager.py`
  - Purpose: Extend existing centralized counter management with client/form/webhook counters
- [x] 1.2.2 Verify counter reset integration
  - Files: Test that existing `reset_all_counters()` includes new counters
  - Purpose: Ensure test isolation works with new counters

## 1.3 Domain Data Factories
- [x] 1.3.1 Create client domain data factories
  - Files: `tests/contexts/client_onboarding/data_factories/client_factories.py`
  - Purpose: Generate deterministic test data using `counter_manager.py` patterns
- [x] 1.3.2 Create command and event factories
  - Files: `tests/contexts/client_onboarding/data_factories/domain_factories.py`
  - Purpose: Support domain testing with realistic data using existing counter patterns
- [x] 1.3.3 Add factory configuration and utilities
  - Files: `tests/contexts/client_onboarding/data_factories/__init__.py`
  - Purpose: Centralize factory imports following recipes_catalog patterns

## 1.4 Domain Unit Tests
- [x] 1.4.1 Test SetupOnboardingFormCommand
  - Files: `tests/contexts/client_onboarding/core/domain/test_commands.py`
  - Purpose: Validate command behavior using existing test utilities from `utils.py`
- [x] 1.4.2 Test UpdateWebhookUrlCommand
  - Files: `tests/contexts/client_onboarding/core/domain/test_commands.py`
  - Purpose: Verify webhook URL update logic with deterministic test data
- [x] 1.4.3 Test domain events (FormResponseReceived, ClientDataExtracted)
  - Files: `tests/contexts/client_onboarding/core/domain/test_events.py`
  - Purpose: Ensure events contain proper data using existing comparison utilities
- [x] 1.4.4 Test OnboardingFormWebhookSetup event
  - Files: `tests/contexts/client_onboarding/core/domain/test_events.py`
  - Purpose: Validate webhook setup event behavior

## 1.5 Context-Specific Test Utilities
- [x] 1.5.1 Create context-specific test helpers
  - Files: `tests/contexts/client_onboarding/utils/test_helpers.py`
  - Purpose: Client onboarding specific utilities that complement `tests/utils/utils.py`
- [x] 1.5.2 Set up basic fixture data
  - Files: `tests/contexts/client_onboarding/fixtures/basic_data.json`
  - Purpose: Static test data for consistent scenarios

## Validation
- [x] Tests: `poetry run python pytest tests/contexts/client_onboarding/core/domain/` (33 tests passed in 0.21s)
- [x] Lint: `poetry run python ruff check tests/contexts/client_onboarding/` (All checks passed)
- [x] Type: `poetry run python mypy tests/contexts/client_onboarding/` (No errors in client_onboarding code)
- [x] Counter integration: Verified new counters reset with main `reset_all_counters()`
- [x] Coverage: Domain tests achieve 100% coverage for tested components (commands and events)

**Phase 1 Status: COMPLETED ✅**
**Completion Date**: 2024-12-26
**Artifacts Generated**: 
- phase_1_completion.json
- phase_1_analysis_report.md
- Updated shared_context.json

**Next Phase**: phase_2.md ready for execution 