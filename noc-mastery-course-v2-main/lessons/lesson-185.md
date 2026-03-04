# Lesson 185: Technical Communication — Writing Clear Status Updates
**Module 6 | Section 6.1 — Communication Skills**
**⏱ ~6 min read | Prerequisites: Lesson 108-110**

---

You can be the most technically brilliant NOC engineer in the room, but if you can't communicate what's happening during an incident, your technical skills are half as effective. Communication during incidents is a force multiplier — or a force divider. Clear updates reduce panic, prevent duplicate work, and build trust. Unclear updates generate a flood of follow-up questions that pull engineers away from troubleshooting.

## The Audience Problem

The fundamental challenge of incident communication is that different audiences need different information from the same event.

**Engineering team** wants:
- What's broken and what's the hypothesis
- What diagnostic steps have been taken
- What specific help is needed

**Management** wants:
- Customer impact (how many, how severe)
- Timeline (when did it start, when will it end)
- Risk (is it getting worse or contained)

**Customers** (via status page) want:
- Is the service working or not
- What's being done about it
- When will it be fixed

Sending the same update to all three audiences fails everyone. The engineer writes a technically accurate update that management can't understand. Or writes a simple summary that gives engineering nothing actionable.

🔧 **NOC Tip:** Write the engineering update first (it's the most detailed), then distill it for management and customer audiences. It's easier to simplify a detailed message than to add detail to a vague one.

## The Status Update Template

Every status update should answer four questions:

1. **What's happening?** (Symptom, not diagnosis)
2. **What's the impact?** (Who's affected, how severely)
3. **What are we doing?** (Current action, not technical details)
4. **What's the ETA?** (Honest estimate or "investigating")

### Bad Example:
> "We're seeing elevated 503 responses from the Kamailio instances in the us-east-1 cluster. The registration cache appears to be corrupted after the v2.4.7 deployment which used a new serialization format for the location table entries. We're analyzing core dumps and comparing the htable configuration between versions."

This is fine for the engineering channel. It's terrible for management or customers. Nobody outside the SIP team knows what Kamailio is, what 503 means, or what htable configuration refers to.

### Good Example (for management):
> "**Incident Update — INC-0847 (03:55 UTC)**
> 
> **What:** Some customers in the US-East region are experiencing failed calls.
> **Impact:** Approximately 15% of calls in US-East are failing. ~200 customers affected. Other regions unaffected.
> **Action:** We've identified the cause (a recent software update) and are rolling back.
> **ETA:** Full recovery expected within 20 minutes."

### Good Example (for status page/customers):
> "**Investigating — Voice Service Degradation (US-East)**
> 
> Some voice calls in the US-East region may experience failures. Our team has identified the issue and is implementing a fix. We expect full resolution within 20 minutes. Other regions are not affected."

Same incident, three communication styles. The engineering channel gets full technical detail. Management gets business impact and timeline. Customers get reassurance and ETA.

## Update Frequency

How often should you update? This depends on severity and audience:

| Severity | Engineering | Management | Status Page |
|----------|------------|------------|-------------|
| P1 (critical) | Continuous (as findings emerge) | Every 15 minutes | Every 15-30 minutes |
| P2 (major) | Every 15-30 minutes | Every 30 minutes | Every 30-60 minutes |
| P3 (minor) | As needed | Initial + resolution | If public-facing |

The cardinal sin of incident communication: **silence**. Even if nothing has changed, say so: "Still investigating. No new findings. Next update in 15 minutes." Silence causes stakeholders to assume the worst and start interrupting with "any update?" messages — which is exactly the distraction engineers don't need.

🔧 **NOC Tip:** Set a timer for your next update. During an incident, time perception is distorted — what feels like 5 minutes might be 25. A timer ensures you don't accidentally go silent.

## Avoiding Jargon Traps

Technical jargon is efficient between engineers but exclusionary for everyone else. Some translations:

| Jargon | Plain Language |
|--------|---------------|
| "503 responses" | "Service is rejecting connections" |
| "ASR dropped to 31%" | "About 70% of calls are failing" |
| "Memory leak in the registration cache" | "A software bug is causing the service to slow down" |
| "Rolling back to v2.4.6" | "Reverting to the previous software version" |
| "PCAP analysis shows asymmetric RTP" | "We've identified a network routing issue affecting audio" |
| "DNS TTL hasn't expired" | "The fix is deployed but some systems are still using cached information; this will resolve automatically" |

You're not dumbing things down — you're translating between domains. The CFO who reads "70% of calls are failing" can immediately assess business impact. "ASR dropped to 31%" requires telecom-specific knowledge.

## Written vs. Verbal Communication

**Use written updates (Slack, email, status page) when:**
- Information needs to reach multiple people simultaneously
- You need an audit trail
- Stakeholders are in different time zones
- The update is factual and doesn't need discussion

**Use verbal communication (call, video) when:**
- The situation is rapidly evolving and written can't keep up
- You need real-time collaboration (war room)
- The message is sensitive or nuanced
- You need immediate feedback or decisions

During major incidents, both happen simultaneously: the incident channel has written updates while a voice bridge hosts real-time troubleshooting discussion.

## Real-World Scenario: The Cascading Update

A database failover causes a 12-minute voice service outage. Here's how updates should flow:

**T+0 (detection):**
> Engineering: "Database primary failover detected. Replica promoted. SIP proxies reconnecting. Call processing interrupted."
> Management: "Voice service disruption detected. Team investigating. Update in 10 minutes."
> Status page: "Investigating — Voice service interruption. Our team is aware and investigating."

**T+5 (identified):**
> Engineering: "DB failover complete, replica promoted to primary. SIP proxies re-establishing connections. 3 of 8 reconnected. Expected full reconnection in 5 minutes."
> Management: "Cause identified — database failover. Recovery in progress, expect full restoration in 5-10 minutes."
> Status page: "Identified — The cause has been identified and recovery is in progress. ETA: 10 minutes."

**T+12 (resolved):**
> Engineering: "All SIP proxies reconnected. Registration recovery 98%. Call processing normal. Post-mortem to investigate why failover was triggered."
> Management: "Voice service fully recovered. Total outage: 12 minutes. Post-mortem scheduled for tomorrow."
> Status page: "Resolved — Voice service has fully recovered. We will publish a post-incident report."

Notice how each audience gets the right level of detail at each stage, and updates are proactive rather than reactive.

## Building the Habit

Good incident communication is a skill that improves with practice:

1. **Template it**: Pre-written templates with blanks to fill reduce cognitive load during incidents
2. **Review it**: Include communication quality in post-mortems — were updates timely and clear?
3. **Practice it**: During game days (Lesson 176), practice communication alongside technical response
4. **Delegate it**: In major incidents, the incident commander should handle communication while engineers troubleshoot

---

**Key Takeaways:**
1. Different audiences (engineering, management, customers) need different levels of detail from the same incident
2. Every update must answer: What's happening, What's the impact, What are we doing, What's the ETA
3. Silence during incidents is worse than "no change, still investigating" — set timers for updates
4. Translate jargon for non-technical audiences without losing accuracy
5. Use written communication for reach and audit trails; verbal for real-time collaboration
6. Pre-written templates and dedicated communication roles reduce cognitive load during incidents

**Next: Lesson 170 — Stakeholder Management During Incidents**
