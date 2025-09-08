# Phase 2: Implement Input Sanitization with Pydantic v2

---
phase: 2
depends_on: [phase_1]
estimated_time: 4 hours
risk_level: medium
---

## Objective
Implement input sanitization using Pydantic v2 validators to prevent sensitive data leakage and malicious input in error responses.

## Prerequisites
- [ ] Phase 1 complete: Security headers implemented
- [ ] Pydantic sanitization models created

# Tasks

## 2.1 Pydantic Sanitization Models
- [ ] 2.1.1 Create sanitized error message model
  - Files: `src/contexts/shared_kernel/middleware/error_handling/sanitized_models.py`
  - Purpose: Create Pydantic model using existing SanitizedText fields and validators
  - Dependencies: `src/contexts/seedwork/adapters/api_schemas/base_api_fields.py`, `src/contexts/seedwork/adapters/api_schemas/validators.py`
- [ ] 2.1.2 Integrate existing validators
  - Files: `src/contexts/shared_kernel/middleware/error_handling/sanitized_models.py`
  - Purpose: Import and use existing sanitize_text_input and security pattern validators
  - Dependencies: `src/contexts/seedwork/adapters/api_schemas/validators.sanitize_text_input`, `src/contexts/seedwork/adapters/api_schemas/base_api_fields.SanitizedText`
- [ ] 2.1.3 Add middleware-specific sanitization
  - Files: `src/contexts/shared_kernel/middleware/error_handling/sanitized_models.py`
  - Purpose: Add sensitive data sanitization (DB connections, API keys) on top of existing validators
  - Dependencies: `src/contexts/seedwork/adapters/api_schemas/validators.sanitize_text_input`

## 2.2 Error Response Sanitization
- [ ] 2.2.1 Add sanitization to ErrorResponse
  - Files: `src/contexts/shared_kernel/middleware/error_handling/error_response.py`
  - Purpose: Use existing SanitizedText fields and validators for error messages and details
  - Dependencies: `src/contexts/seedwork/adapters/api_schemas/base_api_fields.SanitizedText`, `src/contexts/seedwork/adapters/api_schemas/validators.sanitize_text_input`
- [ ] 2.2.2 Add validation error sanitization
  - Files: `src/contexts/shared_kernel/middleware/error_handling/error_response.py`
  - Purpose: Use existing validators to sanitize validation error messages and field names
  - Dependencies: `src/contexts/seedwork/adapters/api_schemas/validators.sanitize_text_input`
- [ ] 2.2.3 Add context sanitization
  - Files: `src/contexts/shared_kernel/middleware/error_handling/error_response.py`
  - Purpose: Use existing validators to sanitize platform context and correlation IDs
  - Dependencies: `src/contexts/seedwork/adapters/api_schemas/validators.sanitize_text_input`

## 2.3 Exception Handler Integration
- [ ] 2.3.1 Integrate sanitized models
  - Files: `src/contexts/shared_kernel/middleware/error_handling/exception_handler.py`
  - Purpose: Use Pydantic models for error response creation with automatic sanitization
- [ ] 2.3.2 Add sanitization to error creation
  - Files: `src/contexts/shared_kernel/middleware/error_handling/exception_handler.py`
  - Purpose: Ensure all error responses use sanitized Pydantic models

## 2.4 Testing
- [ ] 2.4.1 Run information leakage tests
  - Files: `tests/security/contexts/shared_kernel/middleware/error_handling/test_exception_handler_security.py`
  - Purpose: Verify sensitive data is not leaked in error responses
- [ ] 2.4.2 Run malicious input tests
  - Files: `tests/security/contexts/shared_kernel/middleware/error_handling/test_exception_handler_security.py`
  - Purpose: Verify malicious input is sanitized in error responses

## Validation
- [ ] Tests: `uv run python -m pytest tests/security/contexts/shared_kernel/middleware/error_handling/ -k "information_leakage" -v`
- [ ] Tests: `uv run python -m pytest tests/security/contexts/shared_kernel/middleware/error_handling/ -k "malicious_input" -v`
- [ ] Lint: `uv run python -m ruff check src/contexts/shared_kernel/middleware/error_handling/`
