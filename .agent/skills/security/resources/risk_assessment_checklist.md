# Risk Assessment Checklist

<!--
name: risk_assessment_checklist
description: Domain-by-domain risk assessment checklist covering authentication, data protection, network security, cloud/container hardening, supply chain, API security, and AI/agent-specific risks. Score each item to prioritize remediation.
-->

## How to Use This Checklist
For each item, assign a status:
- ✅ **Compliant** — The control is fully implemented.
- ⚠️ **Partial** — The control is partially implemented or documented but not enforced.
- ❌ **Missing** — The control is absent.
- N/A — Not applicable to this system.

Use the results to build a prioritized remediation backlog. Address all ❌ items rated **Critical** or **High** before production launch.

---

## 1. Authentication & Identity

| Status | Risk Level | Control |
|---|---|---|
| | Critical | Passwords are hashed using bcrypt, argon2, or scrypt (NOT MD5, SHA-1, or plaintext). |
| | Critical | Multi-Factor Authentication (MFA) is enforced for admin and privileged accounts. |
| | High | Session tokens are stored in `httpOnly + secure + SameSite` cookies. |
| | High | Sessions are invalidated immediately on user logout and password change. |
| | High | JWT tokens carry an `exp` claim and are signed with RS256. |
| | High | JWT payloads do not contain sensitive PII or credential data. |
| | Medium | Account lockout or exponential backoff is applied after repeated failed login attempts. |
| | Medium | Password reset tokens are single-use, short-lived, and sent to a verified channel. |
| | Medium | OAuth2/OIDC flows enforce PKCE for public clients; `redirect_uri` is strictly validated. |

---

## 2. Authorization & Access Control

| Status | Risk Level | Control |
|---|---|---|
| | Critical | Principle of Least Privilege is applied to all IAM roles, DB users, and service accounts. |
| | Critical | All authorization checks are enforced at the backend (server-side), not frontend. |
| | Critical | Object IDs (user_id, order_id) passed from the client are validated for ownership before accessing records (IDOR prevention). |
| | High | Role-Based Access Control (RBAC) or Attribute-Based Access Control (ABAC) is implemented. |
| | High | Multi-tenant systems enforce `tenant_id` filtering at the data access layer. |
| | High | Row-Level Security (RLS) is enabled in the database for tenant-isolated data. |
| | Medium | Access rights are reviewed and revoked immediately upon employee offboarding. |
| | Medium | Privileged access (admin, DBA) uses just-in-time provisioning and is logged. |

---

## 3. Data Protection

| Status | Risk Level | Control |
|---|---|---|
| | Critical | All data-in-transit is protected by TLS 1.2 or higher. |
| | Critical | Sensitive data-at-rest is encrypted using AES-256. |
| | Critical | No secrets, API keys, or passwords are hardcoded in source code or configuration files. |
| | Critical | Secrets are managed via a vault service (e.g., HashiCorp Vault, AWS Secrets Manager) or environment variables injected at runtime. |
| | High | Backup data is encrypted and stored separately with restricted access. |
| | High | Restore procedures are tested at least once per quarter. |
| | High | Encryption keys are rotated on a defined schedule. |
| | Medium | Sensitive fields (card numbers, SSN, health data) are masked or tokenized in the UI. |
| | Medium | Logs do not contain passwords, tokens, PII, or card data. |
| | Medium | Data residency requirements are met (e.g., Vietnamese user data stored in Vietnam per NĐ 53/2022). |

---

## 4. Input Validation & Injection Prevention

| Status | Risk Level | Control |
|---|---|---|
| | Critical | All external inputs are validated server-side using whitelists. |
| | Critical | Database queries use Parameterized Queries or ORM — no string concatenation with user input. |
| | Critical | Output is contextually escaped (HTML, JS, URL, SQL) to prevent XSS. |
| | High | File uploads are validated for type, size, and content. Uploaded files are not executed. |
| | High | XML parsers have external entity processing (XXE) disabled. |
| | High | Outbound server-side HTTP requests validate/allowlist target URLs to prevent SSRF. |
| | Medium | Deserialization of untrusted formats (Python pickle, Java serialization) is prohibited. |
| | Medium | Template engines receive only sanitized data — no dynamic template construction from user input (SSTI prevention). |

---

## 5. Network & Infrastructure Security

| Status | Risk Level | Control |
|---|---|---|
| | Critical | Databases and internal services are not directly accessible from the public internet. |
| | Critical | Production environment uses network segmentation (public vs private subnets). |
| | High | Security Groups / Firewall rules follow a default-deny policy; only necessary ports are open. |
| | High | Service-to-service communication uses mutual TLS (mTLS) or an equivalent authenticated channel. |
| | High | Cloud IAM roles follow Least Privilege; no root keys or wildcard (`*`) permissions are used in production. |
| | High | Infrastructure changes are managed via IaC (Terraform/Pulumi) with PR reviews required. |
| | Medium | CSPM tooling (e.g., AWS Config, Wiz) scans for cloud misconfigurations continuously. |
| | Medium | Container images are scanned for CVEs before deployment. |
| | Medium | Containers do not run as root. |

---

## 6. Supply Chain & Dependencies

| Status | Risk Level | Control |
|---|---|---|
| | High | Dependency versions are pinned. Lock files (`package-lock.json`, `poetry.lock`) are committed. |
| | High | Automated dependency scanning (Dependabot, Snyk, `npm audit`) runs in CI/CD. |
| | High | New dependencies are reviewed for license compatibility and repository trustworthiness before adoption. |
| | Medium | An SBOM (Software Bill of Materials) is maintained and updated on each release. |
| | Medium | CI/CD pipeline secrets are masked in build logs. |
| | Medium | Branch protection rules prevent direct pushes to main; at least one approver is required per PR. |

---

## 7. API Security

| Status | Risk Level | Control |
|---|---|---|
| | Critical | Rate limiting and throttling are applied per user and per IP at the API Gateway or application level. |
| | High | CORS is configured with specific origins — wildcard `*` is never used with credentials. |
| | High | API endpoints validate input schema (Pydantic, Joi, OpenAPI). Oversized or malformed payloads are rejected. |
| | High | GraphQL introspection is disabled in production. Query depth and complexity limits are enforced. |
| | Medium | API versioning is in place to allow safe deprecation of old endpoints. |

---

## 8. AI & Agent-Specific Security

| Status | Risk Level | Control |
|---|---|---|
| | Critical | All user-supplied prompts are sanitized to prevent Prompt Injection before being passed to the LLM. |
| | Critical | Agent-generated tool call arguments are validated and sanitized before execution. |
| | Critical | All Vector DB queries include `tenant_id` and `user_id` metadata filters to prevent cross-session data leakage. |
| | High | Agents require Human-in-the-loop approval before executing any irreversible action (file writes, DB mutations, external API calls). |
| | High | LLM output is validated and sanitized before being returned to the frontend (prevent LLM-generated XSS). |
| | High | LLM agents are granted Least Privilege — only the tools and scopes strictly required for the task. |
| | Medium | RAG document ingestion pipeline validates and sandboxes ingested content to prevent Indirect Prompt Injection. |

---

## 9. Repository & Secrets Hygiene

| Status | Risk Level | Control |
|---|---|---|
| | Critical | A `.gitignore` file exists at the project root. |
| | Critical | `.env`, `*.pem`, `*.key`, `secrets.*`, `credentials.*` files are listed in `.gitignore`. |
| | Critical | No sensitive files are currently tracked by Git (`git ls-files` audit passed). |
| | High | `node_modules/`, `venv/`, `.venv/`, `dist/`, `build/` directories are listed in `.gitignore`. |
| | High | IDE and OS config files (`.vscode/`, `.idea/`, `.DS_Store`, `Thumbs.db`) are listed in `.gitignore`. |
| | Medium | Pre-commit hooks or CI checks scan for secret leaks (e.g., using `detect-secrets` or `gitleaks`). |
