# Lesson 166: Query Optimization - EXPLAIN Plans and Index Tuning
**Module 5 | Section 5.3 - Databases for NOC**
**⏱ ~8 min read | Prerequisites: Lesson 149**

---

## Why Query Optimization Matters for NOC

Slow database queries don't just cause inconvenience - they cause incidents. A query that takes 30 seconds instead of 30 milliseconds can trigger connection pool exhaustion (Lesson 122), cascade failures (Lesson 121), and complete service outages.

Understanding query optimization helps NOC engineers:
- Identify why an application is slow
- Verify if a reported "database issue" is actually a query problem
- Determine if an index is missing or not being used
- Communicate effectively with database administrators

## Reading EXPLAIN Output

### Basic EXPLAIN

```sql
EXPLAIN SELECT * FROM cdr WHERE customer_id = 12345;
```

Output shows the query plan - how PostgreSQL will execute the query:

```
Index Scan using cdr_customer_id_idx on cdr  (cost=0.43..8.45 rows=1 width=256)
  Index Cond: (customer_id = 12345)
```

Key fields:
- **Scan type**: How data is accessed (Index Scan vs. Seq Scan)
- **Cost**: Estimated computational effort (startup..total)
- **Rows**: Estimated rows returned
- **Width**: Estimated bytes per row

### EXPLAIN ANALYZE

```sql
EXPLAIN ANALYZE SELECT * FROM cdr WHERE customer_id = 12345;
```

This actually executes the query and shows real timing:

```
Index Scan using cdr_customer_id_idx on cdr  (cost=0.43..8.45 rows=1 width=256) (actual time=0.025..0.026 rows=1 loops=1)
  Index Cond: (customer_id = 12345)
Planning Time: 0.100 ms
Execution Time: 0.050 ms
```

**Critical fields:**
- **actual time**: Real milliseconds spent (startup..total)
- **rows**: Actual rows returned (not estimated)
- **Planning Time**: Time to generate the plan
- **Execution Time**: Time to run the query

🔧 **NOC Tip:** Use `EXPLAIN ANALYZE` on replicas, not production primary, for slow queries. The ANALYZE option actually executes the query, which can impact production. For production primary, use just `EXPLAIN` (no execution).

## Scan Types: The Critical Distinction

### Index Scan (Good)

```
Index Scan using cdr_customer_id_idx on cdr
```

The database uses an index to find exactly the rows needed. Fast for selective queries (few rows from large table).

**When it happens:**
- WHERE clause matches an index
- Selective query (returns small percentage of table)
- Index exists and is usable

### Sequential Scan (Potentially Bad)

```
Seq Scan on cdr  (cost=0.00..250000.00 rows=5000000 width=256)
```

The database reads every row in the table. Fast for small tables or when you need most rows. **Extremely slow for selective queries on large tables.**

**When it happens:**
- No matching index exists
- Query is not selective (returns high % of table)
- Index is unusable (function on column, type mismatch)

### Bitmap Index Scan (Middle Ground)

```
Bitmap Heap Scan on cdr
  Recheck Cond: (customer_id = 12345)
  -> Bitmap Index Scan on cdr_customer_id_idx
```

Combines index lookup with heap access. Used when multiple conditions or returning moderate rows.

## Identifying Slow Query Causes

### Missing Index

```sql
EXPLAIN ANALYZE SELECT * FROM cdr WHERE destination_number = '+1234567890';

-- Output shows Seq Scan
Seq Scan on cdr  (cost=0.00..500000.00 rows=5 width=256) (actual time=5000..15000 rows=3 loops=1)
  Filter: (destination_number = '+1234567890'::text)
  Rows Removed by Filter: 9999997
```

Problem: 10 million rows scanned to find 3. Index needed.

**Fix:**
```sql
CREATE INDEX idx_cdr_destination ON cdr (destination_number);
```

### Function on Column Prevents Index Use

```sql
-- Query
EXPLAIN SELECT * FROM cdr WHERE LOWER(destination_number) = '+1234567890';

-- Plan shows Seq Scan (index not used)
Seq Scan on cdr
  Filter: (lower(destination_number) = '+1234567890'::text)
```

Problem: `LOWER()` function on column prevents index use. Database must evaluate function for every row.

**Fix options:**
1. Remove function if not needed: `WHERE destination_number = '+1234567890'`
2. Create function-based index: `CREATE INDEX idx_lower_dest ON cdr (LOWER(destination_number))`
3. Store normalized data separately

### Type Mismatch

```sql
-- Column is VARCHAR, query uses INTEGER
EXPLAIN SELECT * FROM cdr WHERE customer_id = '12345';

-- Might use index
EXPLAIN SELECT * FROM cdr WHERE customer_id = 12345::text;

-- Column is INTEGER, query uses VARCHAR
EXPLAIN SELECT * FROM cdr WHERE customer_id = '12345';

-- Implicit cast prevents index use
```

Problem: Type mismatch forces implicit cast, preventing index use.

**Fix:** Ensure query types match column types.

### OR Condition Preventing Index Use

```sql
-- OR across different columns
EXPLAIN SELECT * FROM cdr 
WHERE customer_id = 12345 OR destination_number = '+1234567890';

-- Likely Seq Scan (can't use two indexes efficiently)
```

**Fix:** Rewrite as UNION:
```sql
SELECT * FROM cdr WHERE customer_id = 12345
UNION
SELECT * FROM cdr WHERE destination_number = '+1234567890';
```

Each query uses its own index, results combined.

## Index Strategies

### When to Create an Index

**Good candidates:**
- Columns in WHERE clauses that filter to small result sets
- Columns used in JOIN conditions
- Columns used in ORDER BY with LIMIT
- Columns with high selectivity (many distinct values)

**Poor candidates:**
- Columns with few distinct values (boolean, status with 3 values)
- Columns rarely used in queries
- Tables with small row counts (sequential scan is fine)
- Columns that change frequently (index maintenance overhead)

### Composite Indexes

Multiple columns in one index:

```sql
-- Query pattern
SELECT * FROM cdr 
WHERE customer_id = 12345 
  AND start_time > NOW() - INTERVAL '1 hour';

-- Composite index (order matters!)
CREATE INDEX idx_cdr_customer_time ON cdr (customer_id, start_time);
```

**Column order rules:**
1. Equality columns first (= conditions)
2. Range columns second (> < BETWEEN conditions)
3. Sort columns if needed

```sql
-- For this query:
SELECT * FROM cdr 
WHERE customer_id = 12345              -- equality
  AND start_time > NOW() - INTERVAL '1 hour'  -- range
ORDER BY start_time DESC               -- sort
LIMIT 100;

-- Optimal index:
CREATE INDEX idx_cdr_customer_time ON cdr (customer_id, start_time DESC);
```

### Partial Indexes

Index subset of data:

```sql
-- Only index active records
CREATE INDEX idx_active_customers ON customers (email) 
WHERE status = 'active';

-- Only index failed calls
CREATE INDEX idx_failed_calls ON cdr (customer_id, start_time)
WHERE status = 'failed';
```

Benefits: Smaller index, faster for targeted queries, less maintenance overhead.

### Covering Indexes

Include all columns needed by query:

```sql
-- Query
SELECT customer_id, start_time, duration_seconds 
FROM cdr 
WHERE customer_id = 12345;

-- Covering index (INCLUDE for non-key columns)
CREATE INDEX idx_cdr_customer_covering ON cdr (customer_id)
INCLUDE (start_time, duration_seconds);
```

Query can be satisfied entirely from index without accessing table.

## Query Optimization Workflow

### Step 1: Identify Slow Query

From application logs, pg_stat_statements, or slow query log:

```sql
-- pg_stat_statements shows slowest queries
SELECT 
    query,
    calls,
    total_exec_time,
    mean_exec_time,
    rows
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 10;
```

### Step 2: EXPLAIN ANALYZE

```sql
EXPLAIN ANALYZE <slow query>;
```

Look for:
- Seq Scan on large table → missing index
- High actual time → quantify the problem
- Rows removed by filter → inefficient scan
- Nested Loop with many iterations → join issue

### Step 3: Identify Root Cause

Common causes:
- Missing index
- Index not used (function, type, OR)
- Wrong index (low selectivity)
- Outdated statistics

### Step 4: Apply Fix

```sql
-- Create missing index
CREATE INDEX CONCURRENTLY idx_name ON table (column);

-- CONCURRENTLY prevents table lock
-- Can run in production without blocking
```

### Step 5: Verify Improvement

```sql
EXPLAIN ANALYZE <query>;
-- Compare execution time
```

### Step 6: Monitor

Watch for regression over time:
- Data growth might change plan
- Index bloat might degrade performance
- Statistics might become stale

## pg_stat_statements for NOC

Essential query performance monitoring:

```sql
-- Enable extension (one time)
CREATE EXTENSION pg_stat_statements;

-- Top queries by total time
SELECT 
    queryid,
    LEFT(query, 100) as query_preview,
    calls,
    ROUND(total_exec_time::numeric, 2) as total_time_ms,
    ROUND(mean_exec_time::numeric, 2) as avg_time_ms,
    rows
FROM pg_stat_statements
ORDER BY total_exec_time DESC
LIMIT 20;

-- Queries with highest average time
SELECT 
    queryid,
    LEFT(query, 100) as query_preview,
    calls,
    ROUND(mean_exec_time::numeric, 2) as avg_time_ms
FROM pg_stat_statements
WHERE calls > 100  -- Enough data to be meaningful
ORDER BY mean_exec_time DESC
LIMIT 20;

-- Reset statistics (after making changes)
SELECT pg_stat_statements_reset();
```

🔧 **NOC Tip:** When investigating database slowness, check `pg_stat_statements` first. It shows actual query performance, not estimates. Focus on queries with both high total time AND high average time - these are slow AND frequent.

## Real-World Scenario: The Slow CDR Query

**Report:** Customer dashboard timing out when loading call history.

**Investigation:**

```sql
-- Application query (simplified)
SELECT * FROM cdr 
WHERE customer_id = 12345 
ORDER BY start_time DESC 
LIMIT 50;

-- EXPLAIN ANALYZE
EXPLAIN ANALYZE SELECT * FROM cdr 
WHERE customer_id = 12345 
ORDER BY start_time DESC 
LIMIT 50;

-- Output
Sort  (cost=50000..50005 rows=200 width=256) (actual time=15000..15000 rows=50 loops=1)
  Sort Key: start_time DESC
  Sort Method: top-N heapsort  Memory: 35kB
  -> Seq Scan on cdr  (cost=0.00..45000 rows=200 width=256) (actual time=0..14000 rows=50000 loops=1)
        Filter: (customer_id = 12345)
        Rows Removed by Filter: 9995000
Planning Time: 0.5 ms
Execution Time: 15000 ms
```

**Analysis:**
- Seq Scan on 10 million row table
- Finds 50,000 rows for customer, then sorts
- 15 seconds execution time

**Problem:** No index on `customer_id`, forcing full table scan.

**Fix:**

```sql
CREATE INDEX CONCURRENTLY idx_cdr_customer ON cdr (customer_id, start_time DESC);

-- Re-run EXPLAIN ANALYZE
Index Scan Backward using idx_cdr_customer on cdr  (cost=0.43..50.45 rows=50 width=256) (actual time=0.05..0.10 rows=50 loops=1)
  Index Cond: (customer_id = 12345)
Execution Time: 0.15 ms
```

**Result:** 15,000 ms → 0.15 ms (100,000x faster)

🔧 **NOC Tip:** After creating an index, the query plan doesn't immediately change - PostgreSQL needs to update statistics. Run `ANALYZE cdr;` after index creation, or wait for autovacuum. If plan doesn't change, check if autovacuum is running.

## Statistics and Autovacuum

PostgreSQL statistics guide query planning:

```sql
-- Check if statistics are current
SELECT 
    tablename,
    last_vacuum,
    last_autovacuum,
    last_analyze,
    last_autoanalyze
FROM pg_stat_user_tables
WHERE schemaname = 'public';

-- Force statistics update
ANALYZE cdr;

-- Force vacuum and analyze
VACUUM ANALYZE cdr;
```

Outdated statistics cause bad plans. If query suddenly slows down after data changes, stale statistics might be the cause.

---

**Key Takeaways:**
1. EXPLAIN shows the plan; EXPLAIN ANALYZE executes and shows actual performance - use ANALYZE only on replicas
2. Index Scan is fast for selective queries; Seq Scan on large tables with selective WHERE indicates missing index
3. Functions on columns, type mismatches, and OR conditions can prevent index usage even when indexes exist
4. Composite index column order matters: equality columns first, range columns second
5. pg_stat_statements shows actual query performance - use it to identify slow queries systematically
6. Use CREATE INDEX CONCURRENTLY in production to avoid blocking - regular CREATE INDEX locks the table

**Next: Lesson 151 - Connection Pooling: PgBouncer and Connection Management**
