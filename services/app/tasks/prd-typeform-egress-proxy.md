# PRD: Typeform Egress Proxy Lambda

---
feature: typeform-egress-proxy
complexity: detailed
created: 2025-08-11
version: 1.0
---

## Executive Summary
### Problem Statement
Lambdas inside our VPC cannot reach `api.typeform.com` (TCP connect hangs) without a NAT gateway. This blocks onboarding flows (Typeform form verification/webhook setup) and previously obscured failures.

### Proposed Solution
Introduce a small helper Lambda (Node.js 20) deployed outside the VPC to proxy outbound HTTPS calls to `api.typeform.com`. Private Lambdas invoke it synchronously via the Lambda Invoke API through a VPC interface endpoint. The proxy enforces an allowlist of methods/paths and injects the Typeform API key from a managed secret.

### Business Value
- Avoids NAT gateway cost/ops
- Unblocks critical onboarding path
- Improves observability and error clarity

### Success Criteria
- Create/Update/Delete webhook flows succeed without NAT
- p95 end-to-end extra latency via proxy < 150ms
- Clear error classification (DNS, connect, TLS, read, 4xx/5xx)
- Invocation restricted to specific caller roles

## Goals and Non-Goals
### Goals
1. Provide reliable egress to Typeform from private Lambdas.
2. Enforce strict security (allowlist, secret isolation, least privilege).
3. Deliver strong observability (structured logs, metrics, alarms).
4. Minimize cold start and steady-state latency.

### Non-Goals
1. Generic HTTP proxy for arbitrary destinations.
2. NAT replacement for all services.
3. UI or domain logic changes.

## User Stories
### Story 1: Proxy Invocation
As a backend service, I want to invoke a helper Lambda to perform Typeform API calls so that my private Lambda can operate without NAT.
- [ ] Given valid request, when invoking helper with path/method in allowlist, then response contains Typeform status/body/headers.

### Story 2: Error Transparency
As an operator, I want distinct error categories logged so that I can diagnose network vs. app errors quickly.
- [ ] DNS/connect/TLS timeouts are logged with correlation_id and classified.

### Story 3: Security Guardrails
As a security engineer, I want strict resource policies and method/path allowlist so that misuse is prevented.
- [ ] Only caller role(s) can invoke helper; Authorization header cannot be overridden by caller.

## Technical Specifications
### System Architecture
- Caller Lambda(s) in VPC -> VPC Endpoint (Lambda) -> Helper Lambda (public, no VPC) -> `api.typeform.com` over HTTPS.
- Secrets Manager/SSM stores `TYPEFORM_API_KEY`; helper reads at startup/runtime.
- CloudWatch Logs for both Lambdas; metrics via embedded metric format or CW metrics filters.

### Proxy Contract (Helper Lambda Input/Output)
Input (JSON):
- method: GET|PUT|DELETE (limited set)
- path: e.g., `forms/{id}`, `forms/{id}/webhooks/{tag}`
- query: object of query params (optional)
- headers: limited pass-through (e.g., If-None-Match) (optional)
- body: string or object (optional)
- correlation_id: string (optional)

Output (JSON):
- statusCode: integer
- headers: map (sanitized)
- body: string (raw Typeform response body)

### Allowed Targets
- Host: `api.typeform.com`
- Paths: `^/forms/`, `^/forms/[^/]+/webhooks(/[^/]+)?$`
- Methods: GET, PUT, DELETE

### Security
- Resource policy on helper: allow `lambda:InvokeFunction` only from specified caller role(s)/account(s).
- IAM role for helper: read secret, write logs, egress to internet.
- IAM role for caller: permission to invoke helper; no access to Typeform secret.
- Strip/ignore inbound Authorization headers; inject `Bearer ${TYPEFORM_API_KEY}` in helper.
- Validate and reject non-allowlisted paths/methods.

### Configuration
- Feature flag: `TYPEFORM_VIA_PROXY=true|false`
- Helper function name: `TYPEFORM_PROXY_FUNCTION_NAME`
- Timeouts: helper connect 5s, read aligned to business need; caller end-to-end < api timeout.

### Performance & Limits
- Runtime: Node.js 20 (fast cold start) or Go as alternative.
- HTTP client: node-fetch/undici with AbortController and 5s connect budget.
- Concurrency: provisioned concurrency optional to cap cold start.

## Functional Requirements
1. FR-Proxy-Allowlist: Reject requests outside configured paths/methods.
2. FR-Auth-Injection: Always inject Typeform API key; forbid caller-supplied auth.
3. FR-Observability: Log correlation_id, method, URL, status, latency; classify network vs. HTTP errors.
4. FR-Config-Flag: Toggle usage per env via config.
5. FR-Error-Mapping: Map 4xx/5xx transparently; return 503 for network failures.

## Non-Functional Requirements
- Reliability: 99.9% monthly availability for helper.
- Latency: Additional p95 latency < 150ms.
- Security: Least privilege IAM; no secret exposure to caller.
- Cost: No NAT required; helper execution cost minimal.

## Risk Assessment
- Network Egress Blocked: Helper must be public/no VPC to ensure internet access.
- Secret Exposure: Ensure no echo of Authorization; restrict logs.
- Abuse/Misuse: Enforce allowlist and resource policies.
- Latency Inflation: Consider provisioned concurrency if needed.

## Testing Strategy
- Unit tests for allowlist, header injection, error mapping.
- Integration tests: end-to-end invoke -> Typeform mock.
- Load tests: measure added latency.
- Security tests: validate policy restrictions.

## Implementation Plan
### Phase 1: Proxy Lambda
- [ ] Create helper Lambda (Node.js 20) and package.
- [ ] Add allowlist and error handling; structured logs with correlation_id.
- [ ] Read `TYPEFORM_API_KEY` from Secrets Manager/SSM.

### Phase 2: Infra & IAM
- [ ] Resource policy to allow invoke from caller role(s).
- [ ] Add VPC Interface Endpoint for Lambda in caller VPC.
- [ ] Update IAM roles/policies.

### Phase 3: Client Integration
- [ ] Add proxy toggle and client implementation in Python (`TypeFormClient` proxy path).
- [ ] Map responses/errors consistently with current client semantics.

### Phase 4: Observability & Alarms
- [ ] CW metrics (success rate, p95 latency, 4xx/5xx, connect errors).
- [ ] Alarms for error rate and latency.

### Phase 5: Rollout
- [ ] Stage in dev -> staging -> prod with flag gating.
- [ ] Remove NAT dependency (if present) after validation.

## Monitoring
- Metrics: Invocations, Success %, p95 latency, ConnectError count, 4xx/5xx by code.
- Logs: Correlation id, method, path, status, timing; redacted headers.

## Dependencies
- AWS Lambda, IAM, VPC Endpoint (Lambda), CloudWatch, Secrets Manager.
- Typeform availability.

## Timeline
- Phase 1–2: 3–4 days
- Phase 3–4: 3–4 days
- Phase 5: 1–2 days
