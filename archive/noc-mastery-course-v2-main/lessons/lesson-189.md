# Lesson 189: Building Your Personal Runbook Library
**Module 6 | Section 6.2 — Career Development**
**⏱ ~6min read | Prerequisites: Lesson 172**
---

Every seasoned NOC engineer has a secret weapon: a personal runbook library. Not the shared wiki that's perpetually outdated, not the Confluence page last edited by someone who left two years ago — your own curated, battle-tested collection of procedures that you *know* work because you've used them.

In this lesson, you'll learn how to build, organize, and maintain a personal runbook library that accelerates your troubleshooting and makes you the engineer everyone turns to during outages.

---

## Why Personal Runbooks Beat Shared Wikis

Shared documentation is essential — but it has well-known failure modes:

| Problem | Shared Wiki | Personal Runbook |
|---------|-------------|-----------------|
| Ownership | Diffuse — "someone should update this" | You own it — you update it |
| Relevance | Generic, covers every edge case | Tailored to *your* role and shift patterns |
| Currency | Often stale (months or years old) | Updated after every use |
| Speed | Search through hundreds of pages | You know exactly where everything is |
| Context | Procedure only | Includes *your* notes, gotchas, mental models |

Personal runbooks don't *replace* shared documentation — they *complement* it. Think of shared wikis as the textbook and your personal runbook as your annotated lecture notes.

🔧 **NOC Tip:** At Telnyx, shared runbooks live in the internal wiki and are linked from PagerDuty escalation policies. Your personal runbook should reference these but add your own context: "Step 3 says restart the service — but check the connection pool first because 60% of the time that's the actual issue."

---

## Template for Personal Runbook Entries

Consistency is what makes a runbook *usable* under pressure. Here's a proven template:

```markdown
# [SYMPTOM or TITLE]
**Last used:** 2026-01-15
**Last updated:** 2026-01-15
**Confidence:** High | Medium | Low

## Symptoms
- What does the alert look like?
- What do customers report?
- What metrics move?

## Quick Check (< 2 minutes)
1. First command to run
2. What to look for in the output
3. Decision point: if X → go to Section A, if Y → go to Section B

## Investigation

### Section A: [Most Common Root Cause]
```bash
# Commands with actual hostnames/paths you use
kubectl get pods -n voice-gateway -o wide | grep -v Running
```
- Expected output vs. problem output
- What to do next

### Section B: [Second Most Common Root Cause]
...

## Resolution
- Steps to fix
- Validation commands
- Who to notify

## Gotchas & Notes
- Things that look like this problem but aren't
- Mistakes I've made before
- Related incidents: INC-2024-0847, INC-2025-0123

## References
- Link to shared wiki procedure
- Link to architecture diagram
- Relevant Slack threads
```

The key sections are **Quick Check** (what you do in the first two minutes) and **Gotchas** (the hard-won knowledge that only comes from experience).

🔧 **NOC Tip:** Include actual commands with real paths and service names — not generic placeholders. Under pressure at 3 AM, you want to copy-paste, not think about what to substitute. For Telnyx-specific services, include the exact `kubectl` namespace, the Grafana dashboard URL, and the specific panel to check.

---

## Categorizing by Symptom vs. System

There are two natural ways to organize runbooks, and the best libraries use both:

### Symptom-Based Organization (Primary)

This is how you'll actually *find* things during an incident. You don't think "I have a Kamailio problem" — you think "calls are failing with 503s."

```
symptoms/
├── calls-failing-503.md
├── one-way-audio.md
├── registration-timeouts.md
├── high-latency-media.md
├── api-5xx-errors.md
├── missing-cdrs.md
├── number-porting-stuck.md
└── customer-cannot-provision.md
```

### System-Based Organization (Secondary)

For deeper investigation or proactive work:

```
systems/
├── kamailio/
│   ├── connection-pool-exhaustion.md
│   ├── dialog-table-growth.md
│   └── tls-certificate-renewal.md
├── rtpengine/
│   ├── port-exhaustion.md
│   └── kernel-module-crash.md
├── kubernetes/
│   ├── pod-eviction-storms.md
│   └── pvc-stuck-pending.md
└── postgresql/
    ├── replication-lag.md
    └── long-running-queries.md
```

### Cross-Referencing

The magic is in the links between them:

```markdown
# calls-failing-503.md

## Quick Check
...

## Possible Causes
1. **Kamailio connection pool** → see [systems/kamailio/connection-pool-exhaustion.md]
2. **Upstream carrier outage** → see [symptoms/carrier-outage-detection.md]
3. **K8s pod failures** → see [systems/kubernetes/pod-eviction-storms.md]
```

🔧 **NOC Tip:** Start symptom-first. After every incident, ask yourself: "What was the symptom that woke me up?" Create or update the runbook entry for that symptom. The system-based entries will grow naturally as you investigate root causes.

---

## Version Control for Runbooks

Your runbooks are code. Treat them like code.

### Git-Based Workflow

```bash
# Initialize your runbook repo
mkdir ~/runbooks && cd ~/runbooks
git init

# Structure
mkdir -p symptoms systems templates

# After updating a runbook
git add symptoms/calls-failing-503.md
git commit -m "Updated 503 runbook: added carrier health check step

After INC-2026-0215, discovered that checking carrier 
health dashboard BEFORE restarting Kamailio saves 10min."

# Push to your private repo (GitLab, GitHub, etc.)
git remote add origin git@gitlab.internal:yourname/runbooks.git
git push origin main
```

### Why Version Control Matters

1. **History**: See how your understanding evolved over time
2. **Blame**: Find *when* you added a step and why (commit messages!)
3. **Branching**: Try a new approach without losing the old one
4. **Backup**: Your laptop dies — your runbooks survive
5. **Diffing**: After an incident, see exactly what you changed

```bash
# "When did I add that carrier check step?"
git log --oneline symptoms/calls-failing-503.md

# "What did this runbook look like 6 months ago?"
git show HEAD~50:symptoms/calls-failing-503.md
```

🔧 **NOC Tip:** Use meaningful commit messages tied to incident numbers. Six months from now, `git log --grep="INC-2026"` will show you every runbook change driven by a specific incident.

---

## Sharing Learnings with the Team

A personal runbook library shouldn't stay personal forever. The best NOC teams have a culture of sharing:

### The "Runbook Review" Practice

After resolving a significant incident:

1. **Update your personal runbook** with what you learned
2. **Identify what's generalizable** — strip out your personal shortcuts and notes
3. **Propose an update** to the shared wiki with the refined procedure
4. **Share the "gotcha"** in your team's Slack channel or during handoff

### From Personal to Shared

```
Personal runbook entry (detailed, your voice, your shortcuts)
    ↓ Extract the universal parts
Shared wiki update (formal, step-by-step, anyone can follow)
    ↓ Discuss in retro
Team training material (why this matters, how to recognize it)
```

### The Friday Runbook Share

Consider a weekly ritual: each engineer shares one runbook entry they created or updated that week. Five minutes, maximum value:

- "Here's a new symptom I documented: intermittent onetimeout on registrations from behind symmetric NAT. Here's the quick check..."
- "I updated the RTPEngine port exhaustion runbook — the old threshold was wrong, here's why..."

🔧 **NOC Tip:** At Telnyx, post your best runbook additions to the NOC team channel with a brief summary. Tag it with `#runbook-update` so others can find it. This builds a culture where documentation is valued, not an afterthought.

---

## Getting Started: Your First Five Runbooks

Don't try to document everything at once. Start with these five:

1. **The alert you see most often** — whatever wakes you up the most
2. **The incident you handled worst** — the one where you floundered; document what you wish you'd known
3. **The thing only you know** — that procedure only you seem to remember
4. **The most common customer complaint** — what does the support team escalate most?
5. **The scariest scenario** — the one you dread; having a runbook reduces the fear

```bash
# Quick start
mkdir -p ~/runbooks/{symptoms,systems,templates}
cp template.md ~/runbooks/symptoms/my-most-common-alert.md
# Edit it right now. Don't wait.
```

After your first five, momentum takes over. Every incident becomes an opportunity to update or create a runbook entry.

---

## Maintenance: Keeping Runbooks Alive

A runbook that's never updated is a liability — it gives false confidence.

### Update Triggers

- **After every use**: Did the steps work? What was missing?
- **After architecture changes**: New service deployed? Update affected runbooks
- **Monthly review**: Scan your library; archive anything obsolete
- **Confidence decay**: If you haven't used a runbook in 6+ months, mark confidence as "Low" and re-verify

### The "Last Used" Field

The most important metadata in your template:

```markdown
**Last used:** 2026-01-15
**Last updated:** 2026-01-15
**Confidence:** High
```

If `Last used` is more than 6 months ago, the runbook needs re-validation. Systems change. Commands change. Thresholds change.

---

## Key Takeaways

1. **Personal runbooks complement shared documentation** — they're your annotated, battle-tested notes tailored to your role and experience
2. **Use a consistent template** with Quick Check, Investigation, Resolution, and Gotchas sections so you can navigate them under pressure
3. **Organize by symptom first** (how you'll search during incidents) with cross-references to system-based entries
4. **Version control your runbooks** with Git — commit messages tied to incident numbers create a searchable history of your learning
5. **Share generalizable learnings** with the team through wiki updates, Slack posts, and weekly runbook review sessions
6. **Start with five runbooks** covering your most common, most painful, and most feared scenarios — then grow organically
7. **Maintain actively** — update after every use, review monthly, and mark confidence levels honestly

---

**Next: Lesson 174 — Mentoring and Knowledge Transfer**
