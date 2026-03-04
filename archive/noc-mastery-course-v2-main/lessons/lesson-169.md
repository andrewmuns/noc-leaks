# Lesson 169: ClickHouse Queries for NOC — CDR Analytics and Dashboards
**Module 5 | Section 5.3 — Databases for NOC**
**⏱ ~7 min read | Prerequisites: Lesson 152**

---

## From Storage to Insight

In Lesson 152, you learned why ClickHouse is fast. Now let's use it. NOC engineers spend significant time querying CDR data — investigating quality issues, validating carrier performance, tracking traffic patterns, and building dashboards. Mastering ClickHouse query patterns turns hours of investigation into minutes.

## Time-Series Aggregation: The Foundation

Almost every NOC query involves time bucketing. ClickHouse provides powerful time-truncation functions:

```sql
-- Calls per minute for the last 2 hours
SELECT
    toStartOfMinute(timestamp) AS minute,
    count() AS calls,
    countIf(status = 'answered') AS answered,
    round(answered / calls * 100, 2) AS asr
FROM cdrs
WHERE timestamp > now() - INTERVAL 2 HOUR
GROUP BY minute
ORDER BY minute
```

Key time functions:
- `toStartOfMinute()` — 1-minute buckets
- `toStartOfFiveMinutes()` — 5-minute buckets (great for dashboards)
- `toStartOfHour()` — hourly aggregation
- `toStartOfDay()` — daily summaries
- `toStartOfInterval(timestamp, INTERVAL 15 MINUTE)` — custom intervals

🔧 **NOC Tip:** For Grafana dashboards, use `toStartOfInterval(timestamp, INTERVAL $__interval_s SECOND)` to automatically adjust bucket size based on the time range the user selects. Zooming into 30 minutes shows per-minute data; zooming to 7 days shows hourly data.

## Essential NOC Queries

### 1. ASR and NER by Carrier (Real-Time)

```sql
SELECT
    carrier,
    count() AS attempts,
    countIf(status = 'answered') AS answered,
    countIf(sip_code BETWEEN 200 AND 299 OR sip_code BETWEEN 400 AND 499) AS user_responses,
    round(answered / attempts * 100, 2) AS asr,
    round((attempts - countIf(sip_code IN (500,502,503,504))) / attempts * 100, 2) AS ner
FROM cdrs
WHERE timestamp > now() - INTERVAL 1 HOUR
GROUP BY carrier
ORDER BY attempts DESC
```

ASR tells you what percentage of calls are answered. NER tells you what percentage reach the destination (excluding network failures). A carrier with low ASR but high NER is working fine — the calls just aren't being picked up. A carrier with low NER has a network problem.

### 2. Error Code Distribution

```sql
SELECT
    sip_code,
    count() AS occurrences,
    round(occurrences / sum(count()) OVER () * 100, 2) AS percentage,
    any(status) AS status_description
FROM cdrs
WHERE timestamp > now() - INTERVAL 30 MINUTE
  AND sip_code >= 400
GROUP BY sip_code
ORDER BY occurrences DESC
LIMIT 20
```

During an incident, this immediately shows which error codes dominate. A flood of 503s means capacity exhaustion. A spike in 408s means timeouts. 403s point to authentication issues.

### 3. Traffic Pattern Comparison (Today vs. Yesterday)

```sql
SELECT
    toStartOfFiveMinutes(timestamp) AS slot,
    countIf(toDate(timestamp) = today()) AS today_calls,
    countIf(toDate(timestamp) = yesterday()) AS yesterday_calls,
    round((today_calls - yesterday_calls) / yesterday_calls * 100, 2) AS pct_change
FROM cdrs
WHERE timestamp > now() - INTERVAL 2 HOUR
   OR (timestamp > now() - INTERVAL 26 HOUR AND timestamp < now() - INTERVAL 22 HOUR)
GROUP BY slot
ORDER BY slot
```

Comparing current traffic to the same window yesterday reveals anomalies. A 40% drop at peak hours means something is wrong even if no alerts fired.

### 4. Call Duration Distribution (Detecting Fraud)

```sql
SELECT
    multiIf(
        duration = 0, '0s (failed)',
        duration < 6, '1-5s (short)',
        duration < 30, '6-29s',
        duration < 120, '30-119s',
        duration < 300, '2-5min',
        '5min+'
    ) AS duration_bucket,
    count() AS calls,
    round(calls / sum(count()) OVER () * 100, 2) AS pct
FROM cdrs
WHERE timestamp > now() - INTERVAL 1 HOUR
  AND status = 'answered'
GROUP BY duration_bucket
ORDER BY duration_bucket
```

A sudden spike in very short calls (1-5 seconds) to international destinations is a classic fraud pattern — automated calls to premium-rate numbers that connect just long enough to incur charges.

🔧 **NOC Tip:** Set up a Grafana alert on this query pattern. If short-duration international calls exceed 2x the baseline, it could indicate an IRSF (International Revenue Share Fraud) attack — as discussed in Lesson 134.

## Approximate Functions: Speed Over Precision

When investigating, you often need quick answers rather than exact numbers. ClickHouse's approximate functions trade minor accuracy for major speed gains:

```sql
-- Exact unique count (slower)
SELECT uniqExact(source_number) AS exact_unique_callers FROM cdrs
WHERE timestamp > now() - INTERVAL 24 HOUR

-- Approximate unique count (~2% error, much faster on huge datasets)
SELECT uniq(source_number) AS approx_unique_callers FROM cdrs
WHERE timestamp > now() - INTERVAL 24 HOUR

-- Approximate quantiles (P50, P95, P99 latency)
SELECT
    quantile(0.50)(duration) AS p50_duration,
    quantile(0.95)(duration) AS p95_duration,
    quantile(0.99)(duration) AS p99_duration
FROM cdrs
WHERE timestamp > now() - INTERVAL 1 HOUR
  AND status = 'answered'
```

For dashboard panels showing "unique callers in last 24h" over a billion-row table, `uniq()` returns in milliseconds while `uniqExact()` might take seconds. A 2% error is irrelevant for monitoring.

## Materialized Views: Pre-Computed Dashboards

The most impactful optimization for NOC dashboards is materialized views. Instead of aggregating 100 million rows every time a dashboard refreshes, pre-compute the aggregations as data arrives:

```sql
-- Source table receives raw CDRs
CREATE TABLE cdrs_raw ( ... ) ENGINE = MergeTree() ...

-- Materialized view aggregates automatically on insert
CREATE MATERIALIZED VIEW cdrs_per_minute_mv
ENGINE = SummingMergeTree()
ORDER BY (minute, carrier, region)
AS SELECT
    toStartOfMinute(timestamp) AS minute,
    carrier,
    region,
    count() AS total_calls,
    countIf(status = 'answered') AS answered_calls,
    sum(duration) AS total_duration
FROM cdrs_raw
GROUP BY minute, carrier, region
```

Now querying `cdrs_per_minute_mv` is instant because it contains pre-aggregated data. Your dashboard showing "ASR by carrier per minute for the last 24 hours" reads thousands of rows from the materialized view instead of millions from the raw table.

🔧 **NOC Tip:** Build materialized views for every metric on your primary NOC dashboard. The raw table is for ad-hoc investigation; materialized views are for dashboards that refresh every 30 seconds.

## Sampling for Quick Investigation

When you need a quick estimate during an incident and can't wait for a full table scan:

```sql
-- Sample 10% of data for a quick estimate
SELECT
    carrier,
    count() * 10 AS estimated_calls  -- multiply by inverse of sample rate
FROM cdrs SAMPLE 0.1
WHERE timestamp > now() - INTERVAL 1 HOUR
GROUP BY carrier
ORDER BY estimated_calls DESC
```

The `SAMPLE` clause reads only a fraction of the data. For large tables, this returns in milliseconds with reasonable accuracy. Perfect for "is this carrier the problem?" quick checks.

## Grafana + ClickHouse Integration

The typical Grafana dashboard for NOC operations:

**Panel 1: Call Volume** — Time series of `count()` grouped by `toStartOfMinute(timestamp)`, with yesterday's data overlaid for comparison.

**Panel 2: ASR by Carrier** — Stacked time series showing each carrier's ASR trend, making drops immediately visible.

**Panel 3: Error Distribution** — Pie/bar chart of SIP error codes in the last 30 minutes.

**Panel 4: P95 Call Duration** — Time series of `quantile(0.95)(duration)` showing quality trends.

**Panel 5: Top Destinations** — Table showing top 20 destination prefixes by volume with ASR for each.

Each panel maps to one of the query patterns above. The key is using materialized views for panels that refresh frequently and raw tables for investigation panels.

### Grafana Variables for Dynamic Filtering

```sql
-- Variable: $carrier (dropdown)
SELECT DISTINCT carrier FROM cdrs WHERE timestamp > now() - INTERVAL 24 HOUR

-- Dashboard query using variable
SELECT toStartOfMinute(timestamp) AS time, count() AS calls
FROM cdrs
WHERE timestamp BETWEEN $__fromTime AND $__toTime
  AND carrier = '$carrier'
GROUP BY time ORDER BY time
```

Variables let NOC engineers filter dashboards interactively — selecting a specific carrier, region, or error code to drill into.

## Real Investigation Workflow

1. **Dashboard shows anomaly** — ASR dip on the overview panel
2. **Filter by time** — Narrow to the 15-minute window where it started
3. **Group by carrier** — Which carrier is affected?
4. **Group by error code** — What errors are occurring?
5. **Sample raw CDRs** — `SELECT * FROM cdrs WHERE carrier = 'X' AND timestamp > ... LIMIT 100` — look at individual calls
6. **Correlate with logs** — Use call_id from CDRs to search Graylog/Loki for SIP traces

This workflow — dashboard → aggregation → drill-down → raw data → logs — is the fundamental pattern for CDR-based investigation.

---

**Key Takeaways:**
1. Time-bucketing functions (`toStartOfMinute`, `toStartOfFiveMinutes`) are the foundation of NOC queries
2. ASR and NER by carrier is the single most important query for call quality monitoring
3. Approximate functions (`uniq`, `quantile`) provide speed gains that matter for dashboards
4. Materialized views pre-aggregate data for instant dashboard loading — build them for every primary metric
5. The investigation workflow is: dashboard anomaly → aggregate → drill-down → raw data → log correlation
6. Short-duration call pattern analysis helps detect fraud attacks early

**Next: Lesson 154 — Database Replication and Failover for NOC**
