---
name: api-integration-design
description: Guides the agent through designing API contracts and third-party integration strategies at the architectural level — NO implementation code is produced. Covers RESTful API design principles (consistency, versioning, idempotency, error schema, observability), Contract-First design (OpenAPI 3.1), integration pipeline design (async queue, webhook, circuit breaker, reconciliation), and the Adapter Pattern for external providers (Payment, SMS, etc.). Activate when the user requests an API specification, OpenAPI/Swagger contract, integration strategy document, webhook design, idempotency strategy, or any communication contract between system boundaries and external services.
triggers:
  - "api design"
  - "openapi"
  - "swagger"
  - "integration strategy"
  - "api contract"
  - "webhook design"
  - "rest api"
  - "idempotency"
  - "payment integration"
  - "third-party integration"
  - "api versioning"
  - "integration pipeline"
---

# API & Integration Design

This skill positions the agent as the **"API & Integration Design"** department of the Solution Architecture Consultancy. Its sole mandate is to produce **communication contracts and integration blueprints** — not implementation code.

The output of this skill is consumed by independent engineering teams as the authoritative specification for what to build.

## When to Use This Skill

- Use when designing **new REST API endpoints** or defining a resource model for a service.
- Use when producing an **OpenAPI 3.1 specification** as a Contract-First deliverable.
- Use when designing the **integration strategy** for a third-party provider (Payment, SMS, Email, KYC, etc.).
- Use when defining **webhook contracts**, idempotency strategies, or async queue pipelines.
- Use when **reviewing an existing API design** for consistency, security, and standards violations.
- **Do NOT use** to write implementation code (`.js`, `.py`, `.go`, `.java`). All outputs are markdown artifacts, YAML specs, and Mermaid diagrams.

---

## Step-by-Step Instructions

### Step 1: Context Gathering & Scope Definition

Read `resources/api_design_questionnaire.md` and collect the following from the user:

- **Domain & Bounded Context**: Which business domain does this API belong to? (e.g., Order, Payment, User, Inventory)
- **Consumer type**: Who calls this API? (Internal frontend, mobile app, partner API, machine-to-machine)
- **Integration type**: Internal API or third-party integration?
- **Sensitivity level**: Does the API handle financial transactions, PII, or health data?
- **Scale expectation**: Estimated RPS, peak load, SLA requirements.
- **Existing conventions**: Does the project already have an API convention (`snake_case` vs `camelCase`, existing version scheme)?

Do not proceed to design until the domain, consumer type, and sensitivity level are established.

---

### Step 2: Resource Modeling (Domain → Resource)

Apply **Domain-Driven Design (DDD)** noun-first resource modeling:

1. List all **business nouns** from the domain (e.g., `Order`, `Payment`, `Invoice`, `User`).
2. Map each noun to a **REST resource** with plural naming: `/orders`, `/payments`, `/invoices`.
3. **Reject action-based endpoints**: `/doPayment` ❌ → `POST /payments` ✅; `/getUser` ❌ → `GET /users/{id}` ✅.
4. Define **resource relationships**: nested only up to one level (e.g., `/orders/{id}/items`). Avoid deeply nested paths.
5. Document in `resources/resource_model.md`.

---

### Step 3: API Design — Apply the 9 Core Principles

Read `resources/api_design_principles.md` and enforce every principle on the spec being designed:

| # | Principle | Key Rule |
|---|---|---|
| 1 | **Consistency** | `snake_case` OR `camelCase` — never mixed. Plural resource names. |
| 2 | **Standard HTTP Semantics** | Correct verb + correct status code. Never `200 OK` with `{"error":...}` in body. |
| 3 | **Versioning** | Always `/v1/...` from day one. Breaking changes bump major version. |
| 4 | **Payload Optimization** | All `GET` list endpoints MUST have pagination + filtering + sorting. |
| 5 | **Security by Design** | UUID over auto-increment IDs. JWT/OAuth2. Rate Limiting declared. |
| 6 | **Uniform Error Schema** | All errors MUST use RFC 7807 Problem Details (`type, title, status, detail, instance`). |
| 7 | **Backward Compatibility** | New fields are optional. Deprecated fields use `Sunset`/`Deprecation` headers before removal. |
| 8 | **Idempotent Mutations** | `POST` for important mutations (order creation, payments) MUST support `Idempotency-Key` header. |
| 9 | **Observability Contract** | Every request propagates `X-Request-ID` or W3C `traceparent`. Document in spec. |

---

### Step 4: Contract-First Design (Spec Before Code)

> **Rule**: The OpenAPI spec is the Single Source of Truth. Code follows the spec — never the reverse.

1. **Draft the OpenAPI 3.1 YAML** using `resources/template_openapi.yaml` as the base template.
2. Structure must include:
   - `info` block: title, version, description with breaking-change policy.
   - `servers`: versioned base URL.
   - `paths`: every endpoint with summary, parameters, requestBody, responses (200/201/400/401/403/404/409/422/500).
   - `components.schemas`: all domain objects + RFC 7807 `Error` schema.
   - `components.securitySchemes`: `bearerAuth` (JWT) or `oauth2`.
   - `security`: applied globally or per-operation.
3. Every endpoint must have **example request and response** in the spec.
4. Run the **Design Review Checklist** (Step 5) before finalizing.

---

### Step 5: Design Review Checklist

Before delivering the spec, verify every item:

- [ ] Naming is consistent with all existing resources in the system
- [ ] Every `GET` list endpoint has `page`, `limit`, `sort`, and filter parameters
- [ ] All error responses reference the central `Error` (RFC 7807) schema
- [ ] `security` field declared on every protected operation
- [ ] Rate limit response headers documented (`X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`)
- [ ] `Idempotency-Key` header declared on all important `POST` mutations
- [ ] `X-Request-ID` or `traceparent` documented in request headers
- [ ] Example request/response provided for every operation
- [ ] `Deprecated` flag set on any retiring operations

---

### Step 6: Integration Pipeline Design (Third-Party)

For third-party integrations (Payment, SMS, KYC, etc.), design the full async pipeline using `resources/integration_pipeline_template.mmd`:

**Mandatory Pipeline Pattern:**
```
[Client Request]
      │
      ▼
[API Gateway] → validate, auth, rate limit
      │
      ▼
[Service Layer] → idempotency check → create PENDING record
      │
      ▼
[Queue: BullMQ / Kafka] → decouple from request cycle → return 202 Accepted
      │
      ▼
[Worker] → Adapter (PaymentInterface / SMSInterface)
         → Timeout (3–5s) + Retry (Exponential Backoff + Jitter) + Circuit Breaker
         │
         ├── Success → update status, emit event
         └── Fail    → Fallback Provider OR Dead Letter Queue
      │
      ▼
[Webhook Receiver] → verify HMAC signature → dedupe by event_id → update final status
      │
      ▼
[Reconciliation Job] → periodic cross-check against provider's query API
```

**Design Rules:**
- **Never synchronously block** on a third-party call from the main request thread.
- **Adapter Pattern is mandatory**: Core logic depends on `PaymentGatewayInterface`, not a specific SDK.
- **Webhook security**: HMAC-SHA256 signature verification + timestamp + nonce replay protection.
- **Reconciliation job**: Minimum once-per-hour cron to detect lost webhooks.
- **Data boundary**: Never store raw card numbers, OTPs. Store only provider-issued tokens/reference IDs (PCI-DSS).

---

### Step 7: Produce the Integration Strategy Document

Use `resources/template_integration_strategy.md` to produce the deliverable for stakeholders and partners. The document must cover:

1. **Integration Objective** — Business context and provider selection rationale.
2. **Architecture** — Sync vs. Async decision, sequence diagram (Mermaid).
3. **Idempotency Strategy** — Key generation, TTL (typically 24h), collision behavior.
4. **Error Handling & Retry Policy** — Timeout value, retry count, backoff formula, circuit breaker thresholds.
5. **Webhook Contract** — Receiver endpoint, signature method, idempotent processing.
6. **Reconciliation** — Frequency, data source, mismatch resolution.
7. **Security & Compliance** — Data ownership boundary, what is NOT stored.
8. **Rollback Plan** — Feature flag kill switch, manual fallback flow.

---

### Step 8: Deliverables

Produce standardized outputs using templates in `resources/` and `examples/`:

**For API design** → Deliver:
- `api-contract.yaml` — Full OpenAPI 3.1 specification.
- `resource_model.md` — Domain nouns mapped to REST resources.

**For third-party integration** → Deliver:
- `integration_strategy.md` — Full integration strategy document from `resources/template_integration_strategy.md`.
- `integration_flow.mmd` — Mermaid sequence diagram of the full async pipeline.

**For both** → Also run the Design Review Checklist and report any violations found.

---

## Decision Trees

- If the API handles **financial transactions** → Mandatory: `Idempotency-Key` on all mutations, async pipeline, reconciliation job, PCI-DSS data boundary.
- If the API handles **PII or health data** → Mandatory: UUID IDs, field-level encryption note in spec, GDPR/HIPAA compliance annotation.
- If this is a **public/partner API** → Mandatory: versioning from day one, backward compatibility policy, `Deprecated` header workflow, published `Sunset` dates.
- If this is an **internal API** → Still required: consistent naming, UUID IDs, error schema, but idempotency and versioning may be lighter-weight.
- If **breaking changes** are needed → Create a new version (`/v2`). Never mutate a published `/v1` contract.
- If consumer is **mobile** → Prioritize payload size (sparse fieldsets), explicit deprecation timelines (mobile release cycles are slow).

---

## Accompanying Resources

- `resources/api_design_questionnaire.md` — Pre-design context collection form.
- `resources/api_design_principles.md` — Full 9-principle reference with examples and anti-patterns.
- `resources/template_openapi.yaml` — Reusable OpenAPI 3.1 base template.
- `resources/template_integration_strategy.md` — Integration strategy document template for stakeholders.
- `resources/postman_mcp_integration.md` — Guide to setting up and using Postman MCP Server for API testing, mock generation, and code generation.
- `examples/order_service_openapi.yaml` — Full worked example: Order Service API contract.
- `examples/payment_integration_flow.mmd` — Full worked example: Payment Gateway integration pipeline (Mermaid).
- `examples/core_banking_openapi.yaml` — Full worked example: Core Banking Engine OpenAPI 3.1 contract (Double-Entry Ledger, Accounts, Holds, Transfers).
- `examples/core_banking_transfer_flow.mmd` — Full worked example: Core Banking Fund Transfer & Clearing Pipeline (Mermaid sequence diagram).
- `examples/core_banking_api_blueprint.md` — Full worked example: Core Banking Architecture Blueprint (Double-entry principle, ACID locking, Outbox, 3-Way Reconciliation).
