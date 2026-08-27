---
name: erd_design_framework.md
description: The canonical 12-step ERD design process. Use this as the primary workflow when designing any database schema from business requirements. Each step builds on the previous — do not skip or reorder steps.
---
# ERD Design Framework — 12-Step Process

## Core Principle

> Model business first. Model database second.

Before touching any table definition, understand the business objects and operations the
system manages. Begin with domain language (Customer, Order, Product), not technical
naming (customer_tbl, order_tbl).

---

## The 12-Step Process

### Step 1 — Identify Business Concepts

Ask the user or stakeholder:

> "What are the core objects and activities this system manages?"

Output a flat list of domain nouns. Example for an e-commerce system:

```
Customer
Product
Order
Payment
Shipment
Review
```

These are candidates, not confirmed entities yet.

---

### Step 2 — Identify Entities

For each candidate noun, apply the **6-question Entity test**:

| Question | If "Yes" → leans toward Entity |
|---|---|
| Does it have its own identity? | customer_id, product_id... |
| Does it have multiple distinct attributes? | name, status, date... |
| Does it have its own lifecycle? | Created → Active → Closed |
| Does it have relationships with other concepts? | Customer → Order |
| Does the business query/manage it independently? | "Find all addresses..." |
| Can it exist relatively independently? | Address managed on its own |

More "Yes" answers = stronger case for Entity.
Few "Yes" answers = likely just an Attribute.

Also apply the **verb test**: if the system has verbs acting on a concept
(create, update, delete, activate, cancel, approve, track, search, assign),
that concept is almost certainly an Entity.

---

### Step 3 — Identify Attributes

For each confirmed Entity, list all its descriptive properties.
Classify each attribute as:

- **Simple**: single atomic value (name, email, price)
- **Composite**: made up of sub-parts (full_address has street, city, country)
- **Single-value**: one value per entity instance (email)
- **Multi-value**: multiple values per instance (phone_numbers) — flag for Step 8
- **Derived**: computable from other attributes (age from birth_date, total from line items)
  — do not store unless read performance justifies denormalization

---

### Step 4 — Identify Primary Keys

Every entity must have a unique, stable identifier.

**Rules for PKs:**
- Prefer surrogate keys (UUID, auto-increment integer) over natural keys (email, SSN)
- Surrogate keys survive business rule changes (email can change, customer_id cannot)
- Natural/business identifiers (email, national ID) should be marked UNIQUE, not PK

```
Customer
--------
customer_id  PK   ← surrogate
email        UK   ← business key, unique but not PK
```

---

### Step 5 — Identify Relationships

For each pair of related entities, read the relationship as a sentence in both directions:

```
"One Customer can have many Orders."
"One Order belongs to exactly one Customer."
```

Confirm the relationship has business meaning, not just a technical link.

---

### Step 6 — Determine Cardinality

Three fundamental types:

**One-to-One (1:1)**
```
User 1 ──── 1 UserProfile
```
Rare. Use to split sensitive data (security) or rarely accessed columns (performance).

**One-to-Many (1:N)**
```
Customer 1 ──── N Order
```
Most common. FK lives on the "many" side.

**Many-to-Many (N:N)**
```
Student N ──── N Course
```
Cannot exist directly in relational model — resolve in Step 8.

---

### Step 7 — Determine Optionality (Participation)

For each relationship end, decide:

- **Mandatory (total participation)**: every instance must participate → NOT NULL FK
- **Optional (partial participation)**: instance may or may not participate → nullable FK

Example:

```
Customer 1 ──── 0..N Order   (Customer may have zero orders)
Order    ──── 1   Customer   (Order MUST belong to a customer)
```

For Guest Checkout:
```
Order ──── 0..1 Customer     (Order may have no registered customer)
```

This is frequently omitted in ERD design and causes real bugs in constraints.

---

### Step 8 — Resolve N:N Relationships

Every N:N must become an Associative (Junction) Entity.

**Before:**
```
Order N ──── N Product
```

**After:**
```
Order 1 ──── N OrderItem N ──── 1 Product
```

The associative entity often carries its own attributes — attributes that belong to
the relationship itself:

```
OrderItem
---------
order_id    FK
product_id  FK
quantity
unit_price  ← price at time of order (snapshot)
discount
```

Key rule: If the relationship itself has attributes, it must become an Entity.

Also resolve multi-value attributes found in Step 3:

```
Customer
CustomerPhone (customer_id FK, phone_number, type)
```

---

### Step 9 — Identify Constraints

Map each business rule to a database constraint:

| Business Rule | DB Constraint |
|---|---|
| Email must be unique | UNIQUE(email) |
| Order must have a customer | NOT NULL on customer_id FK |
| Quantity must be positive | CHECK(quantity > 0) |
| OrderItem cannot exist without Order | FK + ON DELETE CASCADE |
| Customer cannot be deleted with Orders | FK + ON DELETE RESTRICT |

Rule: Any invariant the database can enforce, it should enforce.
Do not leave integrity solely to application code.

---

### Step 10 — Check Normalization

Evaluate against normal forms for OLTP systems:

**1NF — Atomic values**
Each column holds one indivisible value. No comma-separated lists.

**2NF — Full functional dependency** (relevant when composite PKs exist)
Every non-key attribute depends on the FULL composite key, not just part of it.
Violation example: `product_name` in `OrderItem(order_id, product_id)` — depends only on `product_id`.

**3NF — No transitive dependency**
No non-key attribute depends on another non-key attribute.
Violation example: `department_name` in Employee table where `employee_id → department_id → department_name`.

**Practical rule:**
- OLTP → normalize to 3NF to prevent insert/update/delete anomalies
- OLAP / reporting → controlled denormalization is acceptable (star/snowflake schema)
- Never over-normalize: if an attribute has no lifecycle/identity/query needs of its own, keep it as a column

---

### Step 11 — Check History and Temporal Data

For each attribute, ask:

> "Does this value change over time? Does the business need to know past values?"

If yes, design a history table:

```
OrderStatusHistory
------------------
id           PK
order_id     FK
status
changed_at
changed_by   FK → User
```

If temporal range queries are needed (e.g., "What was the price on July 1?"):

```
ProductPrice
------------
product_id   FK
price
effective_from
effective_to
```

Critical for: ERP, HR, insurance, financial, and billing systems.

---

### Step 12 — Validate Against Use Cases

For each major business query, trace the path through the ERD:

Example — "Total spend by customer A in August":
```
Customer → Order → OrderItem → Product
```

Example — "Who changed this Order's status?":
```
Order → OrderStatusHistory → User
```

If a use case cannot be satisfied by the current ERD structure, revise.
A good ERD must support all critical business queries efficiently.

---

## Framework Summary Diagram

```
Business Requirements
        ↓
1. Identify Business Concepts
        ↓
2. Identify Entities (6-question test)
        ↓
3. Identify Attributes (type classification)
        ↓
4. Identify Primary Keys (surrogate preferred)
        ↓
5. Identify Relationships (read as sentences)
        ↓
6. Determine Cardinality (1:1, 1:N, N:N)
        ↓
7. Determine Optionality (mandatory vs optional)
        ↓
8. Resolve N:N → Associative Entities
        ↓
9. Identify Constraints (UNIQUE, NOT NULL, CHECK, FK behavior)
        ↓
10. Check Normalization (1NF → 3NF for OLTP)
        ↓
11. Check History / Temporal Data
        ↓
12. Validate Against Use Cases
```
