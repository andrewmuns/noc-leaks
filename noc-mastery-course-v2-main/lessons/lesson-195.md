# Lesson 195: Capstone — Full Incident Simulation: Cascading Infrastructure Failure

**Module 6 | Section 6.4 — Capstone**
**⏱ ~10 min read | Prerequisites: All Previous**

---

## Scenario: 14:23 UTC — The Cascade Begins

### Alert 1: Storage Degraded

```
PagerDuty Alert: P2 — Degraded
Host: ceph-mon@telnyx.com
Time: 14:23 UTC

Alert: "Ceph cluster tnx-storage-prod-01 degraded
        PGs in undersized state: 47
        OSDs down: 2/24"
```

**Initial assessment:** Hardware failure in storage cluster. Ceph is self-healing, but recovery impacts performance.

### Alert 2: Billing Pipeline Lag

```
Time: 14:31 UTC
Alert: "billing-pipeline: CDR processing lag 15 minutes and growing"
Normal: <2 minutes lag
Current: 15 minutes
```

**Connection suspected:** Storage degradation affects CDR writes.

### Alert 3: Provisioning Slow

```
Time: 14:45 UTC
Alert: "provisioning-api: P95 latency 8s, normally 200ms"
```

**Pattern emerging:** Shared storage infrastructure affected.

### Alert 4: Customer Portal Unavailable

```
Time: 15:02 UTC
Alert: "CRITICAL: customer-portal timeout rate >50%"
```

**Cascade confirmed:** Multiple systems failing from shared dependency.

---

## Phase 1: Understanding the Cascade

### System Dependency Map

```
                    ┌──────────────────┐
                    │  Ceph Storage    │
                    │  tnx-storage-01  │
                    └────────┬─────────┘
                             │
         ┌───────────────────┼───────────────────┐
         │                   │                   │
         ↓                   ↓                   ↓
    ┌─────────┐        ┌─────────┐        ┌─────────────┐
    │Billing  │        │CDR      │        │Customer DB  │
    │Pipeline │        │Storage  │        │(Postgres)   │
    └────┬────┘        └────┬────┘        └──────┬──────┘
         │                  │                     │
         │                  │                     │
         ↓                  ↓                     ↓
    ┌────────────────────────────────────────────────────┐
    │           Provisioning API                         │
    │  (needs billing status + customer DB + CDR)        │
    └────────────────────────────────────────────────────┘
                              │
                              ↓
                    ┌──────────────────┐
                    │  Customer Portal │
                    └──────────────────┘
```

**Critical insight:** Billing pipeline lag → provisioning checks billing status → timeouts pile up → portal dies.

---

## Phase 2: Investigation

### Storage Deep Dive

```bash
# Ceph status
ceph -s

cluster:
  id:     3a4b2c1d-...
  health: HEALTH_WARN
  mons:   3 daemons (tnx-mon-01, -02, -03)
  mgr:    tnx-mgr-01(active)
  osd:    24 osds (22 up, 2 down)
  
data:
  pools:   6 pools, 512 pgs
  objects: 2.4M objects, 48 TiB
  usage:   92 TiB / 144 TiB (64%)
  
io:
  client:   12 MiB/s rd, 8 MiB/s wr
recovery: 156 MiB/s (osd.14 recovering)
```

```bash
# Check failed OSDs
ceph osd tree | grep down

# Output:
ID  CLASS  WEIGHT   TYPE NAME       STATUS  REWEIGHT
14  hdd    0.01459  osd.14          down    0
19  hdd    0.01459  osd.19          down    0
```

```bash
# Check smartctl on osd.14
ssh osd.14 "smartctl -a /dev/sda"

# Finding:
"Current_Pending_Sector: 247"  # Disk failing!
"Temperature_Celsius: 52"       # Within range
```

**Finding:** Two OSDs on different hosts failed simultaneously — different failure than initial diagnosis. Likely: batch of drives from same manufacturing lot.

### Billing Pipeline Analysis

```bash
# Check CDR queue depth
kubectl -n billing exec deploy/cdr-consumer -- rabbitmqctl list_queues | grep cdr

# Output:
cdr-ingress    180,000 messages    # Massive backlog
cdr-processed  2,400 msgs/sec out  # Throttled
```

```bash
# Why throttled?
kubectl -n billing logs deploy/cdr-processor | grep -i "slow"

# Finding:
"Slow database write detected: avg 450ms (target <50ms)"
"Ceph write latency p99: 2.3s"
```

**Root cause chain:**
1. OSD failures trigger Ceph recovery
2. Recovery I/O saturates storage network
3. CDR writes slow down (need Ceph)
4. Pipeline backs up
5. Provisioning API queries billing status → waits
6. API thread pool exhausted
7. Portal requests timeout

---

## Phase 3: Stopping the Cascade

### Priority 1: Restore Portal (Customer-Facing)

```bash
# Emergency: Bypass billing check for reads
kubectl -n provisioning set env deploy/provisioning-api \
  BILLING_CHECK=DISABLED \
  BILLING_TIMEOUT=5s

# Scale up API replicas
kubectl -n provisioning scale deploy/provisioning-api --replicas=20
```

**Result:** Portal recovers (15:18 UTC). Customers can access — they just see "billing pending" status.

### Priority 2: Isolate Storage Recovery

```bash
# Slow down Ceph recovery to reduce I/O impact
ceph osd pool set cdr-pool recovery_priority 1
ceph config set osd osd_recovery_max_active 1
ceph config set osd osd_recovery_sleep 0.5
```

**Result:** Recovery slows from 156 MiB/s to 45 MiB/s. Billing latency drops to ~200ms.

### Priority 3: Replace Failed OSDs

```bash
# Mark OSDs out for replacement (data will re-replicate)
ceph osd out 14
ceph osd out 19

# Replace physical drives (dc-ops ticket)
# After replacement:
ceph osd in 14
ceph osd in 19
```

### Priority 4: Drain Billing Backlog

```bash
# Scale up CDR processors temporarily
kubectl -n billing scale deploy/cdr-processor --replicas=50

# Monitor lag
watch kubectl -n billing exec deploy/cdr-monitor -- \
  "rabbitmqctl list_queues | grep cdr-ingress"

# Lag clears in 45 minutes
```

---

## Phase 4: Verification

### Recovery Timeline

| Time | Event | Metric |
|------|-------|--------|
| 14:23 | Ceph degraded | 2 OSDs down |
| 14:31 | Billing lag 15min | 180K backlog |
| 14:45 | Provisioning slow | P95 8s |
| 15:02 | Portal down | 50% timeout |
| 15:18 | Mitigation applied | Portal recovering |
| 15:25 | Billing latency normal | 200ms |
| 16:08 | CDR backlog cleared | 0 messages |
| 16:30 | OSDs replaced | Ceph HEALTH_OK |
| 17:00 | All systems normal | Full recovery |

---

## Post-Mortem: Cascading Failure Analysis

### Why It Cascaded

| System | Dependency | Failure Mode |
|--------|------------|--------------|
| Billing | Ceph (CDR storage) | Write latency |
| Provisioning | Billing (status check) | Sync call blocking |
| Portal | Provisioning (all data) | Timeout cascade |

**Design flaw:** Synchronous coupling. Provisioning waited for billing.

### Circuit Breakers Missing

```python
# What existed (BAD)
def get_billing_status(customer_id):
    response = requests.get(f"{billing_api}/status/{customer_id}")
    return response.json()  # Blocks forever if billing down

# What should exist (GOOD)
@circuit_breaker(threshold=5, timeout=1)
def get_billing_status(customer_id):
    try:
        response = requests.get(f"{billing_api}/status/{customer_id}", timeout=1)
        return response.json()
    except Timeout:
        return {"status": "UNKNOWN", "billable": True}  # Graceful degrade
```

### Action Items

| Priority | Action | Owner | Timeline |
|----------|--------|-------|----------|
| P0 | Add circuit breakers to provisioning→billing | Platform | +2 days |
| P0 | Add async billing status (cache + update) | Billing | +1 week |
| P1 | Ceph recovery rate limiting policies | Storage | +2 weeks |
| P1 | Billing pipeline SLO: 5 min max lag | SRE | +1 week |
| P2 | Separate critical vs non-critical storage pools | Storage | +1 month |
| P2 | Drive firmware batch tracking | DC Ops | +2 weeks |

---

## Key Lessons

### Cascade Prevention Patterns

1. **Circuit breakers** — Fail fast, don't block forever
2. **Bulkheads** — Isolate critical paths from dependency failures
3. **Timeouts everywhere** — Never wait indefinitely
4. **Graceful degradation** — Partial service beats total outage
5. **Async where possible** — Don't make users wait for non-critical checks

### This Incident Demonstrated

- **Storage is a critical single point of failure** — impacts everything
- **Recovery can hurt** — Ceph healing caused more damage than initial failure
- **Latency kills** — not just errors, slowness propagates
- **Thread pools exhaust** — one slow dependency → cascading timeouts
- **Customer impact matters most** — prioritize customer-facing recovery

---

## Key Takeaways

1. **Cascading failures start small** — 2 failed disks shouldn't take down the portal
2. **Synchronous dependencies are dangerous** — async + circuit breakers prevent cascades
3. **Recovery can be worse than the failure** — rate-limit healing traffic
4. **Monitor queue depths** — backlog is often the first sign of trouble
5. **Graceful degradation** — partial service with "unknown" status beats total outage
6. **Fix the cascade, then fix the root cause** — customer-facing recovery first

---

**Next: Lesson 180 — Course Completion — Your NOC Engineering Toolkit**
