# Lesson 167: Connection Pooling — PgBouncer and Connection Management
**Module 5 | Section 5.3 — Databases for NOC**
**⏱ ~6 min read | Prerequisites: Lesson 148**

---

## Why Connection Pooling Exists

Here's a fact that surprises many engineers: every PostgreSQL connection spawns a dedicated backend process on the server. Each of those processes consumes approximately 5–10 MB of RAM just by existing — before any queries run. If you have a telecom platform with 200 microservice instances, each opening 5 connections, that's 1,000 connections consuming 5–10 GB of memory purely for connection overhead.

Now scale that to a real Telnyx-like environment: dozens of services, multiple replicas per service, connection pools per replica. You can easily hit thousands of concurrent connections. PostgreSQL's default `max_connections` is 100. Even if you raise it to 1,000, the server spends more time managing processes than executing queries.

This is the fundamental problem connection pooling solves: **decoupling the number of application-level connections from the number of actual database connections**.

## How Connection Pooling Works

A connection pooler sits between your application and PostgreSQL as a lightweight proxy. Applications connect to the pooler (thinking it's the database). The pooler maintains a much smaller pool of real PostgreSQL connections and multiplexes application requests across them.

Think of it like an airline check-in counter. You don't need one counter per passenger on a flight — you need enough counters to handle the throughput. Most passengers spend more time waiting, walking, or sitting at the gate than actually at the counter. Similarly, most application connections spend more time idle than actively querying.

A typical ratio might be 500 application connections multiplexed across 50 real database connections — a 10:1 reduction.

## PgBouncer: The Industry Standard

PgBouncer is the most widely deployed PostgreSQL connection pooler, and for good reason: it's lightweight (single-threaded, uses libevent), rock-solid, and simple to configure. A single PgBouncer instance can handle thousands of client connections while maintaining a small pool of server connections.

### Configuration Essentials

```ini
[databases]
mydb = host=pg-primary.internal port=5432 dbname=telecom_production

[pgbouncer]
listen_port = 6432
listen_addr = 0.0.0.0
auth_type = md5
auth_file = /etc/pgbouncer/userlist.txt
pool_mode = transaction
default_pool_size = 50
max_client_conn = 1000
reserve_pool_size = 5
reserve_pool_timeout = 3
```

The key settings: `default_pool_size` controls how many real PostgreSQL connections exist per database/user pair. `max_client_conn` limits how many application connections PgBouncer accepts. The ratio between these is your multiplexing factor.

## Pool Modes: The Critical Decision

PgBouncer offers three pool modes, and choosing the right one is the most important configuration decision:

### Session Pooling
A server connection is assigned to a client for the entire session (connect → disconnect). This is the safest but least efficient mode — essentially just connection caching. You still need as many server connections as concurrent clients.

### Transaction Pooling
A server connection is assigned only for the duration of a transaction. Between transactions, the connection returns to the pool. This is the **sweet spot for most telecom applications** — dramatic multiplexing gains with minimal application changes. However, session-level features don't work: `SET` commands, prepared statements, `LISTEN/NOTIFY`, and advisory locks are lost between transactions.

### Statement Pooling
A server connection is assigned per individual statement. Maximum multiplexing, but multi-statement transactions break. Rarely used in practice.

🔧 **NOC Tip:** Transaction pooling is the default choice for telecom workloads. If an application breaks after enabling PgBouncer, check if it uses prepared statements or session-level `SET` commands — these are the most common incompatibilities.

## Monitoring Pool Health

PgBouncer exposes an internal admin database where you can run diagnostic queries:

```sql
-- Connect to PgBouncer admin
psql -h localhost -p 6432 -U pgbouncer pgbouncer

-- Show pool statistics
SHOW POOLS;

-- Show active client connections
SHOW CLIENTS;

-- Show server connections
SHOW SERVERS;

-- Show aggregate stats
SHOW STATS;
```

The critical metrics to monitor:

| Metric | Healthy | Warning | Action |
|--------|---------|---------|--------|
| `cl_active` | < max_client_conn × 80% | > 80% | Scale application or increase limit |
| `sv_active` | < pool_size × 80% | > 80% | Increase pool_size or investigate slow queries |
| `sv_waiting` | 0 | > 0 for extended periods | Clients queuing for connections — critical |
| `avg_wait_time` | < 1ms | > 10ms | Connection contention |

### A Real Troubleshooting Scenario

**Alert:** Application response times spiking. Grafana shows P99 latency jumping from 50ms to 2 seconds.

**Investigation:**
1. Connect to PgBouncer admin: `SHOW POOLS;`
2. Observe: `sv_active = 50` (pool fully used), `cl_waiting = 127` (clients queuing!)
3. Check `SHOW SERVERS;` — all connections show long-running queries
4. One query has been running for 45 seconds — a missing index on a CDR lookup

**Root cause:** A new analytics query was deployed without proper indexing, monopolizing all pooled connections. Other applications queue behind it.

**Fix:** Kill the long-running query (`SELECT pg_terminate_backend(pid)`), add the missing index, and consider separate pools for analytics vs. OLTP workloads.

🔧 **NOC Tip:** Always set `query_timeout` and `client_idle_timeout` in PgBouncer to prevent runaway queries from monopolizing the pool. A 30-second `query_timeout` protects against missing-index disasters.

## Connection Pooling Architecture Patterns

### Single PgBouncer per Database Host
The simplest pattern: one PgBouncer instance co-located with each PostgreSQL server. Applications connect to PgBouncer on port 6432 instead of PostgreSQL on 5432.

### Sidecar PgBouncer
Each application pod in Kubernetes runs a PgBouncer sidecar container. This moves the pooling closer to the application and avoids a central bottleneck, but means more PgBouncer instances to manage.

### Centralized PgBouncer Cluster
Dedicated PgBouncer instances behind a load balancer. Applications connect to a single DNS name. This centralizes management but introduces another network hop and potential single point of failure.

For Telnyx-scale operations, the sidecar pattern is increasingly common in Kubernetes environments — each pod manages its own connection pool, and the total pool across all pods is sized to stay within PostgreSQL's connection limit.

## When Connection Pooling Goes Wrong

The most dangerous failure mode is **pool exhaustion**: all server connections are in use, and new requests queue indefinitely. This cascades — upstream services time out waiting for database responses, health checks fail, orchestrators restart pods, restarted pods try to reconnect, and the pool remains saturated.

Prevention:
- **Set aggressive timeouts.** `query_timeout`, `server_idle_timeout`, `client_idle_timeout`
- **Monitor queue depth.** Alert when `cl_waiting > 0` for more than 30 seconds
- **Separate pools.** Critical real-time paths (call routing) should have dedicated pools separate from analytics/reporting queries
- **Size conservatively.** `default_pool_size` should leave headroom; PostgreSQL's `max_connections` should exceed total pool connections across all PgBouncers

🔧 **NOC Tip:** During incidents, `SHOW POOLS;` in PgBouncer is your fastest diagnostic. If `cl_waiting` is high, the database is the bottleneck. If pools are underutilized but apps are slow, look elsewhere in the stack.

## Beyond PgBouncer: Alternatives

- **Pgpool-II**: More features (load balancing, query caching) but heavier and more complex
- **Built-in pooling** (Odyssey, Supavisor): Newer alternatives with multi-threaded architectures
- **Application-level pooling**: Libraries like HikariCP (Java), SQLAlchemy pool (Python) — but these don't solve the cross-service aggregation problem

For most telecom NOC environments, PgBouncer in transaction mode remains the right choice: battle-tested, lightweight, and well-understood.

---

**Key Takeaways:**
1. Each PostgreSQL connection consumes ~5-10 MB RAM; uncontrolled connections exhaust server memory
2. PgBouncer multiplexes many application connections across few database connections
3. Transaction pooling mode offers the best efficiency-to-compatibility ratio for telecom workloads
4. Monitor `cl_waiting` (clients queuing) as the primary pool health indicator
5. Pool exhaustion cascades into application-wide failures — set timeouts and separate critical pools
6. `SHOW POOLS` is the fastest diagnostic command during database-related incidents

**Next: Lesson 152 — ClickHouse for Analytics — Columnar Storage Fundamentals**
