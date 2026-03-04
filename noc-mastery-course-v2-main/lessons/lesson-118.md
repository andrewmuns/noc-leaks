# Lesson 118: Logs — Loki and Graylog

**Module 3 | Section 3.6 — Observability**
**⏱ ~8 min read | Prerequisites: Lesson 88**

---

Metrics tell you *that* something is wrong (error rate is 12%). Logs tell you *what* happened and *why* ("Database connection timeout after 5 attempts"). Telnyx uses two log aggregation systems: Loki for fast label-based filtering, and Graylog for full-text search with powerful query syntax. Understanding when to use each — and how to write effective queries — is essential for NOC investigations.

## Why Two Log Systems?

**Loki** is optimized for queries like "show me logs for this service in this time range." It uses labels (like Prometheus) for filtering, making it blazingly fast for structured queries. Loki integrates directly with Grafana — logs appear alongside metrics in the same dashboard.

**Graylog** is optimized for queries like "find all SIP messages where the Call-ID contains 'abc123'." It provides full-text search with Boolean operators, wildcards, and field-specific queries.

They're complementary. When you know which service is affected, use Loki. When you need to search by message content, use Graylog.

## Structured Logging: The Foundation

Neither Loki nor Graylog work effectively with unstructured log lines:

```
# BAD: Unstructured log - hard to query
2026-02-22 14:15:23 INFO sip-proxy Starting server on port 5060
```

This requires full-text search to find — slow and imprecise.

Structured logs use consistent JSON:

```json
{
  "timestamp": "2026-02-22T14:15:23Z",
  "level": "INFO",
  "service": "sip-proxy",
  "message": "Starting server",
  "port": 5060,
  "pod_name": "sip-proxy-7d4f8c-a3b4c",
  "datacenter": "chi"
}
```

This enables filtered queries: "show me INFO logs from sip-proxy in Chicago." Labels isolate the relevant data without scanning all logs.

🔧 **NOC Tip:** When writing queries, prefer structured fields over full-text search. `service="sip-proxy"` uses an indexed label and is instant. `message=~"sip-proxy"` scans all log content and is slow. Check your log format before querying — knowing available fields saves investigation time.

## Loki: The "Labels First" Approach

Loki is built on the same mental model as Prometheus. Instead of indexing log content, it only indexes labels. The logs themselves are stored compressed in tiers (hot/warm/cold).

This makes Loki extremely fast for label-based queries but slow for full-text search. Loki wins when you can filter by labels first.

### LogQL Basics

LogQL is Loki's query language:

```
# Select logs by label selector
{app="sip-proxy"}

# Multiple labels
{app="sip-proxy", namespace="voice-services", datacenter="chi"}

# Filter by log level after selection
{app="sip-proxy"} |= "ERROR"

# Extract and filter by JSON field
{app="sip-proxy"}
  | json
  | status_code >= 500

# Extract and aggregate
{app="sip-proxy"}
  | json
  | status_code = 503
  | count_over_time(5m)
```

The label selector `{app="sip-proxy"}` runs first and filters logs by labels (fast, indexed). Everything after the initial selector processes actual log content (slower).

### Understanding LogQL Operators

**Filter operators** (run after label selection):
- `|="error"` — log line contains substring
- `!="error"` — log line does NOT contain substring
- `|~"regex"` — log line matches regex
- `!~"regex"` — log line does NOT match regex

**Parser operators**:
- `| json` — parse JSON log, make fields available
- `| logfmt` — parse logfmt (key=value pairs)
- `| pattern` — parse with pattern template

**Aggregation operators**:
- `| count_over_time(1m)` — count logs per time bucket
- `| rate(1m)` — rate of log lines per second
- `| sum_over_time(1m)` — sum extracted values

## Graylog: Full-Text Power

Graylog uses Elasticsearch under the hood for full-text indexing. It's slower than Loki for label queries but far more flexible for content search.

### Graylog Query Syntax

```
# Simple full-text search
sip-proxy

# Field search
type:SIP AND source_ip:10.0.1.5

# Range queries
response_code:[500 TO 599]
timestamp:["2026-02-22 14:00:00" TO "2026-02-22 14:05:00"]

# Boolean operators
type:SIP AND (response_code:503 OR response_code:504)
type:SIP AND NOT response_code:200

# Wildcards
call_id:abc123*

# Phrase search
"Internal Server Error"

# Exists check
exists:source_ip

# Regular expressions
message:/INVITE sip:.*@telnyx\.com/
```

### Log Streams: Pre-Filtered Views

Graylog "streams" continuously filter incoming logs into buckets:

- **SIP Messages**: `type:SIP`
- **Error Logs**: `level:ERROR`  
- **Security Events**: `type:SECURITY`
- **Voice Quality**: `type:RTP`

Pre-configured streams let you jump directly to relevant logs. During a voice quality incident, open the **Voice Quality** stream instead of searching all logs.

## When to Use Each System

| Scenario | Use | Why |
|----------|-----|-----|
| "Show me logs from sip-proxy in the last hour" | Loki | Label-based, Grafana integrated |
| "Find SIP messages with Call-ID abc123" | Graylog | Full-text search on arbitrary content |
| "Count ERROR logs per pod" | Loki | Fast aggregation with labels |
| "Search for 504 errors in the last 24 hours" | Graylog | Full-text search across long time ranges |
| "Correlate metrics and logs" | Loki | Grafana displays both together |
| "Find all INVITE messages to +1-555*" | Graylog | Wildcard matching on message content |

## Real-World Troubleshooting Scenario

**Alert:** Increased 503 errors on the billing service API.

**Investigation:**

Step 1: Check Loki for billing service errors
```logql
{app="billing-api", namespace="billing"}
  | json
  | status_code = 503
```

Step 2: Add time range, group by error message
```logql
{app="billing-api", namespace="billing"}
  | json
  | status_code = 503
  | line_format "{{.message}}"
  | count_over_time(5m) by (message)
```

Step 3: The error count spike correlates with a timestamp. Open that time range in Graylog for deeper investigation:
```
service:billing-api AND message:"connection pool" AND timestamp:["2026-02-22 14:00" TO "2026-02-22 14:05"]
```

Step 4: Find the root cause in Graylog:
```
2026-02-22 14:02:15 ERROR billing-api connection pool exhausted: max 100 connections, 100 in use
2026-02-22 14:02:15 ERROR billing-api cannot acquire connection for query SELECT * FROM bills WHERE...
```

Root cause: Database connection pool exhaustion. The billing service ran out of database connections, causing all requests to fail with 503s.

🔧 **NOC Tip:** Create Loki queries in Grafana dashboards for common patterns: "ERROR logs by service", "Status code distribution", "Latency by endpoint". During incidents, open the dashboard instead of writing queries from scratch. The dashboard already has the right labels and filters — just add the time range.

## Log Retention and Storage

Both systems require retention planning:

**Loki**: Often configured for tiered retention — hot (SSD, 7 days), warm (SSD, 30 days), cold (S3, 1+ year). Queries beyond retention show empty results.

**Graylog**: Elasticsearch index retention — indices older than N days are deleted or archived. Graylog typically has shorter retention (7-30 days) than Loki (30-90 days).

For long-term compliance or forensics, logs should ship to cold storage (S3) with tools like Fluentd or Logstash.

🔧 **NOC Tip:** If you can't find logs you expect, check retention. Loki and Graylog don't warn you — queries for times beyond retention just return empty. Know your retention policies: Loki typically has longer retention than Graylog for cost reasons.

---

**Key Takeaways:**

1. Loki is label-based (like Prometheus) — fast for filtering by service, pod, datacenter; slow for full-text search
2. Graylog is full-text (Elasticsearch-based) — powerful for searching message content, SIP headers, wildcards
3. Structured logging (JSON) enables fast label filtering; unstructured logs require slow full-text search
4. Use Loki when you know which service is affected; use Graylog when you need to search by arbitrary content
5. LogQL filters: `|="text"` contains, `|~"regex"` matches, `| json` parses JSON fields
6. Graylog streams provide pre-filtered views for common scenarios — use them instead of raw searches
7. Log retention varies by system — query empty results might mean logs aged out, not that they never existed

**Next: Lesson 103 — Traces — Distributed Request Tracing**
