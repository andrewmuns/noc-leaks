# Lesson 160: Replication Strategies - Single-Leader, Multi-Leader, Leaderless
**Module 5 | Section 5.2 - Distributed Systems**
**⏱ ~7 min read | Prerequisites: Lesson 141**

---

## Why Replication Exists

Data replication serves multiple purposes:
- **High availability**: If one server fails, replicas continue serving requests
- **Fault tolerance**: Even if a datacenter fails, data survives elsewhere
- **Read scaling**: Distribute read traffic across replicas
- **Geographic distribution**: Place data near users for lower latency
- **Backup**: Replicas serve as live backups

But replication introduces complexity: how do you keep replicas consistent when writes happen? Different strategies make different trade-offs.

## Single-Leader Replication

### How It Works
One node designated as the **leader** (primary, master) handles all writes. All **replicas** (followers, secondaries) copy data from the leader.

**Write path:**
1. Client sends write to leader
2. Leader writes to its local storage
3. Leader replicates to replicas
4. Leader acknowledges write to client

**Read path:**
1. Client sends read to leader OR replica (configurable)
2. Node responds with data

### Synchronous vs. Asynchronous Replication

**Synchronous:**
- Leader waits for replica acknowledgment before responding to client
- Guarantees data is on at least two nodes
- Higher latency (especially across datacenters)
- If replica is slow/dead, writes stall

**Asynchronous:**
- Leader responds immediately after local write
- Replica receives data after acknowledgment
- Lower latency
- Brief window where replica is stale

Most production systems use async by default with optional sync for critical writes.

### PostgreSQL Streaming Replication

PostgreSQL uses single-leader replication (physical or logical):

1. Primary writes changes to Write-Ahead Log (WAL)
2. WAL records stream to standby servers
3. Standbys apply WAL changes to their copy
4. If primary fails, promote standby to primary

**Hosting at Telnyx:**
- Primary in Site A handles writes
- Standby in Site B receives WAL stream
- If Site A fails, failover to Site B
- Patroni automates failover using Consul (Lesson 154)

### Pros and Cons

**Pros:**
- Simple to understand
- No write conflicts (single leader)
- Strong consistency options (synchronous replication)
- Mature, well-understood

**Cons:**
- Single point of failure for writes (if leader fails, no writes)
- Write scaling limited to one node
- Failover complexity (promotion, catching up replicas)
- Replication lag during heavy writes

🔧 **NOC Tip:** Monitor replication lag on single-leader systems: `SELECT EXTRACT(EPOCH FROM (now() - pg_last_xact_replay_timestamp())) AS lag_seconds;` on PostgreSQL. Lag >30 seconds during normal operation indicates network issues or replica overload.

## Multi-Leader Replication

### How It Works
Multiple nodes accept writes. Each node replicates to others. Writes to any leader propagate to all others.

**Use cases:**
- Multi-datacenter where each datacenter takes local writes
- Offline-first applications (mobile apps, edge devices)
- Real-time collaboration tools

### The Conflict Problem

What happens when:
1. Client A writes `x=1` to Leader A
2. Client B writes `x=2` to Leader B
3. Leaders replicate to each other simultaneously

Now what is x? This is a **write conflict**.

**Conflict resolution strategies:**

1. **Last-Write-Wins (LWW)**: Timestamps decide. Later timestamp wins, earlier is discarded.
   - Simple but can lose data ("earlier" write lost forever)
   - Clock skew can cause wrong winner

2. **Merge function**: Combine values somehow. Set union, number sum, etc.
   - For a shopping cart: both items appear
   - For a counter: increment both times

3. **Manual resolution**: Flag conflicts, human decides.
   - Used when automatic resolution is impossible
   - Pushes burden to application

4. **Vector clocks**: Track causality, not just time.
   - Can tell if writes are concurrent (both need to be kept)
   - Or if one happened-before another (clear ordering)
   - More complex but preserves more semantics

### When To Use Multi-Leader

- **Multi-datacenter writes**: Users write to nearest datacenter, replicate to others. Lower latency than cross-country writes to single leader.
- **Offline operation**: Devices write locally, sync when online. Airline reservation systems, mobile apps.
- **Real-time collaboration**: Multiple users editing same document simultaneously.

**Don't use multi-leader unless you have a specific use case.** Single-leader is simpler and sufficient for most applications.

## Leaderless Replication (Dynamo-Style)

### How It Works
Pioneered by Amazon Dynamo, used by Cassandra, Riak, Voldemort:

**No leader.** Any replica can accept writes. Client writes to multiple replicas. Client reads from multiple replicas.

**Quorum mechanism:**
- Write sent to N replicas
- Wait for W acknowledgments (write quorum)
- Read sent to R replicas
- Wait for R responses, take most recent version

**Parameters:**
- N = total replicas (typically 3)
- W = write replicas to wait for
- R = read replicas to request

**Quorum condition for strong reads:**
W + R > N ensures read sees at least one replica with the write

**Examples:**
- N=3, W=2, R=2: Almost always sees latest write
- N=3, W=1, R=1: Fastest, may see stale data
- N=3, W=3, R=1: Writes to all, highly consistent

### Handling Unavailable Replicas

If a replica is down during write:
- Write proceeds if it reaches W replicas
- Hinted handoff: temporarily store write on another node to forward later
- Read repair: when reading, if replicas disagree, update stale ones
- Anti-entropy: background process compares replicas and fixes differences

### Eventual Consistency

Leaderless systems are typically eventually consistent (Lesson 141). If you read immediately after write, you might not see the write (if you hit a replica that didn't receive it yet).

Use W + R > N to increase consistency at the cost of latency and availability.

🔧 **NOC Tip:** When using Cassandra or similar, understand your consistency levels. Using `ONE` for reads during incident investigation might return stale data. Use `QUORUM` for troubleshooting to see the most recent values. Default application to `LOCAL_QUORUM` for balance of speed and consistency.

## Comparing the Three Approaches

| Aspect | Single-Leader | Multi-Leader | Leaderless |
|--------|--------------|--------------|------------|
| Write scaling | Single node | Multiple nodes | Multiple nodes |
| Read scaling | Many replicas | Many replicas | Many replicas |
| Conflict handling | None | Required (complex) | Not applicable |
| Failover | Complex | Not needed | Not needed |
| Read consistency | Strong | Eventual | Configurable (quorum) |
| Complexity | Low | High | Medium |
| Use cases | Most databases | Multi-DC, offline | High write throughput |

## Real-World Scenario: The Wrong Replication Choice

A team chooses multi-leader replication for a customer configuration database "for high availability" and "in case of datacenter failure."

**Problem:** Customer configuration is updated rarely. Conflict resolution wasn't carefully designed.

**Failure:** During a partition, two operators in different datacenters update the same customer's route. Both changes are valid but incompatible decisions. When partition heals, conflicting values exist. The merge function doesn't know how to reconcile "route via Carrier A" vs. "route via Carrier B" - they're not mergeable.

**Result:** Incorrect routing for customer. Calls go wrong way. Confusion, incident, rollback to single-leader.

**Lesson:** Multi-leader adds complexity that should only be used when needed. For a config database that's read-heavy and updated rarely, single-leader with replicas in multiple datacenters is simpler and safer.

## Choosing a Strategy

**Use single-leader when:**
- Read-heavy workloads
- Strong consistency required
- 
Most OLTP databases fit here. PostgreSQL, MySQL, Redis, etcd all built around single-leader.

**Use multi-leader when:**
- Must write from multiple datacenters (latency)
- Offline-first requirement
- Write conflicts are rare or automatically resolvable

**Use leaderless when:**
- Very high write throughput needed
- Can accept eventual consistency
- Geographic distribution critical
- Netflix, Cassandra, DynamoDB use cases

---

**Key Takeaways:**
1. Single-leader replication is simplest: one node handles writes, replicas copy. Used by PostgreSQL, MySQL, etcd.
2. Multi-leader allows writes from multiple nodes but requires conflict resolution. Complex, use only when needed.
3. Leaderless replication (Cassandra-style) uses quorum reads/writes. No failover needed but harder to reason about consistency.
4. W + R > N quorum condition ensures reads see writes in leaderless systems
5. Monitor replication lag in single-leader systems - high lag indicates network issues or replica overload
6. Default to single-leader unless your specific use case demands multi-leader complexity

**Next: Lesson 145 - Service Discovery and Health Checking**
