# Lesson 96: Storage — Monitoring Storage Health
**Module 2 | Section 2.12 — Storage/AI**
**⏱ ~5min read | Prerequisites: Lesson 85**
---

## Introduction

Storage is one of those systems that works silently for months and then fails catastrophically at 3 AM. Disks degrade slowly, RAID arrays lose redundancy without anyone noticing, and storage clusters can fill up in hours during a bulk ingestion. As a NOC engineer, your job is to catch these problems early — before a customer loses data or an application grinds to a halt.

This lesson covers the metrics, tools, and alert patterns you need to monitor storage health at Telnyx.

---

## The Four Core Storage Metrics

### 1. IOPS (Input/Output Operations Per Second)

IOPS measures how many read/write operations a storage device or system handles per second. Different workloads have different IOPS profiles:

| Workload | Typical IOPS Pattern |
|----------|---------------------|
| Call recordings (write) | Sequential writes, moderate IOPS |
| Database (PostgreSQL) | Random reads/writes, high IOPS |
| Object storage metadata | Random reads, very high IOPS |
| AI model loading | Sequential reads, burst IOPS |

```promql
# Prometheus query: IOPS per disk
rate(node_disk_reads_completed_total[5m])
rate(node_disk_writes_completed_total[5m])
```

### 2. Throughput (MB/s)

Throughput measures data volume per second. High IOPS with low throughput means lots of tiny operations (metadata-heavy). Low IOPS with high throughput means large sequential operations (streaming, backups).

```promql
# Throughput in bytes per second
rate(node_disk_read_bytes_total[5m])
rate(node_disk_written_bytes_total[5m])
```

### 3. Latency

Storage latency is the time between issuing an I/O request and receiving the response. This is the metric most directly felt by applications.

| Device Type | Expected Latency |
|-------------|-----------------|
| NVMe SSD | 0.1–0.5 ms |
| SATA SSD | 0.5–2 ms |
| HDD (7200 RPM) | 5–15 ms |
| Degraded RAID | 20–100+ ms |

```promql
# Average I/O latency
rate(node_disk_read_time_seconds_total[5m]) / rate(node_disk_reads_completed_total[5m])
```

🔧 **NOC Tip:** When storage latency suddenly doubles or triples, check in this order: (1) Is a disk failing? (2) Is the I/O queue full? (3) Is there a RAID rebuild in progress? (4) Is the storage cluster rebalancing? Any of these will increase latency.

### 4. Capacity

Running out of storage space causes cascading failures — databases crash, writes fail, logs stop, and services halt.

```promql
# Disk space usage percentage
(1 - node_filesystem_avail_bytes / node_filesystem_size_bytes) * 100

# Alert: disk over 85% full
(1 - node_filesystem_avail_bytes{mountpoint="/"} / node_filesystem_size_bytes{mountpoint="/"}) * 100 > 85
```

🔧 **NOC Tip:** At Telnyx, the **85% threshold** triggers a warning, and **93%** triggers a critical alert. For Ceph/storage clusters, capacity alerts are even more important: Ceph becomes read-only at 95% full (`nearfull`) and stops entirely at 97% (`full`). Never let a Ceph cluster exceed 85% — at that point, you need to add capacity urgently.

---

## Monitoring Disk Health with SMART

**SMART** (Self-Monitoring, Analysis, and Reporting Technology) is built into every HDD and SSD. It tracks internal health metrics that predict failure.

### Key SMART Attributes

| Attribute | What It Means | Concern Level |
|-----------|--------------|---------------|
| Reallocated Sector Count | Bad sectors remapped to spares | Rising = disk dying |
| Current Pending Sector Count | Sectors waiting to be remapped | Any value > 0 is concerning |
| Uncorrectable Sector Count | Sectors that couldn't be read | Critical — data loss risk |
| Wear Leveling Count (SSD) | SSD cell wear percentage | Below 10% remaining = replace |
| Temperature | Drive temperature | > 55°C for HDDs is too hot |
| Power-On Hours | Total hours of operation | Context for other metrics |

### Checking SMART Data

```bash
# Full SMART report
smartctl -a /dev/sda

# Quick health check
smartctl -H /dev/sda

# SMART attributes table
smartctl -A /dev/sda

# Example output showing a failing disk:
# ID# ATTRIBUTE_NAME          FLAG     VALUE WORST THRESH TYPE     RAW_VALUE
#   5 Reallocated_Sector_Ct   0x0033   098   098   010    Pre-fail 47
# 197 Current_Pending_Sector  0x0012   100   100   000    Old_age  3
# 198 Offline_Uncorrectable   0x0010   100   100   000    Old_age  1
```

🔧 **NOC Tip:** A disk with **Reallocated Sector Count > 0 and rising** is actively dying. It may work fine for days or weeks, but it will fail. At Telnyx, any disk with reallocated sectors gets flagged for proactive replacement during the next maintenance window. Don't wait for it to fail completely — that risks data loss and RAID degradation.

---

## RAID Degradation Alerts

RAID provides disk-level redundancy, but a degraded RAID array is running without its safety net. If a second disk fails before the first is replaced, data is lost.

### RAID States

| State | Meaning | Urgency |
|-------|---------|---------|
| Optimal | All disks healthy | Normal |
| Degraded | One disk failed, array still functional | **High** — replace ASAP |
| Rebuilding | New disk being integrated | Monitor — performance impact |
| Failed | Multiple disk failure, data loss | **Critical** — incident |

### Monitoring RAID

```bash
# Software RAID (mdadm)
cat /proc/mdstat
mdadm --detail /dev/md0

# Example degraded output:
# md0 : active raid6 sdf1[5] sde1[4] sdd1[3] sdc1[2] sdb1[1] sda1[0](F)
#       9767424 blocks super 1.2 level 6, 512k chunk, algorithm 2 [6/5] [_UUUUU]
#                                                                        ^ Failed

# Hardware RAID (MegaRAID)
storcli /c0 show
storcli /c0/v0 show
```

### RAID Rebuild Times

RAID rebuilds are I/O intensive and slow:

| Array Size | RAID Level | Typical Rebuild Time |
|-----------|------------|---------------------|
| 4 TB HDD | RAID 6 | 12–24 hours |
| 8 TB HDD | RAID 6 | 24–48 hours |
| 2 TB SSD | RAID 10 | 2–4 hours |

During rebuilds, both performance degrades and the array is vulnerable to another disk failure.

🔧 **NOC Tip:** RAID rebuild is the most dangerous time for a storage system. At Telnyx, when a RAID degradation alert fires: (1) Immediately check if a hot spare kicked in. (2) If not, schedule disk replacement within 4 hours. (3) Reduce I/O load on the array if possible (shift traffic away). (4) Monitor for additional disk failures — a second failure during rebuild is a data loss event.

---

## Ceph/Storage Cluster Health

Telnyx's distributed storage platform is built on Ceph (or similar). Ceph has its own health monitoring system.

### Ceph Health States

```bash
# Quick health check
ceph health
# HEALTH_OK        — Everything fine
# HEALTH_WARN      — Something needs attention
# HEALTH_ERR       — Critical issue

# Detailed health
ceph health detail

# Cluster status summary
ceph -s
```

### Key Ceph Metrics

```bash
# Overall cluster status
ceph -s
# Shows: mon health, OSD status, PG status, usage

# OSD (Object Storage Daemon) status
ceph osd tree
# Shows all OSDs, their status (up/down, in/out), and location

# Placement Group health
ceph pg stat
# Shows: active+clean (good), degraded (bad), recovering (rebuilding)
```

### Common Ceph Alerts

| Alert | Meaning | Response |
|-------|---------|----------|
| `OSD_DOWN` | A storage daemon is offline | Check the host — disk failed, process crashed, or network issue |
| `PG_DEGRADED` | Data has fewer copies than configured | Self-healing if OSDs are available; monitor progress |
| `PG_NOT_DEEP_SCRUBBED` | Integrity check overdue | Schedule scrub; may indicate overloaded cluster |
| `NEARFULL` | Cluster approaching capacity limit | **Urgent** — add capacity or delete data |
| `POOL_NEARFULL` | Specific pool near capacity | Expand pool or rebalance |
| `SLOW_OPS` | Operations taking too long | Check for failed disks, network issues, or overload |

```bash
# Check for slow operations
ceph daemon osd.0 dump_ops_in_flight

# Check OSD performance
ceph osd perf
```

🔧 **NOC Tip:** The `SLOW_OPS` warning in Ceph is your early warning system for storage performance problems. It means some operations are taking longer than the configured threshold (usually 30 seconds). Common causes: (1) a dying HDD in an OSD, (2) network issues between OSDs, (3) the cluster is overloaded. Investigate immediately — what starts as slow ops can cascade to client timeouts.

---

## NOC Response to Storage Alerts

### Triage Framework

```
Storage Alert Fires
  │
  ├── Is it capacity-related?
  │     ├── > 93% full → CRITICAL: Add capacity NOW, consider emergency cleanup
  │     └── > 85% full → WARNING: Plan capacity addition this week
  │
  ├── Is it a disk failure?
  │     ├── RAID degraded → Schedule replacement within 4 hours
  │     ├── SMART warning → Schedule proactive replacement (next maintenance)
  │     └── Multiple disks on same node → Drain node, escalate
  │
  ├── Is it performance (latency/IOPS)?
  │     ├── Single disk slow → Likely failing disk, check SMART
  │     ├── Entire node slow → Check network, check for rebuild activity
  │     └── Cluster-wide → Major issue: network, overload, or correlated failure
  │
  └── Is it cluster health?
        ├── HEALTH_WARN → Investigate, usually self-healing
        └── HEALTH_ERR → Immediate investigation, potential data risk
```

### Communication Templates

For storage incidents affecting customers:

```
STORAGE DEGRADATION — [Site]
Status: [Investigating/Identified/Monitoring]
Impact: Increased latency for object storage operations in [region]
Cause: [Disk failure/Rebalancing/Capacity]
ETA: [Estimated resolution]
```

---

## Key Takeaways

1. **IOPS, throughput, latency, and capacity** are the four pillars of storage monitoring — understand what's normal for each workload type.
2. **SMART monitoring** catches dying disks before they fail; rising reallocated sector counts mean replacement is needed.
3. **RAID degradation** is a race against time — a second disk failure during rebuild means data loss. Replace failed disks within hours.
4. **Ceph health** (HEALTH_OK/WARN/ERR) gives you a single indicator of cluster state; use `ceph -s` and `ceph health detail` for diagnosis.
5. **Capacity alerts** at 85% and 93% are critical thresholds — Ceph goes read-only near 95%, causing cascading application failures.
6. **SLOW_OPS** in Ceph is an early warning for performance degradation — investigate immediately.
7. **Triage storage alerts** by category: capacity, disk failure, performance, or cluster health — each has a different response pattern.

---

**Next: Lesson 87 — Billing and Rating Systems: How Usage Becomes Revenue**
