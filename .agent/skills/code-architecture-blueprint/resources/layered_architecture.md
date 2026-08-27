# Layered Architecture — Comparison and Selection Criteria

The goal here is NOT to pick the "best" architecture, but the one that fits the **current scale and constraints** of the project (apply KISS/YAGNI at the architecture level too).

## 1. Simple Layered (2–3 layers)

**Structure**: Presentation (UI/API) → Business Logic → Data Access.

**Use when**: small project, CRUD-heavy, team of 1–3, no complex business rules, needs to ship fast.

**Risk if overused**: as business logic grows, it tends to leak into the UI or Data Access layer because there's no dedicated Service layer to contain it.

## 2. MVC (Model-View-Controller)

**Structure**: Model (data + core business rules) — View (presentation) — Controller (receives requests, coordinates Model/View).

**Use when**: the application has a clear UI that needs to stay decoupled from data (traditional web apps, or any framework built around MVC — Rails, Django, many mobile frameworks).

**Risk if overused**: the Controller tends to bloat into a "God Controller" mixing business logic with request handling unless a Service layer is added once business rules grow.

## 3. Controller-Service-Repository

**Structure**:
- **Controller**: receives requests, validates input shape only (no business logic), calls the Service, formats the response.
- **Service**: holds all business logic, orchestrates other Services/Repositories, and must not know anything about HTTP/UI.
- **Repository**: solely responsible for data access (DB, external APIs) — no business logic.

**Use when**: a backend API has moderate-to-high business complexity, needs to unit-test business logic independently of the DB/HTTP layer (mock the Repository), or has multiple developers working in parallel.

**Mandatory dependency rule**: Controller → Service → Repository, one direction only. Repository must never call back up into Service. Service must not import HTTP/web-framework libraries.

**Risk if overused**: for trivial CRUD with no business logic (plain get/set), these three layers add boilerplate for no benefit — Simple Layered (section 1) is enough.

## 4. Clean Architecture / Hexagonal (Ports & Adapters)

**Structure**: concentric circles — Entities (core business rules, depend on nothing) → Use Cases/Application → Interface Adapters (Controllers, Presenters, Gateways) → Frameworks & Drivers (DB, web framework, UI). Dependencies always point inward (Dependency Inversion applied at the architecture level).

**Use when**: a large system with multiple complex business domains, needs the ability to swap frameworks/DBs without touching core logic, needs to test all business logic independent of DB/framework, large or long-lived team.

**Risk if overused**: significant overhead (many interfaces, many DTO ↔ Entity mapping layers). For a small project or an MVP, this is a clear YAGNI violation. Only choose this with concrete evidence (swapping DB, swapping framework, needing isolated business-logic tests) — never "just to be safe."

## 5. Domain-Driven Design (DDD) — supplementary, not a replacement

DDD is not a layered architecture but a way of organizing by **Bounded Context** (each business domain is independent with its own model). It can be combined with Clean Architecture per bounded context. Only consider this when the system has multiple clearly separated business domains (e.g., an HRM system with Auth, Employee, Payroll, and Agent as distinct domains — each potentially its own bounded context).

## Quick Decision Table

| Signal from the project | Suggested architecture |
|---|---|
| Simple CRUD, MVP, 1–3 devs | Simple Layered |
| Already using an MVC-based UI framework (Rails/Django/Laravel...) | MVC (+ Service layer once business logic grows) |
| Backend API, moderate business logic, needs to unit-test business logic | Controller-Service-Repository |
| Large system, multiple domains, needs to swap framework/DB independent of business logic | Clean Architecture / Hexagonal |
| Multiple separated business domains, large long-lived team | DDD (combined with Clean Architecture per context) |

When unsure, ask about team size, expected project lifespan, and business complexity — then choose the SIMPLEST option that satisfies those constraints.
