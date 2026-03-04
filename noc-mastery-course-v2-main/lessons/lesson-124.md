# Lesson 124: Incident Response Lifecycle — Detect, Triage, Mitigate, Resolve

**Module 4 | Section 4.1 — Incident Response**
**⏱ ~8 min read | Prerequisites: Module 3 (observability)**

---

Incidents are inevitable. How you respond to them determines customer impact, team morale, and system reliability. Great NOC teams don't just put out fires — they have a systematic process that minimizes damage and prevents recurrence. This lesson defines the incident lifecycle and the engineer's role at each stage.

## The Five Stages of Incident Response

Every incident, from minor degradation to major outage, progresses through the same phases:

### 1. Detection

**The trigger:** Something indicates a problem exists.

**Sources:**
- **Alert-driven**: Monitoring detects threshold breach (error rate, latency, resource exhaustion)
- **Customer-reported**: Support ticket, social media, direct contact
- **Proactive monitoring**: NOC engineers notice anomalous patterns in dashboards
- **Automated health checks**: Synthetic monitoring (pinging endpoints from outside)
- **Upstream notification**: Carrier or provider alerts us to issues affecting their service

**Detection quality metrics:**
- Mean Time to Detect (MTTD): How long between problem start and detection
- Alert coverage: What percentage of real incidents trigger automated alerts

Ideally, MTTD is near zero — the problem triggers alerts immediately. In practice, some incidents are only detected when customers report them (MTTD = hours).

🔧 **NOC Tip:** When an incident is customer-reported before alert-driven, that's a detection failure. After resolution, always investigate why monitoring didn't catch it. Was the alert threshold misconfigured? Was the alert suppressed? Was the metric not instrumented? Every gap is an opportunity to improve detection.

### 2. Triage

**The assessment:** What happened? How bad is it? Who should handle it?

**Triage answers:**
- Is this a real incident or a false alarm? (Verify the alert)
- What's the scope? (Which services, customers, datacenters?)
- What's the severity? (SEV1 total outage? SEV4 minor issue?)
- Should we page the on-call? (Is this urgent?)
- Do we need to escalate? (Is this beyond our capability?)

Triage typically takes 1-5 minutes. The goal isn't to solve the problem — it's to characterize it and decide the response.

**The triage checklist:**
1. Acknowledge the alert (in PagerDuty/OpsGenie)
2. Check if this is ongoing or resolved (spike might have passed)
3. Identify affected scope (x customers, y % error rate)
4. Check recent changes (deployments, configuration changes)
5. Assess severity
6. Page on-call if appropriate

**False positive handling:** Not every alert is a real incident. A brief capacity spike that self-resolved isn't an incident worth declaring. But err on the side of caution — better to investigate a false positive than miss a real problem.

### 3. Mitigation

**The emergency action:** Stop the bleeding, even if you don't know the root cause.

Mitigation precedes resolution. You don't need to understand the bug to stop its impact.

**Common mitigation strategies:**

| Strategy | When to Use | Examples |
|----------|-------------|----------|
| **Rollback** | Recent deployment caused issue | Revert bad code in ArgoCD |
| **Failover** | Primary system degraded/unavailable | Route traffic to DR site |
| **Restart** | Service stuck, leaking, or corrupted | Cycle pods/instances |
| **Scale up** | Capacity exceeded | Add replicas, increase limits |
| **Circuit breaker** | Upstream dependency failing | Stop calls to broken service |
| **Manual intervention** | Automated mitigation not possible | Disable feature flags, block traffic |

The goal of mitigation: **Reduce customer impact to acceptable levels quickly**. If rollback takes 2 minutes but full root cause analysis takes 2 hours, rollback first.

🔧 **NOC Tip:** Always have a rollback plan before every deployment. If you can't roll back quickly, you can't mitigate. Test rollbacks during low-risk periods so the process is muscle memory. During an incident at 2 AM, you don't want to rediscover how reverting works.

### 4. Resolution

**The permanent fix:** Address the root cause, not just the symptom.

Resolution requires understanding what caused the problem and fixing it properly.

**Post-mitigation resolution may involve:**
- Deploying a fixed version of code (with root cause addressed)
- Infrastructure changes (resource limits, network configuration)
- Data fixes (correcting corrupted state)
- Process improvements (preventing the misconfiguration)

**The difference between mitigation and resolution:**
- Mitigation: Customers stop experiencing problems
- Resolution: The problem won't recur

Example: A service crashes due to a memory leak.
- Mitigation: Restart the service every hour with a cron job (symptom management)
- Resolution: Fix the memory leak and deploy patched version (root cause fix)

Sometimes mitigation and resolution are the same action (rolling back a bad deployment). But often, mitigation is temporary (emergency restart) while resolution takes longer (code fix requires change, build, test, deploy cycle).

### 5. Post-Mortem

**The learning:** How can we prevent this from happening again?

The post-mortem isn't blame assignment — it's system improvement. What about the system allowed this failure? What gaps need closing?

**Post-mortem outputs:**
- Root cause analysis: What failed and why
- Timeline reconstruction: What happened, when, who did what
- Impact assessment: Customers affected, duration, severity
- Action items: Specific changes to prevent recurrence

More on post-mortems in Lessons 129-130.

## Incident Response Workflow

```
Detection (Alert fires or customer reports)
    ↓
Triage (1-5 min)
    - Verify problem
    - Assess scope and severity
    - Page on-call if needed
    ↓
Mitigation (5-30 min)
    - Rollback, failover, restart, scale
    - Goal: stop customer impact
    ↓
Resolution (30 min - days)
    - Fix root cause
    - Verify fix works
    ↓
Post-Mortem (within 1 week)
    - Document what happened
    - Document what was learned
    - Assign action items
```

Each phase has different priorities:
- **Triage**: Speed of assessment
- **Mitigation**: Speed of impact reduction
- **Resolution**: Thoroughness of fix
- **Post-mortem**: Learning completeness

## The Incident Commander Role

For significant incidents, an **Incident Commander (IC)** coordinates the response. The IC:

- **Does not**: Fix the problem directly
- **Does**: Coordinate others who fix the problem
- **Focuses on**: Communication, coordination, decision-making

**IC responsibilities:**
1. Establish communication channels (Slack channel, conference bridge)
2. Assign roles (communicator, mitigator, investigator)
3. Track timeline and decisions
4. Distill information for stakeholders
5. Declare incident status changes (impact reduced, service restored, resolved)
6. Ensure post-mortem happens

🔧 **NOC Tip:** For SEV1/SEV2 incidents, appoint an Incident Commander who isn't doing technical work. It's impossible to both debug deeply and maintain broader situational awareness. The IC stays out of the code/logs and focuses on "what's happening, who's doing what, what decisions need to be made." ICs rotate to prevent burnout.

## Incident Documentation During Response

While responding, document in real-time:

**Dedicated incident channel (Slack):**
- Timestamped events: "14:23 — Alert fired, HighErrorRate on sip-proxy"
- Actions taken: "14:25 — Rolling back deployment sip-proxy:v2.3.2"
- Decisions made: "14:30 — Decision: won't fail over to secondary DC, rollback is faster"
- Key findings: "14:35 — Logs show database connection pool exhaustion"

**Why real-time documentation matters:**
1. Distributed team stays synchronized
2. Handoffs between shifts are seamless
3. Post-mortem timeline is mostly written
4. Stakeholder comms have source of truth
5. Prevents "wait, who did what?" confusion

## Time Expectations by Severity

| Phase | SEV1 (Critical) | SEV2 (Major) | SEV3 (Minor) | SEV4 (Info) |
|-------|-----------------|--------------|--------------|-------------|
| **Detection** | <1 min | <5 min | <15 min | May not alert |
| **Triage** | <2 min | <5 min | <15 min | - |
| **Mitigation start** | <5 min | <15 min | <30 min | - |
| **Mitigation complete** | <30 min | <1 hour | <4 hours | <1 day |
| **Resolution** | <24 hours | <48 hours | <1 week | <1 month |
| **Post-mortem** | 48 hours | 1 week | 2 weeks | None |

🔧 **NOC Tip:** Set expectations correctly. Stakeholders will ask "when will it be fixed?" The honest answer during triage/mitigation is usually "we don't know yet; we'll update in 30 minutes." Never promise timelines you can't keep. Better to under-promise and over-deliver than to miss a promised deadline and lose trust.

---

**Key Takeaways:**

1. The five incident stages: Detection, Triage, Mitigation, Resolution, Post-Mortem
2. Detection source determines MTTD — customer-reported = detection failure
3. Triage characterizes the problem and decides response; takes 1-5 minutes
4. Mitigation reduces impact immediately — rollback first, investigate later
5. Resolution fixes the root cause; mitigation and resolution are often separate actions
6. Post-mortems identify system improvements, not blame
7. For major incidents, appoint an Incident Commander focused on coordination, not technical work

**Next: Lesson 109 — Severity Classification and Escalation Procedures**
