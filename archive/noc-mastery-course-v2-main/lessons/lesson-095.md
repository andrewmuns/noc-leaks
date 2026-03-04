# Lesson 95: Storage — Distributed Object Storage and Telnyx Storage
**Module 2 | Section 2.12 — Storage/AI**
**⏱ ~7min read | Prerequisites: None**
---

## Introduction

Every call recording, voicemail, fax, MMS image, and AI model artifact at Telnyx needs to live somewhere durable and accessible. That somewhere is **object storage** — a massively scalable storage system designed for billions of files across multiple data centers.

Telnyx operates its own distributed object storage platform, **Telnyx Storage**, offering an S3-compatible API to both internal services and external customers. As a NOC engineer, you'll need to understand how this system works, where data lives, and what breaks.

---

## Object Storage Concepts

### What Is Object Storage?

Unlike file systems (hierarchical directories) or block storage (raw disk volumes), object storage treats every piece of data as a **flat object** identified by a key within a bucket.

```
Bucket: customer-recordings
  ├── 2026/01/15/call-abc123.wav     (object key)
  ├── 2026/01/15/call-def456.wav
  └── 2026/01/16/call-ghi789.wav
```

Each object consists of:
- **Key:** The unique path/name within a bucket
- **Data:** The actual bytes (a file, image, recording, etc.)
- **Metadata:** Content-type, timestamps, custom headers
- **Version ID:** (If versioning is enabled) for tracking changes

### Buckets

A bucket is a namespace container for objects. Buckets have:
- A globally unique name
- Access policies (public, private, ACLs)
- Region/site placement configuration
- Optional versioning, lifecycle rules, and CORS settings

### The S3 API

Telnyx Storage implements the **Amazon S3 API**, the de facto standard for object storage. This means any tool that works with AWS S3 works with Telnyx Storage.

```bash
# Upload an object using AWS CLI pointed at Telnyx Storage
aws s3 cp recording.wav s3://customer-recordings/2026/01/15/call-abc123.wav \
  --endpoint-url https://storage.telnyx.com

# List objects in a bucket
aws s3 ls s3://customer-recordings/ --endpoint-url https://storage.telnyx.com

# Download an object
aws s3 cp s3://customer-recordings/2026/01/15/call-abc123.wav ./local-copy.wav \
  --endpoint-url https://storage.telnyx.com
```

Key S3 operations you'll encounter in logs and metrics:

| Operation | Description | Common Use |
|-----------|-------------|------------|
| `PutObject` | Upload a new object | Storing a call recording |
| `GetObject` | Download an object | Playing back a recording |
| `DeleteObject` | Remove an object | Lifecycle expiration |
| `ListObjectsV2` | List objects in a bucket | UI browsing, enumeration |
| `HeadObject` | Get metadata without downloading | Checking if object exists |
| `CreateMultipartUpload` | Start a large file upload | Files > 100 MB |

🔧 **NOC Tip:** When debugging storage issues reported by customers, ask: "Which S3 operation is failing?" A `PutObject` failure means writes are broken (serious). A `GetObject` 403 is usually a permissions issue (less urgent). A `ListObjectsV2` timeout on a bucket with millions of objects is often just a slow query, not a system failure.

---

## Telnyx Storage Architecture

Telnyx Storage is built on a distributed storage cluster (based on technology similar to Ceph or MinIO) spanning multiple data center sites.

### Core Components

```
                    ┌──────────────────┐
  Client Request →  │   S3 API Gateway  │  (authentication, routing)
                    └────────┬─────────┘
                             │
                    ┌────────▼─────────┐
                    │  Metadata Service │  (bucket/object index)
                    └────────┬─────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
        ┌──────────┐  ┌──────────┐  ┌──────────┐
        │ Storage   │  │ Storage   │  │ Storage   │
        │ Node A    │  │ Node B    │  │ Node C    │
        │ (CHI)     │  │ (ASH)     │  │ (AMS)     │
        └──────────┘  └──────────┘  └──────────┘
```

- **S3 API Gateway:** Receives client requests, handles authentication (access keys), and routes to the appropriate storage backend.
- **Metadata Service:** Tracks which objects exist in which buckets, their sizes, versions, and where their data chunks are placed.
- **Storage Nodes:** Physical servers with large disk arrays (HDDs for capacity, NVMe for metadata/cache) that hold the actual object data.

### Data Durability

Objects are stored with **erasure coding** — data is split into data chunks and parity chunks spread across multiple disks and nodes. A typical scheme might be 8+4 (8 data + 4 parity), meaning the system can lose any 4 chunks and still reconstruct the object.

```
Object "recording.wav" → Erasure Coded:
  Chunk 1 → Disk A, Node 1 (CHI)
  Chunk 2 → Disk B, Node 1 (CHI)
  Chunk 3 → Disk C, Node 2 (CHI)
  ...
  Parity 1 → Disk A, Node 3 (CHI)
  Parity 2 → Disk B, Node 4 (CHI)
```

This provides **11 nines of durability** (99.999999999%) without the 3x storage overhead of simple replication.

---

## Data Placement Across Sites

Telnyx operates storage clusters in multiple sites (e.g., Chicago, Ashburn, Amsterdam). Data placement depends on the bucket's configuration:

### Single-Region Buckets

Data resides in one site. Lower latency for nearby clients, but vulnerable to site-level failures.

### Multi-Region Buckets

Data is replicated across 2+ sites. Writes go to the primary site and are asynchronously replicated to secondary sites. This provides:
- **Geographic redundancy** — survives a full site outage
- **Read locality** — clients can read from the nearest site
- **Higher write latency** — data must be acknowledged and queued for replication

```
Write path (multi-region):
  Client → API GW (CHI) → Write to CHI cluster → ACK to client
                         → Async replicate to ASH
                         → Async replicate to AMS
```

🔧 **NOC Tip:** When a site goes down, single-region buckets hosted at that site become **completely unavailable**. Multi-region buckets will continue serving reads from the surviving site but may have stale data (replication lag). Know which high-value customers use single-region vs. multi-region buckets — this determines incident severity.

---

## Consistency Model

Telnyx Storage provides **read-after-write consistency** for new objects:
- After a successful `PutObject`, a subsequent `GetObject` will return the new data.

For **overwrites and deletes**, there may be a brief window of eventual consistency:
- After overwriting an object, a `GetObject` might briefly return the old version.
- After deleting an object, a `GetObject` might briefly succeed before the delete propagates.

For multi-region buckets, cross-site reads are **eventually consistent** with a replication lag typically under 1 second but potentially minutes during degraded conditions.

```
Timeline (multi-region overwrite):
  t=0    Client writes v2 to CHI → Success
  t=0    Client reads from CHI   → Gets v2 ✓
  t=0    Client reads from ASH   → Gets v1 ✗ (replication pending)
  t=500ms Client reads from ASH  → Gets v2 ✓ (replication complete)
```

🔧 **NOC Tip:** If a customer reports "I uploaded a file but can't see it," check: (1) Did the upload actually succeed? (Check API logs for 200 response.) (2) Are they reading from a different region than they wrote to? (3) Is replication lagging? Check the replication lag metric in Grafana.

---

## Failure Modes

### Slow Writes

**Symptoms:** `PutObject` latency increases from ~100ms to 5–30 seconds. Customers report timeouts on uploads.

**Common Causes:**
- Disk failures reducing cluster capacity, causing rebalancing
- Network congestion between storage nodes
- Metadata service overload (too many small objects)
- Erasure coding rebuild consuming I/O bandwidth

**NOC Response:** Check storage cluster health dashboard. Look for degraded disks, high I/O wait, or rebalancing activity. If rebalancing is the cause, it's self-healing but slow — communicate ETA to affected customers.

### Unavailable Buckets

**Symptoms:** API returns 503 (Service Unavailable) for specific buckets or all operations.

**Common Causes:**
- Metadata service failure — the system can't look up where objects are stored
- API gateway overload or crash
- Network partition isolating storage nodes
- Full site outage (for single-region buckets)

**NOC Response:** Check API gateway health, metadata service, and inter-node connectivity. If a site is down, failover multi-region traffic. For single-region, communicate outage to customers.

### Data Integrity Issues

**Symptoms:** `GetObject` returns corrupted data (checksum mismatch), or objects appear missing.

**Common Causes:**
- Silent disk corruption (bit rot) not caught by scrubbing
- Bug in erasure coding reconstruction
- Incomplete replication after a failure

**NOC Response:** This is a **critical** incident. Escalate immediately. Check if the issue is isolated to one disk/node or widespread. Enable emergency scrubbing to detect extent of corruption.

### Replication Lag

**Symptoms:** Multi-region reads return stale data. Replication lag metric growing.

**Common Causes:**
- WAN link between sites congested or down
- Source cluster overloaded, can't keep up with replication queue
- Large bulk upload saturating replication bandwidth

**NOC Response:** Check WAN link health between sites. If the link is degraded, replication will catch up when it recovers. If the lag exceeds SLA thresholds, notify affected customers.

---

## Operational Commands

```bash
# Check cluster health (Ceph-based example)
ceph -s
ceph health detail

# Check storage utilization
ceph df

# List pools and their replication/EC profile
ceph osd pool ls detail

# Check replication lag (custom Telnyx tooling)
telnyx-storage replication-status --bucket customer-recordings

# Check for degraded placement groups
ceph pg stat
```

---

## Key Takeaways

1. **Object storage** uses buckets and keys with an S3-compatible API — understand PutObject, GetObject, and ListObjects as the primary operations.
2. **Telnyx Storage** consists of API gateways, metadata services, and distributed storage nodes with erasure coding for durability.
3. **Data placement** varies: single-region (lower latency, less resilient) vs. multi-region (geo-redundant, eventually consistent across sites).
4. **Read-after-write consistency** applies within a region; cross-region reads are eventually consistent with replication lag.
5. **Slow writes** usually stem from disk failures or rebalancing; **unavailable buckets** usually point to metadata or gateway failures.
6. **Replication lag** is the key metric for multi-region buckets — monitor it closely during WAN degradations.
7. **Data integrity issues** are rare but critical — escalate immediately and check the blast radius.

---

**Next: Lesson 86 — Storage: Monitoring Storage Health**
