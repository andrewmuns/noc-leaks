# Lesson 159: Distributed Locking and Leader Election in Practice
**Module 5 | Section 5.2 - Distributed Systems**
**⏱ ~7 min read | Prerequisites: Lesson 142**

---

## Why Distributed Locks Are Needed

In distributed systems, multiple services often need to coordinate access to shared resources. Consider these scenarios:

- **Scheduled jobs**: Multiple instances of a cron service run, but only one should execute a specific job
- **Cache warming**: Only one worker should warm a cache entry, others should wait
- **Billing aggregation**: Only one process should aggregate billing for a specific hour
- **Database migrations**: Only one instance should run migrations at startup
- **Message processing**: Only one consumer should process a specific message

Without coordination, you'd get duplicate operations. Distributed locks provide that coordination.

## What Is a Distributed Lock

A distributed lock is a coordination primitive that ensures only one process holds the lock at a time, regardless of which node the process runs on.

**Basic semantics:**
- **Acquire**: Try to get the lock. Returns success/failure.
- **Hold**: While holding the lock, do the protected work.
- **Release**: Release the lock when done.

Only if acquire succeeds can the process proceed.

## Consul Sessions and Locks

Consul provides distributed locking through sessions:

### Sessions
A session represents a long-lived contract. When creating a session:
- Session has a TTL (time-to-live): if not renewed, it expires
- Session can be associated with health checks
- If health checks fail, session is invalidated
- Session can be bound to a lock on a key-value pair

### Lock Acquisition

```
# Try to acquire lock on 'jobs/billing-aggregation'
consul kv put -acquire -session=<session-id> jobs/billing-aggregation "worker-42"

# If returns true: lock acquired. If returns false: lock held by someone else.
```

The acquire succeeds only if no other session holds a lock on that key. It's atomic.

### Lock Holding
While holding the lock:
- The worker must periodically renew its session (heartbeat)
- If the worker crashes, session TTL expires, lock releases automatically
- If the node fails health check, session invalidated, lock releases

### Lock Release
```
# Explicit release
consul kv put -release -session=<session-id> jobs/billing-aggregation

# Or delete the key
consul kv delete jobs/billing-aggregation
```

Even if release fails to execute (process crash), TTL expiration eventually releases the lock.

🔧 **NOC Tip:** Monitor Consul session counts and lock contention. If locks are held for much longer than expected work duration, investigate - the holder might have crashed without releasing properly. Check if the session is still active with `consul session info <session-id>`.

## Lock TTL and Fencing Tokens

### The TTL Problem

A common anti-pattern: acquire lock, do work, release lock. But what if the worker crashes between acquire and release? The lock is held forever (or until manual intervention).

### TTL-Based Locks

The solution: locks tied to sessions with TTL. If the holder dies:
- Session TTL expires (no renewals happen)
- Session destroyed
- Lock released automatically
- Another worker can acquire

**Trade-off**: TTL must balance:
- Long enough for work to complete
- Short enough that crashed worker releases promptly
- If work takes longer than TTL, session expires mid-work

### Fencing Tokens

Even with TTL, a subtle problem remains: lock delay.

**Scenario:**
1. Worker A holds lock, session TTL is 30 seconds
2. Worker A gets network partitioned, session expires at 30 seconds
3. Worker B acquires lock at 31 seconds, starts work
4. Network heals, Worker A's partition ends at 35 seconds
5. Worker A thinks it still holds lock (didn't get session expiry notification), continues work
6. Workers A and B both think they hold the lock

**Fencing token solution:**
- Each lock acquisition gets a monotonically increasing token (123, 124, 125...)
- Protected resource validates the token
- If request has old token, resource rejects it

Example: Billing service requires token with aggregation request. Worker A has old token, gets rejected. Worker B has new token, succeeds.

## Redis- vs. Consul-Based Locks

### Redis Redlock
Redis provides `SET key value NX EX <seconds>` for single-node locking.

**Redlock algorithm**: For multiple Redis instances:
1. Get current time in milliseconds
2. Try to acquire lock on each instance with short timeout
3. Quorum exists if locked on majority
4. Valid if total time elapsed < lock TTL

**Redlock problems:**
- Clock skew affects validity
- If Redis master fails, lock state unclear
- Complex implementation, hard to get right
- Martin Kleppmann's analysis showed subtle issues

### Consul Locks
Based on Raft consensus (Lesson 142):
- No single point of failure (Consul cluster)
- TTL-based cleanup of dead holders
- Health check binding for holder monitoring
- Built-in fencing token support (session ID)

**Consul is generally preferred for production distributed locking** due to the underlying consensus reliability.

## Leader Election with Locks

Distributed locking enables leader election:

```
All candidates try to acquire lock on "leader/my-service"

Winner continues as leader
Losers watch lock, wait for it to release

When leader crashes:
- Session TTL expires
- Lock released
- Watchers notified
- New election, new leader
```

This is exactly how Consul-based leader election works.

## Real-World Scenario: The Duplicate Processing

A billing aggregation job runs every hour. 100 instances of the billing service run across the cluster. Without coordination, all 100 try to aggregate the previous hour's calls - duplicate charging, race conditions, database conflicts.

**With Consul locks:**

```python
import consul

client = consul.Consul()

while True:
    # Try to acquire lock
    session = client.session.create(ttl="60s")
    acquired = client.kv.put("locks/billing-aggregation", "worker-42",
                             acquire=session)

    if acquired:
        try:
            # Only this worker does aggregation
            aggregate_billing()
        finally:
            # Release lock
            client.kv.delete("locks/billing-aggregation", release=session)
            client.session.delete(session)
    else:
        # Lock held by another worker, sleep and retry
        time.sleep(30)
```

Result: Exactly one worker processes billing each hour. If it crashes, another takes over after 60 seconds.

🔧 **NOC Tip:** If you see duplicate billing records, notification emails sent twice, or cron jobs running multiple times simultaneously, you have a distributed locking problem. Check if all instances are trying to acquire the same lock, or if lock TTL is too long allowing overlap.

## Monitoring Distributed Locks

### Key Metrics

```promql
# Lock acquisition rate
rate(consul_lock_acquisitions_total[5m])

# Lock contention (failed acquisitions)
rate(consul_lock_acquisition_failures_total[5m])

# Average lock hold time
histogram_quantile(0.99, rate(consul_lock_hold_duration_bucket[5m]))

# Sessions by expiration
consul_session_count
```

### Lock Contention Alert

```promql
# High lock contention - many workers waiting for the same lock
rate(consul_lock_acquisition_failures_total[5m]) / rate(consul_lock_acquisitions_total[5m]) > 0.9
```

High contention means:
- Lock duration is too long compared to work time
- Too many workers for the workload
- Lock not being released properly

## Troubleshooting Lock Issues

### Symptom: Jobs not running
- Check if lock holder is healthy: `consul session list`
- Check if holder's session is being renewed
- Check if lock actually exists: `consul kv get locks/job-name`

### Symptom: Duplicate job execution
- Check if lock TTL is shorter than job duration
- Check if all instances use the same lock key
- Check if session isn't properly associated with lock

### Symptom: Lock not releasing
- Check for explicit release in code
- Check for proper exception handling (lock released in finally block)
- Shorten TTL as safety net for crashed holders

---

**Key Takeaways:**
1. Distributed locks coordinate access to shared resources across multiple nodes
2. Consul provides TTL-based locks through sessions - dead holders release locks automatically
3. Fencing tokens prevent race conditions when lock holder crashes and recovers
4. Consul's Raft-based locks are more reliable than Redis Redlock for production
5. Lock contention metrics reveal when locks aren't properly tuned
6. Always release locks in finally blocks and use short TTLs as safety nets

**Next: Lesson 144 - Replication Strategies: Single-Leader, Multi-Leader, Leaderless**
