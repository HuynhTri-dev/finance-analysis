---
name: code-architecture-blueprint
description: Guides an agent through designing software architecture and enforcing clean-code standards for ANY programming language — this is not a style guide for one specific language. Covers two distinct concerns kept deliberately separate — architecture (system-level deployment topology, internal layering, and Design Patterns as reusable blueprints for recurring structural problems) and code hygiene (naming, comments, control flow, SOLID, DRY/KISS/YAGNI, linting). Activate this skill whenever the user is starting a new project or module and needs to choose a layered architecture (MVC, Controller-Service-Repository, Clean/Hexagonal Architecture) or a system-level architecture (Monolith vs Microservices, Event-Driven, CQRS, MVVM); needs to pick a Design Pattern (Creational, Structural, or Behavioral — Singleton, Factory, Builder, Adapter, Decorator, Observer, Strategy, etc.) to solve a recurring code-organization problem as a conceptual blueprint rather than copy-paste code; is reviewing or writing code and needs guidance on naming, comments, guard clauses, SOLID, or DRY/KISS/YAGNI; or is setting up linting/formatting tooling. Activate even when the user does not use the exact words "design pattern" or "clean code" — any request to design, structure, or review code in any language qualifies.
triggers:
  - "design a new design pattern"
  - "create a software architecture"
  - "clean code"
  - "code review"
  - "SOLID principles"
  - "DRY KISS YAGNI"
  - "layered architecture"
  - "naming convention"
  - "refactor"
  - "microservices"
  - "MVC"
  - "controller service repository"
  - "create clean architecture"
  - "linting setup"
---

# Code Architecture & Clean Code Blueprint

This skill turns the agent into a software architect / code reviewer that works across **any programming language**. It deliberately separates two concerns:

1. **Architecture** — how to split system-level deployment topology, how to layer code inside a service, and which Design Pattern solves a recurring structural problem. This is conceptual (a blueprint), NOT ready-to-paste code.
2. **Code hygiene** — naming, comments, control flow, SOLID, DRY/KISS/YAGNI, linting. These are review standards that apply regardless of language.

Never optimize recommendations for one specific language's syntax — express guidance at the concept level, and only add a short language-specific example when it actually helps.

## When to Use This Skill

- Use this skill when the user is starting a new project or module and asks how to organize the codebase, or explicitly asks for a design/architecture document.
- Use this skill when the user describes a recurring code-organization problem (e.g., "every time I add a payment type I have to edit if-else blocks everywhere") and needs a Design Pattern recommendation.
- Use this skill when the user is writing or reviewing code and wants feedback on naming, comments, nested conditionals, SOLID violations, or duplication.
- Use this skill when the user asks how to set up a linter/formatter for their language or ecosystem.
- **Do NOT use** this skill to write language-specific syntax optimizations (e.g., "how do I use Python decorators") — that is a language question, not an architecture question. Only bring in `resources/design_patterns.md` if the underlying problem is genuinely structural.
- **Do NOT** default to the most complex architecture available. Every recommendation must be justified against project scale — bias toward the simplest option that satisfies the actual constraints (KISS/YAGNI).

## Step-by-Step Instructions

### Workflow A — Initial architecture design for a project (produces `design_pattern.md`)

Trigger: the user describes a new project/feature and asks how to organize it, or explicitly requests an architecture/design document.

1. **Gather context before committing to an architecture.** Ask 2–4 targeted questions for whatever is missing (skip anything already answered by project docs):
   - System type: API backend, full-stack app, mobile app, library/SDK, CLI tool...
   - Primary language/framework (read existing project files instead of re-asking when possible).
   - Scale: number of domains/modules, team size — this drives the choice between a simple layered structure and something like Clean Architecture or DDD.
   - Special constraints: real-time, offline-first, multi-tenant, high test-coverage requirements, etc.
2. **Choose the system-level architecture, then the internal layered architecture** — these are two separate layers of decision, always made in this order:
   - **System layer** (only relevant once scale goes beyond a single service/app): Monolith vs Microservices, synchronous calls vs Event-Driven, whether CQRS is warranted, UI architecture (MVVM/Micro-Frontends) if the frontend is complex. See `resources/system_architecture_patterns.md`.
   - **Internal layer** (inside each service/app): Simple Layered, MVC, Controller-Service-Repository, Clean/Hexagonal Architecture. See `resources/layered_architecture.md`.
   These two layers combine — they don't replace each other. Do not default to the most sophisticated option at either layer; apply KISS/YAGNI and only escalate when there's concrete evidence the project needs it (not "big companies use this so we should too").
3. **Identify relevant Design Patterns** (only if a specific recurring problem justifies one) — see `resources/design_patterns.md`. Never suggest a pattern just because it sounds impressive; there must be a real, named problem it solves.
4. **Fill in the template** at `resources/design_pattern_template.md` and write a real file `design_pattern.md` for the user (use the file-creation tool — don't just answer inline). The file must include:
   - The chosen system architecture (if applicable) and internal layered architecture, plus a data-flow description (text or a diagram if the project already uses one).
   - Each layer's responsibility and the dependency rule (which layer may call which).
   - Design Patterns applied to specific identified problems, with the reasoning for each choice.
   - Code hygiene standards for this project: naming convention (pick one consistent camelCase/PascalCase/snake_case scheme per identifier type, matching the project's primary language — see `resources/naming_conventions.md`), commenting rules, guard clauses, SOLID.
   - A pre-merge review checklist.
5. Confirm the architecture with the user before treating it as final — an architecture mistake made early is far more expensive than a locally messy piece of code.

### Workflow B — Recommending a Design Pattern for a specific problem

Trigger: the user describes a recurring structural problem (e.g., "I need a single object managing config app-wide", "adding a new discount type means editing conditionals in three files").

1. Classify the problem — see `resources/design_patterns.md`:
   - **Creational**: the problem is HOW an object gets created (too many constructor parameters, need to guarantee a single instance, need to create a family of related objects...).
   - **Structural**: the problem is the RELATIONSHIP between objects/classes (two incompatible interfaces, need to add behavior without touching the original class, need to simplify a complex subsystem...).
   - **Behavioral**: the problem is HOW objects COMMUNICATE (several interchangeable behaviors, one event needs to notify many listeners, one algorithm has multiple variants...).
2. Recommend one pattern (at most two if there's a genuine trade-off worth surfacing) and explain:
   - The root problem this pattern actually solves.
   - The conceptual structure (the role each participant plays), not full code.
   - The trade-off: every pattern adds abstraction/indirection — state plainly when NOT to use it (apply KISS: if a few lines of straightforward logic solve it, skip the pattern).
3. Only write illustrative code when explicitly asked, and when you do, write it in the project's actual language, following Workflow C standards.

### Workflow C — Clean code standards while writing/reviewing code

Apply directly to the code being written or reviewed; no separate file is needed unless this is the first time the project's architecture is being locked in (Workflow A).

1. **Naming** — see `resources/naming_conventions.md`. Names must be self-explanatory, no cryptic abbreviations, one responsibility per function ("And" in a function name is a signal to split it).
2. **Comments** — see `resources/commenting_standards.md`. Explain business intent and WHY, not WHAT the code already says. Mandatory for: magic numbers/strings, workarounds/hacks, regex, TODO/FIXME/NOTE, and the input/output contract of important public functions.
3. **Control flow** — see `resources/control_flow.md`. Prefer early returns/guard clauses over nested conditionals. Flag any function with if-nesting deeper than two levels for refactor.
4. **Core principles** — see `resources/core_principles.md` (DRY/KISS/YAGNI) and `resources/solid_principles.md` (SOLID). When reviewing, point to the specific violating line — never give vague feedback.
5. **Linting** — if asked about setup, use `resources/linting_setup.md` for tooling recommendations by language.

When reviewing code, always distinguish architecture-level issues (Workflow A/B) from code-hygiene issues (Workflow C) — they require different kinds of fixes.

## Decision Trees

- If the user is designing a **new project or module** -> run **Workflow A** and produce `design_pattern.md`.
- If the user already has a project and describes a **recurring structural pain point** -> run **Workflow B**, recommend a pattern, don't touch the architecture doc unless asked.
- If the user pastes code or a diff and asks for **feedback/review** -> run **Workflow C** directly on the code, no new file needed.
- If the described problem is about HOW an object is built -> Creational patterns.
- If the described problem is about the RELATIONSHIP/structure between objects -> Structural patterns.
- If the described problem is about HOW objects communicate/behave -> Behavioral patterns.
- If the project is small/MVP with no concrete evidence of scale pressure -> default to Monolith + Simple Layered or Controller-Service-Repository; do not propose Microservices/Event-Driven/CQRS/Clean Architecture without a specific justification.

## Accompanying Scripts & Resources

- `resources/system_architecture_patterns.md` — system-level architecture patterns: Monolith, Microservices, Serverless, Event-Driven, CQRS, MVVM, Micro-Frontends, and selection criteria.
- `resources/layered_architecture.md` — internal layered architectures: Simple Layered, MVC, Controller-Service-Repository, Clean/Hexagonal Architecture, and selection criteria.
- `resources/design_patterns.md` — all three Design Pattern groups (Creational/Structural/Behavioral), organized by root problem rather than by syntax.
- `resources/design_pattern_template.md` — the template used to produce the project's `design_pattern.md` file.
- `resources/naming_conventions.md` — naming rules and per-identifier-type convention table.
- `resources/commenting_standards.md` — commenting standard: magic numbers/strings, workarounds, TODO/FIXME/NOTE, regex.
- `resources/control_flow.md` — early return / guard clause pattern.
- `resources/core_principles.md` — DRY, KISS, YAGNI, with the Rule of Three for balancing DRY against over-abstraction.
- `resources/solid_principles.md` — the five SOLID principles with concrete violation signals to look for during review.
- `resources/linting_setup.md` — recommended lint/format tooling per language ecosystem.

Read the relevant resource file(s) before producing output for Workflow A or B — do not rely on memory for pattern definitions or architecture trade-offs when the reference exists on disk.
