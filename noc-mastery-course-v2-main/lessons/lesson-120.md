# Lesson 120: Grafana Dashboards — Reading and Building Queries

**Module 3 | Section 3.6 — Observability**
**⏱ ~9 min read | Prerequisites: Lessons 101, 102**

---

Grafana is more than a tool — it's the primary interface between NOC engineers and the system's health. Every alert leads to a dashboard. Every investigation starts with graphs. Understanding how to read dashboards effectively and build useful queries transforms you from a consumer of metrics into an investigator with insight.

## Dashboard Anatomy: Panels, Rows, and Variables

A Grafana dashboard is a collection of **panels** (visualizations) organized into **rows**. Understanding the structure helps you navigate quickly.

**Panels** show data:
- Graph panels: Time series (metrics over time)
- Stat panels: Single values with thresholds (red/yellow/green)
- Table panels: Lists of values with sortable columns
- Log panels: Side-by-side log lines
- Gauge panels: Circular indicators like speedometers

**Rows** group related panels:
```
Row 1: "SIP Trunk Overview"
  ├─ Panel: CPS (Calling rate)
  ├─ Panel: Active calls
  └─ Panel: ASR (Answer seizure ratio)

Row 2: "Error Details"
  ├─ Panel: 5xx errors by response code
  └─ Panel: Error rate percentage
```

Collapsing rows lets you focus. Starting with SIP Trunk Overview — expanded — and keeping Error Details collapsed until needed.

**Variables** allow dynamic filtering:
- `$datacenter` → dropdown: chi, dal, nyc
- `$namespace` → dropdown: voice-services, messaging, billing
- `$service` → dropdown: sip-proxy, media-server

Selecting variables updates all panels simultaneously. During an incident: select the datacenter where the alert fired, and every panel filters accordingly.

🔧 **NOC Tip:** Bookmark dashboards with pre-selected variables. Instead of opening "Service Health" and then selecting datacenter=chi, namespace=voice-services, service=sip-proxy — bookmark `https://grafana/d/service-health?var-datacenter=chi&var-namespace=voice-services`. One click and you're viewing the right filtered view.

## Reading Dashboards Effectively

Don't just look at the graphs — read them systematically:

### Step 1: Set the time range
Individual alert firing time vs. wider context:
- Last 5 minutes: See the immediate issue
- Last 1 hour: See when it started, check for gradual buildup
- Last 24 hours: See daily patterns, verify this isn't "normal Tuesday morning"
- Last 7 days: See if this correlates with a weekly pattern or deployment

### Step 2: Look for correlations
Multiple panels changing together suggests a common cause:
- CPU ↑ at same time as error rate ↑ → resource exhaustion
- Latency ↑ before error rate ↑ → service degrading then failing
- All datacenters affected → global issue (upstream dependency)
- Single datacenter affected → regional issue (network, infrastructure)

### Step 3: Follow the drill-down path
Well-designed dashboards link panels to more detailed dashboards:
```
Service Overview
  ↓ click "SIP Errors" panel
SIP Error Details
  ↓ click "503 Errors" series
503 Error Breakdown by Pod
  ↓ click specific pod
Pod Logs in Loki
```

Follow the trail from high-level overview to specific evidence.

## PromQL in Grafana

Grafana panels display PromQL queries. Understanding common patterns helps you read and modify panels.

### The Basic Query Structure

```promql
# Simple metric
sip_requests_total

# Filtered by labels
sip_requests_total{status_code="200", datacenter="chi"}

# Rate over time
rate(sip_requests_total[5m])

# Aggregated by label
sum by (status_code)(rate(sip_requests_total[5m]))
```

### Dashboard Variables in Queries

```promql
# Use $variable syntax
rate(sip_requests_total{datacenter="$datacenter"}[5m])

# Multi-value variables use regex matching
rate(sip_requests_total{datacenter=~"$datacenter"}[5m])

# All option
rate(sip_requests_total{datacenter=~"$datacenter|.+"}[5m])
```

The variable `$datacenter` is replaced by whatever you've selected in the dropdown.

### Common Query Patterns

**Error rate as percentage:**
```promql
sum(rate(http_requests_total{status_code=~"5.."}[5m]))
/
sum(rate(http_requests_total[5m]))
```

**Rate per instance:**
```promql
sum by (instance)(rate(sip_requests_total[5m]))
```

**Top N consumers:**
```promql
topk(10, sum by (customer_id)(rate(sip_requests_total[5m])))
```

**Heatmap for latency:**
```promql
histogram_quantile(
  0.95,
  sum by (le)(
    rate(sip_request_duration_seconds_bucket[5m])
  )
)
```

## Log Panels with LogQL

Grafana integrates Loki logs directly:

```logql
# Simple log query
{app="sip-proxy", namespace="voice-services"}

# With level filter
{app="sip-proxy"} |= "ERROR"

# Parsed and filtered
{app="sip-proxy"}
  | json
  | status_code >= 500
```

Log panels next to metrics panels show causes for symptoms. If a graph shows error spike at 14:30, the adjacent log panel automatically shows logs from 14:30.

## Annotations: Marking Events on Timelines

Dashboards support annotations — vertical lines marking specific events:

- **Deployments**: ArgoCD sync events
- **Incidents**: PagerDuty alert start/end
- **Manual changes**: Maintenance windows, config changes
- **External events**: Datacenter incidents, upstream issues

Annotations visually correlate changes with problems. If the error rate spikes 3 minutes after a deployment annotation, you found the cause.

🔧 **NOC Tip:** Create a "Deployments" annotation query on every service dashboard. It overlays the exact timestamp when new code deployed. When investigating sudden metric changes, look for nearby deployment lines first — it's the most common cause of metric shifts.

## Building Your First Query

During an investigation, the built-in queries might not answer your question. Build your own:

**Scenario**: "We suspect a specific customer is causing traffic spikes." The dashboard shows aggregate traffic, not per-customer.

**Build the query:**
```promql
# Step 1: Find the right metric
# Looking at existing panels, they use sip_requests_total

# Step 2: Add your dimension
# Does the metric have customer_id? Check with autocomplete.
rate(sip_requests_total{customer_id="CUST-12345"}[5m])

# Step 3: Explore what values exist
# Add a query with label_values
topk(10, sum by (customer_id)(rate(sip_requests_total[5m])))

# Step 4: Focus on specific customer
rate(sip_requests_total{customer_id=~"CUST.*"}[5m])
```

Pro tip: Use the Explore view (the compass icon) to iterate on queries before adding them to dashboards.

## Dashboard Variables: Creating Dynamic Filters

Adding variables makes dashboards truly useful:

1. **Settings → Variables → New**
2. **Query variable**: Uses a PromQL query to populate options
   ```
   # Query to get all datacenters
   label_values(sip_requests_total, datacenter)
   ```
3. **Custom variable**: Manual list for fixed options
4. **Text box**: Free-form input (e.g., customer ID)

Enabling **Multi-value** lets you select multiple options. **Include All option** selects everything (useful for "everything except...").

## Real-World Investigation

**Alert**: Call setup latency p95 >2 seconds.

**Dashboard workflow:**

1. Open "Voice Service Health" dashboard
2. Select `$namespace=voice-services`, `$datacenter=chi` (where alert fired)
   - All 12 panels update to Chicago

3. Look at "Latency Over Time" panel:
   - Spike starting at 14:15
   - Was flat at ~200ms before

4. Look at "Latency by Service" panel:
   - `api-gateway`: ~50ms (fast, not the problem)
   - `sip-proxy`: ~50ms
   - `billing-service`: 1800ms ←←← The spike

5. Notice deployment annotation at 14:12
   - ArgoCD synced `billing-service` at 14:12
   - Latency spike at 14:15

6. Correlation established. Billing service deployment → latency spike.

7. Open ArgoCD, rollback `billing-service` to previous version.

**Time to root cause**: 3 minutes. Without the dashboard variables and annotations, this would take 15+ minutes of manual queries.

🔧 **NOC Tip:** Build muscle memory for reading latency graphs. A single-spike pattern (|/) suggests a burst traffic event. A stair-step pattern (━━/\) suggests gradual degradation then failure. A sawtooth pattern (╱╲╱╲) suggests garbage collection pauses or periodic batch jobs. Recognizing these patterns by sight gives you instant hypotheses.

---

**Key Takeaways:**

1. Dashboards consist of panels (visualizations), rows (groupings), and variables (dynamic filters)
2. Bookmark dashboards with pre-selected variables for one-click filtered views
3. During investigations: set appropriate time range, look for correlations across panels, follow drill-down paths
4. Annotations mark deployments and incidents — always check for correlation between annotations and metric changes
5. Build custom queries in Explore view first, then add to dashboards
6. Variables populated by PromQL queries (`label_values()`) keep dropdowns synchronized with reality
7. Latency pattern recognition (spike, stair-step, sawtooth) gives instant diagnostic clues

**Next: Lesson 105 — Building Effective Grafana Queries for Incident Investigation**
