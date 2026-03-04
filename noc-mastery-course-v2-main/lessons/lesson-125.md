# Lesson 125: Severity Classification and Escalation Procedures

**Module 4 | Section 4.1 — Incident Response**
**⏱ ~7 min read | Prerequisites: Lesson 108**

---

Not all incidents are equal. A 30-second latency spike affecting 0.1% of calls and a complete service outage affecting all customers require different responses, different notifications, and different urgency. Severity classification provides that framework, while escalation procedures ensure the right people are engaged at the right time.

## The Purpose of Severity Levels

Severity levels answer two questions:

1. **How urgently should we respond?** Page immediately vs. handle tomorrow
2. **Who should be involved?** Single on-call vs. all-hands vs. executives

Without severity classification, every alert becomes urgent or none do. The result is either complete alert fatigue ("I just ignore these") or complete paralysis ("What do I do first?").

## SEV Levels at Telnyx

While definitions vary by company, this is the standard Telnyx severity framework:

### SEV1 — Critical: Total Service Outage

**Criteria:**
- Complete service unavailability (100% failure)
- Major customer cannot use service
- Significant revenue impact (>10% of revenue at risk)
- Data loss or security breach

**Response:**
- All hands on deck
- Incident Commander appointed within 5 minutes
- Executive leadership engaged immediately
- Status page updated within 15 minutes
- Customer success contacts affected customers

**Examples:**
- All voice calls failing globally
- All API requests returning 5xx
- Customer data exposed (security incident)
- Complete datacenter loss

### SEV2 — Major: Significant Degradation or Partial Outage

**Criteria:**
- Major feature unavailable or severely degraded (>50% failure)
- Multiple customers affected (>10 customers or >5% traffic)
- Workaround exists but significantly impacts experience
- Single datacenter outage (others operational)

**Response:**
- On-call team engaged
- Incident Commander appointed if multi-team
- Status page updated within 30 minutes
- Customers notified if >5% impact

**Examples:**
- Outbound calls failing but inbound works
- Messaging API down, other APIs work
- Voice quality severely degraded (>50% calls affected)
- Single-region infrastructure failure

### SEV3 — Minor: Limited Impact or Degraded Performance

**Criteria:**
- Single feature degraded (<50% failure)
- Small number of customers affected (1-10 customers or <5% traffic)
- Workaround available with minimal impact
- Performance degradation (elevated latency, reduced throughput)

**Response:**
- On-call responds within business hours
- Status page may be updated for transparency
- Customers notified if they report issues

**Examples:**
- Delayed delivery for some messages
- Single customer experiencing intermittent failures
- Some calls experiencing one-way audio
- Elevated latency on non-critical endpoints

### SEV4 — Informational: No Customer Impact

**Criteria:**
- Anomaly detected with no current customer impact
- Capacity approaching limits
- Single instance failure (automatically recovered)
- Test environment issues

**Response:**
- Create ticket, handle during work hours
- No status page update unless trending toward SEV3
- No customer notification

**Examples:**
- One pod restarted (others handling load)
- Disk usage >80% (but plenty of headroom)
- Error rate slightly elevated but within SLA
- Non-production environment issues

## Severity Determination During Triage

Severity can change during an incident. Start with best assessment, update as information improves.

**Assess dimensions:**
1. **Scope**: How many customers? What percentage of traffic?
2. **Impact type**: Complete failure vs. degraded performance vs. inconvenience
3. **Duration**: Brief spike vs. ongoing
4. **Data risk**: Any data loss, exposure, or corruption
5. **Revenue**: Direct or indirect revenue impact

**Initially SEV1, discovered to be SEV2:**
- "All calls failing" → Investigation shows only outbound, inbound works
- SEV2 is appropriate (major, not critical)

**Initially SEV3, discovered to be SEV2:**
- "Single customer impact" → Investigation shows 15 customers in same region
- Escalate to SEV2

**Better to over-severity and de-escalate than under-severity and scramble to catch up.**

🔧 **NOC Tip:** When in doubt, escalate. A SEV1 declared for a SEV2 situation is embarrassing but functional. A SEV2 declared for a SEV1 situation is catastrophic — you're understaffing the response and under-communicating to stakeholders. Err on the side of higher severity at declaration time; you can always downgrade as you learn more.

## Escalation Criteria

Escalation means "bring in more help." Define when escalating is mandatory:

### Auto-Escalation Triggers

| Condition | Escalate To | Timeframe |
|-----------|-------------|-----------|
| No acknowledgment of SEV1 page | Level 2 on-call | 5 minutes |
| No acknowledgment of SEV2 page | Level 2 on-call | 10 minutes |
| No mitigation progress on SEV1 | Engineering lead | 15 minutes |
| No mitigation progress on SEV2 | Engineering lead | 30 minutes |
| Customer executive escalates | NOC manager + VP | Immediate |
| Revenue impact >$100K/hour | CFO + CTO | Immediate |
| Security incident confirmed | Security team + legal | Immediate |

### Manual Escalation Triggers

Escalate immediately when:
- The issue is beyond your expertise ("I've never seen this error")
- You need authority to make a decision ("Should we fail over?")
- Multiple teams need to coordinate ("This needs voice + billing together")
- External vendors need to be engaged ("The issue is our upstream carrier")
- The issue is getting worse despite mitigation attempts
- You're overwhelmed and need help prioritizing

**How to escalate:**
1. State what you know (what's broken, scope, impact)
2. State what you've done (mitigation attempts, what's been ruled out)
3. State what you need (decision, expertise, resources, coordination)
4. Provide data (dashboard links, log queries, error messages)

**Bad escalation:** "Help! Things are broken!"

**Good escalation:** "SEV1: Outbound calls failing for all customers in CHI datacenter. Error rate 100% starting 14:22. No recent deployments. Database connections appear healthy. Need to decide: should we fail over to backup datacenter or investigate in place? Dashboard links: [Grafana], last 5 minutes logs: [Loki]."

## Incident Communication Hierarchy

Who cares about this incident and what do they need to know?

**Incident Response Team (Engineers fixing):**
- Technical details
- Current hypothesis
- What was tried, what worked

**Incident Commander (Coordinating):**
- Status of each workstream
- Estimated time to mitigation
- Decisions needed

**Stakeholders (Engineering managers, executives):**
- Impact scope (customers, revenue)
- Estimated time to resolution
- External communication sent

**Customers:**
- What's affected
- What we're doing
- When to expect resolution

**External (Press, community):**
- What happened (high-level)
- What we did
- What we're doing to prevent recurrence

Each group has different information needs. Don't share technical stack traces with customers, and don't share customer impact embargo information publicly.

🔧 **NOC Tip:** Create a standard communication template for each channel and fill it in as the incident progresses. For example, the executive summary template: "[STATUS: Investigating/Mitigating/Monitoring/Resolved] [SEVERITY: SEV1/2/3] [IMPACT: X customers, Y % traffic] [ESTIMATE: Time to mitigation/resolution or "Unknown"] [NEXT UPDATE: Time of next communication]". Using a template ensures you don't forget key information under pressure.

## Status Page Updates

The status page is your customer-facing communication during incidents.

**Update frequency:**
- SEV1: Every 15 minutes or upon significant change
- SEV2: Every 30 minutes or upon significant change
- SEV3: Upon resolution or if duration >2 hours

**Update components:**
1. **Status**: Investigating / Identified / Mitigating / Monitoring / Resolved
2. **Affected services**: Specifically what's impacted
3. **Start time**: When the incident began
4. **Current understanding**: What you know
5. **Customer impact**: What customers should expect
6. **Workaround**: Any temporary solution available

**Sample update:**
```
Status: Investigating - SEV2 Outbound Call Failures

We are investigating reports of outbound call failures affecting 
approximately 5% of Telnyx Voice customers. Inbound calls are 
not affected.

Start time: 14:32 UTC

We have identified that the issue is isolated to our Chicago datacenter 
and are working to restore service. We will provide an update in 30 
minutes or upon significant change.

Workaround: Customers can temporarily route traffic to our Dallas 
datacenter by updating connection settings.
```

## Post-Incident Severity Review

After resolution, review the severity:
- Was initial severity correct?
- Did it need escalation that didn't happen?
- Should we have communicated differently?

Use lessons to improve future triage. If SEV2 incidents keep becoming SEV1 before proper escalation, the criteria are wrong.

---

**Key Takeaways:**

1. SEV1 (Critical) = total outage, all hands; SEV2 (Major) = significant degradation; SEV3 (Minor) = limited impact; SEV4 (Informational) = no impact
2. Severity determines response speed, team involvement, and communication approach
3. Start with best estimate, update as you learn; better to over-severity initially than under-severity
4. Escalate when you need expertise, authority, coordination, or help prioritizing
5. Effective escalation includes: what you know, what you've done, what you need, data links
6. Status page updates: SEV1 every 15 min, SEV2 every 30 min; include status, scope, impact, workarounds
7. Different audiences need different information — don't overshare technical details externally

**Next: Lesson 110 — Incident Communication — Internal and External**
