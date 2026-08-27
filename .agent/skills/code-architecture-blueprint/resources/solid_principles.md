# SOLID Principles

Applies to object-oriented programming (OOP) and, to a similar extent, to any well-structured module in non-OOP languages.

## S — Single Responsibility Principle (SRP)

**Definition**: a class/module should have ONLY ONE reason to change.

**Violation signal**: a class called `UserManager` that validates data, sends emails, writes logs, AND queries the DB — four separate reasons this class might need to change (a validation rule changes / the email provider changes / the log format changes / the DB changes). It should be split into `UserValidator`, `EmailService`, `Logger`, `UserRepository`.

**Related to**: this is the same principle as "a function should do one thing," applied at the class level — see also `naming_conventions.md` (the "And" signal in function names).

## O — Open/Closed Principle (OCP)

**Definition**: code should be OPEN for extension but CLOSED for modification — adding a new feature shouldn't require editing existing, already-stable code.

**Violation signal**: every time a new type/case is added, you have to reopen an old file and add another `if/switch` branch. This is usually a signal to use Strategy or Factory (see `design_patterns.md`) — add a new type by adding a new class, not by editing an old one.

## L — Liskov Substitution Principle (LSP)

**Definition**: a subclass must be fully substitutable for its parent class anywhere the parent is used, without breaking the correctness of the program.

**Violation signal**: a subclass overrides a parent method but changes its behavior/contract in a way that breaks expectations — the classic example: a `Square` class inheriting from `Rectangle` but overriding the width/height setters in a way that breaks code written against `Rectangle` when a `Square` is passed in. Or: an override throws an exception the parent method never throws, catching the calling code off guard.

## I — Interface Segregation Principle (ISP)

**Definition**: several small, focused interfaces are better than one large, catch-all interface — a class shouldn't be forced to implement methods it doesn't use.

**Violation signal**: a `Worker` interface with both `work()` and `eat()`, but a `RobotWorker` class is forced to implement `eat()` even though it makes no sense (usually implemented as empty or throwing NotImplementedError) — a clear sign the interface is bundling two unrelated responsibilities and should be split into separate `Workable` and `Eatable` interfaces.

## D — Dependency Inversion Principle (DIP)

**Definition**: high-level modules (business logic) should not depend directly on low-level modules (implementation details like a specific DB or HTTP client) — both should depend on a shared abstraction (interface).

**Violation signal**: the Service layer directly imports a concrete `PostgresUserRepository` class instead of depending on an `IUserRepository` interface. Consequence: you can't swap the implementation (e.g., switch to MongoDB, or mock it in tests) without modifying the Service.

**Architectural link**: this is the foundational principle behind Clean Architecture/Hexagonal — dependencies always point from detail toward abstraction, never the reverse (see `layered_architecture.md`).

## How to Apply This When Reviewing

Don't list SOLID generically — for each violation found, state: **which principle is violated + the specific line/class + the concrete consequence** if left unfixed (harder to test, harder to extend, easier to introduce bugs elsewhere). Don't force SOLID onto very short pieces of code that are unlikely to change (that would itself violate KISS/YAGNI).
