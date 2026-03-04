# Lesson 145: Post-Mortem Writing — Learning from Incidents
**Module 4 | Section 4.7 — Maintenance**
**⏱ ~7 min read | Prerequisites: Lesson 108**

---

## Why Post-Mortems Matter More Than Incident Response

Here's a counterintuitive truth: how you respond to an incident matters less than what you do after it. Fast incident response minimizes damage from *this* incident. A good post-mortem prevents the *next ten* incidents.

Organizations that skip post-mortems or treat them as formalities are doomed to repeat their failures. Organizations that invest in honest, thorough post-mortems build increasingly resilient systems.

## The Blameless Post-Mortem

The most important principle: **post-mortems are blameless**. This doesn't mean no one is accountable. It means the focus is on systemic causes, not individual mistakes.

Why blameless? Because blame destroys learning. If an engineer is punished for admitting they ran the wrong command, the next engineer will hide their mistake. Hidden mistakes mean the systemic issue (why was it possible to run the wrong command?) never gets fixed.

The question isn't "who caused this?" but "what made this possible?" and "how do we prevent it?"

Consider: "Engineer X ran a database migration against production instead of staging." The blameful response fires or reprimands Engineer X. The blameless response asks:
- Why was it possible to accidentally target production?
- Why didn't the migration tool require confirmation for production?
- Why weren't production and staging credentials different?
- Why wasn't there a pre-flight check that validates the target environment?

The blameless approach leads to guardrails that prevent anyone from making this mistake again.

## Post-Mortem Structure

### 1. Summary (2-3 sentences)
What happened, how long it lasted, and what the impact was. This is for executives who won't read the full document.

> *On February 20, 2026, SIP trunk registration failures affected approximately 2,000 customers for 47 minutes (14:23-15:10 UTC). The cause was an expired TLS certificate on the SIP registrar load balancer.*

### 2. Impact
Quantify the damage:
- Number of affected customers
- Duration of impact
- Call/message failure rates during the incident
- Revenue impact (if measurable)
- SLA impact (error budget consumption)

Be precise. "Many customers were affected" is useless. "2,147 customers experienced 100% registration failure for 47 minutes, with an estimated 12,400 failed call attempts" is actionable.

### 3. Timeline
A chronological sequence of events from detection through resolution. Include timestamps, who did what, and what was discovered at each step.

```
14:23 UTC — Alert fires: "SIP registration success rate below 80%"
14:25 UTC — NOC engineer A acknowledges alert, begins investigation
14:28 UTC — Engineer A identifies TLS handshake failures in Graylog
14:32 UTC — Engineer A checks certificate: expired at 14:00 UTC
14:35 UTC — Engineer A escalates to security team for certificate renewal
14:42 UTC — Security engineer B generates new certificate
14:48 UTC — Certificate deployed to load balancer
14:52 UTC — SIP registrations resuming, success rate climbing
15:10 UTC — Registration success rate back to 99.8%, incident resolved
```

🔧 **NOC Tip:** Start your timeline when the problem *began*, not when it was *detected*. If the certificate expired at 14:00 but the alert fired at 14:23, the 23-minute gap is important — it reveals a detection delay that should be addressed.

### 4. Root Cause Analysis

Go beyond the immediate cause. The "5 Whys" technique helps:

1. **Why did registrations fail?** TLS certificate expired.
2. **Why did the certificate expire?** Automated renewal failed.
3. **Why did automated renewal fail?** The ACME DNS challenge couldn't complete because the DNS API key had been rotated.
4. **Why wasn't the DNS API key updated in the renewal system?** The key rotation procedure didn't include updating dependent systems.
5. **Why didn't we detect the renewal failure earlier?** The renewal failure alert was set to "warning" severity and wasn't actively monitored.

The root cause isn't "certificate expired" — it's "key rotation procedure doesn't account for dependent systems" AND "certificate renewal failure alerts aren't treated as high severity."

### 5. What Went Well
Acknowledge what worked:
- Alert detected the issue within 23 minutes
- NOC engineer correctly identified TLS as the cause
- Certificate deployment process was fast (6 minutes)

This reinforces good practices and gives credit to the team.

### 6. What Went Wrong
Honest assessment of failures:
- Certificate expiry monitoring didn't alert before expiry
- Automated renewal had been failing for 3 days without escalation
- Key rotation procedure was incomplete

### 7. Action Items
Specific, measurable, assigned, and time-bound:

| Action | Owner | Due Date |
|--------|-------|----------|
| Escalate cert renewal failure alerts to critical severity | SRE Team | 2026-02-27 |
| Update key rotation procedure to include renewal system | Security | 2026-03-06 |
| Add 30/14/7-day cert expiry monitoring | Monitoring | 2026-03-06 |
| Audit all automated renewal systems for similar gaps | Security | 2026-03-13 |

Every action item must have an owner (a person, not a team) and a due date. "Improve monitoring" is not an action item. "Add Prometheus alert for cert expiry < 14 days, assigned to Jane, due March 6" is.

## Writing the Timeline

The timeline is the hardest part to write well. Tips:

- **Use UTC timestamps**: Avoid timezone confusion
- **Be specific**: "Checked logs" is vague. "Searched Graylog for 'tls_handshake_error' filtered to sip-registrar service" is useful.
- **Include wrong turns**: Document investigation paths that didn't lead anywhere. Future readers will benefit from knowing what was ruled out.
- **Include timestamps for decisions**: "At 14:40, decided to escalate rather than attempt manual certificate generation" explains the reasoning.

## When to Write a Post-Mortem

Not every incident needs a full post-mortem. Guidelines:

- **Always**: SEV1 and SEV2 incidents
- **Usually**: SEV3 incidents with novel failure modes
- **Sometimes**: SEV4 incidents that reveal systemic issues
- **Always**: Incidents that could have been worse (near-misses)

🔧 **NOC Tip:** Write the timeline while the incident is fresh — within 24 hours. Memory fades quickly, and Slack history only goes so far. Some teams designate a "scribe" during incidents whose job is to document actions and timestamps in real-time.

## The Post-Mortem Meeting

After the document is drafted, hold a meeting with responders and stakeholders:

1. **Walk through the timeline**: Confirm accuracy, fill in gaps
2. **Discuss root causes**: Ensure agreement and sufficient depth
3. **Review action items**: Confirm they address root causes, assign owners
4. **Discuss what went well**: Reinforce good practices
5. **Share learnings**: What should other teams know?

Keep the meeting blameless. If anyone starts pointing fingers, redirect to systems and processes.

## Sharing and Follow-Up

Post-mortems lose their value if they sit unread in a wiki:

- Share broadly within engineering — other teams learn from your incidents
- Review action item completion weekly until all are done
- Reference relevant post-mortems in future incident investigations
- Update runbooks based on post-mortem learnings

---

**Key Takeaways:**
1. Post-mortems prevent future incidents — they're more valuable than fast incident response
2. Blameless culture focuses on systemic causes, not individual mistakes, enabling honest analysis
3. The "5 Whys" technique drives root cause analysis beyond surface-level causes
4. Action items must be specific, measurable, assigned to a person, and time-bound
5. Write timelines within 24 hours while details are fresh — include wrong turns and decision rationale
6. Share post-mortems broadly and track action item completion to prevent follow-through failures

**Next: Lesson 130 — Post-Mortem Anti-Patterns and Best Practices**
