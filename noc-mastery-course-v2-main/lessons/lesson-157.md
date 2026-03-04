# Lesson 157: Eventual Consistency - Living with Stale Data
**Module 5 | Section 5.2 - Distributed Systems**
**⏱ ~7 min read | Prerequisites: Lesson 140**

---

## What Eventual Consistency Actually Means

Eventual consistency is the guarantee that if no new updates are made to a given data item, eventually all accesses to that item will return the last updated value. In plain English: data might be temporarily inconsistent across nodes, but given enough time without changes, everyone agrees.

For NOC engineers, this means that after you update something, reads on other nodes might not immediately reflect your change. This can be confusing during troubleshooting when you're looking at what appears to be wrong data.

## The Update Propagation Problem

When you write data in a distributed system, here's what happens:

1. **Write accepted**: The primary/leader/receiving node accepts the write and acknowledges success
2. **Replication begins**: The node begins propagating the change to replicas
3. **Propagation delay**: Network latency, queue depth, and processing delays mean replicas don't receive the change instantly
4. **Convergence window**: Time between write acknowledgment and all replicas having the data

During the convergence window, different nodes have different views:
- The primary node: has latest data
- Up-to-date replicas: have latest data
- Slow replicas: have stale data

## Read Your Own Writes

A critical concept for debugging: after you write, can you read what you just wrote?

**Strong consistency**: Yes, guaranteed. The write doesn't acknowledge until replicas have it. Read goes to a replica with the data.

**Eventual consistency**: Maybe. If you read from a different node than you wrote to, you might get stale data.

**Practical example:**
```
write(customer_config) to Node A
read(customer_config) from Node B  # Might return old value!
```

This is why NOC engineers experience this:
1. Update a customer's routing rule via API
2. Query the configuration to verify
3. See old configuration
4. "The update isn't working!"
5. Wait 30 seconds
6. Query again
7. See new configuration
8. "Oh, it was eventual consistency"

🔧 **NOC Tip:** After updating configuration data, add a small delay or retry with backoff before reading to verify. In consistently AP systems (Cassandra, DynamoDB), wait 1-5 seconds. In strongly consistent systems, read from the same node/session you wrote to.

## Consistency Levels in Practice

Databases let you choose consistency per-operation:

### Cassandra Consistency Levels
- **ONE**: Write/read from one replica. Fastest. Might be stale.
- **QUORUM**: Write/read from majority of replicas. Stronger consistency.
- **ALL**: Wait for all replicas. Slowest. Most consistent.

**Trade-off table:**

| Consistency | Latency | Availability | Use Case |
|-------------|---------|--------------|----------|
| ONE | Fastest | Highest | Analytics, metrics |
| QUORUM | Medium | Medium | Most applications |
| ALL | Slowest | Lowest | Financial, critical |

### DynamoDB Consistency
- **Eventually consistent reads**: Might return stale data (default, cheaper)
- **Strongly consistent reads**: Returns most recent data (slower, more expensive)

### Choose Based on Need

```
Reading Call Detail Records for billing:  Use QUORUM/strong
Reading metrics for a dashboard:          Use ONE/eventual
Writing customer routing config:          Use QUORUM
Writing a telephone number assignment:    Use ALL
```

## The Convergence Window

How long until all replicas agree? Depends on:

### Network Latency
Cross-datacenter replication takes 10-100ms. Cross-continent takes 100-300ms.

### Database Load
Under heavy write load, replication queues form. Convergence might take seconds or minutes.

### Replication Topology
- **Single-leader**: All writes to leader, async to replicas. 95% of systems.
- **Multi-leader**: Writes to multiple nodes, conflict resolution. More complex.
- **Leaderless**: Write to multiple, read from multiple, quorum decides. Cassandra-style.

### Configuration
- **Synchronous**: Write waits for replicas. Longer convergence (zero for reads).
- **Asynchronous**: Write doesn't wait. Reads might be stale. Shorter write latency.

🔧 **NOC Tip:** Monitor replication lag metrics: `replication_lag_seconds`, `seconds_behind_master`. Alert when lag exceeds expected bounds. High lag indicates the system is struggling to keep up with writes - often a precursor to availability issues.

## Detecting Stale Data During Troubleshooting

### Symptoms of Reading Stale Data

- Configuration you just updated isn't reflected
- Values change between queries ("flapping")
- Query shows "version 5" when another query shows "version 4"
- Timestamps on data are older than expected
- Some instances work, others don't for the same configuration

### How to Verify

```bash
# Query multiple replicas directly
SELECT * FROM config WHERE key='routing_rules';  # on Node A
SELECT * FROM config WHERE key='routing_rules';  # on Node B
SELECT * FROM config WHERE key='routing_rules';  # on Node C

# If results differ, you're seeing eventual consistency in action

# For Cassandra - use consistency level
CONSISTENCY ALL;
SELECT * FROM config WHERE key='routing_rules';
# Forces read from all replicas, returns most recent
```

## Conflict Resolution

What happens if two different values are written during a partition and the partition heals?

### Last-Write-Wins (LWW)
The write with the latest timestamp is kept. Fast but might lose meaningful data if clocks are skewed.

### Vector Clocks
Track causality - which writes happened before others. Complex but preserves meaningful ordering.

### CRDTs (Conflict-free Replicated Data Types)
Data structures designed to merge automatically. Sets, counters, maps that can be reconciled without conflict.

### Manual Reconciliation
System flags the conflict and requires a human to choose. Used when conflicts can't be automatically resolved.

🔧 **NOC Tip:** If you see duplicate entries or "ghost" data after a partition heals, it might be unresolved conflict. Check system logs for conflict warnings. Some systems hide conflicts - they just pick a winner arbitrarily - which can lead to mysterious "configuration changes" that weren't made.

## Read-Your-Writes Consistency

A middle ground between strong and eventual consistency:

Guarantee that after a process writes value V, any subsequent reads by that same process will return V (or a version after V).

Only provides this guarantee to the writer's session, not globally.

**Implementation:**
- Answers from same replica you wrote to
- Session tokens that track write order
- Client-side caching of written values

This covers the most common pain point ("I set it, why don't I see it?") while allowing replicas to be eventually consistent for other readers.

## NOC Operational Guidance

### When Eventual Consistency Is Acceptable

- Call detail records (slight delay in CDR visibility is OK)
- Metrics and monitoring data (5-30 second delay is fine)
- User preferences (stale data for a few seconds doesn't hurt)
- Cached routing data (routes change rarely, eventual is fine)

### When It's Dangerous

- Call processing decisions (need current config)
- Billing calculations (must be accurate)
- Emergency failover configuration (can't be stale)
- Authentication/authorization data (security critical)

### Incident Response

If you suspect eventual consistency is causing symptoms:

1. **Check replication lag metrics** - how far behind are replicas?
2. **Force strong consistency** - use QUORUM or read from primary
3. **Wait and recheck** - verify if data converges after a few seconds
4. **Query specific replicas** - see which have which versions

Don't assume "the data is wrong" - assume "I'm seeing a replica that hasn't received the update yet."

## Real-World Scenario: The Ghost Configuration

An engineer updates a customer's outbound route from Carrier A to Carrier B. They verify via API: success, route updated.

Five minutes later, the customer reports calls still going via Carrier A.

**Investigation:**
- API query from engineer's terminal: shows Carrier B (query hit up-to-date replica)
- API query from customer's perspective: shows Carrier B (query hit same replica)
- Calls trace: actually routing via Carrier A (routing engine has stale cache)
- Routing engine query: shows Carrier A (cache hasn't refreshed yet)

**Problem:** Three layers of consistency - database layer (eventual), cache layer (TTL-based), application layer (in-memory). Each layer introduces delay.

**Fix:** Explicit cache invalidation after config update, shorter TTLs, or read-from-source when freshness matters.

**Lesson:** Eventual consistency plus caching plus multiple layers equals debugging complexity. Corroborate across layers when troubleshooting configuration.

🔧 **NOC Tip:** Always verify at the behavior layer, not just the data layer. If you've updated a route, actually place a test call to verify it took effect. Reading the configuration back isn't authoritative - the routing engine might have cached the old value.

---

**Key Takeaways:**
1. Eventual consistency means data converges but might be temporarily inconsistent between replicas
2. The convergence window depends on network latency, system load, and replication topology
3. After a write, reads on other nodes might return stale data - wait or read at stronger consistency
4. Monitor replication lag metrics - high lag indicates system struggling to replicate
5. Layer eventual consistency with caching exponentially increases debugging complexity
6. Verify configuration changes at the behavior layer (actual calls) not just the data layer

**Next: Lesson 142 - Consensus Algorithms: Raft and Paxos Simplified**
