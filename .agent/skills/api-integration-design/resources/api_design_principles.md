# API Design Principles — Full Reference

This document is the authoritative reference for the 9 mandatory API design principles enforced by the **API & Integration Design** skill. Read during **Step 3** of the design workflow.

---

## Principle 1 — Consistency

**Rule**: Use a single, project-wide naming convention. Never mix conventions within one system.

| Dimension | Standard |
|---|---|
| Field names | `snake_case` OR `camelCase` — pick one and enforce globally |
| Resource names | Plural nouns: `/users`, `/orders`, `/payments` |
| Path segments | Lowercase, hyphen-separated: `/payment-methods`, not `/paymentMethods` |
| Query parameters | `snake_case`: `?sort_by=created_at`, `?page_size=20` |

**Anti-patterns to reject:**
- Endpoint A returns `user_id`, endpoint B returns `userId`, endpoint C returns `IdUser` — **NEVER**
- Mix of `/getUser` (verb-based) and `/orders` (noun-based) in the same system — **NEVER**

---

## Principle 2 — Standard HTTP Semantics

**Rule**: HTTP method and status code must accurately describe the operation and its outcome.

### Method → Intent Mapping

| Method | Intent | Body? |
|---|---|---|
| `GET` | Read, non-destructive | No |
| `POST` | Create a new resource | Yes |
| `PUT` | Full replace of a resource | Yes |
| `PATCH` | Partial update | Yes |
| `DELETE` | Remove a resource | No |

### Status Code Reference

| Code | When to Use |
|---|---|
| `200 OK` | Successful GET, PUT, PATCH |
| `201 Created` | Successful POST (resource created) |
| `202 Accepted` | Async operation accepted (e.g., job queued) |
| `204 No Content` | Successful DELETE (or PATCH with no body) |
| `400 Bad Request` | Client sent malformed/invalid data |
| `401 Unauthorized` | Missing or invalid authentication credentials |
| `403 Forbidden` | Authenticated but not authorized for the resource |
| `404 Not Found` | Resource does not exist |
| `409 Conflict` | State conflict (e.g., duplicate Idempotency-Key with different payload) |
| `422 Unprocessable Entity` | Valid format but failed business rule validation |
| `429 Too Many Requests` | Rate limit exceeded |
| `500 Internal Server Error` | Unexpected server failure |

**Critical Anti-pattern:**
```json
// ❌ NEVER return 200 with an error body
HTTP/1.1 200 OK
{ "error": "User not found", "code": -1 }

// ✅ CORRECT
HTTP/1.1 404 Not Found
{ "type": "...", "title": "User not found", "status": 404, ... }
```

---

## Principle 3 — Versioning

**Rule**: Version every API from day one. Never deploy a public or partner API without a version prefix.

```
✅  https://api.example.com/v1/orders
❌  https://api.example.com/orders
```

**Version bump policy:**
- **Patch** (`1.0.1`): Bug fixes, no contract change → same URL, no version bump needed.
- **Minor** (`1.1.0`): Additive changes (new optional field, new endpoint) → backward compatible, no URL bump.
- **Major** (`2.0.0`): Breaking change (field removed, type changed, behavior changed) → **MUST** create `/v2` and deprecate `/v1` with `Sunset` header.

**Deprecation workflow:**
1. Add `Deprecated: true` to the operation in OpenAPI.
2. Add response header `Sunset: Sat, 31 Dec 2025 23:59:59 GMT`.
3. Add response header `Deprecation: Mon, 01 Jul 2025 00:00:00 GMT`.
4. Keep `/v1` alive for the published sunset period before removal.

---

## Principle 4 — Payload Optimization

**Rule**: Every `GET` list endpoint MUST support pagination, filtering, and sorting. Never return an unbounded dataset.

**Standard pagination parameters:**
```
GET /orders?page=1&limit=20&sort_by=created_at&sort_order=desc&status=pending
```

**Standard pagination response envelope:**
```json
{
  "data": [ ... ],
  "meta": {
    "page": 1,
    "limit": 20,
    "total": 348,
    "total_pages": 18
  }
}
```

**Maximum limit cap**: Always enforce a server-side maximum (e.g., `limit` cannot exceed `100`).

---

## Principle 5 — Security by Design

**Rule**: Security is a first-class design concern, not an afterthought.

| Control | Rule |
|---|---|
| **IDs** | Use UUID v4 (`format: uuid`) for all resource identifiers exposed externally. Never expose auto-increment integers. |
| **Authentication** | JWT Bearer Token or OAuth2 on every protected endpoint. Document in `securitySchemes`. |
| **Rate Limiting** | Define rate limit policy. Document response headers in spec. |
| **CORS** | Never use `Access-Control-Allow-Origin: *` with credentials. |
| **Input** | All inputs validated server-side. Whitelist-first approach. |

---

## Principle 6 — Uniform Error Schema (RFC 7807)

**Rule**: All services in the system MUST use a single error schema. Adopt **RFC 7807 Problem Details**.

```json
{
  "type": "https://api.example.com/errors/insufficient-stock",
  "title": "Insufficient Stock",
  "status": 409,
  "detail": "SKU ABC123 only has 2 items remaining, but 5 were requested.",
  "instance": "/orders/req-uuid-123"
}
```

| Field | Description |
|---|---|
| `type` | URI identifying the error type (links to human-readable documentation) |
| `title` | Short, human-readable summary of the problem (stable across occurrences) |
| `status` | HTTP status code |
| `detail` | Human-readable, instance-specific explanation |
| `instance` | URI reference to the specific occurrence of the problem |

**Extension fields** are permitted (e.g., `errors: [...]` for validation errors):
```json
{
  "type": "https://api.example.com/errors/validation-failed",
  "title": "Validation Failed",
  "status": 422,
  "detail": "One or more fields failed validation.",
  "instance": "/users",
  "errors": [
    { "field": "email", "message": "Must be a valid email address." },
    { "field": "phone", "message": "Must start with +84." }
  ]
}
```

---

## Principle 7 — Backward Compatibility & Deprecation Policy

**Rule**: A published API contract is a promise to consumers. Breaking it silently is unacceptable.

| Change Type | Backward Compatible? | Action Required |
|---|---|---|
| Add new optional field to response | ✅ Yes | None — consumers must tolerate unknown fields |
| Add new optional query parameter | ✅ Yes | None |
| Add new endpoint | ✅ Yes | None |
| Remove a field from response | ❌ No | Deprecation cycle → major version bump |
| Change a field type | ❌ No | Deprecation cycle → major version bump |
| Change a field from optional to required | ❌ No | Deprecation cycle → major version bump |
| Change HTTP method of an endpoint | ❌ No | Deprecation cycle → major version bump |

---

## Principle 8 — Idempotent Mutations

**Rule**: Any mutation that could cause significant harm if duplicated (financial, account creation, order placement) MUST support an `Idempotency-Key` header.

**How it works:**
1. Client generates a unique UUID v4 as `Idempotency-Key` before sending the request.
2. Server checks if the key has been seen before (TTL: 24 hours typical).
   - **Not seen**: Process the request, store the key + full response.
   - **Already seen, same payload**: Return the cached response immediately with `200 OK`.
   - **Already seen, different payload**: Return `409 Conflict` — key collision.
3. Client can safely retry on network failure without fear of double-execution.

**OpenAPI declaration:**
```yaml
parameters:
  - name: Idempotency-Key
    in: header
    required: true
    schema:
      type: string
      format: uuid
    description: >
      Client-generated unique key to ensure idempotency. 
      Safe to retry with the same key on network failure.
```

---

## Principle 9 — Observability Contract

**Rule**: Every request must carry a trace identifier that can be correlated across all services in a distributed system.

**Standard headers:**
- `X-Request-ID`: A UUID generated by the client or API Gateway for correlation. Echoed back in all responses.
- `traceparent` (W3C Trace Context): Structured distributed trace ID for integration with OpenTelemetry / Jaeger / Zipkin.

**Server behavior:**
1. If `X-Request-ID` is absent, the server generates one and logs it.
2. If `traceparent` is present, propagate it unchanged to all downstream service calls.
3. Include `X-Request-ID` in every response for client-side correlation.

**In error responses**, always include the request ID:
```json
{
  "type": "...",
  "title": "Internal Server Error",
  "status": 500,
  "instance": "/orders",
  "request_id": "550e8400-e29b-41d4-a716-446655440000"
}
```
