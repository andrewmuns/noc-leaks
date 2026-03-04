# Lesson 117: Metrics — Prometheus and Time-Series Data

**Module 3 | Section 3.6 — Observability**
**⏱ ~8 min read | Prerequisites: Lesson 87**

---

Metrics are numbers over time. CPU usage at 14:00 was 45%, at 14:01 it was 72%, at 14:02 it was 68%. This time-series data is the foundation of monitoring — without it, you're flying blind. Prometheus is the metrics engine that powers Telnyx's observability, and understanding its data model and query language (PromQL) is essential for every NOC engineer.

## The Time-Series Data Model

Every Prometheus metric is a time series identified by:

```
metric_name{label1="value1", label2="value2"} value timestamp
```

For example:
```
sip_requests_total{method="INVITE", response_code="200", datacenter="chi"} 1547823 1708617600
```

This says: "The total count of SIP INVITE requests with 200 response code in the Chicago datacenter is 1,547,823 at this timestamp."

**Metric name**: What's being measured (`sip_requests_total`)
**Labels**: Dimensions for filtering and grouping (`method`, `response_code`, `datacenter`)
**Value**: The current measurement (1547823)
**Timestamp**: When it was recorded

Labels are powerful — they turn one metric into many time series. `sip_requests_total` with labels for method, response code, and datacenter generates hundreds of distinct time series, each independently queryable.

## Metric Types

Prometheus defines four metric types, and understanding them is critical for writing correct queries:

### Counter
A counter only goes up (or resets to zero on restart). Examples: total requests served, total errors, total bytes transferred.

```
sip_requests_total{method="INVITE"} → 1000, 1050, 1100, 1150...
```

**Never** display a raw counter on a dashboard — the value "1,547,823 total requests" isn't useful. Instead, use `rate()` to compute the per-second rate of increase:

```promql
rate(sip_requests_total{method="INVITE"}[5m])
# → 10.5 requests per second (averaged over 5 minutes)
```

### Gauge
A gauge can go up or down. Examples: current CPU usage, active call count, queue depth, temperature.

```
active_calls{datacenter="chi"} → 5000, 5200, 4800, 5100...
```

Gauges are displayed directly — the current value is meaningful.

### Histogram
A histogram tracks the distribution of values (like request latency) by counting observations in configurable buckets:

```
sip_request_duration_seconds_bucket{le="0.1"} 8500   # 8500 requests took ≤100ms
sip_request_duration_seconds_bucket{le="0.5"} 9200   # 9200 requests took ≤500ms
sip_request_duration_seconds_bucket{le="1.0"} 9800   # 9800 requests took ≤1s
sip_request_duration_seconds_bucket{le="+Inf"} 10000 # 10000 total requests
```

Use `histogram_quantile()` to extract percentiles:
```promql
histogram_quantile(0.99, rate(sip_request_duration_seconds_bucket[5m]))
# → 0.82 (the 99th percentile latency is 820ms)
```

### Summary
Similar to histogram but calculates quantiles on the client side. Less commonly used because quantiles can't be aggregated across instances.

## The Prometheus Pull Model

Unlike traditional monitoring (where agents push metrics to a server), Prometheus **pulls** metrics from targets by scraping HTTP endpoints.

Every instrumented service exposes a `/metrics` endpoint:

```
$ curl http://sip-proxy:9090/metrics

# HELP sip_requests_total Total SIP requests processed
# TYPE sip_requests_total counter
sip_requests_total{method="INVITE",code="200"} 45231
sip_requests_total{method="INVITE",code="486"} 1023
sip_requests_total{method="REGISTER",code="200"} 89412

# HELP active_calls Current number of active calls
# TYPE active_calls gauge
active_calls 5247
```

Prometheus scrapes this endpoint every 15-30 seconds (configurable) and stores the results.

**Why pull?** If a target goes down, Prometheus detects it immediately (scrape fails). With push, you can't distinguish between "the service is down" and "the service is fine but the network is partitioned."

🔧 **NOC Tip:** When metrics suddenly stop updating for a service in Grafana, check if Prometheus can scrape the target. In the Prometheus UI (typically port 9090), go to Status → Targets. If the target shows "DOWN" with a "connection refused" error, the service or its metrics endpoint is down. If the target shows "UP" but metrics seem stale, the application might have stopped updating its metrics (frozen process, deadlock).

## Essential PromQL

PromQL is Prometheus's query language. Master these patterns:

### rate() — Convert counter to per-second rate
```promql
rate(sip_requests_total[5m])
```
The `[5m]` is the lookback window — it averages the rate over 5 minutes, smoothing out spikes. Shorter windows (1m) are noisier but more responsive.

### sum() — Aggregate across labels
```promql
sum(rate(sip_requests_total[5m]))  # Total request rate across all labels
sum by (method)(rate(sip_requests_total[5m]))  # Rate per SIP method
sum by (datacenter)(active_calls)  # Active calls per datacenter
```

### increase() — Total increase over a period
```promql
increase(sip_errors_total[1h])  # How many errors in the last hour
```

### histogram_quantile() — Percentile from histograms
```promql
histogram_quantile(0.95, sum by (le)(rate(request_duration_seconds_bucket[5m])))
# 95th percentile request duration
```

### topk() — Find the top N
```promql
topk(10, sum by (customer_id)(rate(sip_requests_total[5m])))
# Top 10 customers by request rate
```

### Comparison and filtering
```promql
# Only show when error rate exceeds 5%
sum(rate(sip_requests_total{code=~"5.."}[5m])) / sum(rate(sip_requests_total[5m])) > 0.05
```

## Metric Naming Conventions

Good naming makes metrics discoverable:

- **Counter**: `_total` suffix → `http_requests_total`
- **Histogram**: `_seconds`, `_bytes` suffixes → `request_duration_seconds`
- **Gauge**: No special suffix → `active_calls`, `cpu_usage_percent`
- **Units in name**: `_seconds`, `_bytes`, `_celsius` (avoid ambiguity)

## Real-World Troubleshooting with PromQL

**Scenario:** Alert fires for high SIP error rate. You need to understand what's failing.

```promql
# Step 1: Overall error rate
sum(rate(sip_requests_total{code=~"[45].."}[5m])) / sum(rate(sip_requests_total[5m]))
# → 0.08 (8% error rate)

# Step 2: Break down by response code
sum by (code)(rate(sip_requests_total{code=~"[45].."}[5m]))
# → 503: 120/s, 408: 30/s, 486: 15/s

# Step 3: Which datacenter?
sum by (datacenter, code)(rate(sip_requests_total{code="503"}[5m]))
# → chi: 115/s, dal: 5/s  — Chicago is the problem

# Step 4: Which service instance?
sum by (instance)(rate(sip_requests_total{code="503", datacenter="chi"}[5m]))
# → sip-proxy-03: 110/s, others: ~1/s  — one instance
```

In four queries, you've gone from "high error rate" to "sip-proxy-03 in Chicago is returning 503s." Time: under 60 seconds.

🔧 **NOC Tip:** Build a mental library of these PromQL patterns. During incidents, you don't have time to look up syntax. Practice writing these queries during calm periods so they're automatic during emergencies.

---

**Key Takeaways:**

1. Prometheus metrics are time series with names, labels, values, and timestamps — labels enable multi-dimensional filtering
2. Four metric types: counters (always up, use `rate()`), gauges (current value), histograms (distributions), summaries (client-side quantiles)
3. Prometheus pulls metrics by scraping `/metrics` endpoints — check Targets page when metrics stop updating
4. `rate()` converts counters to per-second rates; never display raw counters
5. `sum by (label)` is the primary aggregation tool — break down errors by code, datacenter, or instance
6. `histogram_quantile()` extracts percentiles from histograms — essential for latency monitoring

**Next: Lesson 102 — Logs — Loki and Graylog**
