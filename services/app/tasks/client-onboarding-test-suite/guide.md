# Implementation Guide: Client Onboarding Test Suite Development

---
feature: client-onboarding-test-suite
complexity: standard
risk_level: medium
estimated_time: 15-20 days
phases: 3
---

## Overview
Develop comprehensive test infrastructure for client_onboarding context, mirroring recipes_catalog patterns. Focus on TypeForm integration reliability, webhook processing, and behavioral testing with fakes over mocks.

## Architecture
```
/tests/contexts/client_onboarding/
├── core/
│   ├── domain/           # Unit tests for commands, events, entities
│   ├── services/         # Service layer behavioral tests  
│   └── integrations/     # TypeForm API & webhook tests
├── data_factories/       # Test data creation utilities
├── fakes/               # Fake implementations for external services
├── e2e/                 # End-to-end integration tests
├── scenarios/           # Edge cases and error scenarios
└── utils/               # Context-specific test helpers
```

## Existing Testing Infrastructure
**Leverage existing patterns and utilities:**
- `tests/conftest.py` - Global fixtures, counter reset, performance timing, test markers
- `tests/integration_conftest.py` - Database fixtures for integration tests  
- `tests/utils/counter_manager.py` - Centralized deterministic counters
- `tests/utils/utils.py` - Model comparison, round-trip testing, mock utilities

## Files to Modify/Create
### Core Files
- `tests/contexts/client_onboarding/core/domain/test_commands.py` - Command unit tests (NEW)
- `tests/contexts/client_onboarding/core/domain/test_events.py` - Event unit tests (NEW)
- `tests/contexts/client_onboarding/core/services/test_webhook_handler.py` - Webhook processing tests (NEW)
- `tests/contexts/client_onboarding/core/integrations/test_typeform_client.py` - TypeForm API tests (NEW)
- `tests/contexts/client_onboarding/data_factories/client_factories.py` - Domain data factories (NEW)
- `tests/contexts/client_onboarding/data_factories/typeform_factories.py` - TypeForm response fixtures (NEW)
- `tests/contexts/client_onboarding/fakes/fake_typeform_api.py` - Fake TypeForm implementation (NEW)
- `tests/contexts/client_onboarding/conftest.py` - Context-specific fixtures (NEW)

### Updated Existing Files
- `tests/utils/counter_manager.py` - Add client_onboarding counters (MODIFIED)

### Supporting Files
- `tests/contexts/client_onboarding/utils/test_helpers.py` - Context-specific utilities (NEW)
- `tests/contexts/client_onboarding/fixtures/webhook_payloads.json` - Realistic webhook data (NEW)

## Testing Strategy
- **Unit Tests**: Pure domain logic without external dependencies
- **Integration Tests**: Service layer with fake TypeForm API + database fixtures from `integration_conftest.py`
- **Behavioral Tests**: End-to-end webhook processing scenarios
- **Performance**: Leverage `benchmark_timer` fixture from main `conftest.py`
- **Commands**: 
  - Full suite: `poetry run python pytest tests/contexts/client_onboarding/`
  - Unit only: `poetry run python pytest tests/contexts/client_onboarding/core/domain/`
  - Integration: `poetry run python pytest tests/contexts/client_onboarding/core/integrations/ --integration`
  - E2E: `poetry run python pytest tests/contexts/client_onboarding/e2e/ --e2e`
- **Coverage target**: 90%+ for core domain, 85%+ overall

## Phase Dependencies
```
Phase 1 (Foundation) → Phase 2 (Service Testing) → Phase 3 (Integration & Polish)
```

**Phase 1**: Test structure, domain tests, extend counter_manager, basic factories
**Phase 2**: Service tests, TypeForm fake API, webhook processing with existing utils  
**Phase 3**: Full integration tests, performance optimization, documentation

## Risk Mitigation
- **TypeForm API changes**: Use versioned fake implementations with clear interface contracts
- **Complex webhook scenarios**: Build comprehensive fixture library from real-world examples
- **Test performance**: Use existing `benchmark_timer`, monitor execution time <30s
- **Team adoption**: Follow recipes_catalog patterns exactly, leverage existing utils
- **Code duplication**: Extend existing `counter_manager.py` and `utils.py` rather than recreate

## Success Criteria
1. 90%+ test coverage for domain logic (commands, events, business rules)
2. All TypeForm API operations tested with fake implementations
3. Webhook processing pipeline fully tested with realistic scenarios  
4. Test execution time under 30 seconds for full suite using existing performance fixtures
5. Zero flaky tests in local development environment with existing counter reset infrastructure
6. New team members can write tests following established patterns using existing utilities 