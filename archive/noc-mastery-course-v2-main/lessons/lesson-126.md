# Lesson 126: Incident Communication — Internal and External

**Module 4 | Section 4.1 — Incident Response**
**⏱ ~6 min read | Prerequisites: Lesson 109**

---

During an incident, communication is as important as technical fixes. Stakeholders need information to make decisions. Customers need assurance that we're aware and acting. The response team needs coordination. Poor communication leads to confusion, duplicated effort, and extended impact. This lesson covers how to communicate effectively across all channels during incidents.

## The Principle: Facts Over Speculation

The single most important rule: **communicate facts, not guesses.**

**Bad:** "We think the database might be the problem."
**Good:** "We see elevated error rates from the billing service. Investigating cause."

**Why this matters:**
- Stakeholders make decisions based on your words
- Retracting speculation damages credibility
- "Might be" creates anxiety without adding value
- If you're wrong, you look incompetent

If you don't know, say "investigating" or "assessing scope." It's honest and accurate.

## Internal Communication: The Incident Channel

Create a dedicated incident channel (Slack, Teams) for every SEV1 and major SEV2 incident. This becomes the single source of truth.

**Channel naming:**
```
incident-2026-02-22-sev1-voice-outage
incident-2026-02-22-sev2-api-latency
```

**Channel topic:**
```
SEV1: Outbound voice calls failing
Impact: All customers, CHI datacenter
IC: @sarah.eng
Status: Mitigating
Next update: 15:15 UTC
Grafana: https://grafana/d/...
```

**Who to include:**
- Incident Commander (mandatory)
- Response engineers (technical team)
- Stakeholders (engineering managers, product)
- Communications lead (for customer updates)
- Optional: Legal (if compliance/security), Marketing (if public-facing)

**What to post:**
```
14:30 Alert fired: HighErrorRate on sip-proxy @noc-oncall
14:32 Confirmed: Outbound calls failing, 100% error rate @john.doe
14:35 Hypothesis: Recent deployment, rolling back @sarah.eng
14:37 Rollback initiated @sarah.eng
14:45 Error rate decreasing, now 40% @john.doe
```

Every action, decision, and observation is timestamped. The channel history becomes the incident timeline.

🔧 **NOC Tip:** Use @mentions for direct communication. @sarah.eng in a channel with 50 people = unnecessary notifications. Reply in a thread or ping privately. Reserve @channel for urgent updates that truly require everyone's attention. Respect the cognitive load of incident responders — unnecessary notifications break focus.

## Communication Cadence

**Internal updates (incident channel):**
- Every significant action or decision
- When status changes (investigating → mitigating → resolved)
- When new information changes understanding
- When external communication goes out

**Stakeholder updates (manager channel, email):**
- SEV1: Every 15 minutes or upon major developments
- SEV2: Every 30 minutes
- SEV3: Upon resolution or significant scope change

**Customer updates (status page):**
- SEV1: Every 15-30 minutes
- SEV2: Every 30-60 minutes
- SEV3: As needed

**Executive updates (email/SMS):**
- SEV1: Every 30 minutes or upon major developments
- SEV2: Every 60 minutes
- Only if revenue impact or media attention likely

## Status Page Communication

The status page is your public voice during incidents. Write for stressed customers who need clarity.

### Status Levels
Use consistent status indicators:
- **Investigating**: We know something's wrong, figuring out what
- **Identified**: We know the cause, working on fix
- **Mitigating**: Fix in progress, but not complete
- **Monitoring**: Fix applied, watching to confirm
- **Resolved**: Back to normal

### The Anatomy of a Good Status Update

```
Title: [STATUS] [IMPACT DESCRIPTION]

Status: Investigating/Identified/Mitigating/Monitoring/Resolved

Affected Services: Specific list

What happened: Factual description

Impact: Specific, quantified when possible
  - "Approximately 500 customers unable to make outbound calls"
  - "All customers in EMEA region experiencing latency >2s"

What we're doing: Current actions
  - "Rolling back recent deployment"
  - "Failing over to secondary datacenter"

What you can do: Any workarounds
  - "Temporarily use Dallas datacenter"
  - "No action needed on your part"

Timeline: Expected updates
  - "Next update in 30 minutes or upon significant change"
  - "Expected resolution within 1 hour"
```

### Tone Guidelines

**Be direct:** State what's wrong clearly. Vague language creates confusion.

**Don't minimize:** "Minor issues" when customers can't make calls is insulting.

**Don't over-promise:** "Fix expected in 10 minutes" when you don't know is dangerous. Better: "Working on mitigation, no ETA yet."

**Avoid jargon:** Customers don't know what "ASR" or "INVITE" means. Use plain language.

**Take responsibility:** Even if the root cause is an upstream provider, Telnyx owns the customer relationship.

### Sample Status Updates

**SEV1, initial:**
```
Title: [Investigating] Voice service interruption

We are currently investigating reports of voice service interruption 
affecting outbound calls. Our team has been notified and is working 
to restore service as quickly as possible.

We will provide an update in 30 minutes.
```

**SEV1, mitigating:**
```
Title: [Mitigating] Voice service restored for some customers

We have identified the issue was related to a configuration change 
in our Chicago datacenter. We are in the process of rolling back 
this change.

Approximately 60% of customers have seen service restoration as 
of 15:30 UTC. We expect full restoration within the next 30 minutes.

Next update in 30 minutes.
```

**SEV1, resolved:**
```
Title: [Resolved] Voice service fully restored

Voice service has been fully restored for all customers as of 16:00 UTC.

The issue was caused by a misconfiguration in a load balancer that 
was deployed at 14:30 UTC. We rolled back to the previous configuration 
at 15:15 UTC.

We are conducting a full post-mortem to prevent similar issues. 
We will publish a summary within 48 hours.

If you continue to experience issues, please contact support.
```

🔧 **NOC Tip:** Before posting to the status page, read it aloud. If it sounds like marketing speak, rewrite it. Stressed customers reading "We are experiencing some technical difficulties" want to scream. They want "Calls are failing and we're fixing it." Clarity over polish.

## Customer Notifications

Beyond the status page, proactive customer communication may be needed:

**When to notify specific customers:**
- They reported the issue and want acknowledgment
- They're a high-value account and deserve proactive outreach
- Their specific service is known to be affected
- They have contractual SLA notification requirements

**Notification template:**
```
Subject: Service Impact - Telnyx Voice

Dear [Customer Name],

We are writing to inform you of a service impact affecting Telnyx 
Voice.

Impact Summary:
- Service: Outbound voice calling
- Duration: 14:30 UTC to 15:45 UTC (1 hour 15 minutes)
- Impact: Approximately 40% of your calls failed during this period
- Current Status: Service restored and stable

Your Success Manager will follow up within 24 hours to discuss 
any questions or concerns.

For real-time updates: [status page link]
```

## Communication During Mitigation vs. Resolution

**During mitigation (urgent):**
- Focus: What we're doing to restore service
- Frequency: High (15 min updates)
- Channels: Status page, incident channel
- Tone: Action-oriented, "we're fixing this"

**During resolution (post-mitigation):**
- Focus: Root cause, permanent fix, prevention
- Frequency: Lower (daily check-ins)
- Channels: Internal only, status page resolved notice
- Tone: Analytical, "here's what we learned"

Don't confuse the two. Mitigation communication is about "it's broken, we're fixing it." Resolution communication is about "it's fixed, here's why it broke."

## Communication Anti-Patterns

**The Ghost:** An incident fires, someone acknowledges, then silence for 30 minutes.

**The Spiral:** "5 minutes to fix" → 10 minutes later: "5 more minutes" → 10 minutes later: "almost there"

**The Deflection:** "This is an upstream provider issue" — avoiding ownership

**The Jargon Dump:** "Our ingress controllers are experiencing elevated 5xx rates due to a downstream dependency failure in our message broker" — customers don't understand this

**The Minimizer:** "Minor disruption" when customers are completely down

## Real-World Scenario

**Situation:** SEV1 declared, IC appointed, but customer support is getting calls from angry customers who don't see any status page update.

**Problem:** 20-minute gap between incident declaration and first status page update.

**Investigation:** Engineering was focused on mitigation and "didn't have time" to write an update.

**Solution:** IC appoints a dedicated communications role for every SEV1. This person's only job is communications — status updates, customer support coordination, stakeholder notifications. They don't do technical work.

**Lesson:** Technical work and communication require different mindsets. Don't ask engineers to context-switch between debugging and writing customer-facing updates. Separate the roles.

---

**Key Takeaways:**

1. Communicate facts, not speculation — credibility depends on accuracy
2. Create a dedicated incident channel with clear naming, topic, and purpose
3. Status page updates follow cadence: SEV1 every 15 min, SEV2 every 30 min
4. Use consistent status levels (Investigating, Identified, Mitigating, Monitoring, Resolved)
5. Write status updates for stressed customers — direct, clear, no jargon, take responsibility
6. Separate technical response from communication tasks — one person can't do both effectively
7. Avoid anti-patterns: ghosting, deadline spirals, deflection, jargon, minimizing

**Next: Lesson 111 — Reading SIP Traces — A Systematic Approach**
