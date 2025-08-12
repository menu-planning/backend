# Implementation Guide: Typeform Egress Proxy

---
feature: typeform-egress-proxy
complexity: standard
risk_level: medium
estimated_time: 2-4 days
phases: 2
---

## Overview
Implement a small helper Lambda (Node.js 20) to proxy HTTPS requests to `api.typeform.com`. Use environment variables only for the Typeform API key and function name; implement the method/path allowlist in code (version-controlled). Integrate the Python client to optionally route through the proxy via feature flag.

## Architecture
Caller → Proxy Lambda → Typeform. Proxy validates method/path (code-level allowlist), injects `Authorization: Bearer ${TYPEFORM_API_KEY}`, logs correlation_id, and returns status/body/headers.

## Files to Modify/Create
### Core Files
- `/Users/joaquim/projects/menu-planning/backend/services/app/tools/typeform_proxy_lambda/index.mjs` - Proxy handler (NEW)
- `/Users/joaquim/projects/menu-planning/backend/services/app/tools/typeform_proxy_lambda/package.json` - Node package manifest (NEW)
- `/Users/joaquim/projects/menu-planning/backend/services/app/src/contexts/client_onboarding/config.py` - Add flags `TYPEFORM_VIA_PROXY`, `TYPEFORM_PROXY_FUNCTION_NAME` (MODIFIED)
- `/Users/joaquim/projects/menu-planning/backend/services/app/src/contexts/client_onboarding/core/services/integrations/typeform/client.py` - Add proxy invocation path and error mapping (MODIFIED)
- `/Users/joaquim/projects/menu-planning/backend/services/app/src/logging/logger.py` - Ensure structured logs support correlation_id (MODIFIED)

### Tests
- `/Users/joaquim/projects/menu-planning/backend/services/app/tests/contexts/client_onboarding/services/test_typeform_proxy_integration.py` - End-to-end via mocked Lambda Invoke (NEW)

## Testing Strategy
- Commands: `poetry run python -m pytest -q`
- Focus: allowlist enforcement, header injection, error transparency, flag toggle behavior
- Coverage target: 80%+ in changed areas

## Phase Dependencies
- Phase 1 → Phase 2

## Risk Mitigation
- Strict allowlist in code; ignore inbound Authorization
- Short connect timeout; classify network vs HTTP errors; redact sensitive headers

## Success Criteria
1. Webhook operations succeed via proxy when flag enabled
2. Additional proxy hop p95 latency < 150ms (best effort, non-infra)
3. Errors clearly classified and observable


