# Phase 2: Service Testing

---
phase: 2
depends_on: [1]
estimated_time: 5-7 days
---

## Objective
Build fake TypeForm API implementation, create comprehensive webhook handler tests, implement TypeForm client integration tests, and establish service layer behavioral testing leveraging existing integration fixtures.

# Tasks

## 2.1 Fake TypeForm API
- [x] 2.1.1 Create fake TypeForm API implementation
  - Files: `tests/contexts/client_onboarding/fakes/fake_typeform_api.py`
  - Purpose: Consistent, testable TypeForm API responses without network calls
- [x] 2.1.2 Create TypeForm response factories
  - Files: `tests/contexts/client_onboarding/data_factories/typeform_factories.py`
  - Purpose: Generate realistic TypeForm API responses using existing counter patterns
- [x] 2.1.3 Add webhook signature validation utilities
  - Files: `tests/contexts/client_onboarding/fakes/webhook_security.py`
  - Purpose: Test webhook signature validation with valid/invalid scenarios

## 2.2 Webhook Handler Testing
- [x] 2.2.1 Test webhook processing pipeline
  - Files: `tests/contexts/client_onboarding/core/services/test_webhook_handler.py`
  - Purpose: Verify end-to-end webhook processing behavior with existing performance fixtures
- [x] 2.2.2 Test webhook security validation
  - Files: `tests/contexts/client_onboarding/core/services/test_webhook_handler.py`
  - Purpose: Ensure proper signature validation using existing test utilities
- [x] 2.2.3 Test error handling scenarios
  - Files: `tests/contexts/client_onboarding/core/services/test_webhook_handler.py`
  - Purpose: Validate error recovery using existing `benchmark_timer` for performance checks

## 2.3 TypeForm Client Integration
- [x] 2.3.1 Test TypeForm client CRUD operations
  - Files: `tests/contexts/client_onboarding/core/integrations/test_typeform_client.py`
  - Purpose: Verify all TypeForm API operations with fake responses using `@pytest.mark.integration`
- [x] 2.3.2 Test authentication and error scenarios
  - Files: `tests/contexts/client_onboarding/core/integrations/test_typeform_client.py`
  - Purpose: Handle API authentication leveraging existing mock utilities from `utils.py`
- [x] 2.3.3 Test rate limiting and retry logic
  - Files: `tests/contexts/client_onboarding/core/integrations/test_typeform_client.py`
  - Purpose: Verify proper handling of API limits with existing timing fixtures

## 2.4 Database Integration Testing
- [x] 2.4.1 Test webhook data persistence
  - Files: `tests/contexts/client_onboarding/core/services/test_webhook_persistence.py`
  - Purpose: Verify webhook data is properly stored using existing `clean_async_pg_session` fixture
- [ ] 2.4.2 Test client data extraction with database
  - Files: `tests/contexts/client_onboarding/core/services/test_client_data_service.py`
  - Purpose: Test data extraction and storage using existing database fixtures

## 2.5 Event Publisher Testing
- [ ] 2.5.1 Test event publishing behavior
  - Files: `tests/contexts/client_onboarding/core/services/test_event_publisher.py`
  - Purpose: Verify events are published correctly using existing comparison utilities
- [ ] 2.5.2 Add webhook payload fixtures
  - Files: `tests/contexts/client_onboarding/fixtures/webhook_payloads.json`
  - Purpose: Realistic webhook payloads for comprehensive testing

## Validation
- [ ] Unit tests: `poetry run python pytest tests/contexts/client_onboarding/core/services/`
- [ ] Integration tests: `poetry run python pytest tests/contexts/client_onboarding/core/integrations/ --integration`
- [ ] Database tests: `poetry run python pytest tests/contexts/client_onboarding/ -k "persistence" --integration`
- [ ] Performance: Use existing `benchmark_timer` to ensure service tests <100ms each
- [ ] Coverage: Service layer achieves 85%+ coverage 