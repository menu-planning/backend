# Phase 1: Proxy Lambda (Node.js 20)

---
phase: 1
depends_on: []
estimated_time: 1-2 days
risk_level: medium
---

## Objective
Implement the proxy Lambda to call `api.typeform.com` with strict allowlist and header injection, using environment variables for configuration and API key.

## Prerequisites
- [ ] Environment variables available at runtime:
  - `TYPEFORM_API_KEY`: Typeform API key
  - Optional: `TYPEFORM_BASE_URL` default `https://api.typeform.com`

# Tasks

## 1.1 Proxy Handler
- [x] 1.1.1 Create Node handler
  - Files: `/Users/joaquim/projects/menu-planning/backend/services/app/tools/typeform_proxy_lambda/index.mjs`
  - Purpose: validate input, enforce allowlist, call Typeform, map response
- [x] 1.1.2 Add package manifest and scripts
  - Files: `/Users/joaquim/projects/menu-planning/backend/services/app/tools/typeform_proxy_lambda/package.json`
  - Purpose: dependencies (undici), scripts, engine (node 20)
  - Example package.json:
    {
      "name": "typeform-proxy-lambda",
      "type": "module",
      "version": "1.0.0",
      "engines": { "node": ">=20" },
      "dependencies": { "undici": "^6.19.8" }
    }

## 1.2 Security & Limits
- [x] 1.2.1 Ignore inbound Authorization; inject `Bearer ${TYPEFORM_API_KEY}` from env
  - Files: `/Users/joaquim/projects/menu-planning/backend/services/app/tools/typeform_proxy_lambda/index.mjs`
  - Purpose: ensure least privilege and no secret exposure
- [x] 1.2.2 Enforce methods/paths allowlist (in code) and size limits
  - Files: `/Users/joaquim/projects/menu-planning/backend/services/app/tools/typeform_proxy_lambda/index.mjs`
  - Purpose: prevent misuse and unexpected payload sizes
  - Suggested limits: max 128KB request body; max 1MB response body

## 1.3 Observability
- [x] 1.3.1 Structured logs with correlation_id, method, path, status, latency
  - Files: `/Users/joaquim/projects/menu-planning/backend/services/app/tools/typeform_proxy_lambda/index.mjs`
  - Purpose: clarity for operations
  - Log fields: correlation_id, method, url, statusCode, dur_ms, err_category

## Validation
- [ ] Local/unit tests for allowlist and header injection (Node)
- [ ] Manual curl-style local invocation using `node --experimental-modules` or test harness
- [ ] `poetry run python -m pytest -q` (Python tests still pass)


