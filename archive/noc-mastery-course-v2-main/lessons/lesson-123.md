# Lesson 123: Writing and Tuning Alert Rules

**Module 3 | Section 3.7 — Alerting**
**⏱ ~6 min read | Prerequisites: Lesson 106**

---

Every alert should be actionable. Every alert should matter. This sounds obvious, yet most production alerting systems are polluted with alerts that don't meet either criterion. This lesson teaches how to write alerts that actually help during incidents and how to tune existing alerts to reduce noise without sacrificing coverage.

## The Anatomy of a Good Alert

A good alert has five properties:

### 1. Actionable
The receiver can do something about it. "Customer ABC experiencing 50% error rate" is actionable — you can investigate, contact the customer, or shift traffic. "Disk will be full in 90 days based on current growth rate" is not actionable — it's too far in the future.

### 2. Relevant
The alert should be sent to the right people. A voice infrastructure alert goes to the voice team, not the messaging team. A customer-specific issue goes to the account manager, not the infrastructure on-call.

### 3. Timely
The alert fires early enough to prevent impact (if possible), or early enough to minimize impact (if not). "Database is down" is not timely — the impact already happened. "Database connection failures increasing" is timely — it predicts the problem.

Bad example: `disk_usage > 95%`
Good example: `predict_linear(disk_usage[6h], 4*3600) > 90%` — predict if disk will be full in 4 hours

### 4. Specific
The alert indicates exactly what's wrong and where. "High latency" is vague. "SIP proxy latency p95 >500ms in Chicago DC" is specific.

### 5. Attributable
Someone needs to own the response and resolution. If an alert has no clear owner, it won't be handled.

## Writing Alert Expressions

### The Syndrome vs. The Cause

**Symptom-based alerts** detect user-visible problems:
```yaml
# User can't make calls → direct impact
- alert: CallsFailing
  expr: rate(sip_invites_total{response_code!="200"}[5m]) 
        / rate(sip_invites_total[5m]) > 0.10
  for: 2m
```

**Cause-based alerts** detect problems that will become visible:
```yaml
# Database connection pool filling → will cause call failures
- alert: DatabaseConnectionPoolHigh
  expr: database_connections_active / database_connections_max > 0.8
  for: 5m
```

You need both. Symptom alerts catch problems that slipped through. Cause alerts prevent problems if caught and fixed early. But cause alerts are higher noise — you might fill a connection pool and it recovers naturally.

🔧 **NOC Tip:** Prioritize symptom-based alerts for paging. A call-failure alert (symptom) always pages — customers are actively impacted. A database pool alert (cause) might page during business hours or create a ticket — it's a warning. During an incident, symptom alerts are what customers see; cause alerts are what you check while mitigating.

### Using `for:` Effectively

The duration balances sensitivity against noise:

```yaml
# Too sensitive - fires on every brief spike
for: 0m  

# Good for symptoms - customers impacted long enough to notice
for: 2m

# Good for causes - sustained problem not self-healing
for: 10m

# For trends - building up over time
for: 30m
```

Think about the user impact duration. If customers can't make calls for 30 seconds, most won't notice. But if calls fail for 2+ minutes, that's a noticeable outage. Set `for:` to the threshold where impact becomes significant.

### Multi-Condition Alerts

Single-metric alerts can be noisy. Combine conditions for higher confidence:

```yaml
# Error rate is high AND volume is significant
# (Avoids alerting on 1 error out of 2 requests)
expr: |
  (
    rate(errors_total[5m])
    /
    rate(requests_total[5m])
  ) > 0.10
  AND
  rate(requests_total[5m]) > 100
```

This says "only alert if error rate >10% AND we're processing >100 requests per second." Low-traffic services with 1 error won't trigger false alarms.

## Severity Levels

Define what each severity means for your organization:

### Critical (Page Immediately)
Customer-impacting, revenue-affecting, or safety-related. Wake up the on-call immediately.

Examples:
- Call failure rate >5%
- Complete datacenter unreachable
- Major customer can't use service
- Security incident (unauthorized access, data breach)

### Warning (Page During Business Hours)
Problems that should be addressed but aren't immediately customer-impacting, or isolated to a small subset.

Examples:
- Single service degraded but failover working
- Disk usage >80% (will become critical in days)
- Single node down in a cluster
- Elevated latency but acceptable

### Info (Create Ticket)
Trends or observations that don't require immediate action but should be reviewed.

Examples:
- Error rate elevated but within SLA
- Resource usage trending up
- Unusual traffic pattern detected

🔧 **NOC Tip:** Be paranoid about critical alerts. If an alert is waking people at 3 AM, it must represent real customer impact. If it's not customer-impacting, drop it to warning. Engineers who repeatedly get paged for non-issues will stop responding promptly to all alerts, including real emergencies.

## Tuning Existing Alerts

### The Alert Review Process

Review alerts monthly:

1. **Alert reporting**: List every alert that fired and its outcome
   - True positive (real problem, action taken): Keep
   - False positive (no problem, or problem didn't match): Tune or remove
   - True negative (alert should have fired but didn't): Tune for sensitivity
   - Actionable but not addressed: Escalate or tune threshold

2. **Threshold review**: Did the alert fire too early? Too late?
   - Compare alert time to when customer impact started
   - Ideal: alert fires 2-5 minutes before significant impact

3. **Response review**: What did recipient do?
   - If answer is "acknowledged and did nothing": Alert not actionable
   - If action was automation candidate: Build it
   - If response was escalate: Tune routing or description

### Common Tune Patterns

**Problem**: Alert fires on brief spikes
```yaml
# Before
for: 0m

# After  
for: 5m
```

**Problem**: Alert fires on low-traffic events
```yaml
# Before
expr: rate(errors_total[5m]) > 10

# After - add minimum volume check
expr: |
  rate(errors_total[5m]) > 10 
  AND rate(requests_total[5m]) > 100
```

**Problem**: Alert fires at predictable times
```yaml
# Before
expr: rate(batch_jobs_failed[5m]) > 0
# Fires every night during batch window

# After - exclude known maintenance window
expr: |
  rate(batch_jobs_failed[5m]) > 0
  AND ON() hour() < 2 OR hour() > 4
# Only alert outside 2-4 AM batch window
```

**Problem**: Alert description doesn't help
```yaml
# Before
annotations:
  summary: "High error rate"

# After
annotations:
  summary: "{{ $labels.service }} error rate {{ $value | humanizePercentage }} in {{ $labels.datacenter }}"
  description: "Error rate for {{ $labels.service }} has exceeded 10% for 5+ minutes. Likely causes: upstream dependency failure, database connectivity issue, or traffic spike. Check runbook: https://runbook/{{ $labels.service }}-errors"
  dashboard: "https://grafana/d/{{ $labels.service }}-health?var-datacenter={{ $labels.datacenter }}"
```

## Alert Suppression During Maintenance

Planned maintenance should suppress related alerts:

```yaml
# In Alertmanager configuration
route:
  routes:
    # Main route
    - match_re:
        alertname: .+
      receiver: default
      continue: true
      
      # Sub-route for maintenance windows
      routes:
        - match:
            severity: warning
          receiver: maintenance-silence
          matchers:
            - maintenance="true"
```

Or use time-based silencing in Alertmanager:
```yaml
# Silence alerts during scheduled maintenance
silences:
  - matchers:
      - alertname =~ "Kube.*"
    target_matchers:
      datacenter: chi
    start_time: 2026-02-25T02:00:00Z
    end_time: 2026-02-25T04:00:00Z
    comment: "Scheduled maintenance window"
```

🔧 **NOC Tip:** During maintenance windows, the on-call engineer should not be distracted by expected disruption. All alerts related to the maintenance ("Pod restarted", "Node offline", "Service unavailable") should be silenced 30 minutes before the maintenance starts and unsilenced 30 minutes after. This prevents alert fatigue and ensures real problems aren't buried in noise.

## Every Alert Needs a Runbook

Every alert should have a `runbook_url` label that points to "what to do." The runbook should include:

1. **What this alert means**: The underlying failure mode
2. **How to verify**: Commands or dashboards to confirm
3. **Common causes**: Top 3-5 reasons this fires
4. **Investigation steps**: Systematic debugging approach
5. **Mitigation**: Emergency actions to reduce impact
6. **Resolution**: How to fix the root cause
7. **Escalation**: When to involve others
8. **Post-resolution**: Any follow-up actions

If a year-old runbook never mentions a cause that actually happened, update it with new learnings.

## Real-World Scenario

**Problem**: The `SIPProxyHighCPU` alert fires twice daily at around 2 AM, but CPU usage is normal 99% of the time. The on-call engineer checks, acks, and does nothing.

**Investigation:**
- Review alert history: fires ~02:00-02:30 daily
- Check metrics at that time: nightly backup job runs, causes CPU spike
- Backup job completes in 20 minutes, CPU returns to normal

**Solutions:**
1. Add time-based exemption: exclude 02:00-02:30 window
2. Or increase threshold since brief spikes are expected
3. Or change from `for: 1m` to `for: 10m` — sustained high CPU only

Chose option 3: `for: 10m`

**Result**: Alert now only fires if CPU stays elevated for 10+ minutes. Brief backup spikes don't wake anyone. Real CPU problems (stuck process, traffic surge) still alert.

---

**Key Takeaways:**

1. Good alerts are actionable, relevant, timely, specific, and attributable
2. Symptom alerts (user impact) page immediately; cause alerts (pre-failure) may create tickets
3. Use `for` duration to balance sensitivity: 2m for symptoms, 5-10m for causes, 30m for trends
4. Add volume checks to prevent low-traffic false positives
5. Review alerts monthly: true positive rate, time-to-impact, response actions taken
6. Silence alerts during planned maintenance — expected disruption shouldn't wake anyone
7. Every alert needs a runbook with what, why, investigation, mitigation, and escalation

**Next: Lesson 108 — Incident Response Lifecycle — Detect, Triage, Mitigate, Resolve**
