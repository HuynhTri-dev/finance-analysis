---
name: erd_tips.md
description: Advanced heuristics and practical tips for ERD design. Covers the 6-question Entity test, the "verb test", ownership via delete cascade reasoning, temporal entity discovery, Thing vs Value Object distinction, normalization trade-offs (OLTP vs OLAP), SQL vs NoSQL access-pattern thinking, and the Source of Truth principle.
---
# ERD Design Tips and Heuristics

## Tip 1 — Identifying Entities: use the 6-question test, not just "is it a noun?"

A common heuristic is to find nouns in requirements:
> "Customer creates Order and Order contains Product."
→ Customer, Order, Product are candidate Entities.

But noun ≠ Entity automatically.

For each candidate concept, apply the 6-question test:

| Question | If "Yes" → leans toward Entity |
|---|---|
| Does it have its own identity? | customer_id, order_id |
| Does it have multiple distinct attributes? | name, status, date... |
| Does it have its own lifecycle? | Created → Active → Closed |
| Does it have relationships with other things? | Customer → Order |
| Does the business query/manage it independently? | "Find all Addresses" |
| Can it exist relatively independently? | Address is managed on its own |

More "Yes" → more likely Entity. Few "Yes" → likely just an Attribute.

---

## Tip 2 — The verb test: "What actions does the system perform on it?"

Read requirements through verbs:

> "Admin can create, edit, lock, unlock, and search Customers."
→ Customer is clearly an Entity.

> "Admin edits the Customer's name."
→ `name` is an attribute; it doesn't need to become an Entity.

> "Admin can add, edit, and delete multiple Addresses per Customer."
→ `Address` starts showing Entity characteristics.

Verbs that signal an Entity: `create`, `update`, `delete`, `activate`, `deactivate`,
`assign`, `approve`, `cancel`, `search`, `track`, `history`.

---

## Tip 3 — Ownership test: "If I delete A, does B still make sense?"

This determines ownership, dependency, lifecycle, and cascade behavior.

```
Order → OrderItem
```
"If I delete an Order, does an OrderItem still make sense?" → No
→ OrderItem is a dependent child of Order. Use ON DELETE CASCADE.

```
Customer → Order
```
"If I deactivate a Customer, should Orders disappear?" → No
→ Order must survive Customer deactivation. Use ON DELETE RESTRICT or SET NULL.

This single question defines:
- Ownership
- Dependency
- Cascade delete behavior
- Lifecycle coupling

---

## Tip 4 — History discovery: "What if I need to store the history of it?"

This technique surfaces hidden Entities.

Initial model:
```
Employee { employee_id, department }
```

Then a requirement arrives:
> "Show all Departments an Employee has worked in."

The `department` attribute must become a relationship with history:

```
EmployeeDepartment { employee_id FK, department_id FK, from_date, to_date }
```

The relationship itself has become historical data — an Entity.

---

## Tip 5 — Thing vs Value distinction

Clearer than just applying 1NF/2NF/3NF.

**Entity = Thing** (has identity, lifecycle, relationships)
```
Customer, Product, Order, Employee, Warehouse
```

**Value = Attribute** (describes a Thing, has no independent identity)
```
name, age, price, status, email
```

**Borderline (Value Object or Entity depending on domain):**
```
Address, Money, PhoneNumber, DateRange, Location
```

Example — Address as a Value:
```
Customer { address = "123 ABC Street" }
```
→ Simple string, one address, no management needed → Attribute.

Example — Address as an Entity:
```
Customer can have: Home Address, Office Address, Shipping Address, Billing Address
Each address has: street, city, country, type, is_default
```
→ Managed independently, queried separately → Entity.

The domain context determines this, not the word itself.

---

## Tip 6 — Normalization trade-offs: OLTP vs OLAP vs Distributed

Normalization is a **tool**, not a goal. Normal Form is not a competition:
> "Higher form = better database" is FALSE.

| System type | Priority | Normalization approach |
|---|---|---|
| OLTP / transactional | Consistency, integrity, easy updates | Normalize to 3NF |
| Reporting / analytics | Read performance, aggregation | Denormalize (star/snowflake schema) |
| Distributed / high-scale reads | Read performance, pre-computation | Controlled duplication, materialized views |

The real questions before deciding are:
- What is the read/write ratio?
- How expensive are JOINs at this scale?
- How critical is consistency vs. performance?
- Are snapshots required for audit or compliance?

---

## Tip 7 — Functional Dependency is the true foundation of normalization

Instead of memorizing form definitions, think in functional dependencies:

```
product_id → product_name
product_id → category_id
category_id → category_name
```

The chain `product_id → category_id → category_name` is a **transitive dependency**
(3NF violation). `category_name` should not live in Product.

But then ask the follow-up questions:
- How frequently is this queried?
- Is the JOIN expensive at production scale?
- Does consistency matter here, or is a snapshot acceptable?

From the answers, decide whether to normalize or denormalize with explicit justification.

---

## Tip 8 — SQL vs NoSQL: it is about access patterns, not just data structure

**SQL/Relational asks:** "What is the data relationship?"

**NoSQL asks additionally:** "How does the application READ this data?"

Example: if every request to `GET /orders/{id}` always needs:
```
Order + Customer + Items + Product snapshots
```

Relational approach:
```
JOIN customer, order_item, product → multiple tables, multiple JOINs
```

MongoDB approach:
```json
{
  "_id": "O001",
  "customer": { "id": "C001", "name": "..." },
  "items": [{ "product_id": "P001", "quantity": 2, "price": 20000 }]
}
```
→ One document read, no JOINs needed.

NoSQL does not mean "no ERD". It means:
> **Model data based primarily on access patterns, not just data relationships.**

---

## Tip 9 — MongoDB embed vs reference rule

| Situation | Decision |
|---|---|
| Data is read together on the same request | Embed |
| Data has independent lifecycle / updated independently | Reference |
| Many-to-many relationship | Reference |
| Data is shared across many parent documents | Reference |

Example — Embed (Order with its Items):
```json
{ "order_id": "O001", "items": [{ "product_id": "P001", "quantity": 2 }] }
```
Order and OrderItems are always read together → embed.

Example — Reference (Order with Customer):
```json
{ "order_id": "O001", "customer_id": "C001" }
```
Customer is used by Order, Invoice, Payment, SupportTicket → reference, not copy.

---

## Tip 10 — Intentional duplication: Source of Truth principle

When duplicating data, always define which copy is the **Source of Truth** and which is a **Snapshot**.

```
Customer.name = "Tri Nguyen"          ← SOURCE OF TRUTH (can be updated)
Order.customer_name = "Tri"           ← SNAPSHOT (value at transaction time)
```

These are NOT the same fact. They represent different moments in time.
The snapshot is not a design flaw — it is a deliberate modeling decision.

Dangerous duplication = duplication without knowing WHY.
Acceptable duplication = duplication with a clear access pattern or business reason.

---

## Tip 11 — System design: 4 diagnostic questions

Use these 4 questions when starting any database design session:

**Q1: Is this a Thing or a Value?**
```
Customer → Thing (Entity)
Product  → Thing (Entity)
Address  → depends on domain
Name     → Value (Attribute)
Price    → Value (Attribute)
```

**Q2: Does it have its own lifecycle?**
```
Order         → Yes (Pending → Paid → Shipped)
OrderItem     → Lifecycle tied to Order
Product       → Yes (Active, Archived)
Name          → No
```

**Q3: Is this data read and updated together, or independently?**
→ Critical question when choosing between embed (NoSQL) and separate tables (SQL).

**Q4: If I duplicate this data, which copy is the Source of Truth?**
→ If you cannot answer this, the duplication is a bug waiting to happen.

---

## Tip 12 — The three mental layers to separate

Always keep these three layers distinct in your thinking:

```
BUSINESS LAYER
"Customer has Orders"

CONCEPTUAL MODEL
Customer ── Order  (pure business objects, no implementation)

LOGICAL MODEL
PK, FK, 1:N, UNIQUE, NOT NULL, CHECK, normalization

PHYSICAL MODEL
       ┌──────────────────┬────────────────┐
  PostgreSQL           MongoDB           Redis
  (tables, JOINs)    (documents, embed)  (keys, hashes)
```

Key insight:
- 3NF lives in the **Logical Model**
- Embedding and denormalization decisions live in the **Physical Model**
- An ERD normalized to 3NF can validly map to a MongoDB embedded document structure

> "ERD is 3NF normalized but MongoDB embeds the data" is NOT a contradiction.

The ERD describes data correctness and relationships.
The physical model describes storage and access optimization.

---

## Tip 13 — Learning path after mastering ERD basics

If normalization feels mechanical, the real mastery comes from understanding:

```
Functional Dependency
       ↓
Candidate Key
       ↓
1NF → 2NF → 3NF → BCNF
       ↓
Lossless Decomposition
       ↓
Dependency Preservation
```

When you understand WHY a table should be split (not just THAT it should),
you can confidently decide when to break the rules for performance.
