# Lesson 142: Traffic Patterns — Daily, Weekly, and Seasonal Cycles
**Module 4 | Section 4.6 — Capacity Planning**
**⏱ ~6 min read | Prerequisites: Lesson 104**

---

## Why Traffic Patterns Matter for NOC Engineers

Understanding normal traffic patterns is your superpower for distinguishing real incidents from natural variation. When a Grafana dashboard shows call volume dropping 40% at 6 PM, is that an outage or just the end of the business day? When messaging volume doubles on a Tuesday morning, is it a spam attack or a scheduled marketing campaign?

Without knowing what "normal" looks like, every fluctuation feels like an incident. With pattern knowledge, you respond only to genuine anomalies.

## Diurnal Patterns: The Daily Cycle

Voice traffic follows the sun. In any single timezone, the pattern is remarkably consistent:

- **6:00-8:00 AM**: Traffic ramps up as businesses open and early commuters make calls
- **10:00 AM - 12:00 PM**: First peak — mid-morning is the busiest calling period
- **12:00-1:00 PM**: Slight dip during lunch
- **1:00-4:00 PM**: Second peak — afternoon business activity
- **5:00-7:00 PM**: Sharp decline as businesses close
- **7:00 PM - 6:00 AM**: Low traffic — 10-20% of peak volume

For a platform like Telnyx serving customers across multiple US timezones, these curves overlap. East Coast peak starts 3 hours before West Coast, creating a plateau from 10 AM ET to 4 PM PT. The absolute trough is 2-5 AM ET (11 PM - 2 AM PT).

**Messaging** follows a different pattern:
- Marketing SMS spikes between 9-10 AM (businesses sending morning campaigns)
- Notification messages (OTP, alerts) are more evenly distributed
- Transactional messages follow application usage patterns

🔧 **NOC Tip:** When investigating off-hours alerts, remember that "normal" at 3 AM is 15% of peak volume. A metric that looks alarming in absolute terms might be perfectly normal for that time of day. Always compare to the same time window on previous days, not to today's peak.

## Weekly Patterns

- **Monday**: Often the highest traffic day — accumulated weekend inquiries, fresh business week
- **Tuesday-Thursday**: Consistently high, relatively flat
- **Friday**: Slightly lower than mid-week, with earlier decline
- **Saturday-Sunday**: 30-50% of weekday volume for business voice; consumer patterns differ

For messaging, weekdays see 3-5x the volume of weekends (driven by business A2P messaging). Consumer messaging is more consistent across the week.

### Grafana Technique: Week-over-Week Comparison

Use PromQL's `offset` to compare current traffic with the previous week:

```promql
# Current calls per second
rate(calls_total[5m])

# Same time last week
rate(calls_total[5m] offset 7d)
```

Overlay both on the same panel. When they diverge significantly, something has changed — either an incident or an unusual event.

## Seasonal and Event-Driven Patterns

### Holidays
- **US Thanksgiving**: Wednesday before is high; Thursday-Friday are very low
- **Christmas/New Year**: Low business traffic, higher consumer traffic
- **Black Friday/Cyber Monday**: Massive messaging spikes from retail campaigns
- **Valentine's Day**: Increased messaging volume
- **Tax season (April)**: Higher call volume for financial services customers

### Marketing Events
Large customers sometimes run campaigns that dramatically spike messaging volume. A retail customer sending 5 million promotional SMS in 2 hours looks like a DDoS attack if you're not expecting it.

🔧 **NOC Tip:** Maintain a calendar of known high-traffic events. Before major holidays and known customer campaigns, pre-check capacity and adjust alerting thresholds. Nothing's worse than paging the on-call engineer for "high traffic" that's actually a planned Black Friday campaign.

## Anomaly Detection: Spotting Real Problems

With pattern understanding, you can build effective anomaly detection:

### Static Thresholds (Basic)
- Alert if CPS exceeds 500 (absolute maximum capacity)
- Works for upper bounds but misses the nuance of daily variation

### Time-of-Day Aware Thresholds (Better)
- Alert if CPS deviates more than 30% from the same hour last week
- Catches both unusual spikes AND unusual dips
- Dips are often more significant — a 50% traffic drop usually indicates an outage

### Statistical Anomaly Detection (Best)
- Calculate rolling mean and standard deviation for each time bucket
- Alert when current value exceeds 2-3 standard deviations from expected
- Tools like Grafana's anomaly detection panels can automate this

### The Drop Is More Important Than the Spike

A sudden traffic drop is almost always an incident. Legitimate traffic doesn't disappear — if call volume drops 40% in 5 minutes during business hours, something is rejecting or failing calls. Investigate immediately.

Traffic spikes have legitimate causes (campaigns, events). Traffic drops almost never do.

🔧 **NOC Tip:** Set up alerts for sudden traffic drops, not just spikes. A PromQL expression like `rate(calls_total[5m]) < 0.5 * rate(calls_total[5m] offset 1h)` alerts when current traffic is less than half of what it was an hour ago.

## Timezone Considerations

For global telecom platforms, timezone awareness is essential:

- When European customers report issues, check if it's during their business hours
- A "traffic drop" at 5 PM ET might just be East Coast going home — check if West Coast traffic is normal
- After-hours for you might be peak hours for customers in another timezone

Monitor traffic broken down by region or customer timezone to get a clear picture.

## Building Your Baseline

Spend your first few weeks on the NOC actively studying traffic patterns:

1. Open the main traffic dashboard every morning and note the current volume
2. Compare weekday vs. weekend patterns
3. Learn what the typical daily peak looks like
4. Note any anomalies and investigate whether they were incidents or natural variation
5. After a month, you'll intuitively know when something "looks wrong"

---

**Key Takeaways:**
1. Voice traffic follows business hours with peaks at 10 AM-12 PM and 1-4 PM; messaging has different patterns driven by campaigns and notifications
2. Always compare current traffic to the same time on previous days — absolute values without context are misleading
3. Traffic drops are almost always incidents; traffic spikes often have legitimate causes
4. Week-over-week comparison using PromQL `offset 7d` is the most effective anomaly detection technique
5. Maintain a calendar of holidays and customer campaigns to avoid false alerts during expected traffic changes
6. Timezone awareness is critical for global platforms — your night is someone else's peak

**Next: Lesson 127 — Capacity Planning: Forecasting and Provisioning**
