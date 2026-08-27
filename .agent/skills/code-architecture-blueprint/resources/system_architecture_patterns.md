# System Architecture Patterns

`layered_architecture.md` answers "**inside one service/app, what layers is the code organized into**" (MVC, Controller-Service-Repository, Clean Architecture...). This file answers a different, higher-level question: "**how is the whole system deployed, and how do its parts communicate**" (deployment topology, data flow, UI architecture). These two layers **do not exclude each other** — they always combine: a service inside a Microservices system still organizes its own internals with Controller-Service-Repository or Clean Architecture.

When running Workflow A (producing `design_pattern.md`), if project scale goes beyond a single service/app, consult this file alongside `layered_architecture.md`.

---

## 1. By Deployment Scale (Deployment Architecture)

### Monolith (default — not a "lesser" option)

The entire application is ONE codebase, ONE deployment unit, sharing a single database.

**Use when**: this is the sensible DEFAULT for most projects — small-to-medium teams, an unproven product (MVP, early-stage startup), no proven need to scale parts independently yet. Apply KISS/YAGNI: don't jump straight to Microservices "for the future" when a Monolith already satisfies current needs.

**Risk if left unrefactored too long**: as the team and business logic grow, a monolith without clear internal module boundaries turns into a "Big Ball of Mud" — everything tangled together, impossible to deploy independently.

### Microservices Architecture

The system is split into independent services, each owning one business capability (e.g., Payment Service, Shipping Service), each with its own database, communicating via APIs (REST, gRPC) or a message broker.

- **Use when**: the system is very large, needs to scale individual capabilities independently, has multiple independent teams/squads that can each deploy on their own.
- **Risk**: operationally complex (more services = more failure points, more CI/CD pipelines), hard to debug across service boundaries (distributed tracing becomes mandatory), higher infrastructure cost, distributed-data problems (no more cross-service ACID transactions — you have to deal with eventual consistency, sagas, etc.).
- **Important warning**: this is the MOST commonly over-applied architecture in practice — small teams adopting Microservices before there's real need create operational overhead that outweighs the benefit. Only choose this with concrete evidence (not "big companies do this, so we should too").

### Serverless Architecture (FaaS)

You write only Functions to run business logic and deploy them to a cloud platform (AWS Lambda, Google Cloud Functions, Vercel Functions...); the provider manages servers and auto-scales based on requests.

- **Use when**: intermittent, event-driven workloads, background jobs, or optimizing for cost (pay only when code runs).
- **Risk**: vendor lock-in (hard to migrate between cloud providers), cold-start latency on first invocation, harder to debug/test in an environment that exactly mirrors production, execution time limits per function.

---

## 2. By Data Flow (Event-Driven Architecture)

### Event-Driven Architecture

Components don't call each other directly and wait; they communicate by publishing/subscribing to events through a message broker (Kafka, RabbitMQ, SQS...).

*Example: a user places an order → the Order Service emits an `OrderCreated` event → the Email Service and the Inventory Service independently listen and handle their own concerns, without the Order Service waiting for them.*

- **Use when**: you need high asynchrony, low latency on the main request path (you don't want the user waiting for every downstream side-effect to finish), or you need to integrate multiple disparate systems without tight direct coupling.
- **Risk**: hard to trace a single request's journey across many events (requires dedicated tooling — correlation IDs, distributed tracing), handling failure/rollback is far more complex than a direct function call (needs compensation/retry/dead-letter-queue mechanisms).

### CQRS (Command Query Responsibility Segregation)

Fully separates the Write/Update path (Command) from the Read/Query path (Query), usually using two different models or even two different databases optimized for each purpose.

- **Use when**: read and write volumes are heavily skewed, and each side has clearly different optimization needs (e.g., a write DB using PostgreSQL for transactional integrity, a read DB using Elasticsearch for fast full-text search).
- **Risk**: complexity rises significantly (syncing data between the two sides); read data can lag behind writes (eventual consistency) — you must confirm the business can tolerate that lag.
- **Often paired with**: Event Sourcing (storing a history of events instead of just the latest state) — only consider this once CQRS itself is genuinely justified, don't add Event Sourcing "to complete the set."

---

## 3. By UI Architecture (Frontend Architecture)

### MVVM (Model-View-ViewModel)

Common in mobile, WPF, and modern frontend frameworks with data binding. The ViewModel is a middle layer: it converts Model data into a shape the View needs, and provides two-way binding (data changes → UI updates automatically, no manual DOM/UI manipulation).

- **Use when**: the app has complex UI with lots of state that needs to stay continuously in sync with the UI — common in Flutter (Provider/Riverpod/Bloc follow this spirit), Vue.js, Android Jetpack, WPF.
- **Distinction from MVC**: MVC has a Controller actively orchestrating the View; MVVM's ViewModel knows NOTHING about the concrete View (the View binds itself to the ViewModel) — a better fit for reactive/data-binding frameworks.
- **Risk if overused**: for simple UIs (a handful of static states), MVVM adds an unnecessary middle layer — plain MVC or Simple Layered is enough (KISS).

### Micro-Frontends

Similar to Microservices but applied to the UI layer — instead of one large frontend app, it's assembled from several independent frontend apps (potentially different frameworks) running together in one browser.

- **Use when**: a very large web product, multiple independent frontend teams own different areas of the same page, and each needs to deploy its UI independently.
- **Risk**: integration overhead (routing, shared state, a shared design system across micro-frontends), easy to create an inconsistent experience without a strictly enforced shared design system.

---

## Extended Decision Table

| Signal from the project | Suggested architecture |
|---|---|
| Small-to-medium team, unproven product, no proven need to scale independently | Monolith (default) |
| Large load, multiple independent teams, features that need independent scaling/deployment | Microservices |
| Asynchronous workloads, multiple components reacting to a single event | Event-Driven |
| Very read-heavy vs write-light (or vice versa), needs separate optimization per side | CQRS |
| No infrastructure management desired, simple logic triggered by events/schedule | Serverless |
| Modern mobile/frontend, UI needs continuous state-driven updates | MVVM |
| Very large web product, multiple independent frontend teams on one page | Micro-Frontends |

## Combination Principle

These architectures **do not exclude each other**, and they **do not exclude** the internal layered architecture in `layered_architecture.md` — they operate at two different layers of the same system:

- **System layer** (this file): how the system is deployed, how its large components communicate (Monolith/Microservices, synchronous/Event-Driven, split Command-Query or not, UI architecture).
- **Internal layer** (`layered_architecture.md`): inside ONE service/app, what layers the code is organized into (Controller-Service-Repository, Clean Architecture...).

Real-world combination example: a Microservices system, services communicating via Event-Driven messaging, each service internally organized with Controller-Service-Repository, the UI built with MVVM.

**When running Workflow A**: always settle the system layer FIRST (based on real scale/constraints), then choose the internal architecture for each service/app. Never pick a complex system architecture just because it's "standard" — apply the same principle from `layered_architecture.md`'s decision table: choose the SIMPLEST option that satisfies the project's real constraints.
