# Lesson 165: PostgreSQL for Telecom - Common Queries and Patterns
**Module 5 | Section 5.3 - Databases for NOC**
**⏱ ~7 min read | Prerequisites: Lesson 148**

---

## Practical SQL for Telecom Operations

Building on Lesson 148's fundamentals, this lesson covers specific patterns for investigating telecom incidents: CDR queries, ASR calculations, configuration lookups, and time-series analysis.

## CDR Queries: The Foundation

Call Detail Records are the primary data source for voice incidents. Mastering CDR queries is essential for NOC work.

### Basic CDR Investigation

```sql
-- Recent calls for a customer in last 15 minutes
SELECT 
    call_id,
    start_time,
    destination_number,
    duration_seconds,
    status,
    sip_response,
    hangup_cause
FROM cdr
WHERE customer_id = 12345
  AND start_time > NOW() - INTERVAL '15 minutes'
ORDER BY start_time DESC;

-- Failed calls investigation
SELECT 
    call_id,
    start_time,
    destination_number,
    sip_status,
    hangup_cause,
    carrier_id,
    source_ip
FROM cdr
WHERE customer_id = 12345
  AND status = 'failed'
  AND start_time > NOW() - INTERVAL '1 hour'
ORDER BY start_time DESC;
```

### ASR (Answer Seizure Ratio) Calculation

ASR is the percentage of calls that complete successfully:

```sql
-- ASR for a customer in last hour
SELECT 
    COUNT(*) FILTER (WHERE status = 'completed') as completed,
    COUNT(*) as total,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status = 'completed') / COUNT(*), 
        2
    ) as asr_percent
FROM cdr
WHERE customer_id = 12345
  AND start_time > NOW() - INTERVAL '1 hour';

-- ASR by carrier (identify routing issues)
SELECT 
    carrier_id,
    COUNT(*) FILTER (WHERE status = 'completed') as completed,
    COUNT(*) as total,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status = 'completed') / NULLIF(COUNT(*), 0), 
        2
    ) as asr_percent
FROM cdr
WHERE start_time > NOW() - INTERVAL '1 hour'
GROUP BY carrier_id
ORDER BY asr_percent ASC;
```

**Healthy ASR**: >45% typically (international varies). <30% indicates serious problems.

### NER (Network Effectiveness Ratio)

Similar to ASR but excludes user-busy and no-answer as "user" causes rather than network failures:

```sql
-- NER calculation
SELECT 
    COUNT(*) FILTER (WHERE status IN ('completed', 'busy', 'no_answer')) as effective,
    COUNT(*) as total,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status IN ('completed', 'busy', 'no_answer')) / COUNT(*), 
        2
    ) as ner_percent
FROM cdr
WHERE start_time > NOW() - INTERVAL '1 hour';
```

**Healthy NER**: >98% typically.

### PDD (Post-Dial Delay)

Time from call initiation to ring. High PDD indicates routing or carrier issues:

```sql
-- Average PDD by destination
SELECT 
    destination_country,
    ROUND(AVG(post_dial_delay_ms), 2) as avg_pdd_ms,
    ROUND(PERCENTILE_CONT(0.95) WITHIN GROUP (ORDER BY post_dial_delay_ms), 2) as p95_pdd_ms,
    COUNT(*) as call_count
FROM cdr
WHERE start_time > NOW() - INTERVAL '1 hour'
  AND status = 'completed'
GROUP BY destination_country
HAVING COUNT(*) > 10
ORDER BY avg_pdd_ms DESC;
```

**Healthy PDD**: <3 seconds. >10 seconds is problematic.

🔧 **NOC Tip:** When investigating quality issues, run the carrier ASR query first. Low ASR for a specific carrier suggests carrier problems, not platform problems. Escalate to carrier operations when ASR drops below 40% for any carrier.

## SIP Response Code Analysis

### Response Code Distribution

```sql
-- Response codes in last 15 minutes
SELECT 
    sip_response_code,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER (), 2) as percentage
FROM cdr
WHERE start_time > NOW() - INTERVAL '15 minutes'
GROUP BY sip_response_code
ORDER BY count DESC;

-- Response codes by destination
SELECT 
    destination_number,
    sip_response_code,
    COUNT(*) as count
FROM cdr
WHERE start_time > NOW() - INTERVAL '1 hour'
GROUP BY destination_number, sip_response_code
HAVING COUNT(*) > 5
ORDER BY count DESC
LIMIT 20;
```

### Specific Error Codes

```sql
-- Common 4xx errors (client failures)
SELECT 
    sip_response_code,
    hangup_cause,
    COUNT(*) as count,
    destination_number
FROM cdr
WHERE sip_response_code >= 400
  AND sip_response_code < 500
  AND start_time > NOW() - INTERVAL '1 hour'
GROUP BY sip_response_code, hangup_cause, destination_number
ORDER BY count DESC
LIMIT 20;

-- 5xx errors (server failures - platform issue)
SELECT 
    sip_response_code,
    destination_number,
    carrier_id,
    COUNT(*) as count
FROM cdr
WHERE sip_response_code >= 500
  AND start_time > NOW() - INTERVAL '15 minutes'
GROUP BY sip_response_code, destination_number, carrier_id
ORDER BY count DESC;
-- 5xx indicates our platform issue - escalate immediately
```

## Configuration Lookups

### Customer Configuration

```sql
-- Customer connection settings
SELECT 
    c.customer_id,
    c.name,
    conn.connection_id,
    conn.trunk_type,
    conn.auth_type,
    conn.allowed_codecs,
    conn.dtmf_mode
FROM customers c
JOIN connections conn ON c.customer_id = conn.customer_id
WHERE c.customer_id = 12345;

-- Enabled telephone numbers
SELECT 
    tn.phone_number,
    tn.status,
    tn.connection_id,
    mp.profile_name
FROM telephone_numbers tn
LEFT JOIN messaging_profiles mp ON tn.messaging_profile_id = mp.profile_id
WHERE tn.customer_id = 12345
  AND tn.status = 'active'
ORDER BY tn.created_at DESC;
```

### Routing Configuration

```sql
-- Outbound routing for customer
SELECT 
    orule.prefix,
    orule.destination,
    orule.priority,
    c.name as carrier_name,
    orule.rate
FROM outbound_routing orule
LEFT JOIN carriers c ON orule.carrier_id = c.carrier_id
WHERE orule.customer_id = 12345
ORDER BY orule.priority;

-- Number pools
SELECT 
    np.pool_name,
    tn.phone_number,
    tn.status
FROM number_pools np
LEFT JOIN telephone_numbers tn ON np.pool_id = tn.pool_id
WHERE np.customer_id = 12345;
```

## Time-Series Analysis

### Hourly Traffic Patterns

```sql
-- Calls per hour for last 24 hours
SELECT 
    DATE_TRUNC('hour', start_time) as hour,
    COUNT(*) as total_calls,
    COUNT(*) FILTER (WHERE status = 'completed') as completed,
    ROUND(AVG(duration_seconds), 2) as avg_duration
FROM cdr
WHERE start_time > NOW() - INTERVAL '24 hours'
GROUP BY DATE_TRUNC('hour', start_time)
ORDER BY hour DESC;
```

### Minute-by-Minute CPS

```sql
-- Calls per second (actually per-minute rate)
SELECT 
    DATE_TRUNC('minute', start_time) as minute,
    COUNT(*) as calls,
    ROUND(COUNT(*)::numeric / 60, 2) as cps_estimate
FROM cdr
WHERE start_time > NOW() - INTERVAL '1 hour'
GROUP BY DATE_TRUNC('minute', start_time)
ORDER BY minute DESC;
```

### Comparison Windows

```sql
-- Compare current hour to same hour yesterday
WITH current_hour AS (
    SELECT 
        status,
        COUNT(*) as count
    FROM cdr
    WHERE start_time >= DATE_TRUNC('hour', NOW())
    GROUP BY status
),
yesterday_hour AS (
    SELECT 
        status,
        COUNT(*) as count
    FROM cdr
    WHERE start_time >= DATE_TRUNC('hour', NOW() - INTERVAL '1 day')
      AND start_time < DATE_TRUNC('hour', NOW() - INTERVAL '1 day') + INTERVAL '1 hour'
    GROUP BY status
)
SELECT 
    COALESCE(ch.status, yh.status) as status,
    COALESCE(ch.count, 0) as current_count,
    COALESCE(yh.count, 0) as yesterday_count,
    ROUND(
        100.0 * (COALESCE(ch.count, 0) - COALESCE(yh.count, 0)) / NULLIF(yh.count, 0),
        2
    ) as percent_change
FROM current_hour ch
FULL OUTER JOIN yesterday_hour yh ON ch.status = yh.status
ORDER BY current_count DESC;
```

## Complex Incident Queries

### Finding Call Patterns

```sql
-- Customers with sudden call spike (potential fraud or attack)
SELECT 
    customer_id,
    COUNT(*) as call_count,
    COUNT(DISTINCT destination_number) as unique_destinations,
    SUM(cost) as total_cost
FROM cdr
WHERE start_time > NOW() - INTERVAL '1 hour'
GROUP BY customer_id
HAVING COUNT(*) > 1000  -- Threshold for investigation
ORDER BY call_count DESC
LIMIT 20;

-- Unusual destination patterns
SELECT 
    destination_country,
    COUNT(*) as call_count,
    COUNT(DISTINCT customer_id) as unique_customers
FROM cdr
WHERE start_time > NOW() - INTERVAL '1 hour'
GROUP BY destination_country
HAVING COUNT(*) > 100
ORDER BY call_count DESC;

-- Short duration calls (possible scanning or click-to-dial)
SELECT 
    customer_id,
    COUNT(*) as call_count,
    ROUND(AVG(duration_seconds)::numeric, 2) as avg_duration
FROM cdr
WHERE start_time > NOW() - INTERVAL '1 hour'
  AND duration_seconds < 5
GROUP BY customer_id
HAVING COUNT(*) > 100
ORDER BY call_count DESC;
```

🔧 **NOC Tip:** When you see unusual patterns (high call counts, unusual destinations, short durations), don't immediately block. Gather data first: check if customer is legitimate with high volume, cross-reference with account management. False positives damage customer relationships.

### Correlated Failures

```sql
-- Find if failures correlate to specific source IPs
SELECT 
    source_ip,
    status,
    COUNT(*) as count
FROM cdr
WHERE start_time > NOW() - INTERVAL '15 minutes'
GROUP BY source_ip, status
HAVING COUNT(*) > 50
ORDER BY source_ip, count DESC;

-- Carrier failure correlation
SELECT 
    carrier_id,
    DATE_TRUNC('minute', start_time) as minute,
    COUNT(*) FILTER (WHERE status = 'failed') as failed,
    COUNT(*) as total,
    ROUND(
        100.0 * COUNT(*) FILTER (WHERE status = 'failed') / COUNT(*), 
        2
    ) as failure_rate
FROM cdr
WHERE start_time > NOW() - INTERVAL '1 hour'
GROUP BY carrier_id, DATE_TRUNC('minute', start_time)
HAVING COUNT(*) > 10
ORDER BY minute DESC, failure_rate DESC;
```

## Read Replica Best Practices

### When to Use Replicas

**Use read replica for:**
- Large aggregation queries (GROUP BY, COUNT, SUM across time periods)
- Historical analysis (data older than current moment)
- Customer reports and exports
- JOIN across multiple large tables
- Full table scans

**Use production primary for:**
- Quick lookups by ID
- Real-time status checks
- Small result sets

### Query Timeout Settings

```sql
-- Set statement timeout (auto-cancel long queries)
SET statement_timeout = '30s';

-- Now run your query
SELECT * FROM huge_table ...;

-- Reset after
SET statement_timeout = 0;
```

🔧 **NOC Tip:** Always set a timeout when running ad-hoc queries. It's easy to accidentally write a query that scans a billion-row table. `SET statement_timeout = '30s'` prevents runaway queries from hanging your session and impacting production.

## SQL Query Templates for Quick Response

Save these as snippets for quick access:

```sql
-- Template: Customer calls last hour
SELECT 
    call_id,
    start_time,
    destination_number,
    duration_seconds,
    status,
    sip_response_code
FROM cdr
WHERE customer_id = :customer_id
  AND start_time > NOW() - INTERVAL '1 hour'
ORDER BY start_time DESC
LIMIT 50;

-- Template: ASR by customer
SELECT 
    customer_id,
    COUNT(*) FILTER (WHERE status = 'completed') as completed,
    COUNT(*) as total,
    ROUND(100.0 * COUNT(*) FILTER (WHERE status = 'completed') / COUNT(*), 2) as asr
FROM cdr
WHERE start_time > NOW() - INTERVAL '1 hour'
GROUP BY customer_id
HAVING COUNT(*) > 100
ORDER BY asr ASC
LIMIT 20;

-- Template: Failed calls by response code
SELECT 
    sip_response_code,
    hangup_cause,
    COUNT(*),
    MIN(start_time),
    MAX(start_time)
FROM cdr
WHERE status = 'failed'
  AND start_time > NOW() - INTERVAL '15 minutes'
GROUP BY sip_response_code, hangup_cause
ORDER BY count DESC;
```

---

**Key Takeaways:**
1. ASR (completed/total) identifies routing and carrier issues - healthy is >45%, concerning is <30%
2. 5xx SIP response codes indicate platform issues requiring immediate escalation
3. Customer configuration queries via JOINs between customers, connections, and telephone_numbers tables
4. Time-series analysis with DATE_TRUNC enables traffic pattern and anomaly detection
5. Correlated failure queries identify if issues are customer-specific, carrier-specific, or platform-wide
6. Use read replicas for heavy queries, always set statement_timeout for ad-hoc investigations

**Next: Lesson 150 - Query Optimization: EXPLAIN Plans and Index Tuning**
