# Lesson 97: Billing and Rating Systems — How Usage Becomes Revenue
**Module 2 | Section 2.13 — Business Systems**
**⏱ ~6min read | Prerequisites: None**
---

## Introduction

Every minute you talk on a Telnyx call, every SMS you send, every API request you make — all of it becomes a **Call Detail Record (CDR)** that flows through the billing pipeline to become an invoice. When billing breaks, customers get the wrong charges or don't get charged at all. Either way, it hurts Telnyx's revenue and reputation.

As a NOC engineer, you won't be calculating invoices, but you will be called when the billing pipeline fails. Pipeline outages can cause lost revenue, angry customers, or regulatory issues. This lesson explains how Telnyx turns network events into billing records, how the pipeline can fail, and what you need to monitor.

---

## The CDR Processing Pipeline

A **Call Detail Record (CDR)** is the atomic unit of billing data. It captures everything about a single billable event.

### What's in a CDR?

```json
{
  "cdr_id": "cdr-2026-02-23-abc123",
  "account_id": "acc-987654",
  "call_id": "uuid-a1b2-c3d4-e5f6",
  "direction": "outbound",
  "source_number": "+14155551234",
  "destination_number": "+14155555678",
  "start_time": "2026-02-23T10:15:00Z",
  "end_time": "2026-02-23T10:17:30Z",
  "duration_sec": 150,
  "region": "US",
  "carrier": "att",
  "status": "completed"
}
```

Every call, SMS, fax, and carrier lookup generates one or more CDRs.

### The Pipeline Flow

```
SIP/Media Servers      Rating Engine       Billing Aggregator       Invoicing System
       │                     │                      │                      │
       │  CDRs (raw)         │                      │                      │
       │  ──────────────►    │                      │                      │
       │                     │  (price lookup)      │                      │
       │                     │  ──────────────►     │                      │
       │                     │                      │  (monthly totals)    │
       │                     │                      │  ──────────────►     │
       │                     │                      │                      │
       ▼                     ▼                      ▼                      ▼
   Data Warehouse       Revenue Tracker      Customer Dashboard     Monthly Invoice
```

### Stages of CDR Processing

1. **Capture:** Telnyx's media servers, SBCs, and API gateways generate CDRs at call/SMS completion.
2. **Collection:** CDRs are queued in a message broker (Kafka) for processing.
3. **Rating:** The **rating engine** looks up pricing for each account and destination.
4. **Aggregation:** CDRs are grouped by account/time for invoice generation.
5. **Invoice Generation:** At month-end, aggregated usage becomes line items.

---

## The Rating Engine

The rating engine is where raw usage gets converted to **money**. It answers: "How much does this cost for this customer?"

### Rating Factors

- **Account tariff:** Each account has a pricing plan (per-minute rates, bundled minutes, flat fees).
- **Destination:** Calling New York vs. calling India have different rates.
- **Time of day:** Some tariffs have peak/off-peak pricing.
- **Route quality:** Premium carrier routes vs. cost-optimized routes may have different pricing.

### Rating Tables

```
Example tariff table for Account 12345:
  US Domestic:     $0.004/min (Tier 1 carrier)
  UK (Mobile):     $0.025/min
  India (Mobile):  $0.035/min
  SMS (Outbound):  $0.0075/SMS
  Number monthly:  $1.00/number
```

🔧 **NOC Tip:** When diagnosing billing issues, the first question is: "Did the CDR reach the rating engine?" Check the CDR processing lag metric. If lag is >1 hour, CDRs are backing up and revenue is at risk. If lag is normal but the amount looks wrong, it's likely a rating table issue — escalate to the billing team.

---

## Real-Time vs Batch Billing

### Real-Time Billing

For **prepaid accounts** and **cost controls**, usage must be rated in real-time to prevent overruns.

```plaintext
Call Start →  Check balance →  Allow call (if enough credit)
    │              │
    │              ▼
    │         Reserve funds
    │              │
    └──►  Call completes →  Finalize actual charge →  Release reserved funds
```

- Real-time rating adds 10–50 ms to call setup.
- If the rating API is down, prepaid calls cannot connect.

### Batch Billing

For postpaid accounts, CDRs are rated in batches:
- Collected throughout the day
- Rated in overnight jobs
- Appear in customer dashboards within 24 hours

🔧 **NOC Tip:** Real-time rating is a **critical path dependency**. If the rating API is slow or failing, prepaid calls fail to place. This is a revenue-blocking incident. Monitor the rating API latency and error rate with the same urgency as call control.

---

## Prepaid Balance Checks

Prepaid accounts must have sufficient balance before a call or SMS is allowed.

### Balance Check Flow

```
Outgoing Call Request
        │
        ▼
  ┌─────────────┐
  │  SBC/Media  │──► Query balance API
  └─────────────┐      (account_id, estimated_cost)
        │              │
        │              ▼
        │        ┌─────────┐
        │        │ Balance │──► [ Sufficient ] ──► Allow call
        │        │ Service │
        │        └────┬────┘
        │             │
        │             └─► [ Insufficient ] ──► Reject call (403)
        │
        ▼
   Reserve amount from balance
   (prevents race conditions with concurrent calls)
```

### Failure Modes

- **Balance API unavailable:** All prepaid calls fail. Escalate immediately.
- **Stale balance data:** Allows overdraft (customer goes negative).
- **Slow balance checks:** Call setup latency increases, triggering timeouts.

---

## Billing Failures and Customer Impact

When the billing pipeline fails, the impact depends on where the failure occurs:

| Failure Stage | Impact | Detection |
|---------------|--------|-----------|
| CDR not generated | Usage not recorded — **revenue loss** | Customer disputes, audit mismatch |
| CDR lost in queue | Delayed billing, potential data loss | CDR lag metric |
| Rating failure | CDRs pile up unrated | Rating queue depth |
| Aggregation stuck | Dashboards don't update, invoicing delayed | Aggregator lag |
| Invoice generation failed | Customers not billed — **revenue loss** | Invoice job alert |

🔧 **NOC Tip:** Billing pipeline issues are often discovered by customers before internal alerts. If a customer says "My dashboard hasn't updated since yesterday," check the CDR processing lag immediately. A 12-hour lag means 12 hours of usage hasn't been rated or charged. This is a P1 revenue incident.

---

## Monitoring Billing Pipeline Health

### Key Metrics

```promql
# CDR lag: time from event to CDR capture
cdr_capture_lag_seconds

# CDR queue depth: unprocessed records
cdr_queue_messages

# Rating lag: time from CDR creation to rating complete
rating_lag_seconds

# Rating queue depth
rating_queue_messages

# Balance API latency and error rate
balance_api_latency_p99
balance_api_error_rate

# Prepaid call rejection rate due to balance check failures
prepaid_call_reject_rate
```

### Key Alerts

```yaml
- alert: CDRProcessingLagHigh
  expr: cdr_capture_lag_seconds > 1800  # 30 minutes
  for: 5m
  labels:
    severity: critical
  annotations:
    summary: "CDR processing lag exceeds 30 minutes"
    
- alert: RatingQueueBacklog
  expr: rating_queue_messages > 100000
  for: 10m
  labels:
    severity: warning
  annotations:
    summary: "Rating queue has over 100k backlog"

- alert: BalanceAPIDown
  expr: rate(balance_api_requests_total{status=~"5.."}[1m]) > 0.1
  for: 1m
  labels:
    severity: critical
  annotations:
    summary: "Balance API error rate high — prepaid calls at risk"
```

### Dashboard Views

1. **Pipeline Overview:** Lag at each stage, throughput CDRs/sec
2. **Rating Performance:** Rate lookup latency, cache hit/miss
3. **Prepaid Health:** Balance check latency, rejection breakdown
4. **Revenue-at-Risk:** Estimated unbilled usage backlog

🔧 **NOC Tip:** Create a billing pipeline runbook with specific commands to check each stage. For example: `kafka-consumer-groups --describe --group cdr-rating` to see consumer lag. When the pipeline is backing up, know how to identify the bottleneck (capture, queue, rating, or aggregation).

---

## Data Warehouse and Audit

Processed CDRs flow to the data warehouse for:
- **Customer dashboards:** Real-time usage visualization
- **Invoice generation:** Monthly billing runs
- **Analytics:** Route optimization, carrier settlement
- **Regulatory:** Lawful intercept, communications records
- **Audit:** Revenue assurance, fraud detection

### Audit Trail

Every rated CDR is immutable and auditable:
- CDR ID enables tracing from source to rated record
- Rating decisions logged with tariff version and timestamp
- Adjustments (credits/refunds) create adjustment CDRs, never modify originals

---

## Key Takeaways

1. **CDRs are billing atoms:** Every billable event generates a CDR that flows through capture → queue → rating → aggregation → invoice.
2. **The rating engine** converts usage to money using account tariffs, destination rates, and routing data.
3. **Real-time billing** is critical for prepaid: if rating is down, prepaid calls cannot connect.
4. **Billable pipeline failures** have different impacts: CDR loss = revenue loss; rating backlog = delayed billing; aggregation stuck = stale dashboards.
5. **Monitor CDR lag and rating queue depth** — these are your early warning signals for billing pipeline health.
6. **Prepaid balance checks** are in the call control path: balance API latency affects call setup time; balance API failures block calls.
7. **Billing issues are often customer-discovered:** If a customer reports missing usage data, escalate immediately — it indicates pipeline breakage.

---

**Next: Lesson 88 — Regulatory Systems: STIR/SHAKEN, CNAM, and Compliance**
