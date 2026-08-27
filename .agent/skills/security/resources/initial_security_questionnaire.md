# Initial Security Questionnaire

<!--
name: initial_security_questionnaire
description: Pre-engagement intake form to collect business context, regulatory requirements, team resources, and asset value before performing any security design or assessment.
-->

Use this questionnaire at the beginning of every security engagement. Document the answers before proceeding to threat modeling or architecture design. Do not skip questions — unanswered items should be flagged as assumptions and reviewed at the earliest opportunity.

---

## Section 1: Business Context

| # | Question | Answer |
|---|---|---|
| 1.1 | What is the primary domain of this system? (e.g., Fintech, Healthcare, E-commerce, SaaS, Government, Internal Tool) | |
| 1.2 | What is the core business capability the system delivers? | |
| 1.3 | Who are the end users? (e.g., consumers, enterprise employees, government officials, third-party developers) | |
| 1.4 | What is the expected scale at launch and at 12 months? (e.g., 1K users → 50K users) | |
| 1.5 | Are there any third-party integrations (e.g., payment gateways, identity providers, external APIs)? | |

---

## Section 2: Regulatory & Compliance Requirements

| # | Standard | Required? (Yes / No / Unsure) | Notes |
|---|---|---|---|
| 2.1 | **PCI-DSS** — Does the system process, store, or transmit payment card data? | | |
| 2.2 | **HIPAA** — Does the system handle Protected Health Information (PHI)? | | |
| 2.3 | **GDPR** — Does the system collect or process personal data of EU residents? | | |
| 2.4 | **Vietnam NĐ 13/2023** — Does the system store personal data of Vietnamese citizens? | | |
| 2.5 | **SOC 2** — Is there a requirement to prove security posture for B2B/Enterprise customers? | | |
| 2.6 | **ISO 27001** — Is a formal Information Security Management System (ISMS) required? | | |
| 2.7 | **NIST CSF** — Is a risk management framework required by a government or enterprise customer? | | |

---

## Section 3: Hosting & Infrastructure

| # | Question | Answer |
|---|---|---|
| 3.1 | Where is the system deployed? (Cloud: AWS / GCP / Azure / Other, or On-premise, or Hybrid) | |
| 3.2 | What is the container/orchestration strategy? (Docker, Kubernetes, bare metal, serverless) | |
| 3.3 | Is there an existing CI/CD pipeline? What tools are used? | |
| 3.4 | Is there a dedicated staging environment that mirrors production? | |
| 3.5 | How is configuration and secret management currently handled? (Hardcoded, .env files, Vault, Cloud Secret Manager) | |

---

## Section 4: Data & Asset Classification

| # | Question | Answer |
|---|---|---|
| 4.1 | What types of data does the system store or process? (PII, Financial, Health, Credentials, Public) | |
| 4.2 | What is the most sensitive data asset? What is its approximate business value or replacement cost? | |
| 4.3 | Is there an existing data classification policy? (Public / Internal / Confidential / Restricted) | |
| 4.4 | How long is data retained? Is there an automated data deletion process? | |
| 4.5 | Is backup and disaster recovery currently in place? What are the RTO and RPO targets? | |

---

## Section 5: Team & Budget

| # | Question | Answer |
|---|---|---|
| 5.1 | Is there a dedicated security team or a Security Champion within the dev team? | |
| 5.2 | What is the approximate budget allocated for security tooling, audits, or penetration testing? | |
| 5.3 | Has a security audit or penetration test ever been performed? If yes, when was the last one? | |
| 5.4 | Is there a documented Incident Response Plan? | |
| 5.5 | Do developers receive regular secure coding training? | |

---

## Section 6: Previous Incidents & Known Risks

| # | Question | Answer |
|---|---|---|
| 6.1 | Has the system experienced a security incident or data breach in the past? | |
| 6.2 | Are there any known open vulnerabilities or security debts the team is aware of? | |
| 6.3 | Are there any third-party components (libraries, SaaS tools) flagged with known CVEs? | |
