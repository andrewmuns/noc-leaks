# Lesson 122: Alerting Pipelines — From Metric to Engineer

**Module 3 | Section 3.7 — Alerting**
**⏱ ~7 min read | Prerequisites: Lessons 101, 104**

---

An alert without context is just noise. An alert with context becomes action. This lesson traces the complete path from a metric spike through Prometheus Alertmanager to the engineer's PagerDuty phone — and explains how each step shapes whether the alert is useful or ignored.

## The Alerting Chain

```
Prometheus Rule (PromQL expression)
    ↓
Alertmanager (grouping, routing, suppression)
    ↓
OpsGenie/PagerDuty (on-call scheduling, escalation)
    ↓
Notification (SMS, phone call, Slack)
    ↓
Engineer response
```

Understanding this chain is essential because problems at any stage break the system. A poorly written rule generates false positives. A badly configured router sends database alerts to the voice team. Poor on-call schedules wake the wrong person at 3 AM.

## Prometheus Alerting Rules

Alerting rules live in Prometheus as YAML configurations:

```yaml
groups:
  - name: voice-service-alerts
    rules:
      - alert: HighSIPErrorRate
        expr: |
          (
            sum(rate(sip_requests_total{response_code=~"5.."}[5m]))
            /
            sum(rate(sip_requests_total[5m]))
          ) > 0.05
        for: 5m
        labels:
          severity: critical
          team: voice
          runbook_url: "https://runbook.telnyx.io/sip-errors"
        annotations:
          summary: "High SIP error rate"
          description: "SIP error rate is {{ $value | humanizePercentage }} in {{ $labels.datacenter }}"
          dashboard: "https://grafana/d/sip-health?var-datacenter={{ $labels.datacenter }}"
```

### The Essential Components

**expr**: A PromQL expression that evaluates to a vector of time series. Each series in the result becomes a separate alert.

**for**: The duration the condition must be true before alerting. `for: 5m` means "only alert if the error rate is above 5% for 5 consecutive minutes."

**labels**: Static or templated metadata attached to the alert:
- `severity`: critical, warning, info
- `team`: which team owns this service
- `runbook_url`: link to investigation procedures

**annotations**: Dynamic, calculated values rendered in notifications:
- `summary`: Short human-readable title
- `description`: Detailed explanation with template variables
- `dashboard`: Direct link to relevant Grafana dashboard

### The Problem with `for`

Without `for`, brief spikes trigger alerts:

```yaml
# BAD: No duration, alerts on every brief spike
for: 0m

# GOOD: Requires 5 minutes of sustained elevated error rate
for: 5m
```

But `for` also delays real alerts. If a service is completely down (`error rate = 100%`), you might want to know immediately, not in 5 minutes.

**Solution**: Different `for` durations by severity:
- `critical` alerts: `for: 1m` (fast notification)
- `warning` alerts: `for: 10m` (reduce noise)
- `info` alerts: `for: 30m` (trend detection)

🔧 **NOC Tip:** When alerts fire too frequently (alert fatigue), check the `for` duration first. The engineer's instinct is to raise the threshold, but extending the `for` duration often fixes false positives without missing real issues. A 5-second spike shouldn't wake anyone; a 5-minute sustained problem should.

## Alertmanager: Grouping, Routing, and Suppression

Alertmanager receives fired alerts from Prometheus and decides:

1. **Grouping**: Should similar alerts be combined?
2. **Inhibition**: Should one alert silence others?
3. **Routing**: Who should receive each alert?
4. **Deduplication**: Has this already been sent?

### Grouping

Without grouping, a datacenter outage generates 50 separate alerts (one per service). With grouping, you get one alert:

```yaml
route:
  group_by: ['alertname', 'datacenter']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
```

- **group_wait**: Wait 30 seconds to see if more related alerts arrive. If 10 services report errors, they batch into one notification.
- **group_interval**: Send follow-up notifications every 5 minutes (not immediate) if the group is still firing.
- **repeat_interval**: Don't send the same alert more than every 4 hours unless it resolves and re-fires.

### Routing

Alerts route based on labels:

```yaml
routes:
  # Critical voice alerts → Voice team
  - match:
      team: voice
      severity: critical
    receiver: voice-oncall-critical
    continue: true
  
  # All voice alerts → Voice Slack
  - match:
      team: voice
    receiver: voice-slack
  
  # Database alerts → DBAs
  - match:
      team: database
    receiver: dba-oncall
```

The `continue` directive means "route to this receiver AND continue matching other routes." Critical voice alerts go to both on-call (phone) AND Slack.

### Inhibition

One alert can suppress others:

```yaml
inhibit_rules:
  # If datacenter-down is firing, suppress service-level alerts
  - source_match:
      alertname: DatacenterDown
    target_match_re:
      alertname: .+
    equal: ['datacenter']
```

If the Chicago datacenter goes down, you get one `DatacenterDown` alert, not 100 "ServiceXDown" alerts.

🔧 **NOC Tip:** If you're getting flooded with alerts during an outage, check for inhibition rules. If a high-level alert exists but isn't suppressing related alerts, the configuration needs updating. Good inhibition prevents alert storms that hide the actual problem.

## PagerDuty/OpsGenie: On-Call and Escalation

Alertmanager sends alerts to PagerDuty or OpsGenie, which handle:

### Scheduling
- Who is on-call right now? Who for the next shift?
- Rotation policies (round-robin, fair distribution)
- Override management (swap shifts, vacation coverage)

### Escalation Policies
- TIER 1: NOC Engineer Level 1
- If no acknowledgment in 15 minutes → TIER 2: NOC Engineer Level 2
- If still no acknowledgment in 15 minutes → TIER 3: Senior Engineer / Manager

### Notification Channels
- **Push**: Mobile app notification
- **SMS**: Text message
- **Phone**: Automated phone call
- **Email**: For lower-severity alerts

### Alert Fatigue: The Silent Killer

When engineers receive too many false alarms:
1. They become desensitized
2. They delay responding ("probably another false alarm")
3. They develop workarounds (silencing phones, complex filtering)
4. Eventually, a real alert is ignored

**Signs of alert fatigue:**
- Acknowledgment rate drops below 90%
- Mean time to acknowledge increases
- Manual filtering of alert channels
- "I just ignore everything from the database team"

The solutions:

1. **Fix the noise**: Tune alert thresholds instead of accepting false positives
2. **Reduce alert count**: One service, one meaningful alert — not 10 variants
3. **Automated remediation**: If the fix is always "restart the service," automate it and alert only on automation failure
4. **Business hours for warnings**: High-severity alerts page; low-severity alerts create tickets for business hours

🔧 **NOC Tip:** If you find yourself ignoring alerts, it's not your fault — it's a system failure. Alert fatigue is dangerous. Escalate to management: "This alert fires 5 times per day and is a false positive 99% of the time. We need to tune or remove it." Ignored alerts become silently ignored real problems.

## Writing Good Alert Descriptions

Bad alert:
```
High CPU usage
CPU usage is 87.3%
```

Good alert:
```
High CPU Usage on sip-proxy-7d4f8c-a3b4c
Deployment: sip-proxy/voice-services
Node: worker-chi-05
CPU Throttling: Currently experiencing 85% CPU usage with throttling events
Likely Impact: Increased call setup latency, potential INVITE timeouts
Runbook: https://runbook.telnyx.io/cpu-throttling
Dashboard: https://grafana/d/sip-proxy?var-pod=sip-proxy-7d4f8c-a3b4c
Actions:
  1. Check if the throttle is due to traffic spike or stuck process
  2. Scale deployment if traffic is legitimate
  3. Restart pod if process appears stuck
```

The good alert answers: what, where, impact, likely cause, and what to do next. The receiving engineer can start investigation immediately without hunting for context.

## Real-World Troubleshooting

**Problem:** Engineers report receiving duplicate alerts for the same issue.

**Investigation:**
1. Check Prometheus Alertmanager → "Alerts" page
   - Multiple alerts firing with the same `alertname` but different `instance` labels
2. Check Alertmanager routing configuration
   - No `group_by` configured for this alert type
   - Each instance sends separately
3. Solution: Add `group_by: ['alertname']` to batch by alert type

**Problem:** Database alerts go to voice team, database team never sees them.

**Investigation:**
1. Check alert labels in Prometheus Rules
   - Database alerts have `team: voice` (copy-paste error!)
2. Fix the label in the alert rule YAML
3. Database alerts now route correctly

---

**Key Takeaways:**

1. Alerting flows: Prometheus rule → Alertmanager → PagerDuty → engineer notification
2. The `for` duration prevents alerts on brief spikes; longer `for` = fewer false positives but delayed notification
3. Alertmanager groups related alerts, deduplicates, routes by labels, and inhibits related alerts
4. Alert fatigue kills response quality — tune alerts actively when acknowledgment rates drop
5. Good alert descriptions include: what, where, impact, likely cause, runbook link, and suggested actions
6. Inhibition rules prevent alert storms — one datacenter-down should suppress service-level alerts
7. Escalation policies ensure alerts reach the right person; manual filtering indicates process failure

**Next: Lesson 107 — Writing and Tuning Alert Rules**
