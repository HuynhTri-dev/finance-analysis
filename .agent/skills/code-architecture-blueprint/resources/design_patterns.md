# Design Patterns — Blueprints by Root Problem

Rule for using this file: every pattern is described by the **problem it solves** first, and the **conceptual structure** second. No full code samples are given — this is a blueprint to be adapted to the project's language, not something to copy-paste. Only recommend a pattern when the problem genuinely exists (avoid over-engineering — see the KISS/YAGNI section in `core_principles.md`).

---

## Group 1 — Creational (Object Creation)

Use when the problem is about **how an object gets created**, not how it behaves once created.

### Singleton
- **Root problem**: the system needs exactly ONE instance of something (e.g., a connection pool, a config manager, a logger) with a single global access point to it.
- **Conceptual structure**: the class controls its own instantiation and exposes a single access point; the constructor is prevented from being called externally.
- **Warning**: Singleton is easily misused as hidden "global state" that obscures dependencies and makes testing hard (can't be mocked). Only use it when there is a genuine need for exactly one instance — not just because it's "convenient to access from anywhere."

### Factory Method / Abstract Factory
- **Root problem**: the code that requests an object shouldn't need to know the SPECIFIC CLASS being created — the logic for choosing which type to create needs to be separated from the code that uses it (e.g., creating different payment-processing objects per payment type without scattering if-else logic everywhere).
- **Conceptual structure**: a centralized creation point (the factory); calling code only knows the shared interface, never the concrete class.
- **Signal to use it**: every time a new "type" is added, you have to edit if-else/switch statements in multiple places.

### Builder
- **Root problem**: an object needs to be constructed with MANY parameters, many of them optional — a constructor with 8–10 parameters (or multiple overloads) is hard to read and error-prone in terms of argument order.
- **Conceptual structure**: the construction process is split into sequential steps (method chaining, or a separate configuration object), and the target object is only produced at the final step.

### Prototype
- **Root problem**: creating a new object by CLONING an existing one is cheaper than building from scratch (e.g., an object whose setup is expensive — loaded from DB/network — and you want a copy with a few fields changed).
- **Conceptual structure**: the object provides its own cloning mechanism.

---

## Group 2 — Structural (Relationships Between Objects)

Use when the problem is about how classes/objects **combine** into larger structures.

### Adapter
- **Root problem**: two incompatible interfaces need to work together (e.g., a third-party library returns format A, your code needs format B; you don't want to modify either the third-party library or your existing code).
- **Conceptual structure**: an intermediate class that "translates" between the two interfaces, leaving both sides unchanged.

### Decorator
- **Root problem**: you need to ADD behavior to an object at runtime WITHOUT modifying the original class, and without relying on inheritance sprawl (inheritance causes a combinatorial explosion of subclasses when you need to combine several behaviors).
- **Conceptual structure**: an object wraps the original object, both implementing the same interface; the wrapper adds behavior before/after delegating to the wrapped object. Decorators can be nested.
- **Signal to use it**: you need to flexibly enable/disable combinations of features (e.g., middleware, caching layer, logging layer wrapping a service).

### Facade
- **Root problem**: a complex subsystem (many classes, many steps that must be called in a specific order) makes calling code messy — it needs a simplified entry point.
- **Conceptual structure**: one class exposes a simple API, internally coordinating the subsystem's complex classes. It doesn't replace the subsystem, only hides its complexity from the caller.

### Composite
- **Root problem**: individual objects and collections of objects (tree hierarchies) need to be treated THE SAME way (e.g., files and folders, nested UI components).
- **Conceptual structure**: leaf objects and composite objects implement the same interface; the composite holds a list of children and forwards operations down to them.

### Proxy
- **Root problem**: you need to control access to an object (lazy loading, caching, access control, logging) without modifying the original object.
- **Conceptual structure**: an intermediate object with the same interface as the real object, controlling calls to the real object.

---

## Group 3 — Behavioral (Communication Between Objects)

Use when the problem is about how objects **exchange responsibility and information**.

### Strategy
- **Root problem**: there are MULTIPLE ways (algorithms) to do the same job, and you need to select/swap between them flexibly without sprawling if-else logic (e.g., multiple shipping-fee calculation methods, multiple validation strategies).
- **Conceptual structure**: each algorithm is a class implementing a shared interface; the calling code receives a strategy as a parameter/dependency and doesn't care about its internals.
- **Distinguishing from Factory**: Factory answers "which object to create," Strategy answers "which algorithm to use" — the two can be combined (a factory creates the appropriate strategy).

### Observer
- **Root problem**: when one object's state changes, MULTIPLE other objects need to be notified, and the source object shouldn't need to know the details of its dependents (reducing coupling).
- **Conceptual structure**: a subject holds a list of observers; when an event occurs, it notifies each observer in turn, and each observer decides how to react. This is the foundation of event systems and pub/sub.

### Command
- **Root problem**: you need to encapsulate an ACTION (with its required data) as an object so it can be queued, undone/redone, logged, or passed around as a parameter.
- **Conceptual structure**: each action is an object with an execute() method (and optionally undo()); the caller only knows the Command interface, not the internal logic.

### Chain of Responsibility
- **Root problem**: a request needs to pass through MULTIPLE sequential processing steps, each of which may handle it or pass it along, without hardcoding a chain of if-else statements (e.g., middleware pipelines, validation pipelines).
- **Conceptual structure**: each handler keeps a reference to the next handler and decides whether to process and/or forward the request.

### Template Method
- **Root problem**: several classes share the SAME overall process (the same sequence of steps) but differ in the details of a few steps.
- **Conceptual structure**: a base class defines the fixed process skeleton (step order); subclasses override individual steps.

### State
- **Root problem**: an object's behavior changes based on its INTERNAL STATE, and existing code uses if-else/switch on that state in several different methods (e.g., an Order object with draft/paid/shipped states, each allowing different actions).
- **Conceptual structure**: each state is a class implementing a shared interface; the main object holds a reference to its current state and delegates behavior to it.

---

## How to Select a Pattern for the User's Problem

1. Determine whether the problem is about **creation** (Creational), **structural relationships** (Structural), or **communication/behavior** (Behavioral).
2. Restate the problem in a single sentence before choosing a pattern — if you can't state the problem clearly, no pattern may be needed yet (KISS).
3. Prefer the simplest pattern that correctly solves the problem — don't choose one because it "sounds impressive."
4. Always state the trade-off: every pattern adds at least one layer of abstraction — it's only worth it if the benefit (extensibility, testability, reduced duplication) outweighs the added reading/comprehension cost.
