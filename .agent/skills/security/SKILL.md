---
name: security-architecture-blueprint
description: Guides the agent through designing, reviewing, and verifying secure system architectures from day one (Shift Left). Covers threat modeling (STRIDE/DREAD), risk economics, application security, cloud and network isolation, AI agent security, and automated scanning. Activate when the user requests security design, a threat model, a vulnerability review, or a source-code security audit.
triggers:
  - "security design"
  - "threat modeling"
  - "risk assessment"
  - "review architecture"
  - "security check"
  - "security audit"
  - "vulnerability review"
---

# Security Architecture Blueprint

This skill positions the agent as the "Security Architecture Hub" for any project. It enforces a **Shift-Left** mindset — embedding security decisions at the earliest phase of design rather than bolting them on at release time.

## When to Use This Skill
- Use this skill when **designing a new system** or microservice boundary from scratch.
- Use this skill when performing **threat modeling** (STRIDE/DREAD) or risk assessment.
- Use this skill when **reviewing existing architecture**, source code, or configurations for security gaps.
- Use this skill when **auditing `.gitignore`** and repository hygiene to ensure secrets are never committed.
- **Do NOT use** when performing active network penetration tests, dynamic binary analysis, or live exploit execution.

---

## Step-by-Step Instructions

### Step 1: Context Gathering & Initial Questionnaire
Read `resources/initial_security_questionnaire.md` and ask the user the relevant questions to collect:
- **Business domain**: Fintech, Healthcare, E-commerce, SaaS, Government, etc.
- **Compliance requirements**: PCI-DSS, HIPAA, GDPR, SOC 2, ISO 27001, Vietnam NĐ 13/2023.
- **Scale**: Expected user count, deployment environment (Cloud: AWS/GCP/Azure vs On-premise).
- **Team resources**: Security expertise, budget, and tooling available.
- **Asset value**: What data or services are being protected and what is their business value?

Do not proceed to Step 2 without establishing the scope of assets and compliance requirements.

### Step 2: Security Economics & Risk Calibration
Read `resources/security_economics_matrix.md` and apply the core rule:

> **Cost to Attack must always exceed the Value of the Target Asset.**

- Calculate `Risk = Likelihood × Impact` for each identified threat. Use `resources/risk_assessment_checklist.md` as the scoring guide.
- **Reject over-engineering**: Do not propose Zero-Trust full-stack, mTLS, or HSM for an early-stage startup with no sensitive PII.
- **Recommend proportional controls**: WAF + rate limiting can block 90% of attacks cheaply.
- Present a cost vs. benefit summary before recommending any architectural component.

### Step 3: Threat Modeling (STRIDE)
Read `resources/threat_modeling_templates.md` and map threats to the system's trust boundaries:

| STRIDE Category | Question to Ask | Primary Control |
|---|---|---|
| **Spoofing** | Can an attacker impersonate a legitimate user or service? | MFA, mTLS, JWT RS256 |
| **Tampering** | Can data be modified in-transit or at-rest? | TLS 1.2+, HMAC, Digital Signatures |
| **Repudiation** | Can an actor deny performing an action? | Immutable audit logs, cryptographic log signing |
| **Info Disclosure** | Can sensitive data be exposed without authorization? | AES-256 at-rest, field-level encryption, output masking |
| **Denial of Service** | Can the system be made unavailable? | Rate limiting, DDoS shields, circuit breakers, redundancy |
| **Elevation of Privilege** | Can a low-privilege actor gain higher permissions? | RBAC/ABAC, Least Privilege IAM, validated IDOR checks |

### Step 4: Application Security Design
Apply the following secure-coding standards when reviewing or generating code:
1. **Authentication & Session Management**:
   - Hash passwords using `bcrypt`, `argon2`, or `scrypt`. Never MD5/SHA-1.
   - Enforce MFA via WebAuthn/FIDO2 or TOTP. Treat SMS OTP as a fallback only (SIM-swap risk).
   - Secure session cookies: `httpOnly + secure + SameSite`. Invalidate sessions on logout and password change.
   - JWTs must carry an `exp` claim, be signed with RS256, and must never contain sensitive PII in the payload.
2. **Input Validation & Injection Prevention**:
   - Validate all external inputs server-side (whitelist-first approach). Client-side validation is UX only.
   - Use Parameterized Queries or ORMs to prevent SQL Injection.
   - Escape output contextually (HTML, JS, URL, SQL) to prevent XSS.
   - Protect against SSRF by validating/allowlisting outbound URLs. Block metadata endpoints (`169.254.169.254`).
3. **Data Protection**:
   - Enforce TLS 1.2+ on all data-in-transit connections.
   - Apply AES-256 encryption for data-at-rest, especially PII and health data.
   - Rotate secrets regularly. Use a Vault (HashiCorp Vault, AWS Secrets Manager) for secret distribution.
   - Mask sensitive fields in logs (passwords, tokens, card numbers, PII).
4. **AI & Agent Security**:
   - Sanitize user prompts to prevent Direct and Indirect Prompt Injection (especially via RAG document ingestion).
   - Never trust LLM-generated tool call arguments. Validate and sanitize them as if they are untrusted user input.
   - Require Human-in-the-loop approval for all agent actions that mutate data (DB writes, file deletions, API calls with side effects).
   - Enforce `tenant_id` and `user_id` metadata filters on every Vector DB query to prevent cross-session context bleed.
5. **API Security**:
   - Apply rate limiting and throttling per user and per IP.
   - Configure CORS strictly — never use `*` with credentials.
   - Disable GraphQL introspection in production and limit query depth.

### Step 5: Infrastructure & Cloud Security
1. **Network Segmentation**: Separate systems into public/private/database subnets. Databases must never be directly accessible from the internet.
2. **Zero Trust Communication**: Authenticate every service-to-service call. Apply mTLS via a service mesh (Istio, Linkerd).
3. **Multi-tenant Isolation**: Apply `tenant_id` as a mandatory filter at the data access layer. Use PostgreSQL Row-Level Security (RLS).
4. **Container Security**: Do not run containers as `root`. Use minimal base images (Distroless/Alpine).
5. **IaC & Change Management**: Manage all infrastructure via code (Terraform/Pulumi). Require PR reviews before applying changes to production.

### Step 6: Mobile Security (if applicable)
1. Detect root/jailbreak using SafetyNet/Play Integrity API (Android) or DeviceCheck/App Attest (iOS).
2. Store credentials and tokens in Keychain (iOS) or Android Keystore.
3. Implement SPKI-based Certificate Pinning with at least 2 backup keys.
4. Obfuscate with R8/ProGuard (Android); strip symbols (iOS).

### Step 7: Automated Scanning & Verification
Run tools and report findings. Use `--help` to inspect available arguments rather than reading script source:
1. **Source Code Security Scan**:
   ```bash
   python scripts/general_security_scanner.py --dir .
   ```
2. **Gitignore Audit** (ensures no sensitive files are tracked by Git):
   ```bash
   python scripts/gitignore_checker.py --dir .
   ```
3. **Dependency Vulnerability Audit**:
   ```bash
   npm audit        # Node.js
   safety check     # Python
   ```
4. **Container Image Scan** (before deployment):
   ```bash
   trivy image <image_name>:<tag>
   ```

### Step 8: Deliverables
Based on the request type, produce standardized outputs using templates in `resources/`:

**For new system design** → Use `resources/template_security_architecture.md`:
- Security Architecture Diagram (Mermaid flowchart showing trust boundaries and security controls).
- Secure Coding Guidelines tailored to the project's language stack.
- Access Control Matrix (RBAC/ABAC: who can read/write what).
- Incident Response Quick Reference for developers.

**For existing system review/audit** → Use `resources/template_vulnerability_report.md`:
- Current Architecture Diagram (describe actual data flows and security controls).
- Vulnerability Assessment Report (rated Critical/High/Medium/Low with remediation steps).
- Gitignore and secret-leak findings from automated scans.

---

## Decision Trees

- If the project handles **payment card data** → Mandatory: PCI-DSS controls, tokenization, TLS 1.2+, audit logs.
- If the project handles **health data** → Mandatory: HIPAA/GDPR controls, field-level encryption, access control matrix.
- If the project is a **SaaS/multi-tenant platform** → Mandatory: Tenant isolation at DB, cache, and Vector DB layers.
- If the system uses **LLM/AI agents** → Mandatory: Prompt injection guards, tool call validation, human-in-the-loop for mutations.
- If the project is an **MVP with low asset value** → Apply: Basic auth, TLS, CORS, rate limiting. Defer: HSM, mTLS, full Zero-Trust.

---

## Accompanying Scripts & Resources
- `resources/initial_security_questionnaire.md` — Pre-engagement context collection.
- `resources/risk_assessment_checklist.md` — Risk scoring by domain.
- `resources/security_economics_matrix.md` — Build vs Buy vs OSS cost analysis.
- `resources/threat_modeling_templates.md` — STRIDE/DREAD templates.
- `resources/template_security_architecture.md` — New system design document template.
- `resources/template_vulnerability_report.md` — Audit report template.
- `scripts/general_security_scanner.py` — Regex-based SAST scanner.
- `scripts/gitignore_checker.py` — Gitignore coverage and git-tracked file auditor.
