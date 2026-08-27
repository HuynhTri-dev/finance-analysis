# Validation Checklists

Use these checklists to self-review documents before finalizing, or to review documents provided by the user. When reviewing, point out SPECIFICALLY which sentence or section violates each criterion — do not give general feedback.

## 1. BRD / Vision & Scope (per BABOK v3)
- [ ] The Problem Statement describes the PROBLEM, not a solution
- [ ] Each business objective is measurable (or has at least a clear success criterion)
- [ ] The stakeholder list does not omit anyone with final approval authority
- [ ] In-scope and Out-of-scope items are specific — no vague entries like "fully supports" / "all scenarios"
- [ ] No item appears in both In-scope and Out-of-scope (contradiction)
- [ ] Constraints and assumptions are separated — not mixed into scope

## 2. SRS / FRD (per IEEE 830-1998 — 8 Quality Attributes)
Check each FR/NFR individually against the following attributes:
- [ ] **Correct** — accurately reflects a need confirmed with the user
- [ ] **Unambiguous** — can only be interpreted one way (avoid unquantified terms like "fast," "user-friendly," "flexible")
- [ ] **Complete** — covers all input/output/exception cases; no sections left blank
- [ ] **Consistent** — does not conflict with any other requirement in the document
- [ ] **Verifiable** — a test case can be written to validate it (if you cannot write a test case → this requirement does not pass)
- [ ] **Ranked** — has a priority level (must/should/could)
- [ ] **Traceable** — has an ID and appears in the RTM
- [ ] **Modifiable** — clearly structured, with no content duplicated across multiple locations in ways that make it hard to update

NFRs specifically: every entry MUST include a concrete numeric threshold (e.g., "< 2s," "99.9% uptime") — without a number, it does not pass "Verifiable."

## 3. User Stories & Acceptance Criteria (per Agile Alliance / INVEST)
- [ ] Correct format: "As a... I want to... So that..." with a clear value statement (the "So that..." clause)
- [ ] **Independent** — not hard-locked to the sequential delivery of another story
- [ ] **Negotiable** — does not prescribe implementation details (that is for dev/design)
- [ ] **Valuable** — value is for the end user, not internal technical value
- [ ] **Estimable** — sufficient information for the team to estimate effort
- [ ] **Small** — completable within one sprint (if not, suggest splitting)
- [ ] **Testable** — Acceptance Criteria are in Given/When/Then form and not vague
- [ ] At least 1 AC covers the happy path and at least 1 AC covers an edge case / error scenario

## 4. RTM
- [ ] No Business Requirement is unmapped to any FR (orphan requirement)
- [ ] No FR is unmapped to a User Story or Test Case
- [ ] No Test Case is untraceable back to its source requirement
- [ ] IDs are consistent with the IDs used in the BRD/SRS/FRD/User Stories (no ID format changes across documents)

## 5. Diagrams (Mermaid)
- [ ] Use Case Diagram: every actor has at least 1 use case; no "orphan" use case (unassigned to any actor)
- [ ] Sequence Diagram: alternate flow (error/exception) is handled — not just the happy path
- [ ] ERD: every entity has at least 1 primary key (PK); all relationships have explicit cardinality (1-1, 1-n, n-n)
- [ ] Wireframe: used only to align on flow and layout — do not substitute for a detailed UI spec; if the user needs pixel-level detail, recommend a real design tool (e.g., Figma)