# Lesson 186: Stakeholder Management During Incidents
**Module 6 | Section 6.1 — Communication Skills**
**⏱ ~6 min read | Prerequisites: Lesson 169**

---

In Lesson 169, we covered writing clear status updates for different audiences. Now we zoom out to the broader challenge: managing the humans around the incident. Stakeholder management during incidents isn't about bureaucracy — it's about ensuring the right people have the right information so they can make decisions and stay out of the troubleshooters' way.

## Identifying Your Stakeholders

During any incident, multiple groups have legitimate needs for information:

**Tier 1 — Direct responders** (need real-time technical detail):
- On-call engineers working the incident
- Incident commander
- Subject matter experts pulled in for specific expertise

**Tier 2 — Operational stakeholders** (need impact and timeline):
- NOC management / shift leads
- Account managers for affected customers
- Support team leads fielding customer tickets
- On-call executives (for P1 incidents)

**Tier 3 — Informed parties** (need summary at key milestones):
- Engineering leadership
- Product management
- Compliance/legal (if regulatory implications exist)
- External partners affected by the incident

Each tier needs different information at different frequencies. Tier 1 gets continuous updates in the incident channel. Tier 2 gets structured updates every 15-30 minutes. Tier 3 gets milestone notifications (identified, mitigated, resolved).

🔧 **NOC Tip:** Map your stakeholders *before* incidents happen. Create a stakeholder matrix in your runbooks that lists who to notify at each severity level. During an incident, you shouldn't be figuring out who needs to know — you should be following a pre-defined notification list.

## Proactive Communication

The most effective communication strategy during incidents is **proactive** — update before being asked. Every incoming "What's the status?" message represents a communication failure: someone needed information and didn't have it.

Proactive communication has compound benefits:
- **Reduces interruptions**: Engineers aren't pulled away from troubleshooting to answer status questions
- **Builds trust**: Stakeholders who receive regular updates trust that the team is in control
- **Prevents escalation**: Managers who feel informed don't escalate "just to make sure someone is working on it"
- **Controls narrative**: You define the story, rather than having stakeholders fill the silence with assumptions

The opposite — reactive communication — creates a vicious cycle. Silence breeds anxiety. Anxiety generates interruptions. Interruptions slow troubleshooting. Slower troubleshooting means more silence. The cycle feeds itself.

## Managing Expectations: The Art of Honest ETAs

ETAs are the hardest part of incident communication. Give a specific time and miss it — trust erodes. Give no ETA — stakeholders assume the worst.

The framework:

**When you understand the problem:**
> "We've identified the cause and are implementing the fix. Expected recovery in approximately 20 minutes."

**When you're still investigating:**
> "We're actively investigating. We've narrowed it to [area] and are running diagnostics. Next update in 15 minutes."

**When you genuinely don't know:**
> "The cause is not yet identified. Multiple teams are investigating in parallel. We'll update as soon as we have more information, no later than 15 minutes from now."

Never say "should be fixed soon" without a timeframe. "Soon" means 5 minutes to an engineer and 60 seconds to a customer. Always anchor to a specific next-update time, even if you can't estimate resolution.

🔧 **NOC Tip:** Pad your ETAs by 50%. If you think recovery will take 20 minutes, say 30. Delivering early builds confidence. Delivering late destroys it. Under-promise, over-deliver.

## Escalation Communication

Escalating an incident is not admitting failure — it's good engineering judgment. But how you escalate matters:

**Bad escalation:**
> "Hey, SIP proxies are broken, can you look?"

**Good escalation:**
> "P2 Incident INC-0847: SIP registration failures in US-East. Started 03:47 UTC. Affecting ~200 customers, 15% call failure rate.
> 
> What we've done:
> - Confirmed issue is in the registration cache module
> - Isolated to nodes running v2.4.7
> - Attempted service restart — issue returns after ~10 minutes
> 
> What we need:
> - Someone familiar with the registration cache code to analyze the memory pattern
> 
> Incident channel: #inc-0847-sip-reg-failures"

The good escalation gives the receiving team everything they need to start helping immediately: context, impact, what's been tried, and what specifically is needed. They join the incident channel fully briefed rather than asking 10 catch-up questions.

## The "Too Many Cooks" Problem

Major incidents attract attention. Suddenly, 15 people are in the incident channel offering suggestions, asking questions, and running independent investigations. This is counterproductive — more people doesn't mean faster resolution.

The incident commander's role (from Lesson 108) is to manage this:

1. **Assign clear roles**: "Sarah investigates the application. Mike checks the network. Alex monitors metrics."
2. **Channel management**: Create a separate channel for stakeholder updates; keep the incident channel focused on technical work
3. **Redirect helpers**: "Thanks for joining. We have the technical investigation covered. Best way to help right now is [specific task] or monitoring #inc-status for updates."
4. **Protect the troubleshooters**: Shield active investigators from management questions and status requests

🔧 **NOC Tip:** Use a two-channel pattern: `#inc-0847-work` for technical troubleshooting (restricted participation) and `#inc-0847-status` for updates (everyone can read). This prevents well-meaning stakeholders from interrupting the investigation.

## Customer-Facing Communication

When incidents affect customers, communication must be:

**Timely**: Customers should learn about issues from your status page before they discover them through failed calls.

**Honest**: "We are experiencing issues" is better than pretending everything is fine while customers see failures.

**Actionable**: If customers can do something (use a backup route, retry later), tell them.

**Complete**: When resolved, explain what happened and what you're doing to prevent recurrence.

At Telnyx, customer-facing incident communication flows through the status page and direct notifications for enterprise customers. Account managers relay technical updates in business terms: "Your SIP trunk to the UK route is experiencing intermittent failures. We've identified the issue with our upstream carrier and expect resolution within 30 minutes. Calls to other destinations are unaffected."

## Real-World Scenario: The Executive Escalation

3 AM incident. The NOC team is 20 minutes in, making progress. Suddenly, the VP of Engineering joins the channel:

> VP: "What's going on? I got paged. Customer ABC Corp's CEO called our CEO."

**Bad response** (gets defensive):
> "We're handling it. The Kamailio htable module is corrupting registration entries due to a race condition in the concurrent write path..."

The VP doesn't need technical details. They need to answer their CEO's question.

**Good response:**
> "P1 incident, started 35 minutes ago. ~200 customers affected including ABC Corp. Cause identified — software bug in tonight's release. Rollback in progress, expected full recovery in 15 minutes. Status page and direct customer notifications already sent. I'll update you when resolved."

The VP now has everything needed: severity, impact, cause (high level), action, timeline. They can relay this upward and step back without micromanaging the response.

## Post-Incident Communication

After resolution, communication continues:

1. **Resolution notification**: Confirm the incident is over and services are restored
2. **Preliminary summary**: Same day — brief summary of what happened, duration, impact
3. **Post-mortem**: Within 48 hours — detailed analysis, root cause, action items
4. **Customer follow-up**: Account managers contact affected enterprise customers with the post-mortem summary

The post-mortem is your opportunity to rebuild trust through transparency. Customers who see a thorough, honest post-mortem with concrete preventive actions retain more confidence than customers who just see "resolved."

---

**Key Takeaways:**
1. Map stakeholders and notification lists *before* incidents happen — don't figure it out during the crisis
2. Proactive communication reduces interruptions and builds trust; silence breeds anxiety and escalations
3. Give honest ETAs with padding — under-promise, over-deliver; always include a next-update time
4. Good escalations include context, impact, what's been tried, and what specific help is needed
5. Use two-channel patterns to separate technical work from stakeholder updates
6. Post-incident communication (summary, post-mortem, customer follow-up) rebuilds trust through transparency

**Next: Lesson 171 — Documentation as a Discipline**
