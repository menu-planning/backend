# Phase 2: Python Client Integration

---
phase: 2
depends_on: [1]
estimated_time: 1-2 days
risk_level: medium
---

## Objective
Update the Python Typeform client to optionally use the proxy Lambda when enabled via env flags.

## Prerequisites
- [ ] Proxy Lambda deployed and reachable by name
- [ ] Environment variables set in runtime:
  - `TYPEFORM_VIA_PROXY=true|false`
  - `TYPEFORM_PROXY_FUNCTION_NAME` (the Lambda function name/alias)

# Tasks

## 2.1 Toggle & Config
- [x] 2.1.1 Add/read flags in config
  - Files: `/Users/joaquim/projects/menu-planning/backend/services/app/src/contexts/client_onboarding/config.py`
  - Purpose: centralize feature toggle and function name

## 2.2 Client Changes
- [x] 2.2.1 Implement proxy invocation path
  - Files: `/Users/joaquim/projects/menu-planning/backend/services/app/src/contexts/client_onboarding/core/services/integrations/typeform/client.py`
  - Purpose: when flag enabled, construct proxy payload {method, path, query, headers, body, correlation_id} and invoke Lambda
- [x] 2.2.2 Error mapping parity
  - Files: same as above
  - Purpose: pass through Typeform status/headers/body; convert network errors to a 503-equivalent in current error model

## 2.3 Tests
- [ ] 2.3.1 Integration test via mocked boto3 Lambda client
  - Files: `/Users/joaquim/projects/menu-planning/backend/services/app/tests/contexts/client_onboarding/services/test_typeform_proxy_integration.py`

## Validation
- [ ] `poetry run python -m pytest -q`
- [ ] Toggle works in dev: direct vs proxy path


