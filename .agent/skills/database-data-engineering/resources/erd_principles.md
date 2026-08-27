---
name: erd_principles.md
description: 24 numbered ERD design principles distilled from domain modeling practice, covering entity identification, relationships, normalization trade-offs, constraints, naming conventions, and anti-patterns. Also contains the 15-question ERD review checklist.
---
# ERD Design Principles


## Principle 1 — Start from business, not from database

Before designing tables, ask:
> "What objects and activities does this system manage?"

List domain nouns first (Customer, Product, Order, Payment).
Never start with `customer_tbl`, `order_tbl` — that is implementation before design.

---

## Principle 2 — Identify entities by identity and lifecycle

A concept becomes an Entity when it has:
- Its own identity (a unique ID)
- Its own attributes
- Its own lifecycle (can be created, modified, deleted independently)
- Its own relationships with other entities
- Its own query needs (business queries target it directly)

If a concept lacks most of the above, it is an Attribute, not an Entity.

---

## Principle 3 — Every entity must have a Primary Key

Requirements for a good PK:
- Unique across all instances
- Never null
- Stable over time
- Does not depend on business data that may change

Prefer surrogate keys (`customer_id` auto-increment or UUID) over natural keys (`email`, `SSN`).
Natural/business identifiers should be modeled as UNIQUE constraints, not PKs.

---

## Principle 4 — Read relationships as sentences in both directions

Do not connect two entities without verbalizing the relationship:

```
"One Customer can place many Orders."
"One Order is placed by exactly one Customer."
```

This forces clarity on cardinality and optionality before committing to a structure.

---

## Principle 5 — Always determine cardinality explicitly

The three fundamental types:
- **1:1** — rare; use to isolate sensitive or infrequently accessed data
- **1:N** — most common; FK lives on the "many" side
- **N:N** — must always be resolved to an Associative Entity in relational databases

Never leave cardinality ambiguous or implied.

---

## Principle 6 — N:N relationships must have an Associative Entity

```
Order N ──── N Product
```
becomes:
```
Order 1 ──── N OrderItem N ──── 1 Product
```

If the relationship itself has attributes (quantity, unit_price, discount), it has already
become an Entity by definition.

> Rule: If a relationship has attributes, it IS an Entity.

---

## Principle 7 — Determine optionality, not just cardinality

For each relationship end, decide mandatory vs. optional:

```
Customer 1  ──── 0..N Order     (Customer may have no orders)
Order    ──── 1       Customer  (Order MUST belong to a customer)
```

Optionality determines NOT NULL vs. nullable FK. This is the most commonly skipped
step in ERD design and causes real data integrity bugs.

---

## Principle 8 — FK belongs on the "many" side

```
Customer 1 ──── N Order
```
Results in:
```
Order { order_id PK, customer_id FK, ... }
```
NOT:
```
Customer { customer_id PK, order_ids[] }   ← WRONG
```

This is the fundamental rule of relational modeling.

---

## Principle 9 — One fact has one owner

Avoid duplicating data across entities unless there is an explicit business reason.

Wrong (implicit duplication):
```
Order { order_id, customer_id, customer_name, customer_email }
```

Correct (single source of truth):
```
Order { order_id, customer_id FK }
Customer { customer_id, name, email }
```

Exception — intentional snapshot:
```
Order { customer_id FK, customer_name_snapshot }
```
Acceptable when you need the customer name as it was at the time of the transaction
(e.g., invoice). The snapshot and the live record have different semantic meaning.

---

## Principle 10 — Attributes must be atomic (1NF)

No multi-value columns:
```
WRONG: phone_numbers = "0901,0902,0903"
```
Correct:
```
CustomerPhone { customer_id FK, phone_number, type }
```

No repeated groups of columns:
```
WRONG: Product { tag1, tag2, tag3 }
```
Correct:
```
ProductTag { product_id FK, tag }
```

---

## Principle 11 — Normalize to remove redundancy

| Normal Form | Condition | Purpose |
|---|---|---|
| 1NF | Atomic values, no repeating groups | Eliminate multi-value in one cell |
| 2NF | 1NF + no partial dependency on composite PK | Eliminate dependency on part of a PK |
| 3NF | 2NF + no transitive dependency | Eliminate A → B → PK chains |
| BCNF | Every determinant is a candidate key | Handle edge cases not caught by 3NF |

OLTP systems should target 3NF to prevent insert/update/delete anomalies.

---

## Principle 12 — Do not over-normalize

Normalization is a tool, not a competition.

If `Product.color` is a simple string with no lifecycle of its own, do not create:
```
Color, ColorType, ColorTranslation, ColorCategory
```

Just use:
```
Product { product_id, color }
```

Rule: Normalize when it solves redundancy, consistency, or a real business requirement.
Do not normalize mechanically.

---

## Principle 13 — Define ownership and delete behavior

Ask: "Can Entity B exist without Entity A?"

- `OrderItem` cannot exist without `Order` → `ON DELETE CASCADE`
- `Order` should NOT be deleted when `Customer` is deleted → `ON DELETE RESTRICT` or `SET NULL`

Always define FK referential actions explicitly. Never rely on application code alone
to enforce lifecycle dependencies.

---

## Principle 14 — Distinguish current state from history

If the business needs to know "what happened in the past", model a history table:

```
OrderStatusHistory { id, order_id FK, status, changed_at, changed_by FK }
```

Do not try to fit historical data into the main entity by adding columns like
`previous_status`, `status_before_that`. That approach does not scale.

---

## Principle 15 — Model temporal data explicitly

Ask for each attribute: "Does this value change over time? Does anyone need past values?"

For time-varying values, use effective dating:
```
ProductPrice { product_id FK, price, effective_from, effective_to }
```

This is mandatory in ERP, HR, insurance, and financial systems.

---

## Principle 16 — Business rules must become database constraints

Do not document business rules only in prose. Enforce them at the DB layer:

| Rule | Constraint |
|---|---|
| Email must be unique | UNIQUE(email) |
| Order must have a customer | NOT NULL + FK |
| Quantity must be positive | CHECK(quantity > 0) |
| One profile per user | UNIQUE(user_id) in Profile |

Rule: If the database can enforce it, the database should enforce it.

---

## Principle 17 — Distinguish surrogate key from business key

```
Customer
--------
customer_id  PK   ← Surrogate Key (technical, stable)
email        UK   ← Business/Natural Key (meaningful, but can change)
```

Never use business identifiers as PKs. Business rules change; PKs must not.

---

## Principle 18 — Do not create God Entities

A God Entity is a single catch-all table with a `type` discriminator:
```
Entity { id, type, name, status, value1, value2, value3, ... }
type IN ('CUSTOMER', 'PRODUCT', 'ORDER', 'EMPLOYEE')
```

If objects have different business meaning, attributes, and lifecycles, give them
separate tables. The "Entity-Attribute-Value" (EAV) anti-pattern is the extreme version of this.

---

## Principle 19 — Do not split every attribute into its own entity

The opposite anti-pattern:
```
ProductName, ProductDescription, ProductColor, ProductWeight (all separate tables)
```

If these have no independent identity, lifecycle, or query need, they are columns:
```
Product { product_id, name, description, color, weight }
```

---

## Principle 20 — Naming conventions must be consistent

Recommended convention:

**Table names:** singular noun, PascalCase (`Customer`, `OrderItem`) or snake_case (`customer`, `order_item`). Pick one and enforce it across the entire schema.

**Column names:** snake_case, all lowercase (`customer_id`, `created_at`, `is_active`).

**FK columns:** reference table name + `_id` suffix (`customer_id`, `product_id`).

**Timestamps:** `created_at`, `updated_at`, `deleted_at` (for soft delete).

Never mix conventions: `customerID`, `order_id`, `ProductId`, `createdDate` in the same schema.

---

## Principle 21 — ERD must serve use cases

After completing the design, verify each critical business query can be answered:

"Total spend by Customer A in August"
→ Customer → Order → OrderItem → Product

"Which orders are awaiting shipment?"
→ Order (status filter)

"Who changed Order #123 status and when?"
→ Order → OrderStatusHistory → User

A beautiful ERD that cannot serve its queries is a failed ERD.

---

## Principle 22 — Verify all invariants after design

After completing the ERD, systematically check each invariant:

```
Can an Order exist without a Customer? → FK NOT NULL
Can an OrderItem exist without an Order? → FK + CASCADE
Can a Product appear twice in the same Order? → UNIQUE(order_id, product_id) in OrderItem
Can quantity be zero or negative? → CHECK(quantity > 0)
Can a User have two profiles? → UNIQUE(user_id) in Profile
Can the same email be registered twice? → UNIQUE(email)
```

Each answer must map to a PK, FK, UNIQUE, NOT NULL, or CHECK constraint.

---

## Principle 23 — Three-layer model separation

Always mentally separate:

```
BUSINESS LAYER
"Customer has Orders"

CONCEPTUAL MODEL
Customer ── Order (business objects, no implementation detail)

LOGICAL MODEL
PK / FK / cardinality / normalization / constraints

PHYSICAL MODEL
PostgreSQL tables / MongoDB documents / Redis keys
```

3NF normalization lives primarily in the Logical Model.
Denormalization and embedding decisions live in the Physical Model.
A normalized logical ERD that maps to a MongoDB embedded document is NOT a contradiction.

---

## Principle 24 — ERD Review Checklist (15 Questions)

Use these 15 questions to review any ERD before approving or implementing it:

| # | Question |
|---|---|
| 1 | Does this Entity truly exist in the business? |
| 2 | Does this Entity have a clear, stable identity? |
| 3 | Is the PK stable and surrogate (not a business key)? |
| 4 | Does each attribute belong to the correct Entity? |
| 5 | Does each relationship have clear business meaning? |
| 6 | Is the cardinality correctly identified (1:1, 1:N, N:N)? |
| 7 | Is optionality defined (mandatory vs. optional on each side)? |
| 8 | Have all N:N relationships been resolved to Associative Entities? |
| 9 | Is there any unintentional data duplication? |
| 10 | Are there any 1NF / 2NF / 3NF violations? |
| 11 | Is there any over-normalization (splitting things that should stay together)? |
| 12 | Is ownership and cascade delete behavior defined for all dependent entities? |
| 13 | Is there any attribute that changes over time and requires a history table? |
| 14 | Are all business constraints expressed as DB constraints (UNIQUE, NOT NULL, CHECK)? |
| 15 | Can all critical business queries be answered by traversing this ERD? |
