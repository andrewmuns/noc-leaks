# Lesson 121: Building Effective Grafana Queries for Incident Investigation

**Module 3 | Section 3.6 — Observability**
**⏱ ~8 min read | Prerequisites: Lesson 104**

---

Reading dashboards is reactive. Writing effective queries is proactive. During incidents, you'll build custom queries the existing dashboards aren't designed for: "What percentage of customer CUST-12345's calls failed?" "Which pods by AZ have the highest CPU throttling?" This lesson teaches the PromQL patterns that answer complex questions quickly.

## The Investigation Mindset: From Alert to Action

When an alert fires, you need answers in a specific order:

1. **What's affected?** → Find scope (services, datacenters, customers)
2. **How bad is it?** → Quantify impact (error rate, latency p99)
3. **When did it start?** → Correlate with changes
4. **What's the root cause?** → Drill down to specific component
5. **What's the fix?** → Identify corrective action

Each step requires different query patterns. Master these patterns and investigations happen in minutes, not hours.

## Pattern 1: Rate Calculations for Counters

Counters only increase. Raw counter values are meaningless. The fundamental pattern is `rate()` or `increase()`.

```promql
# Requests per second over 5 minutes
rate(http_requests_total[5m])

# Total requests in the last hour
increase(http_requests_total[1h])

# Error rate per second
rate(http_requests_total{status_code=~"5.."}[5m])
```

🔧 **NOC Tip:** Always use `rate()` with ranges of at least 4x the scrape interval. If Prometheus scrapes every 15 seconds, minimum meaningful range is 1m. Using `rate(metric[1s])` produces wildly wrong results. When in doubt, use 5m.

## Pattern 2: Error Rate as Percentage

Calculate what percentage of requests are errors:

```promql
# Method 1: Arithmetic division
sum(rate(http_requests_total{status_code=~"5.."}[5m]))
/
sum(rate(http_requests_total[5m]))

# Method 2: Using `on()` for different label sets
sum(rate(sip_requests_total{response_code=~"5..|6.."}[5m]))
/
sum(rate(sip_requests_total[5m]))
```

For dashboards, set the legend format to `{{status_code}}` so each line shows which error code.

## Pattern 3: Aggregation with `sum by()`

When you need to see patterns across dimensions:

```promql
# Error rate by datacenter
sum by (datacenter)(
  rate(sip_requests_total{response_code=~"5.."}[5m])
)

# CPU usage by pod
sum by (pod)(
  rate(container_cpu_usage_seconds_total[5m])
)

# Active calls by customer (identify heavy hitters)
sum by (customer_id)(active_calls)
```

🔧 **NOC Tip:** When investigating scope, use progressively narrower `sum by()` clauses. Start with `sum by (datacenter)` — is it affecting all DCs? Then `sum by (pod_name)` within the affected DC — which specific instances? This funnel approach isolates the problem component quickly.

## Pattern 4: Percentiles from Histograms

Histograms track distributions. Extract percentiles with `histogram_quantile()`:

```promql
# 99th percentile latency
histogram_quantile(
  0.99,
  sum by (le)(
    rate(request_duration_seconds_bucket[5m])
  )
)

# P95 and P50 (median) on same graph
histogram_quantile(0.95, sum by (le)(rate(request_duration_seconds_bucket[5m])))
histogram_quantile(0.50, sum by (le)(rate(request_duration_seconds_bucket[5m])))
```

**Important**: You must use `sum by (le)` — `le` is the "less than or equal" bucket boundary. `histogram_quantile()` needs the buckets to calculate percentiles.

## Pattern 5: Finding Top/Bottom N

Find outliers quickly:

```promql
# Top 10 customers by request rate
topk(10,
  sum by (customer_id)(rate(api_requests_total[5m]))
)

# Bottom 10 pods by free memory (likely OOM candidates)
bottomk(10,
  container_memory_available_bytes
  / container_memory_limit_bytes
)
```

`topk()` and `bottomk()` are instant queries — they show the current top/bottom values. For time series, they track items over time.

## Pattern 6: Comparing Current to Historical Baseline

Detect when current values deviate from normal:

```promql
# Current error rate vs 1 hour ago
(
  sum(rate(errors_total[5m]))
  -
  sum(rate(errors_total[5m] offset 1h))
)
/
sum(rate(errors_total[5m] offset 1h))

# Current 24h vs previous 24h (year-over-year style)
sum(increase(requests_total[24h]))
/
sum(increase(requests_total[24h] offset 1d))
```

The `offset` modifier shifts the time window back. `offset 1h` means "the value 1 hour ago."

## Pattern 7: Binary Operators for Filtering

Only show series where a condition is true:

```promql
# Only pods with >80% CPU usage(
  sum by (pod)(
    rate(container_cpu_usage_seconds_total[5m])
  )
  /
  sum by (pod)(
    kube_pod_container_resource_limits{resource="cpu"}
  )
) > 0.8

# Only customers with >1000 active calls
sum by (customer_id)(active_calls) > 1000
```

The comparison operator (`> 0.8`) acts as a filter — series that don't match become empty (no data point).

## Pattern 8: `absent()` for Missing Metrics

Detect when a metric disappears (service stopped reporting):

```promql
# Alert when a service stops sending heartbeats
absent(up{job="sip-proxy"})

# Becomes 1 if the metric is missing, absent if it exists
```

Useful for detecting total service outages where metrics stop flowing entirely.

## Pattern 9: Joining Different Metrics

Combine metrics with different labels:

```promql
# Error rate by service name (joining two metrics)
sum by (service)(
  rate(errors_total[5m])
)
/
sum by (service)(
  rate(requests_total[5m])
)
```

Using `on()` for same labels, `ignoring()` for different labels:

```promql
# Memory usage as percentage of request (ignoring different label sets)
(
  container_memory_working_set_bytes
  /
  container_spec_memory_limit_bytes
) * 100
```

## Pattern 10: Subqueries for Complex Analysis

Subqueries let you apply functions over the result of another query:

```promql
# Max error rate in the last hour for each service
max_over_time(
  (
    sum by (service)(rate(errors_total[5m]))
    /
    sum by (service)(rate(requests_total[5m]))
  )[1h:5m]
)

# Syntax: query[range:resolution]
# [1h:5m] = look back 1 hour, evaluate inner query every 5 minutes
```

Complex but powerful for detecting peaks over time windows.

## Real-World Investigation: Putting It Together

**Alert**: `HighLatencyWebhooks` — webhook delivery p95 >5s.

**Investigation queries:**

```promql
# Step 1: Which customers are affected?
# (Top 10 by current latency)
histogram_quantile(
  0.95,
  sum by (customer_id, le)(
    rate(webhook_duration_seconds_bucket[5m])
  )
)
# Result: CUST-ABC123 has p95 of 8.5s

# Step 2: When did it start?
# (Latency for that customer over time)
histogram_quantile(
  0.95,
  sum by (le)(
    rate(webhook_duration_seconds_bucket{customer_id="CUST-ABC123"}[5m])
  )
)
# Result: Spike at 14:15

# Step 3: Error rate for this customer?
(
  sum(rate(webhook_errors_total{customer_id="CUST-ABC123"}[5m]))
  /
  sum(rate(webhook_total{customer_id="CUST-ABC123"}[5m]))
)
# Result: 45% error rate!

# Step 4: What's the error type?
sum by (error_type)(
  rate(webhook_errors_total{customer_id="CUST-ABC123"}[5m])
)
# Result: "connection_timeout" is 98% of errors

# Step 5: Check customer webhook endpoint health
# (External check metric)
up{target="CUST-ABC123-webhook"}
# Result: 0 (down)
```

**Root cause**: CUST-ABC123's webhook endpoint is down/unreachable. Their webhooks are failing with connection timeouts, causing the latency spike (retries + timeouts).

**Action**: Contact customer, temporarily disable their webhooks, or increase timeout + reduce retry attempts to fail faster.

**Total time**: 4 minutes.

🔧 **NOC Tip:** Create a personal PromQL cheat sheet with your most-used patterns. During incidents, you don't have time to look up syntax. The patterns are: `rate()` for counters, `sum by()` for aggregation, `histogram_quantile()` for latency, `/` for percentages, and `topk()` for outliers. These 5 patterns solve 90% of investigation queries.

## Common Query Mistakes

**Mistake 1**: Using raw counters
```promql
# WRONG
sip_requests_total  # Shows ever-increasing number

# RIGHT
rate(sip_requests_total[5m])  # Shows requests per second
```

**Mistake 2**: Missing `sum by (le)` in histograms
```promql
# WRONG
histogram_quantile(0.95, rate(request_duration_bucket[5m]))

# RIGHT
histogram_quantile(0.95, sum by (le)(rate(request_duration_bucket[5m])))
```

**Mistake 3**: Multi-value variables without regex
```promql
# WRONG — fails if multiple datacenters selected
datacenter="$datacenter"

# RIGHT — works with multiple selections
datacenter=~"$datacenter"
```

**Mistake 4**: Unnecessary complex subqueries
```promql
# Overly complex
avg_over_time((max_over_time(rate(x[5m])[10m:]))[1h:])

# Simpler approach
avg_over_time(rate(x[5m])[1h:])
```

---

**Key Takeaways:**

1. Progress from broad aggregation by datacenter → narrow aggregation by pod to isolate the problem scope
2. `rate()` is required for counters; use minimum 4x scrape interval (typically 5m)
3. Error percentages require division; use `sum by ()` for consistent aggregation
4. `histogram_quantile()` needs `sum by (le)` — don't forget the `le` label
5. `topk()` and `bottomk()` find outliers quickly; combined with `sum by ()` identifies problematic instances
6. `offset` compares current values to historical baselines for anomaly detection
7. Build a personal PromQL cheat sheet — speed matters during investigations

**Next: Lesson 106 — Alerting Pipelines — From Metric to Engineer**
