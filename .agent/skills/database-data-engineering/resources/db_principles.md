---
name: db_principles.md
description: Database architecture principles for microservice systems. Covers the Database-per-Service pattern, Polyglot Persistence decision table, data consistency patterns (Saga, CQRS, Event Sourcing, Eventual Consistency), API Composition, CAP theorem, and query optimization techniques (N+1, indexing, transactions, pagination).
---
# Database Architecture Principles


## Part 1 — Microservice Database Patterns

### 1.1 Database-per-Service Principle

Each microservice owns its own database. No other service may access it directly.
Services communicate only via API calls or events.

**Why:**
- Ensures loose coupling between services
- Allows each service to choose the best database type (Polyglot Persistence)
- Prevents a single database failure from cascading system-wide

**Consequence:**
Cross-service JOINs at the database layer are no longer possible.
Alternatives:
- API Composition (application-layer aggregation)
- Denormalize necessary data into the consuming service via events
- Maintain a read-optimized Materialized View updated via CDC

---

### 1.2 Polyglot Persistence — Database Selection by Use Case

| Data type / use case | Recommended database | Examples |
|---|---|---|
| Financial transactions requiring strict ACID | Relational (SQL) | PostgreSQL, MySQL |
| Unstructured data, frequently changing schema | Document store | MongoDB, DynamoDB |
| Session, cache, high-speed temporary data | Key-value store | Redis, Memcached |
| Complex relational data (social graph, recommendations) | Graph database | Neo4j |
| Logs, metrics, time-series | Time-series DB | InfluxDB, TimescaleDB |
| Full-text search | Search engine | Elasticsearch, OpenSearch |
| Large-scale analytics, reporting | Columnar / Data Warehouse | Redshift, BigQuery, Snowflake |

Decision rule: choose the database type that best fits the access pattern and consistency
requirements of the individual service — not the default choice for the organization.

---

### 1.3 Data Consistency Patterns

Distributed transactions (2PC) are avoided in microservices due to performance impact
and availability risk. Use these patterns instead:

**Saga Pattern**
A sequence of local transactions. Each step publishes an event to trigger the next step.
On failure, compensating transactions (logical rollback) are executed.

- *Choreography*: Each service listens for events from other services. Simple but hard
  to trace and debug in large systems.
- *Orchestration*: A central orchestrator service coordinates the saga steps sequentially.
  Easier to control and debug. Introduces a coordination dependency.

Use Orchestration when the saga has more than 3 steps or involves financial operations.

**CQRS (Command Query Responsibility Segregation)**
Separate the write model (Command side) from the read model (Query side).
- Write model: normalized, optimized for correctness (3NF)
- Read model: denormalized, optimized for read performance — can live in a different
  database (e.g., PostgreSQL for write, Elasticsearch for read)
- Synchronize via domain events

Use CQRS when read and write access patterns have fundamentally different requirements.

**Event Sourcing**
Store all state changes as an immutable sequence of events.
Current state = replay of all past events.
Often paired with CQRS.

Advantages:
- Full audit trail for every state change
- Ability to rebuild state at any point in time
- Temporal queries become possible

Disadvantages:
- Significantly higher complexity
- Requires careful event schema versioning
- Eventual consistency by nature

**Eventual Consistency**
Accept that data across services will not be immediately synchronized.
The system will converge to a consistent state over a short time window.

This is the trade-off in AP systems (see CAP theorem).
Appropriate for: social feeds, shopping carts, product catalogs, non-critical dashboards.
Inappropriate for: financial ledgers, inventory reservation, payment confirmation.

---

### 1.4 API Composition (Cross-service Data Aggregation)

When a client needs data owned by multiple services:
- An API Gateway or aggregator service calls each service in parallel
- Results are merged at the application layer

Limitations:
- Increased latency (dependent on the slowest service)
- Complex partial failure handling (what if one service is down?)
- Not suitable for complex filtering across services (no distributed WHERE clause)

Alternative — Materialized View / Read-optimized Replica:
The consuming service stores a local copy of the data it needs from other services.
This local copy is updated via:
- Domain events (event-driven update)
- CDC (Change Data Capture, e.g., Debezium capturing DB write-ahead log → Kafka)

---

### 1.5 CAP Theorem

In distributed systems, you can guarantee at most 2 of 3 properties:
- **C**onsistency: all nodes see the same data at the same time
- **A**vailability: every request receives a response (not necessarily the latest data)
- **P**artition Tolerance: system continues to operate despite network failures between nodes

Partition Tolerance (P) is always required in real distributed systems. So the real choice is:

| Trade-off | Description | Example use case |
|---|---|---|
| CP system | Prefers consistency, may reject requests during partition | Banking core, inventory |
| AP system | Prefers availability, may return stale data temporarily | Social feed, shopping cart |

Design each service boundary with a conscious CP/AP decision.

---

## Part 2 — Query Optimization and Anti-patterns

### 2.1 N+1 Query Problem

**Symptom**: For a list of N records, the application fires 1 query to fetch the list,
then 1 additional query per record to fetch related data → N+1 total queries.

**Example (bad)**:
```
orders = query("SELECT * FROM orders LIMIT 100")    # 1 query
for order in orders:
    customer = query("SELECT * FROM customers WHERE id = ?", order.customer_id)  # 100 queries
```

**Solutions:**

Option A — JOIN or Eager Loading:
```sql
SELECT o.*, c.name FROM orders o
JOIN customers c ON o.customer_id = c.id
LIMIT 100
```

Option B — Batch query (DataLoader pattern):
```
customer_ids = [o.customer_id for o in orders]
customers = query("SELECT * FROM customers WHERE id IN (?)", customer_ids)  # 1 query
```

Detection: slow query logs, ORM debug output, APM tools showing high query count per request.

---

### 2.2 Indexing Strategy

**B-tree index** (default): efficient for equality, range queries, ORDER BY, prefix search.
```sql
CREATE INDEX idx_orders_customer_id ON orders(customer_id);
CREATE INDEX idx_orders_created_at ON orders(created_at);
```

**Hash index**: equality lookup only. Does not support range queries.

**Composite index**: column order matters.
- Put columns used in WHERE equality conditions first
- Put high-selectivity columns (many distinct values) earlier
- Include ORDER BY columns if possible to avoid a sort step

```sql
-- Query: WHERE customer_id = ? AND status = ? ORDER BY created_at
CREATE INDEX idx_orders_composite ON orders(customer_id, status, created_at);
```

**Index coverage**: if all columns in a query are in the index (SELECT + WHERE + ORDER BY),
the database can answer the query from the index alone (no table lookup).

**Trade-off**: every index accelerates reads but slows writes (INSERT/UPDATE/DELETE must
update all indexes). Do not index blindly. Index based on actual query patterns.

---

### 2.3 Reading Execution Plans

For PostgreSQL:
```sql
EXPLAIN ANALYZE SELECT * FROM orders WHERE customer_id = 123 ORDER BY created_at DESC;
```

Key indicators to look for:
- `Seq Scan` → full table scan, no index used → investigate if table is large
- `Index Scan` or `Index Only Scan` → index being used
- `Hash Join` / `Nested Loop` → join strategy
- `actual rows` vs `estimated rows` → large discrepancy means stale statistics, run `ANALYZE`
- `actual time` → identify which step is slowest

---

### 2.4 Transaction Management and Deadlocks

**Transaction Isolation Levels** (from weakest to strongest):

| Level | Allows | Prevents |
|---|---|---|
| Read Uncommitted | Dirty read | — |
| Read Committed | Non-repeatable read | Dirty read |
| Repeatable Read | Phantom read | Dirty read, Non-repeatable read |
| Serializable | — | All anomalies |

Default in PostgreSQL: Read Committed. Default in MySQL InnoDB: Repeatable Read.

**Deadlock prevention:**
- Always acquire locks in a consistent order across all transactions
- Keep transactions short — hold locks for the minimum time
- Use `SELECT FOR UPDATE SKIP LOCKED` for queue-style processing

**Optimistic Locking** (low-contention scenarios):
```sql
-- Add version column to table
UPDATE orders SET status = 'SHIPPED', version = version + 1
WHERE id = ? AND version = ?
-- If 0 rows affected → conflict detected, retry
```

**Pessimistic Locking** (high-contention scenarios):
```sql
SELECT * FROM inventory WHERE product_id = ? FOR UPDATE;
-- Holds a row lock until transaction commits or rolls back
```

---

### 2.5 Pagination Strategies

**OFFSET/LIMIT** (simple, but problematic at scale):
```sql
SELECT * FROM orders ORDER BY created_at DESC LIMIT 20 OFFSET 10000;
```
Problem: database must scan 10020 rows to return 20. Performance degrades linearly.

**Keyset / Cursor-based Pagination** (recommended for large datasets):
```sql
-- First page
SELECT * FROM orders ORDER BY created_at DESC, id DESC LIMIT 20;

-- Next page (using last values from previous page)
SELECT * FROM orders
WHERE (created_at, id) < ('2026-08-01 12:00:00', 500)
ORDER BY created_at DESC, id DESC
LIMIT 20;
```
Performance is O(1) — no offset scan. Requires a stable sort key (usually created_at + id).
Limitation: cannot jump to arbitrary pages. Suitable for infinite scroll, not page numbers.
