# Lesson 164: Relational Database Fundamentals - PostgreSQL
**Module 5 | Section 5.3 - Databases for NOC**
**⏱ ~8 min read | Prerequisites: Lessons 17, 139**

---

## Why NOC Engineers Need PostgreSQL

Many telecom platform operations require interacting with PostgreSQL databases directly:
- Looking up customer configurations during incident investigation
- Checking routing tables and number assignments
- Investigating CDR data for call failures
- Verifying billing records
- Querying audit logs

Understanding basic PostgreSQL operations is essential for effective NOC work. This lesson covers the fundamentals you need to query production databases safely.

## Database Structure Basics

### Tables, Rows, and Columns

**Table**: A collection of related data, like a spreadsheet.
- `customers` table: holds customer records
- `cdr` table: holds call detail records
- `telephone_numbers` table: holds number inventory

**Row**: A single record in a table.
- One row = one customer
- One row = one phone call
- One row = one telephone number

**Column**: A field of data within each row.
- `customer_id`, `name`, `created_at` are columns in the customers table
- Each column has a data type (integer, text, timestamp, etc.)

### Primary Keys

Every table should have a primary key - a unique identifier for each row:

```sql
CREATE TABLE customers (
    customer_id SERIAL PRIMARY KEY,
    name VARCHAR(255),
    created_at TIMESTAMP DEFAULT NOW()
);
```

- Queries using primary keys are fast
- Primary keys are automatically indexed
- Foreign keys reference primary keys

### Foreign Keys

Foreign keys create relationships between tables:

```sql
CREATE TABLE telephone_numbers (
    number_id SERIAL PRIMARY KEY,
    phone_number VARCHAR(15) NOT NULL,
    customer_id INTEGER REFERENCES customers(customer_id)
);
```

The `customer_id` in `telephone_numbers` references `customer_id` in `customers`. This enforces data integrity - you can't assign a number to a non-existent customer.

## Essential SQL for NOC Operations

### SELECT - Retrieving Data

```sql
-- Get all columns for a specific customer
SELECT * FROM customers WHERE customer_id = 12345;

-- Get specific columns
SELECT name, email, created_at FROM customers WHERE customer_id = 12345;

-- Get count of records
SELECT COUNT(*) FROM cdr WHERE start_time > NOW() - INTERVAL '1 hour';
```

### WHERE - Filtering Rows

```sql
-- Equality
SELECT * FROM cdr WHERE status = 'completed';

-- Comparison
SELECT * FROM cdr WHERE duration_seconds > 60;

-- Range (BETWEEN is inclusive)
SELECT * FROM cdr WHERE start_time BETWEEN '2026-02-20' AND '2026-02-21';

-- Multiple conditions (AND)
SELECT * FROM cdr 
WHERE status = 'failed' 
  AND start_time > NOW() - INTERVAL '1 hour';

-- Either condition (OR)
SELECT * FROM cdr 
WHERE status = 'failed' 
   OR status = 'dropped';

-- Pattern matching (LIKE)
SELECT * FROM telephone_numbers 
WHERE phone_number LIKE '+1-312-%';
-- % matches any characters
-- _ matches single character

-- Set membership (IN)
SELECT * FROM cdr WHERE status IN ('failed', 'dropped', 'timeout');

-- Null checks
SELECT * FROM customers WHERE deleted_at IS NULL;
```

🔧 **NOC Tip:** Always use `LIMIT` when exploring tables you don't know. `SELECT * FROM cdr LIMIT 10` instead of `SELECT * FROM cdr`. Large tables (billions of rows) can hang your query for minutes without limits.

### JOIN - Combining Tables

```sql
-- Inner join: only rows that exist in both tables
SELECT 
    c.name,
    tn.phone_number,
    tn.status
FROM customers c
INNER JOIN telephone_numbers tn ON c.customer_id = tn.customer_id
WHERE c.customer_id = 12345;

-- Left join: all rows from left table, nulls for missing right
SELECT 
    c.name,
    tn.phone_number
FROM customers c
LEFT JOIN telephone_numbers tn ON c.customer_id = tn.customer_id;
-- Shows customers even if they have no numbers
```

### ORDER BY / LIMIT - Sorting and Pagination

```sql
-- Most recent calls first
SELECT * FROM cdr 
WHERE customer_id = 12345 
ORDER BY start_time DESC
LIMIT 50;

-- Longest calls first
SELECT * FROM cdr 
ORDER BY duration_seconds DESC 
LIMIT 10;

-- Pagination
SELECT * FROM cdr 
ORDER BY start_time DESC 
LIMIT 50 OFFSET 100;  -- Skip first 100, get next 50
```

### GROUP BY - Aggregation

```sql
-- Count calls by status
SELECT status, COUNT(*) as count
FROM cdr
WHERE start_time > NOW() - INTERVAL '1 hour'
GROUP BY status;

-- Sum call duration by customer
SELECT 
    customer_id, 
    COUNT(*) as call_count,
    SUM(duration_seconds) as total_duration
FROM cdr
WHERE start_time > NOW() - INTERVAL '1 hour'
GROUP BY customer_id
ORDER BY call_count DESC
LIMIT 10;

-- Average call duration by destination country
SELECT 
    destination_country,
    AVG(duration_seconds) as avg_duration,
    COUNT(*) as total_calls
FROM cdr
WHERE start_time > NOW() - INTERVAL '1 hour'
GROUP BY destination_country
ORDER BY total_calls DESC;
```

### HAVING - Filter After Aggregation

```sql
-- Find customers with high call counts (WHERE filters before GROUP BY, HAVING after)
SELECT 
    customer_id,
    COUNT(*) as call_count
FROM cdr
WHERE start_time > NOW() - INTERVAL '1 day'
GROUP BY customer_id
HAVING COUNT(*) > 1000  -- More than 1000 calls
ORDER BY call_count DESC;
```

## Data Types

### Common PostgreSQL Types for Telecom

| Type | Description | Example |
|------|-------------|---------|
| `INTEGER` / `BIGINT` | Whole numbers | customer_id, duration_seconds |
| `NUMERIC(10,2)` | Decimal (precision, scale) | cost, rate |
| `VARCHAR(n)` | Variable string | phone_number, status |
| `TEXT` | Unlimited string | raw_sip_message |
| `TIMESTAMP` | Date and time | call_start, created_at |
| `TIMESTAMPTZ` | Timestamp with timezone | preferred for telecom |
| `BOOLEAN` | True/False | is_active, is_ported |
| `JSONB` | Binary JSON | flexible config storage |
| `INET` | IP address | source_ip, destination_ip |
| `UUID` | Unique identifier | call_id, session_id |

### Date/Time Functions

```sql
-- Current timestamp
SELECT NOW();

-- Timezone handling
SELECT NOW() AT TIME ZONE 'UTC';
SELECT start_time AT TIME ZONE 'America/New_York' FROM cdr;

-- Date arithmetic
SELECT NOW() - INTERVAL '1 hour';
SELECT start_time + INTERVAL '30 seconds' FROM cdr;

-- Date truncation for grouping
SELECT 
    DATE_TRUNC('hour', start_time) as hour,
    COUNT(*) as calls
FROM cdr
WHERE start_time > NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', start_time)
ORDER BY hour DESC;

-- Extract fields
SELECT 
    EXTRACT(HOUR FROM start_time) as hour_of_day,
    COUNT(*) as calls
FROM cdr
WHERE start_time > NOW() - INTERVAL '7 days'
GROUP BY EXTRACT(HOUR FROM start_time)
ORDER BY hour_of_day;
```

## Transactions and ACID

PostgreSQL transactions ensure data integrity:

### ACID Properties

- **Atomicity**: All changes in a transaction complete or none do. No partial updates.
- **Consistency**: Database transitions from valid state to valid state
- **Isolation**: Concurrent transactions don't interfere with each other
- **Durability**: Completed transactions survive crashes

### Transaction Control

```sql
-- Begin transaction
BEGIN;

-- Make changes
UPDATE customers SET status = 'suspended' WHERE customer_id = 12345;
INSERT INTO audit_log (customer_id, action) VALUES (12345, 'suspended');

-- Commit (make permanent) or rollback (cancel)
COMMIT;  -- or ROLLBACK;
```

### Read Replicas

For heavy queries during incident investigation, always use read replicas:

```sql
-- Connect to replica for reporting
psql -h replica-db.internal -U noc_readonly -d telnyx_stats

-- Use for heavy queries
SELECT * FROM huge_table WHERE ...;
```

**Why replicas matter:**
- Protect production from heavy queries
- Replicas can lag slightly (typically seconds)
- Read-only, no accidental updates
- Can be more heavily utilized

🔧 **NOC Tip:** Before running any query on production, know which database you're connected to. Production primary is for quick lookups; replicas for heavy analytics. Use `\conninfo` in psql or check connection string.

## Safe Query Practices

### Never Do

```sql
-- Don't update without WHERE
UPDATE customers SET status = 'deleted';  -- DELETES EVERYONE!

-- Don't delete without confirming
DELETE FROM cdr;  -- ALL GONE!

-- UPDATE/DELETE WHERE without LIMIT
UPDATE cdr SET status = 'processed';  -- MILLIONS OF ROWS

-- SELECT * on billion row tables without LIMIT
SELECT * FROM cdr WHERE start_time > '2020-01-01';  -- WILL HANG
```

### Always Do

```sql
-- Preview before update
SELECT * FROM customers WHERE customer_id = 12345;
-- Verify this looks right, THEN:
UPDATE customers SET status = 'suspended' WHERE customer_id = 12345;

-- Use LIMIT for exploration
SELECT * FROM cdr WHERE start_time > NOW() - INTERVAL '1 hour' LIMIT 100;

-- Use transactions for changes outside runbooks
BEGIN;
UPDATE ...;
-- VERIFY results
COMMIT;  -- or ROLLBACK if wrong

-- Always specify columns, don't rely on *
SELECT customer_id, name, status FROM customers;
```

## Real-World Incident Query

**Scenario**: Customer reports failed calls in the last hour.

```sql
-- First: identify customer ID
SELECT customer_id FROM customers WHERE name ILIKE '%acme corp%';
-- Returns: 12345

-- Look at recent calls
SELECT 
    call_id,
    start_time,
    destination_number,
    duration_seconds,
    status,
    hangup_cause
FROM cdr
WHERE customer_id = 12345
  AND start_time > NOW() - INTERVAL '1 hour'
ORDER BY start_time DESC
LIMIT 50;

-- Look for patterns
SELECT 
    status,
    hangup_cause,
    COUNT(*) as count
FROM cdr
WHERE customer_id = 12345
  AND start_time > NOW() - INTERVAL '1 hour'
GROUP BY status, hangup_cause
ORDER BY count DESC;

-- Check routing decisions
SELECT 
    destination_number,
    routing_decision,
    carrier_id,
    failure_reason
FROM call_routing_log
WHERE customer_id = 12345
  AND created_at > NOW() - INTERVAL '1 hour'
ORDER BY created_at DESC;
```

🔧 **NOC Tip:** When investigating customer issues via SQL, start broad (recent activity) and narrow down (specific errors). Document your queries in the incident channel so others can follow along and validate.

---

**Key Takeaways:**
1. PostgreSQL relational fundamentals: tables hold rows of data, columns define fields, primary keys uniquely identify rows
2. Essential SQL: SELECT filters with WHERE, JOIN combines tables, GROUP BY aggregates, ORDER BY sorts
3. Date/time arithmetic uses INTERVAL and NOW() for telecom timestamp analysis
4. ACID transactions ensure data integrity - BEGIN, COMMIT, ROLLBACK pattern for updates
5. Always query read replicas for heavy analytics, production primary only for quick lookups
6. Safe practices: LIMIT on exploration, preview before UPDATE, use transactions for changes, never UPDATE/DELETE without WHERE

**Next: Lesson 149 - PostgreSQL for Telecom: Common Queries and Patterns**
