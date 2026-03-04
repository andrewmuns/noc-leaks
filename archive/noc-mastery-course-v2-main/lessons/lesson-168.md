# Lesson 168: ClickHouse for Analytics — Columnar Storage Fundamentals
**Module 5 | Section 5.3 — Databases for NOC**
**⏱ ~8 min read | Prerequisites: Lesson 148**

---

## Why Another Database?

In Lesson 148, we covered PostgreSQL — the workhorse of relational data. PostgreSQL excels at transactional operations: inserting a CDR, looking up a customer, updating a routing rule. These are **OLTP** (Online Transaction Processing) workloads — many small, targeted operations on individual rows.

But NOC engineers also ask fundamentally different questions: *"What was the average call duration by carrier over the last 30 days?"* or *"Show me calls per minute for the last 6 hours, broken down by region."* These are **OLAP** (Online Analytical Processing) workloads — scanning millions of rows but reading only a few columns.

PostgreSQL can answer these questions, but slowly. A query scanning 100 million CDRs to calculate average duration takes minutes in PostgreSQL. In ClickHouse, it takes seconds. The difference isn't magic — it's architecture.

## Row-Oriented vs. Column-Oriented Storage

This is the fundamental concept that explains everything about ClickHouse performance.

### Row-Oriented (PostgreSQL)

PostgreSQL stores data row by row on disk:

```
Row 1: [call_id=1, timestamp=2024-01-15 10:00:00, carrier="CarrierA", duration=45, status="answered"]
Row 2: [call_id=2, timestamp=2024-01-15 10:00:01, carrier="CarrierB", duration=0, status="failed"]
Row 3: [call_id=3, timestamp=2024-01-15 10:00:02, carrier="CarrierA", duration=120, status="answered"]
```

To calculate average duration, PostgreSQL must read **every complete row** — including call_id, timestamp, carrier, and status — even though you only need the duration column. With 100 million rows, that's a lot of wasted I/O.

### Column-Oriented (ClickHouse)

ClickHouse stores data column by column:

```
call_id column:    [1, 2, 3, 4, 5, ...]
timestamp column:  [2024-01-15 10:00:00, 2024-01-15 10:00:01, ...]
carrier column:    ["CarrierA", "CarrierB", "CarrierA", ...]
duration column:   [45, 0, 120, 67, 234, ...]
status column:     ["answered", "failed", "answered", ...]
```

Now calculating average duration reads **only the duration column**. If each row has 20 columns and you need 2 of them, columnar storage reads 10x less data from disk.

## Why Columnar Storage Compresses So Well

Here's where it gets interesting. Within a single column, values tend to be similar:

- The `carrier` column has maybe 50 distinct values across millions of rows
- The `status` column has 5-6 distinct values
- The `duration` column values cluster in typical ranges

Similar values compress dramatically. ClickHouse achieves 10:1 to 100:1 compression ratios — a 1 TB dataset might occupy 10-50 GB on disk. This means more data fits in memory, fewer disk reads, and faster queries.

PostgreSQL's row storage mixes different data types on every page — integers next to strings next to timestamps — making compression much less effective.

## The MergeTree Engine Family

ClickHouse's primary storage engine is **MergeTree** — and understanding it explains much of ClickHouse's behavior.

### How MergeTree Works

1. **Inserts go to a new "part"** — a sorted chunk of data written to disk
2. **Background merges** combine small parts into larger ones (hence "Merge" Tree)
3. **Data is sorted** by the `ORDER BY` key within each part
4. **Primary index** is sparse — it stores one entry per ~8192 rows, pointing to granules
5. **No updates in place** — ClickHouse is optimized for append-only workloads

```sql
CREATE TABLE cdrs (
    call_id UUID,
    timestamp DateTime,
    carrier LowCardinality(String),
    source_number String,
    dest_number String,
    duration UInt32,
    status LowCardinality(String),
    sip_code UInt16,
    region LowCardinality(String)
) ENGINE = MergeTree()
ORDER BY (timestamp, carrier)
PARTITION BY toYYYYMM(timestamp)
```

The `ORDER BY` clause is critical — it determines physical sort order and index efficiency. For telecom analytics, ordering by timestamp first makes time-range queries extremely fast.

`PARTITION BY` splits data into physical partitions (one per month here). Old partitions can be dropped instantly — `ALTER TABLE cdrs DROP PARTITION '202312'` — without scanning data.

🔧 **NOC Tip:** The `LowCardinality(String)` type is a game-changer for columns with few distinct values (carrier, status, region). It uses dictionary encoding internally, dramatically reducing storage and speeding up GROUP BY operations.

## ClickHouse vs. PostgreSQL: When to Use Which

| Aspect | PostgreSQL | ClickHouse |
|--------|-----------|------------|
| **Best for** | Single-record lookups, transactions | Aggregations over large datasets |
| **Insert pattern** | Individual rows, with updates | Bulk inserts, append-only |
| **Query pattern** | WHERE on primary key | GROUP BY with time ranges |
| **Latency** | Sub-millisecond for key lookups | Seconds for billion-row scans |
| **Concurrency** | Hundreds of concurrent queries | Tens of concurrent queries |
| **Updates/Deletes** | Efficient | Expensive (mutations) |

In a Telnyx-like architecture:
- **PostgreSQL** stores customer configurations, routing rules, account data — OLTP
- **ClickHouse** stores CDRs, metrics, event logs — OLAP analytics

Both are essential. They complement each other.

## A Real NOC Scenario: Investigating a Quality Degradation

**Alert:** ASR (Answer Seizure Ratio) dropped from 52% to 38% in the last 30 minutes.

In PostgreSQL, this query on 100M rows would timeout:
```sql
-- DON'T run this on PostgreSQL CDR tables
SELECT carrier, COUNT(*) as total, 
       SUM(CASE WHEN status = 'answered' THEN 1 ELSE 0 END) as answered
FROM cdrs
WHERE timestamp > now() - INTERVAL '30 minutes'
GROUP BY carrier;
```

In ClickHouse, this returns in under a second:
```sql
SELECT carrier,
       count() AS total,
       countIf(status = 'answered') AS answered,
       round(answered / total * 100, 2) AS asr
FROM cdrs
WHERE timestamp > now() - INTERVAL 30 MINUTE
GROUP BY carrier
ORDER BY total DESC
```

Instantly you see: CarrierX's ASR dropped from 50% to 12%. Now you know where to focus.

🔧 **NOC Tip:** Build a library of saved ClickHouse queries for common investigations. Having a query ready for "ASR by carrier in last N minutes" saves critical time during incidents.

## ClickHouse Operational Characteristics

### What Makes It Fast
- **Vectorized execution**: processes data in batches (columns of 8192 values) rather than row-by-row
- **SIMD instructions**: uses CPU vector instructions for parallel arithmetic
- **Compression**: less data to read from disk = faster queries
- **Sparse indexing**: skips irrelevant granules without reading them

### What It's Bad At
- **Point lookups**: finding one specific row by ID is slower than PostgreSQL
- **Updates/Deletes**: mutations are expensive background operations, not instant
- **High concurrency**: designed for dozens of analytical queries, not thousands of transactional queries
- **Transactions**: no ACID transactions — data might be partially visible during inserts

### Insert Best Practices
ClickHouse performs best with **batch inserts** — thousands of rows at a time rather than individual row inserts. Each insert creates a new data part; too many small inserts overwhelm the merge process.

```
# Bad: one row at a time (creates thousands of tiny parts)
INSERT INTO cdrs VALUES (...)  -- repeated 10,000 times

# Good: batch insert (creates one part)
INSERT INTO cdrs VALUES (...), (...), (...), ...  -- 10,000 rows at once
```

For streaming data (CDRs arriving continuously), use a buffer table or Kafka engine to batch inserts automatically.

## ClickHouse in the Monitoring Stack

ClickHouse integrates beautifully with the monitoring tools NOC engineers use daily:

- **Grafana**: The ClickHouse datasource plugin enables building dashboards directly from ClickHouse queries
- **Loki + ClickHouse**: Some architectures use ClickHouse as a Loki backend for log analytics
- **Kafka → ClickHouse**: CDRs flow from Kafka topics into ClickHouse tables via the Kafka engine

The typical flow: call completes → CDR written to Kafka → ClickHouse consumes from Kafka → Grafana dashboard queries ClickHouse → NOC engineer sees real-time metrics.

## Replication and High Availability

ClickHouse supports replication via **ReplicatedMergeTree** engine, using ZooKeeper (or ClickHouse Keeper) for coordination. Each shard has multiple replicas that stay synchronized.

For NOC awareness:
- **ZooKeeper health** directly affects ClickHouse replication. If ZooKeeper is slow, ClickHouse inserts slow down
- **Replication lag** means dashboards on different replicas might show slightly different data
- **Shard distribution** affects query performance — data should be distributed evenly

---

**Key Takeaways:**
1. Columnar storage reads only the columns needed, making analytical queries 10-100x faster than row storage
2. Similar values in columns compress dramatically — ClickHouse achieves 10:1 to 100:1 compression
3. MergeTree engine sorts data by ORDER BY key, making time-range queries on CDRs extremely efficient
4. Use PostgreSQL for OLTP (lookups, transactions) and ClickHouse for OLAP (aggregations, analytics)
5. ClickHouse prefers batch inserts — individual row inserts create merge pressure
6. LowCardinality types and proper ORDER BY key selection are the biggest performance wins

**Next: Lesson 153 — ClickHouse Queries for NOC — CDR Analytics and Dashboards**
