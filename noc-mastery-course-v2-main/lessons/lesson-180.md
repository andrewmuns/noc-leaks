# Lesson 180: ChatOps for Incident Management
**Module 5 | Section 5.4 — Automation**
**⏱ ~6 min read | Prerequisites: Lesson 163**

---

In Lesson 163, we covered ChatOps fundamentals — running operational commands through chat. Now we focus on ChatOps specifically for incident management, where the combination of automation, visibility, and real-time collaboration becomes most impactful.

During a major incident, communication is as important as technical troubleshooting. ChatOps for incident management automates the communication scaffolding so engineers can focus on fixing the problem.

## The Incident Channel Pattern

When an incident is declared, the first automation action should be creating a dedicated channel:

```
Engineer: !incident create "SIP registration failures on US-East cluster"

Bot: 🚨 Incident INC-2024-0847 Created
     Channel: #inc-0847-sip-reg-failures
     Severity: P2 (auto-classified, override with !severity P1)
     Commander: @sarah (on-call IC)
     Created: 2024-03-15 03:47:12 UTC
     
     Auto-invited: @noc-team, @sip-oncall, @platform-oncall
     Status page: Updated to "Investigating"
     
     📋 Incident checklist pinned to channel.
```

The bot automatically:
1. Creates a uniquely named channel
2. Invites relevant responders based on the affected service
3. Assigns the on-call incident commander
4. Updates the public status page
5. Pins an incident checklist to the channel
6. Starts the incident timeline

This happens in seconds. Manually, an engineer would spend 5-10 minutes creating a channel, finding and inviting the right people, updating the status page, and posting an initial summary.

## Timeline Tracking

The incident bot automatically records every significant event in the channel:

```
[03:47:12] 🚨 Incident created by @mike
[03:47:15] 👥 Auto-invited: @noc-team, @sip-oncall
[03:48:01] 📊 @sarah: !status sip-proxy-cluster-east
[03:48:03] 📊 Bot: 3 of 8 nodes showing degraded registrations
[03:52:17] 🔧 @sarah: !drain sip-proxy-04
[03:52:19] ✅ sip-proxy-04 drained from load balancer
[03:55:44] 📝 @sarah: Root cause identified — memory leak in registration module after last deploy
[04:01:30] 🔧 @mike: !rollback sip-proxy deployment v2.4.7
[04:03:15] ✅ Rollback to v2.4.6 complete on all nodes
[04:08:22] 📊 @sarah: !metrics registration-count --cluster east --last 30m
[04:08:24] 📊 Bot: Registration count recovering — 78% of baseline
[04:15:01] ✅ @sarah: !incident resolve "Rolled back to v2.4.6, registrations recovered"
```

When someone types `!timeline`, the bot formats this into a clean chronological summary. This timeline becomes the foundation of the post-mortem document.

🔧 **NOC Tip:** Train your team to annotate their findings in the incident channel, not just run commands. "Root cause identified — memory leak" is as important to the timeline as the commands that found it.

## Status Updates and Escalation

During incidents, multiple stakeholders need updates at different intervals and detail levels. ChatOps automates this:

```
Engineer: !update "We've identified a memory leak in the registration module 
          introduced in v2.4.7 deployed at 02:00 UTC. Rolling back to v2.4.6. 
          ETA for full recovery: 20 minutes."

Bot: 📢 Status Update Posted:
     → #inc-0847-sip-reg-failures (full technical detail)
     → #noc-management (summary: SIP registration issue, rollback in progress, ETA 20min)
     → Status page: "Identified — Rolling back affected deployment"
     → Customer notification queue: 3 affected enterprise customers flagged
```

One command updates multiple channels with appropriate detail levels. The engineer doesn't have to context-switch between the technical channel, management channel, and status page.

For escalation:

```
Engineer: !page database-team "Need DBA to verify registration DB state post-rollback"

Bot: 📟 Paging @database-oncall (currently: @alex)
     Context: INC-0847 — SIP registration failures
     Message: "Need DBA to verify registration DB state post-rollback"
     Auto-invited @alex to #inc-0847-sip-reg-failures
```

The page includes incident context, and the paged engineer is automatically invited to the incident channel so they can see the full history.

## Information Gathering Commands

During incidents, standardized queries prevent ad-hoc investigation sprawl:

```
!impact                    → Summarizes affected services, customer count, call volume impact
!affected-customers        → Lists customers experiencing degradation
!changes --last 4h         → Shows recent deployments, config changes, infrastructure changes
!similar-incidents         → Searches past incidents for similar patterns
!runbook sip-registration  → Links to the relevant runbook
```

The `!changes` command is particularly valuable. A huge percentage of incidents correlate with recent changes. Automatically surfacing "deployment v2.4.7 rolled out at 02:00 UTC to sip-proxy cluster" saves critical investigation time.

🔧 **NOC Tip:** The `!similar-incidents` command is a force multiplier. If INC-0612 had the same symptoms and a known fix, the current incident can be resolved in minutes instead of hours by referencing the previous resolution.

## Post-Incident Automation

When the incident is resolved:

```
Engineer: !incident resolve "Rolled back to v2.4.6. Registration counts fully recovered. 
          Root cause: memory leak in v2.4.7 registration caching module."

Bot: ✅ Incident INC-0847 Resolved
     Duration: 28 minutes (03:47 — 04:15 UTC)
     
     Auto-generated:
     → Post-mortem template: https://wiki/postmortems/INC-0847
        (pre-filled with timeline, participants, affected services)
     → Status page: "Resolved — SIP registration service operating normally"
     → Follow-up ticket: JIRA-4821 "Fix memory leak in registration caching"
     → Channel archived (read-only) for future reference
```

The post-mortem template is pre-filled with:
- Full timeline from the channel
- List of participants and their roles
- Affected services and customer impact
- Commands executed and their results
- Duration and resolution summary

This saves 30-60 minutes of manual post-mortem preparation and ensures nothing is forgotten.

## Real-World Scenario: Cascading Failure

3:15 AM — Multiple alerts fire simultaneously. Here's how ChatOps handles it:

```
[03:15:02] 🤖 Alert: SIP proxy CPU >90% on 4 nodes (sip-proxy-01,02,05,06)
[03:15:03] 🤖 Alert: CPS dropping — current 340/s vs baseline 890/s
[03:15:05] 🤖 Alert: ASR dropped to 31% on US-East

IC: !incident create "US-East capacity degradation — multiple SIP proxies overloaded"

Bot: 🚨 INC-0848 Created → #inc-0848-useast-capacity

IC: !changes --last 2h
Bot: 📋 Recent Changes:
     [02:45] DNS update: sip.telnyx.com weights changed (us-east: 25%→60%)
     [02:30] Firewall rule update on edge-fw-03
     No deployments in last 2h.

IC: The DNS weight change is suspicious. @network-team can you verify?

Network: !dns check sip.telnyx.com
Bot: 🔍 sip.telnyx.com resolution:
     US-East: 60% weight (was 25%) ⚠️ 
     US-West: 20% weight (was 35%)
     EU-West: 20% weight (was 40%)

IC: That's it. 60% of global traffic hitting US-East. 
    !page network-oncall "Emergency: DNS weights misconfigured, US-East overloaded"

Network: !dns revert sip.telnyx.com --to-snapshot 02:44
Bot: ✅ DNS reverted. Propagation ETA: 2-5 minutes.

[03:22:15] 📊 CPS recovering: 670/s and climbing
[03:25:01] 📊 All SIP proxy CPUs below 60%. ASR recovering: 42%
[03:30:00] ✅ INC-0848 resolved. Duration: 15 minutes.
```

The `!changes` command identified the root cause in under a minute. Without it, the team might have spent 20+ minutes investigating application-level causes.

## Building Your Incident ChatOps

Start simple and iterate:

1. **Week 1**: Implement `!incident create`, `!timeline`, `!incident resolve`
2. **Week 2**: Add `!update` with multi-channel posting and status page integration
3. **Week 3**: Add `!changes`, `!impact`, `!affected-customers`
4. **Week 4**: Add post-mortem auto-generation and `!similar-incidents`

Each addition compounds the value. Within a month, your incident management process will be measurably faster and more consistent.

---

**Key Takeaways:**
1. Auto-create dedicated incident channels with relevant responders, checklists, and status page updates
2. Automatic timeline tracking from channel activity becomes the post-mortem foundation
3. One `!update` command should propagate to all stakeholders at appropriate detail levels
4. `!changes` is the most valuable incident command — most incidents correlate with recent changes
5. Post-incident automation (post-mortem templates, follow-up tickets, archival) saves significant time
6. Build incrementally — start with create/timeline/resolve and add capabilities weekly

**Next: Lesson 165 — Infrastructure as Code — Ansible Basics for NOC**
