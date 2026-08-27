# Question Bank — Phase 2 (Solution/System Analysis)

Only begin after the Vision & Scope document is established. Ask per module — do not cover all modules at once. This is a starting point — when a business rule is vague, an NFR lacks a specific threshold, or actor/use case authorization conflicts arise, dig deeper immediately rather than recording it and moving on. Proactively suggest domain-specific aspects (multi-tenancy, rate limiting, data residency…) appropriate to the system type being analyzed, not just what is listed below.

## Group A — Features by Module
- In module [X], what are the main actions the user performs? (list by operation, e.g., create, edit, delete, search, export...)
- Which role(s) are permitted to perform this action?
- Are there any approval or validation steps required before an action is finalized?

## Group B — Business Rules
- Are there any logical conditions or constraints that apply to this feature? (e.g., quantity limits, discount conditions, special validation)
- Are there any exceptional cases that require separate handling?

## Group C — Non-Functional Requirements
- How many concurrent users / requests per second must the system handle?
- Are there specific response time requirements (e.g., < 2 seconds)?
- What sensitive data needs encryption or special access controls?
- What are the uptime / SLA requirements?
- What devices or browsers must the system support?

## Group D — Data Structure
- What are the primary entities in the system (e.g., User, Order, Product)?
- What are the relationships between those entities (1-to-1, 1-to-many, many-to-many)?
- Is there any data that needs to be synchronized with an external system?

## Group E — Actors & Use Cases
- How many actor types (users / external systems) interact with the system?
- For each actor, what are their primary use cases?
- Are there any flows where one actor interacts indirectly through another actor (e.g., Admin approves a User's request)?