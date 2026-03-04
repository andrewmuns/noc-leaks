# Lesson 138: Common Failure Pattern — Database Connection Exhaustion
**Module 4 | Section 4.5 — Failure Patterns**
**⏱ ~6 min read | Prerequisites: Lesson 121**

---

## Why Connection Pools Exist

Every time an application needs to talk to a database, it needs a connection. Creating a database connection is expensive — it involves TCP handshake, TLS negotiation (if encrypted), authentication, and session setup. For PostgreSQL, each connection also spawns a dedicated server process consuming roughly 10MB of memory.

If every incoming SIP INVITE required creating a fresh database connection, the overhead would be crippling. Connection pools solve this by maintaining a set of pre-established connections that are borrowed, used, and returned — like a library lending books.

A typical pool configuration:
- **Minimum connections**: 5 (always ready)
- **Maximum connections**: 50 (hard ceiling)
- **Idle timeout**: 300 seconds (close unused connections)
- **Borrow timeout**: 5 seconds (how long to wait if all connections are busy)

When the application needs a database query, it borrows a connection from the pool, executes the query, and returns the connection. Fast queries borrow and return in milliseconds, keeping the pool healthy. Problems start when connections aren't returned promptly.

## How Exhaustion Happens

Connection pool exhaustion follows a predictable pattern:

### Slow Queries Hold Connections
A query that normally takes 5ms starts taking 5 seconds — perhaps because a table grew, an index was dropped, or a lock conflict emerged. Each slow query holds a connection for 1,000x longer than normal. If you have 50 connections and each is held for 5 seconds, you can only process 10 queries/second instead of your normal 10,000/second.

### Connection Leaks
A code bug that fails to return connections to the pool. This is insidious because it happens gradually — one connection leaks per hour, and after 50 hours, the pool is empty. Symptoms appear suddenly (pool full) even though the leak has been happening for days.

### Traffic Spike
Normal traffic uses 30 of 50 connections. A marketing campaign doubles traffic. Now 60 connections are needed, but the max is 50. The 11th through 60th concurrent requests wait for a connection, and if the borrow timeout expires, they fail.

🔧 **NOC Tip:** When you see database connection errors, immediately check three things: (1) Are there slow queries running? (2) Has traffic increased? (3) Was there a recent deployment that might have introduced a leak?

## Recognizing Pool Exhaustion in Grafana

Key metrics to watch:

- **`db_pool_active_connections`**: Number of connections currently borrowed. If this equals `max_pool_size`, you're exhausted.
- **`db_pool_pending_requests`**: Requests waiting for a connection. Any value above 0 means the pool is under stress. Growing values mean you're heading for failure.
- **`db_pool_timeout_total`**: Counter of borrow timeouts. Each increment is a failed request.
- **`db_query_duration_seconds`**: Histogram of query execution time. If the p99 jumps, slow queries are likely holding connections.

The telltale Grafana pattern: `active_connections` flatlines at the maximum while `pending_requests` climbs. Meanwhile, `timeout_total` starts incrementing. Application error logs show "could not acquire connection within timeout."

## Real-World Scenario: The Missing Index

A developer adds a new feature that queries the CDR table by `customer_id` and `created_at`. The query works fine in development with 1,000 rows. In production, the CDR table has 500 million rows.

Without an index on `(customer_id, created_at)`, PostgreSQL performs a sequential scan — reading every row. This takes 30 seconds per query. Each query holds a database connection for 30 seconds.

With a pool of 50 connections, the system can handle fewer than 2 of these queries per second. Normal traffic sends 20 per second. Within seconds, all 50 connections are held by sequential scans. Every other database query — routing lookups, authentication checks, number validation — can't get a connection. Call processing stops.

**The fix**: Add the missing index. `CREATE INDEX CONCURRENTLY idx_cdr_customer_created ON cdr (customer_id, created_at);` — the `CONCURRENTLY` keyword prevents locking the table during index creation.

🔧 **NOC Tip:** If you identify a slow query causing pool exhaustion, you have two immediate options: (1) Kill the slow queries using `pg_terminate_backend()` to free connections, or (2) Restart the application pods to reset the connection pool. Option 1 is more surgical; option 2 is faster but disruptive.

## Upstream Impact: The Cascade Connection

Database connection exhaustion is a common trigger for the cascading failures we covered in Lesson 121. When a service can't get database connections:

1. Its request handling threads block waiting for connections
2. Its API response times skyrocket
3. Upstream services waiting for API responses start timing out
4. The cascade propagates

This is why database connection pool metrics should be among your most watched Grafana panels. Pool exhaustion is often the *root cause* of what looks like a multi-service outage.

## PgBouncer: Connection Pooling at the Infrastructure Level

Many production deployments add PgBouncer (covered in depth in Lesson 151) between applications and PostgreSQL. PgBouncer maintains a small number of actual PostgreSQL connections and multiplexes hundreds of application connections onto them.

Without PgBouncer: 20 application pods × 50 connections = 1,000 PostgreSQL connections (10GB memory overhead).
With PgBouncer: 20 application pods × 50 connections → PgBouncer → 100 PostgreSQL connections (1GB memory overhead).

PgBouncer doesn't eliminate pool exhaustion at the application level, but it dramatically reduces load on PostgreSQL and allows more efficient connection sharing.

## Mitigation Steps During an Active Incident

1. **Identify slow queries**: Run `SELECT pid, now() - query_start AS duration, query FROM pg_stat_activity WHERE state = 'active' ORDER BY duration DESC;`
2. **Kill long-running queries**: `SELECT pg_terminate_backend(pid);` for queries running excessively long
3. **Check for lock contention**: `SELECT * FROM pg_locks WHERE NOT granted;` — blocked locks hold connections
4. **Restart affected application pods** if connection pools are corrupted
5. **Scale horizontally** if the issue is genuine traffic increase
6. **Add the missing index** if identified (use `CONCURRENTLY`)

🔧 **NOC Tip:** Always check `pg_stat_activity` first — it shows every active connection, what query it's running, and how long it's been running. This single view often reveals the root cause immediately.

---

**Key Takeaways:**
1. Connection pools prevent expensive connection creation overhead but have finite capacity
2. Slow queries, connection leaks, and traffic spikes are the three primary causes of pool exhaustion
3. Watch `active_connections` vs `max_pool_size` in Grafana — when they're equal, you're exhausted
4. Database pool exhaustion commonly triggers cascading failures across dependent services
5. `pg_stat_activity` is your first stop for diagnosing database connection issues in PostgreSQL
6. Kill long-running queries and consider PgBouncer for connection multiplexing at scale

**Next: Lesson 123 — Common Failure Pattern: DNS and Certificate Failures**
