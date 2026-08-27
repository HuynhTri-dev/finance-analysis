# Security Economics Matrix

<!--
name: security_economics_matrix
description: A decision framework to evaluate the cost vs. risk trade-off for any proposed security control. Guides the agent to recommend proportional solutions rather than over-engineering.
-->

## Core Principle

> **A security control is justified if and only if: Cost to Attack > Value of the Target Asset.**
>
> Conversely, the cost to implement and maintain a control must be proportional to the risk it mitigates.
> A control that costs more than the asset it protects is a poor investment.

---

## Risk Scoring Formula

```
Risk Score = Likelihood (1–5) × Impact (1–5)

Risk Level:
  1–4   → Low      → Address in next sprint
  5–9   → Medium   → Address in current quarter
  10–19 → High     → Address before next release
  20–25 → Critical → Address immediately
```

---

## Build vs. Buy vs. OSS Decision Matrix

| Control | Build (Custom) | Buy (Commercial SaaS) | Open Source (OSS) |
|---|---|---|---|
| **Identity / Auth** | ❌ High risk; avoid. Auth is complex and easy to get wrong. | ✅ Auth0, Okta, Cognito. Fast and battle-tested. | ✅ Keycloak, Supertokens for self-hosted control. |
| **Web Application Firewall (WAF)** | ❌ Impractical for most teams. | ✅ Cloudflare WAF, AWS WAF. Cost-effective at scale. | ⚠️ ModSecurity — high maintenance burden. |
| **Secret Management** | ❌ Avoid. Homegrown vaults introduce key management risks. | ✅ AWS Secrets Manager, Azure Key Vault. | ✅ HashiCorp Vault — excellent OSS option. |
| **Dependency Scanning (SCA)** | N/A | ✅ Snyk, Checkmarx SCA. Rich reporting. | ✅ `npm audit`, `safety`, OWASP Dependency-Check. |
| **Container Scanning** | N/A | ✅ Wiz, Prisma Cloud. | ✅ Trivy, Grype — production-ready and free. |
| **SAST / Static Analysis** | ✅ Custom regex scanner for project-specific patterns. | ✅ SonarQube, Checkmarx. | ✅ Semgrep, Bandit (Python), ESLint Security (JS). |
| **SIEM / Log Management** | ❌ Avoid. Building a SIEM from scratch is a multi-year project. | ✅ Splunk, Datadog Security. | ✅ Wazuh, OpenSearch. |
| **DDoS Protection** | ❌ Not feasible for most companies. | ✅ Cloudflare, AWS Shield. Mandatory at scale. | N/A |
| **Encryption** | ✅ Use standard libraries (e.g., `cryptography`, `sodium`). Never roll your own crypto. | ✅ AWS KMS, Cloud HSM for enterprise key management. | ✅ OpenSSL, libsodium. |

---

## Proportional Control Recommendation by Project Stage

| Stage | Company Profile | Recommended Baseline Controls | Defer Until Later |
|---|---|---|---|
| **MVP / Pre-launch** | 1–5 engineers, early-stage startup | TLS everywhere, bcrypt passwords, basic rate limiting, CORS, HTTPS redirect, managed auth (Auth0/Cognito), `npm audit` in CI | Full Zero-Trust, mTLS, HSM, SIEM, formal SOC 2 |
| **Growth** | 10–50 engineers, product-market fit, handling real PII | All MVP controls + Secret Vault, WAF, dependency scanning, container scanning, centralized logging, MFA for admin | HSM, Purple Team exercises, formal compliance certifications |
| **Scale / Enterprise** | 50+ engineers, regulated industry, B2B contracts | All Growth controls + SIEM, CSPM, Red/Blue Team exercises, formal SOC 2 / ISO 27001, supply chain security (SBOM, SLSA), Zero-Trust network | Only hardware-level controls (classified government systems) |

---

## Cost Estimation Examples

| Control | Implementation Cost (Effort) | Maintenance Cost (Annual) | Risk Mitigated |
|---|---|---|---|
| HTTPS / TLS | 1–2 hours (Let's Encrypt + auto-renew) | Near zero | High — eliminates all data-in-transit interception |
| bcrypt password hashing | 1–2 hours code change | Near zero | Critical — eliminates credential database theft |
| Rate limiting at API layer | 1 day (middleware or API Gateway config) | Low | High — prevents brute-force and credential stuffing |
| WAF (Cloudflare Free/Pro) | 1 day configuration | $20–$200/month | High — blocks OWASP Top 10 at the edge |
| Secret Vault (HashiCorp Vault OSS) | 2–5 days setup | 1 engineer-day/month | Critical — eliminates hardcoded credential leaks |
| SIEM (Wazuh OSS) | 1–2 weeks setup | 0.5 FTE/month | High — enables threat detection and audit trail |
| Penetration Test (External) | 0 internal effort | $5K–$30K/year | High — identifies unknown vulnerabilities |
| SOC 2 Audit | 3–6 months prep | $20K–$60K/year | Medium (business enabler for enterprise sales) |
| Full Zero-Trust (mTLS, ZTNA) | 2–4 months engineering | 0.5–1 FTE/month | Medium–High (depends on architecture complexity) |
