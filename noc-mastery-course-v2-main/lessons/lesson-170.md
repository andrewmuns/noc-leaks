# Lesson 170: Database Replication and Failover for NOC
**Module 5 | Section 5.3 — Databases for NOC**
**⏱ ~7 min read | Prerequisites: Lessons 144, 148**

---

## Why Replication Matters for Telecom

A telecom platform's database is its brain. Customer configurations, routing rules, number assignments, billing records — all live in the database. If the database goes down and there's no replica, the entire platform goes dark. No calls route. No customers can be looked up. No CDRs get written.

Replication creates copies of your database on other servers. At its most basic, replication provides **high availability** (if the primary fails, a replica takes over) and **read scaling** (spread read queries across multiple servers). For NOC engineers, understanding replication is essential because replication failures and failover events are some of the most impactful incidents you'll handle.

## PostgreSQL Streaming Replication

PostgreSQL's built-in replication works through the **Write-Ahead Log (WAL)**. Every change to the database is first written to the WAL — a sequential log of all modifications. In streaming replication, the primary server continuously streams WAL records to replica servers, which replay them to maintain an identical copy.

```
Primary (read-write)
    │
    ├── WAL Stream ──→ Replica 1 (read-only)
    │
    └── WAL Stream ──→ Replica 2 (read-only)
```

The process:
1. Client writes to primary → WAL record created
2. WAL record written to local WAL file
3. WAL sender process streams the record to replicas
4. Replica WAL receiver writes to local WAL
5. Replica recovery process replays WAL to update data

Replicas are read-only — they can serve SELECT queries but cannot accept writes. This is the architectural pattern that enables read scaling.

## Synchronous vs. Asynchronous Replication

This is the critical trade-off every NOC engineer must understand.

### Asynchronous Replication (Default)
The primary commits a transaction and acknowledges to the client immediately, without waiting for replicas to confirm they received the WAL. This is fast but introduces a window where the primary has data that replicas don't yet have.

**Risk:** If the primary crashes during this window, data written since the last WAL record received by replicas is lost. This window is typically milliseconds to seconds — called **replication lag**.

### Synchronous Replication
The primary waits for at least one replica to confirm it has written the WAL record to disk before acknowledging the transaction to the client. Zero data loss on failover, but every write incurs the round-trip latency to the replica.

```ini
# postgresql.conf on primary
synchronous_standby_names = 'replica1'
synchronous_commit = on  # wait for replica confirmation
```

**Risk:** If the synchronous replica goes down, the primary either blocks (waiting forever) or you must reconfigure to fall back to async. This can cause a **primary stall** — writes stop completely.

🔧 **NOC Tip:** Monitor synchronous replica health obsessively. A down synchronous replica can stall the primary and take the entire platform offline. Many architectures use `synchronous_commit = remote_apply` with a priority list so another replica takes over the synchronous role automatically.

## Monitoring Replication Lag

Replication lag is the delay between a write on the primary and its appearance on the replica. It's the most critical replication metric.

```sql
-- On the primary: check replica status
SELECT client_addr, state, sent_lsn, write_lsn, flush_lsn, replay_lsn,
       pg_wal_lsn_diff(sent_lsn, replay_lsn) AS replay_lag_bytes
FROM pg_stat_replication;

-- On the replica: check how far behind
SELECT now() - pg_last_xact_replay_timestamp() AS replication_delay;
```

| Lag | Status | Action |
|-----|--------|--------|
| < 1 second | Healthy | Normal operation |
| 1-10 seconds | Warning | Investigate — heavy write load or network issue |
| > 10 seconds | Critical | Replica may serve severely stale data |
| NULL / not replicating | Down | Replica disconnected — immediate investigation |

### A Troubleshooting Scenario

**Alert:** Replication lag on replica-2 exceeding 30 seconds and growing.

**Investigation:**
1. Check primary write load: `SELECT * FROM pg_stat_activity WHERE state = 'active';` — is there a massive bulk operation?
2. Check network between primary and replica: `ping`, `mtr` — is there packet loss?
3. Check replica resources: Is disk I/O saturated? Is CPU maxed from replay?
4. Check for long-running queries on replica: `SELECT * FROM pg_stat_activity;` — long analytical queries can block WAL replay if `hot_standby_feedback = on`

**Root cause:** A data migration job was writing millions of rows, generating WAL faster than the replica could replay. The replica's disk I/O was the bottleneck.

**Fix:** Throttle the migration job, or accept temporary lag and monitor for convergence after the migration completes.

## Automated Failover: Patroni

Manual failover requires a human to detect the failure, decide to promote a replica, and execute the promotion. At 3 AM, this means pages, wake-ups, and delayed recovery.

**Patroni** automates this process using a distributed consensus store (etcd or Consul) to coordinate:

1. Patroni agents run on each PostgreSQL server
2. The leader (primary) holds a lock in etcd
3. If the leader fails to renew its lock (crash, network partition), replicas detect the loss
4. Patroni initiates leader election — the replica with the least lag wins
5. The winner promotes itself to primary
6. Other replicas reconfigure to follow the new primary
7. Applications discover the new primary via DNS or Consul

```
etcd cluster (consensus)
    ↑           ↑           ↑
Patroni-1    Patroni-2    Patroni-3
(primary)    (replica)    (replica)
```

### Split-Brain Prevention

The most dangerous failure mode in database replication is **split-brain**: two nodes both think they're the primary and accept writes. The data diverges irreversibly.

Patroni prevents split-brain through:
- **Consensus-based locking**: Only the node holding the etcd lock is primary
- **Fencing**: The old primary is shut down or fenced before the new primary is promoted
- **Watchdog**: A Linux watchdog timer that reboots the server if Patroni becomes unresponsive

🔧 **NOC Tip:** After any failover event — automated or manual — verify there is exactly ONE primary accepting writes. Run `SELECT pg_is_in_recovery();` on all nodes. The primary returns `false`; replicas return `true`. Two nodes returning `false` means split-brain — escalate immediately.

## Failover Impact on Applications

Even with automated failover, applications experience a disruption:

1. **Detection time**: 10-30 seconds for Patroni to detect primary failure
2. **Election time**: 5-10 seconds for a new primary to be elected
3. **DNS propagation**: Seconds to minutes depending on TTL
4. **Connection re-establishment**: Applications must reconnect

Total expected downtime: 15-60 seconds for well-tuned Patroni setups.

Applications must handle this gracefully:
- **Connection retry logic** — reconnect after failures
- **Idempotent operations** — safely retry writes that might have partially committed
- **Read-only fallback** — serve reads from replicas while primary is unavailable

## Database Failover Runbook

Every NOC should have this documented:

1. **Verify the failure**: Is the primary truly down, or is it a monitoring false positive?
2. **Check Patroni status**: `patronictl list` — shows current cluster state
3. **If automated failover succeeded**: Verify new primary is healthy, check replication to remaining replicas
4. **If automated failover failed**: Check etcd health, check Patroni logs, consider manual promotion
5. **Post-failover**: Monitor replication lag on new replicas, check for split-brain, notify stakeholders
6. **Recovery**: Rebuild the old primary as a new replica

```bash
# Check Patroni cluster status
patronictl -c /etc/patroni/patroni.yml list

# Manual failover if needed
patronictl -c /etc/patroni/patroni.yml failover

# Reinitialize a failed node as replica
patronictl -c /etc/patroni/patroni.yml reinit <cluster-name> <node-name>
```

---

**Key Takeaways:**
1. PostgreSQL streaming replication works by continuously shipping WAL records from primary to replicas
2. Asynchronous replication is faster but risks data loss on failover; synchronous replication ensures zero data loss but can stall writes
3. Replication lag is the #1 metric to monitor — growing lag indicates a problem that will worsen
4. Patroni automates failover using etcd consensus, achieving 15-60 second recovery times
5. Split-brain (two primaries) is the worst-case scenario — always verify exactly one primary after failover events
6. After every failover, run the full verification checklist: one primary, replicas connected, lag converging

**Next: Lesson 155 — Database Backup and Recovery Procedures**
