# Lesson 119: Traces — Distributed Request Tracing

**Module 3 | Section 3.6 — Observability**
**⏱ ~6 min read | Prerequisites: Lessons 101, 102**

---

Metrics show you *that* a service is slow. Logs show you *what* the service logged. But when a request flows through ten different services — API gateway → auth service → rate limiter → SIP proxy → media server → billing → CDR generator — how do you find out which one is actually slow?

That's what distributed tracing solves. Traces follow a single request across service boundaries, showing you where time is spent and where errors occur.

## The Trace, Span, and Parent-Child Relationship

A **trace** represents one complete end-to-end request. It contains many **spans**, each representing one operation within that request.

A simple trace for an API call:

```
Trace: api-call-12345
├── Span 1: api-gateway (0ms - 150ms)
│   ├── Span 2: auth-service (10ms - 45ms)
│   ├── Span 3: rate-limiter (50ms - 52ms)
│   └── Span 4: sip-proxy (60ms - 140ms)
│       ├── Span 5: media-server (80ms - 100ms)
│       └── Span 6: billing-service (110ms - 130ms)
```

Each span records:
- **Name**: What operation was performed
- **Start/end time**: When it began and finished
- **Duration**: How long it took
- **Attributes**: Key-value pairs (service, method, status code, etc.)
- **Events**: Timestamps within the span (cache hit, DB query start, etc.)
- **Parent span ID**: Which span called this one (building the tree)

This structure lets you see that the overall request took 150ms, but the billing-service span (span 6) took 20ms while everything else was faster — implying the billing service contributed disproportionately.

## Trace ID Propagation

For traces to work across services, the **trace ID** must propagate from caller to callee. When Service A calls Service B, it includes the trace ID in the request.

HTTP propagation typically uses headers:
```
X-Trace-Id: abc123-def456
X-Span-Id: span-789
X-Parent-Span-Id: parent-456
```

In microservices, every outgoing request from a service must include the trace context. The receiving service extracts it and creates its own span as a child.

If propagation breaks — a service doesn't forward the headers — the trace splits. You see:
```
Trace: abc123 (first half, ends at service 3)
Trace: xyz789 (second half, starts at service 4)
```

No connection between them. During investigations, this makes it impossible to see the full request flow.

## Identifying Bottlenecks with Traces

The value of traces is **latency attribution**. Without traces, you see:

- API gateway latency: 500ms (slow!)
- Auth service latency: 50ms (fast)
- SIP proxy latency: 60ms (fast)
- Media server latency: 30ms (fast)

None of these explain the 500ms. But a trace reveals:

```
Trace: api-call-xyz
├── api-gateway: 500ms total
│   ├── auth-service: 50ms (10% of total)
│   ├── rate-limiter: 30ms
│   └── sip-proxy: 300ms (60% of total) ← Bottleneck!
│       ├── media-server: 30ms
│       └── billing-service: 400ms (this span extends beyond parent!)
```

The billing service took 400ms, but the SIP proxy only waited 300ms of that (100ms cut off by timeout). The trace makes it obvious: billing is the bottleneck.

## Error Tracing: Where Did It Fail?

When distributed systems fail, errors cascade. A database goes down, causing the billing service to fail, which causes the SIP proxy's billing check to fail, which causes the API gateway to return 503.

Traces show the error origin:

```
Trace: call-abc123 ── Error: true
├── api-gateway ── Status: 503
│   ├── auth-service ── OK
│   └── sip-proxy ── Failed
│       └── billing-service ── Error: connection refused to db:5432 ← Root cause!
```

The billing service couldn't reach its database. That's the root cause. Everything upstream is a symptom.

## Correlating Traces with Logs and Metrics

Traces become powerful when correlated with other telemetry:

**Trace to Logs**: Click a span in the trace viewer and "Jump to logs" shows you the log lines from that exact service during that exact time slice. No more guessing which logs align with which request.

**Trace to Metrics**: During high latency spikes in Grafana, click an exemplar trace to see a specific slow request's flow. The trace answers: was it slow everywhere, or was one service particularly slow?

**Logs to Trace**: Click a log line that says "Processing call abc123" and "View trace" opens the full distributed trace for that call.

This correlation is why modern observability stores traces, logs, and metrics with shared context (trace IDs, timestamps, service names).

## OpenTelemetry: The Standard

OpenTelemetry is the emerging standard for collecting traces, metrics, and logs. It provides:

- **SDKs** for instrumenting applications (Java, Go, Python, Node.js, etc.)
- **Collectors** for aggregating and forwarding telemetry
- **Standard format** so traces work across different backends (Jaeger, Zipkin, Tempo)

Before OpenTelemetry, each tracing tool had its own format. Jaeger used Thrift, Zipkin used JSON, proprietary APM tools used their own formats. OpenTelemetry unifies this.

🔧 **NOC Tip:** When traces are missing for a service, the first thing to check: is the service instrumented? Not all services emit traces. Check the service's telemetry documentation or ask the owning team. A service without instrumentation is a blind spot in your distributed traces.

## Reading Traces During Incidents

The workflow:

1. **Start from an alert**: Something is slow or failing
2. **Open traces**: Filter by trace tags (service=X, error=true)
3. **Find slow traces**: Sort by duration, pick one with high latency
4. **Walk the tree**: Find the span consuming disproportionate time
5. **Check attributes**: Look for specific errors, status codes, or timing breakdown
6. **Correlate to logs and metrics**: Click through to related telemetry

The goal is "root cause in 2 minutes." Without traces, it takes 15 minutes of checking each service's metrics and logs individually.

## Real-World Scenario

**Alert:** Webhook delivery latency >5 seconds (p99).

**Investigation:**

1. Open tracing dashboard, filter to webhook-service traces in the last 10 minutes
2. Sort by duration, pick a trace that took 8 seconds
3. The trace shows:
   ```
   webhook-service: 8000ms
   ├── validate-webhook: 50ms
   ├── lookup-customer-url: 200ms
   └── send-http-request: 7750ms ← 97% of total time!
       └── http-client: timeout=7700ms
   ```

4. Check the attributes on that span: `target_url: customer-webhooks.example.com`

5. Open a new browser tab, check that URL's latency from our datacenter

6. Customer's webhook endpoint is slow/unreachable — 7.7 seconds to timeout

7. **Root cause**: Customer's infrastructure is slow. **Mitigation**: Shorten our timeout, notify the customer.

Without traces, we would have guessed at every component in the webhook pipeline. With traces, the answer is visually obvious.

🔧 **NOC Tip:** Trace retention is typically shorter than log retention (hours to days, not weeks). During incidents, save interesting traces. Most trace UIs have "Share" or "Save Snapshot" functionality. A week later, when you're writing the post-mortem, the original trace may have aged out — but your snapshot remains.

## Limitations of Traces

Traces aren't magic:

- **Sampling**: High-traffic services can't trace every request. Typically 1% sampling or adaptive sampling (sample more errors, fewer successes). A specific request might be untraced.
- **Instrumentation gaps**: Services without OpenTelemetry emit no traces. You see the request enter a "black box" and exit, with no visibility inside.
- **Async flows**: When requests flow through message queues (Kafka, RabbitMQ), trace propagation requires the message to carry the trace context. If the consumer doesn't extract it, the trace breaks.
- **Tail sampling decisions**: Some traces are sampled after completion based on criteria (e.g., "only keep traces longer than 1 second"). Short traces may never be stored.

---

**Key Takeaways:**

1. A trace is an end-to-end request; spans are operations within that request with parent-child relationships
2. Trace ID propagation across services is essential — broken propagation creates orphaned trace fragments
3. Traces solve latency attribution: identifying which service in a chain is actually slow
4. Correlation between traces, logs, and metrics enables jumping between telemetry types for complete context
5. OpenTelemetry is the standard format for traces across different backends
6. High-traffic systems use sampling — not every request is traced, so a specific incident might lack a trace
7. Save interesting traces immediately — retention is shorter than logs

**Next: Lesson 104 — Grafana Dashboards — Reading and Building Queries**
