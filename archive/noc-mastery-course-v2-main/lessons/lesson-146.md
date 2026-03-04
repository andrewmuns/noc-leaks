# Lesson 146: Post-Mortem Anti-Patterns and Best Practices
**Module 4 | Section 4.7 — Maintenance**
**⏱ ~5 min read | Prerequisites: Lesson 129**

---

## Learning from Bad Post-Mortems

Even organizations that write post-mortems often undermine their value through common anti-patterns. Recognizing these patterns helps you write post-mortems that actually prevent future incidents rather than just checking a box.

## Anti-Pattern 1: "Human Error" as Root Cause

**The bad post-mortem:** "Root cause: Engineer ran the wrong command in production."

This is the most common and most damaging anti-pattern. It stops the analysis at the surface level and implicitly blames an individual. Worse, the "fix" becomes "tell people to be more careful" — which has never prevented anything.

**The better analysis:**
- Why was it possible to run the wrong command? → No environment safeguard
- Why wasn't there a confirmation prompt? → Tool doesn't distinguish environments
- Why wasn't there a pre-flight check? → Feature was never prioritized

**The actionable fix:** Add environment name to the CLI prompt, require `--production` flag for production commands, add a confirmation step showing the target database.

Humans will always make mistakes. Systems should make dangerous mistakes hard to execute and easy to reverse.

🔧 **NOC Tip:** Every time you see "human error" in a root cause analysis, ask: "What systemic change would prevent ANY human from making this same mistake?" That's your real root cause and your real action item.

## Anti-Pattern 2: Vague Action Items

**Bad:**
- "Improve monitoring"
- "Add better alerting"  
- "Fix the deployment process"
- "Investigate further"

These action items never get completed because they're not specific enough to start working on.

**Good:**
- "Add Prometheus alert for `sip_registration_success_rate < 95%` with 5-minute evaluation window, severity critical" — Owner: Jane, Due: March 6
- "Add certificate expiry metric to the SRE dashboard with 30-day and 7-day threshold alerts" — Owner: Bob, Due: March 6
- "Implement deployment canary that compares error rates between canary and stable for 10 minutes before proceeding" — Owner: Alice, Due: March 20

The test: could someone who wasn't in the post-mortem meeting read the action item and know exactly what to do?

## Anti-Pattern 3: No Follow-Through

Writing action items is easy. Completing them is hard. Without tracking, action items decay:

- Week 1: "We'll get to that next sprint"
- Week 4: "It's in the backlog"
- Week 12: "What action items?"
- Week 24: Same incident happens again

**Best practice:** Review open post-mortem action items weekly. Track completion percentage as an engineering metric. Uncompleted action items from 30+ days ago should be escalated.

Some teams designate a "post-mortem action item owner" who follows up weekly until all items are closed. This single role dramatically improves completion rates.

## Anti-Pattern 4: Shallow Root Cause Analysis

**Shallow:** "The database ran out of connections."

That's the *what*, not the *why*. A proper analysis continues:
- Why did connections run out? → Slow queries held connections too long
- Why were queries slow? → Missing index on a new table
- Why was the index missing? → Schema review process doesn't check query patterns
- Why doesn't the review process check query patterns? → No checklist for database changes

**The deeper you dig, the more systemic the fix.** Surface-level fixes address this incident. Deep fixes prevent entire categories of future incidents.

## Anti-Pattern 5: Post-Mortem as Punishment

If post-mortems feel like interrogations, people will:
- Minimize their involvement
- Hide mistakes
- Avoid being on-call
- Under-report incidents

Signs your organization has this problem:
- People are defensive during post-mortem meetings
- Timeline entries are vague about who did what
- Incidents are classified as lower severity to avoid post-mortem requirements
- Engineers are reluctant to acknowledge errors

**The fix:** Leadership must actively model blameless behavior. Thank people for honest disclosures. Celebrate post-mortems that lead to systemic improvements. Never use post-mortem content in performance reviews.

🔧 **NOC Tip:** If you notice a colleague hesitating to be honest in a post-mortem, reassure them privately. Share your own mistakes openly. A culture of psychological safety takes time to build but is essential for effective learning.

## Best Practice 1: Share Broadly

Post-mortems are organizational learning tools, not team records. Share them:
- Cross-team engineering mailing list or wiki
- Monthly "incident review" meetings where interesting post-mortems are presented
- Onboarding materials for new engineers
- Architecture review discussions

A post-mortem about a DNS failure might prevent a completely different team from making the same mistake.

## Best Practice 2: Categorize and Trend

Over time, post-mortems reveal patterns:
- 40% of incidents are deployment-related → invest in canary deployments
- 25% involve certificate or credential expiry → invest in automated renewal monitoring
- 15% are capacity-related → invest in capacity planning

These trends inform strategic engineering investments far better than any individual incident.

## Best Practice 3: Update Runbooks

Every post-mortem should ask: "If this happened again tomorrow, would the on-call engineer know what to do?" If not, update or create a runbook.

The post-mortem timeline is essentially a draft runbook. Extract the debugging steps, remove the wrong turns, and publish as a reusable procedure.

## Best Practice 4: The Near-Miss Post-Mortem

Some of the most valuable post-mortems are for incidents that *almost* happened:
- A certificate was renewed with 2 hours to spare
- A capacity limit was hit briefly but recovered before customer impact
- A configuration error was caught in canary before full rollout

Near-misses reveal the same systemic weaknesses as actual incidents but without the customer impact. Treat them as learning opportunities.

## The Post-Mortem Maturity Model

1. **Level 0**: No post-mortems. Incidents repeat.
2. **Level 1**: Post-mortems written but superficial. Action items not tracked.
3. **Level 2**: Honest, blameless post-mortems. Action items tracked to completion.
4. **Level 3**: Post-mortems shared broadly. Patterns analyzed. Systemic improvements driven by trends.
5. **Level 4**: Proactive near-miss analysis. Chaos engineering informed by post-mortem findings. Continuous reliability improvement.

---

**Key Takeaways:**
1. "Human error" is never a root cause — always dig deeper to find the systemic issue that allowed the error
2. Action items must be specific enough that someone who wasn't in the meeting could execute them
3. Track action item completion weekly — untracked items don't get done
4. Share post-mortems broadly for organizational learning, not just team records
5. Analyze post-mortem trends over time to guide strategic reliability investments
6. Near-miss post-mortems are as valuable as actual incident post-mortems

**Next: Lesson 131 — Firewalls: Stateful Inspection and Rule Management**
