# Feature Assessment: Typeform Egress Proxy Lambda

---
feature: typeform-egress-proxy
assessed_date: 2025-08-11
complexity: detailed
---

## Feature Overview
**Description**: Introduce a helper AWS Lambda (outside VPC) to proxy outbound requests to `api.typeform.com`, invoked synchronously from our private Lambdas via the Lambda Invoke API, removing the need for a NAT gateway while improving observability and error classification.
**Primary Problem**: Current Lambdas in VPC cannot reach the internet (hangs on TCP connect) without NAT; logs lacked visibility before. We need a reliable, observable egress path for Typeform API.
**Business Value**: Reduces infrastructure cost/complexity (no NAT), unblocks onboarding flows, and improves reliability with clearer errors and metrics.

## Complexity Determination
**Level**: detailed
**Reasoning**: Cross-service architecture (two Lambdas), VPC endpoints, IAM resource policies, secret management, error mapping, feature flagging, and deployment coordination.

## Scope Definition
**In-Scope**:
- New helper Lambda (Node.js 20 runtime) with minimal proxy to Typeform (strict allowlist).
- Caller Lambda changes (Python) to optionally route Typeform calls through proxy (feature flag).
- IAM: resource-based policy to restrict `lambda:InvokeFunction` to caller role; least-privileged execution roles.
- Network: VPC interface endpoint for Lambda to allow private invoke; no NAT required.
- Secrets: store `TYPEFORM_API_KEY` in Secrets Manager/SSM.
- Observability: structured logs with correlation_id, status lines; metrics and alarms.

**Out-of-Scope**:
- NAT gateway setup/removal beyond recommendation.
- Proxying other third-party APIs.
- UI changes.

**Constraints**:
- Maintain current business logic and message bus behavior.
- Keep latency overhead from proxy hop minimal (<150ms p95 under normal conditions).

## Requirements Profile
**Users**: Backend services (client onboarding), DevOps, Observability.
**Use Cases**: Create/update/delete Typeform webhooks; GET form metadata; handle rate limits and network errors clearly.
**Success Criteria**:
- End-to-end create form succeeds without NAT.
- p95 connect+TLS time to Typeform via proxy < 300ms in sa-east-1.
- Clear error surfaces for DNS/Connect/Timeout/HTTP 4xx/5xx.
- Invocation restricted to designated caller roles (policy enforced).

## Technical Considerations
**Integrations**: AWS Lambda, Lambda VPC endpoint, IAM, CloudWatch Logs, AWS Secrets Manager/SSM, Typeform API.
**Performance**: Fast-cold-start runtime (Node.js 20); connect timeout 5s; read timeout aligned to config.
**Security**: Secret never passed from caller; proxy injects Authorization; path/method allowlist; resource policy to limit invoke; TLS only.
**Compliance**: Log redaction for sensitive headers; no PII persisted.

## PRD Generation Settings
**Detail Level**: detailed
**Target Audience**: mixed team (backend + DevOps)
**Timeline**: tight (1–2 sprints)
**Risk Level**: medium

## Recommended PRD Sections
- Executive Summary, Goals/Non-Goals, Architecture, API (proxy contract), Security, NFRs, Risks, Testing, Implementation Plan, Monitoring, Dependencies, Timeline.

## Next Step
Ready for PRD generation with prd-2-generate-prd-document.mdc


