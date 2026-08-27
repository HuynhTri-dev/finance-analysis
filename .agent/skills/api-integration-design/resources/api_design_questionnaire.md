# API Design Pre-Engagement Questionnaire

Use this questionnaire at **Step 1** of the API & Integration Design skill. Ask the user these questions before drafting any spec or diagram.

---

## Section A — Domain & Business Context

1. **What is the name of this service/domain?**
   - Example: `Order Service`, `Payment Service`, `User Identity`

2. **What Bounded Context (DDD) does this API belong to?**
   - Example: `Order Management`, `Billing`, `Auth & IAM`

3. **What specific business capabilities does this API expose?**
   - Example: "Create orders, list orders by status, cancel an order"

4. **Are there existing APIs in this system I should align with?**
   - If yes: What naming convention do they use? (`snake_case` / `camelCase`)
   - What base URL pattern? (e.g., `https://api.example.com/v1`)

---

## Section B — Consumer & Integration Type

5. **Who are the consumers of this API?**
   - [ ] Internal frontend (web SPA)
   - [ ] Internal mobile app (iOS/Android)
   - [ ] Internal backend service (service-to-service)
   - [ ] External partner/B2B integration
   - [ ] Public developer API

6. **Is this an internal API design or a third-party integration design?**
   - **Internal** → Proceed to Section C.
   - **Third-party integration** → Also complete Section D.

7. **What is the expected request volume?**
   - Estimated peak RPS (requests per second)?
   - SLA requirement? (e.g., 99.9% uptime, p99 < 500ms)

---

## Section C — Security & Compliance

8. **What type of data does this API handle?**
   - [ ] Financial transaction data (→ PCI-DSS implications)
   - [ ] Personally Identifiable Information / PII (→ GDPR/PDPA implications)
   - [ ] Health/medical data (→ HIPAA implications)
   - [ ] General non-sensitive business data

9. **What authentication mechanism is in place?**
   - [ ] JWT Bearer Token
   - [ ] OAuth 2.0 (specify grant type)
   - [ ] API Key
   - [ ] mTLS (mutual TLS)
   - [ ] Not yet decided

10. **Are there rate limiting requirements?**
    - Per-user limit? Per-IP limit? Burst allowance?

---

## Section D — Third-Party Integration Context (complete if applicable)

11. **Which third-party provider is being integrated?**
    - Example: VNPay, Stripe, Twilio, SendGrid, Momo, ZaloPay

12. **What is the integration pattern?**
    - [ ] Synchronous (request → immediate response from provider)
    - [ ] Asynchronous (request → PENDING → Queue → Webhook callback)

13. **Does the provider support webhooks?**
    - If yes: What signature method do they use? (HMAC-SHA256, etc.)

14. **Is there a fallback provider if this integration fails?**
    - Example: VNPay fails → fallback to Momo

15. **What is the criticality of this integration?**
    - [ ] Mission-critical (payment, account creation)
    - [ ] Important but degradable (SMS notification)
    - [ ] Nice-to-have (analytics ping)

16. **Are there compliance constraints on data storage?**
    - Example: "We cannot store card numbers per PCI-DSS"
