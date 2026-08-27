# Template — `design_pattern.md`

Use this template when producing the architecture file for a project in Workflow A. Fill it in completely, remove any section that doesn't apply, and never leave placeholders in the final file handed to the user.

```markdown
# Architecture & Code Standards — [Project Name]

> This document is the shared reference for the team when organizing code and reviewing PRs. Update it whenever the architecture changes.

## 1. System Overview

- System type: [API backend / full-stack app / mobile app / ...]
- Primary language & framework: [...]
- Scale: [number of core modules, team size]

## 2. System Architecture (if scale goes beyond a single service/app)

**Deployment**: [Monolith / Microservices] — rationale: [...]
**Communication flow**: [direct synchronous calls / Event-Driven via (Kafka/RabbitMQ/...)] — rationale: [...]
**Read/write separation**: [Not needed / CQRS] — rationale: [...]
**UI architecture** (if the frontend is complex): [MVC / MVVM / Micro-Frontends] — rationale: [...]

If the project is a single service/app at small-to-medium scale, state clearly: "Monolith, direct synchronous communication — no proven need for Microservices/Event-Driven/CQRS yet; will escalate only with concrete evidence (per YAGNI)."

## 3. Internal Layered Architecture (within each service/app)

**Architecture**: [Simple Layered / MVC / Controller-Service-Repository / Clean Architecture / DDD + Clean Architecture]

**Rationale**: [1–3 sentences based on scale and constraints — reference the criteria in resources/layered_architecture.md]

**Flow diagram** (text or a diagram if the project already uses one):

[Layer A] → [Layer B] → [Layer C]

**Responsibility per layer**:

| Layer | Responsibility | Must NOT do |
|---|---|---|
| [e.g., Controller] | Receive requests, validate input shape, call Service, format response | Contain business logic, call Repository directly |
| [e.g., Service] | All business logic, orchestrates other Services/Repositories | Know about HTTP/framework, contain SQL |
| [e.g., Repository] | Data access (DB/external API) | Contain business logic, validate business rules |

**Dependency rule**: [which layer may call which layer, and which direction is forbidden]

## 4. Applied Design Patterns

For each specific problem identified in the project:

| Problem | Pattern | Rationale |
|---|---|---|
| [e.g., multiple payment types, new types added frequently] | Strategy + Factory | Avoids sprawling if-else logic when adding new types |

If no specific problem currently needs a pattern, state clearly: "No pattern applied beyond the layered architecture — will be added when a real problem arises (per YAGNI)."

## 5. Naming Convention

| Identifier type | Convention | Example |
|---|---|---|
| Variables/functions | [camelCase/snake_case] | `getUserById` |
| Classes/interfaces/types | PascalCase | `UserService` |
| Constants | [UPPER_SNAKE_CASE or per-language convention] | `TOKEN_LIFETIME_MS` |
| Files | [kebab-case/snake_case/PascalCase — per language convention] | `user-service.ts` |

Rule: names must be self-explanatory, no cryptic abbreviations; one responsibility per function ("And" in a function name signals it needs to be split).

## 6. Commenting Standard

- Mandatory comments: magic numbers/strings, workarounds/hacks (with rationale), non-trivial regex, the input/output contract of important public functions.
- Standard tags: `TODO:` (future work), `FIXME:` (known bug not yet fixed), `NOTE:` (important context to be aware of).
- Comments explain WHY, not WHAT the code already says.

## 7. Control Flow

Use early returns/guard clauses; avoid nesting conditionals more than 2 levels deep.

## 8. Mandatory Principles

- DRY / KISS / YAGNI — see `resources/core_principles.md`
- SOLID — see `resources/solid_principles.md`

## 9. Pre-Merge Review Checklist

- [ ] Code is in the correct layer, no dependency-rule violations from section 3
- [ ] Variable/function names are self-explanatory, no function doing multiple things
- [ ] Magic numbers/strings are named constants with a comment
- [ ] No unrefactored nested conditionals deeper than 2 levels
- [ ] No clear SOLID violations (especially Single Responsibility)
- [ ] No duplicated logic that could be consolidated (DRY)
- [ ] Linter/formatter has been run with no remaining warnings
```
