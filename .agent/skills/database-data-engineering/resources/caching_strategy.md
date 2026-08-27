---
name: caching_strategy.md
description: Caching strategy reference covering the four main cache patterns (Cache-aside, Read-through, Write-through, Write-behind), cache invalidation techniques, stampede prevention, eviction policies, cache tier placement, and Redis vs Memcached selection guide.
---
# Caching Strategy


## Core Principle

Cache reduces load on the database and decreases response latency. The cost is added
architectural complexity and the risk of serving stale data.

Every caching decision must explicitly answer:
- Which layer is this cache at?
- Which pattern drives reads and writes?
- How is the cache invalidated?
- What happens when the cache fails?

---

## Part 1 — Four Cache Patterns

### Pattern 1 — Cache-Aside (Lazy Loading)

The application manages the cache manually.

**Read flow:**
1. Check cache. If HIT → return cached data.
2. If MISS → query database → write result to cache → return data.

**Write flow:**
The application writes directly to the database.
The cache is invalidated or updated separately (or simply left to expire via TTL).

```
Application
    │
    ├── GET cache.get(key)
    │       │
    │   HIT → return
    │       │
    │   MISS → query DB → cache.set(key, value, ttl) → return
    │
    └── POST/PUT → db.write() → cache.delete(key)  [optional invalidation]
```

**Advantages:**
- Only requested data is cached (no wasted memory)
- Cache failure degrades gracefully (application falls back to DB)

**Disadvantages:**
- First request for any key is always slow (cold start)
- Risk of stale data between writes and cache expiry

Best for: read-heavy workloads with infrequent writes, data that can tolerate slight staleness.

---

### Pattern 2 — Read-Through

The cache layer handles fetching from the database automatically on a miss.
Application always talks to the cache, never directly to the database for reads.

**Read flow:**
1. Application queries cache.
2. MISS → cache layer fetches from DB automatically → stores result → returns to application.

**Advantages:**
- Application code is simpler (no manual cache-miss handling)
- Consistent cache population behavior

**Disadvantages:**
- Requires cache provider to support this pattern (Redis does not natively; needs a library/ORM integration)
- First request per key is still slow

Best for: systems where a cache middleware (DAX, Hibernate 2nd-level cache) manages the logic.

---

### Pattern 3 — Write-Through

Every write goes to the cache AND the database atomically.

**Write flow:**
1. Application writes to cache.
2. Cache layer synchronously writes to database.
3. Both succeed or both fail.

**Advantages:**
- Cache is always consistent with the database
- No risk of serving stale data

**Disadvantages:**
- Write latency increases (must wait for both cache + DB write)
- Wastes cache space for data that is rarely read after being written

Best for: data that is written and then immediately read frequently (user sessions, real-time dashboards).

---

### Pattern 4 — Write-Behind (Write-Back)

Application writes to the cache first. The cache asynchronously flushes to the database later.

**Write flow:**
1. Application writes to cache → returns success immediately.
2. Cache layer asynchronously batches writes to the database.

**Advantages:**
- Extremely fast write path (no DB round-trip in the critical path)
- Natural write batching reduces DB pressure

**Disadvantages:**
- Risk of data loss if the cache node crashes before flushing
- Increased complexity (need to handle flush failures and retries)

Best for: high-frequency write workloads where some data loss is acceptable
(analytics counters, activity feeds, non-critical metrics).

---

## Part 2 — Cache Invalidation

Cache invalidation is one of the hardest problems in systems design.
Two primary strategies:

### TTL (Time-To-Live) Expiry
Set a maximum age for each cached entry. After TTL expires, the cache misses and
data is refreshed from the database.

- Too short TTL → high miss rate, high DB load, defeats the purpose of caching
- Too long TTL → stale data served to users, especially after DB writes

Recommended: set TTL based on acceptable staleness per data type.
Example: user profile → 5 minutes TTL. Product price → 1 minute TTL. Session → 30 minutes TTL.

### Active Invalidation on Write Events
When a write occurs to the source of truth (database), explicitly delete or update
the corresponding cache key.

```python
def update_user_profile(user_id, data):
    db.update("UPDATE users SET ... WHERE id = ?", user_id, data)
    cache.delete(f"user:{user_id}")   # invalidate immediately
```

Best practice: combine TTL as a safety net + active invalidation as the primary mechanism.

---

## Part 3 — Cache Stampede Prevention (Thundering Herd)

**Problem**: A hot cache key expires. At the exact same moment, 1000 concurrent
requests all get a cache miss and all fire a database query simultaneously.
This spike can overwhelm the database.

**Solutions:**

**Mutex / Lock**: Only one process is allowed to rebuild the cache at a time.
Others wait until the rebuild completes.

```python
def get_with_lock(key, fetch_fn, ttl):
    value = cache.get(key)
    if value:
        return value
    lock_acquired = cache.setnx(f"lock:{key}", 1, timeout=10)
    if lock_acquired:
        value = fetch_fn()          # query DB
        cache.set(key, value, ttl)
        cache.delete(f"lock:{key}")
    else:
        sleep(0.1)
        return get_with_lock(key, fetch_fn, ttl)  # retry after lock releases
    return value
```

**Random TTL Jitter**: Add a random offset to TTL so keys do not expire simultaneously.

```python
base_ttl = 300  # 5 minutes
jitter = random.randint(0, 60)
cache.set(key, value, ttl=base_ttl + jitter)
```

**Stale-While-Revalidate**: Return stale data immediately while refreshing in the background.
Eliminates the user-facing latency spike entirely.

---

## Part 4 — Eviction Policies

When the cache is full, entries must be evicted to make room for new ones.

| Policy | Behavior | Best for |
|---|---|---|
| LRU (Least Recently Used) | Evict the entry that was accessed least recently | General-purpose workloads |
| LFU (Least Frequently Used) | Evict the entry accessed the fewest times overall | Workloads with stable "hot" data patterns |
| FIFO | Evict the oldest entry regardless of access | Simple queues |
| Random | Evict a random entry | When LRU overhead is too high |
| TTL-based | Evict expired entries first | When all entries have TTLs |

Default recommendation: **LRU** for most web application cache scenarios.
Use **LFU** when you need to protect frequently accessed entries even if they haven't been
recently used (e.g., popular product pages that are accessed heavily during business hours
but less at night).

---

## Part 5 — Cache Tier Placement

```
User Request
     │
     ▼
1. Client-side (Browser cache, Mobile app cache)
   └── Reduces: outbound bandwidth, repeat requests for static resources
     │
     ▼
2. CDN (CloudFront, Cloud CDN, Fastly)
   └── Reduces: geographic latency for static assets, media, API responses
     │
     ▼
3. Application-level (Redis, Memcached)
   └── Reduces: DB query load for session, computed data, hot entity reads
     │
     ▼
4. Database-level (Query cache, Buffer pool, Materialized views)
   └── Reduces: disk I/O for frequently repeated queries
```

Optimize from the outermost layer inward. Adding application-level caching before
optimizing queries and indexes is premature.

---

## Part 6 — Redis vs Memcached Selection Guide

| Dimension | Redis | Memcached |
|---|---|---|
| Data structures | String, List, Set, Sorted Set, Hash, Stream, Bitmap | String only |
| Persistence | RDB (snapshot) + AOF (append-only log) | None (pure in-memory) |
| Pub/Sub messaging | Yes (built-in pub/sub + Streams) | No |
| Clustering | Redis Cluster (horizontal sharding) | Built-in multi-threading |
| Replication | Primary-replica replication | No |
| Atomic operations | Lua scripting, MULTI/EXEC transactions | Limited |
| Memory efficiency | Slightly lower (data structure overhead) | Slightly higher for plain strings |
| Throughput | Single-threaded core (I/O multiplexed) | Multi-threaded |

**Choose Redis when:**
- You need data structures beyond simple key-value (sorted sets for leaderboards,
  lists for queues, sets for deduplication, hashes for partial object updates)
- You need persistence and durability guarantees
- You need pub/sub messaging or event streaming
- You need atomic operations across multiple keys (Lua scripts)

**Choose Memcached when:**
- You only need simple string key-value caching
- You need maximum raw throughput per CPU core (multi-threaded advantage)
- You want operational simplicity with no persistence concerns
- Memory efficiency for large plain object caches is the priority

Default recommendation: **Redis** for most modern applications due to its versatility.
Memcached is a valid choice only when raw cache throughput at massive scale justifies
the feature trade-offs.
