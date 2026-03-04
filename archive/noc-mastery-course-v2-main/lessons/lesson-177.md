# Lesson 177: Building NOC Runbooks — Structure and Best Practices
**Module 5 | Section 5.4 — Automation**
**⏱ ~7 min read | Prerequisites: Lessons 108, 157**

---

## What Separates Good NOC Teams from Great Ones

The difference between a NOC that resolves incidents in 5 minutes and one that takes 45 minutes is rarely technical skill — it's **runbooks**. A runbook captures the collective experience of every engineer who has ever debugged a particular problem and encodes it into a repeatable procedure.

Without runbooks, every incident is a fresh puzzle. With them, the solution to a known problem is a document away — even for the newest engineer on the team, at 3 AM, during their first week.

## Runbook Structure

Every runbook follows the same pattern. Consistency matters — when an engineer reaches for a runbook under pressure, they need to find information in the same place every time.

### Template

```markdown
# Runbook: [Alert Name / Problem Description]
**Last Updated:** YYYY-MM-DD | **Owner:** [Team/Person]
**Severity:** P1/P2/P3 | **Estimated Resolution Time:** X minutes

## Trigger
What alert, symptom, or customer report activates this runbook.

## Impact Assessment
- What services are affected?
- Who is impacted (all customers, specific region, single account)?
- What is the business impact?

## Diagnosis Steps
1. Step one (with exact commands)
2. Step two
3. Decision point: if X, go to Step 4a. If Y, go to Step 4b.

## Resolution Steps
### Scenario A: [Root Cause 1]
1. Action step with exact command
2. Verification step

### Scenario B: [Root Cause 2]
1. Different action step
2. Verification step

## Escalation
- When to escalate: [criteria]
- Who to escalate to: [team/person/PagerDuty service]
- What information to include

## Verification
How to confirm the problem is actually resolved.

## Post-Resolution
- What follow-up actions are needed?
- What should be documented?
```

## Writing for the 3 AM Reader

The most important principle: **write for the engineer who has never seen this problem before, is exhausted, and under pressure.**

### Bad Runbook Example
```
Check the SIP proxy logs for errors. If you see 503s, there might be a 
capacity issue. Try restarting the service or checking the database.
```

### Good Runbook Example
```markdown
## Diagnosis Step 1: Check SIP Proxy Error Rate

Run this on the affected SIP proxy:
​```bash
grep -c "503 Service Unavailable" /var/log/kamailio/kamailio.log | tail -1
​```

- If count > 100 in the last 5 minutes → **Capacity issue** → Go to Resolution A
- If count < 10 → **Not a proxy issue** → Go to Diagnosis Step 2

## Resolution A: SIP Proxy Capacity Exhaustion

1. Check current connection count:
   ​```bash
   kamctl stats dialog | grep active_dialogs
   ​```

2. If active_dialogs > 8000 (80% of max_connections=10000):
   ​```bash
   # Drain the proxy from the load balancer first
   consul maint -enable -reason "capacity exhaustion - draining"
   
   # Wait 60 seconds for active calls to complete
   sleep 60
   
   # Restart Kamailio
   sudo systemctl restart kamailio
   
   # Verify it's back
   systemctl is-active kamailio
   
   # Re-enable in load balancer
   consul maint -disable
   ​```

3. Verify: Error rate should drop within 2 minutes.
```

The difference: exact commands, copy-pasteable, clear decision logic, step-by-step with verification.

🔧 **NOC Tip:** Include the exact `grep` patterns, exact `kubectl` commands, exact dashboard URLs. Don't say "check the dashboard" — say "open https://grafana.internal/d/sip-proxy?orgId=1 and look at the 'Active Calls' panel."

## Decision Trees

Complex problems have multiple possible root causes. Decision trees guide the engineer through diagnosis.

```markdown
## Diagnosis Flow

Alert: "ASR Below Threshold"

1. Is the drop across ALL carriers?
   - YES → Go to Step 2 (Internal issue)
   - NO → Go to Step 5 (Carrier-specific issue)

2. Check SIP proxy health:
   ​```bash
   for proxy in sip-proxy-{01..06}; do
       echo -n "$proxy: "
       ssh $proxy "systemctl is-active kamailio"
   done
   ​```
   - All healthy → Go to Step 3
   - Any down → Go to Resolution B (Restart failed proxy)

3. Check database connectivity:
   ​```bash
   psql -h db-primary -c "SELECT 1;" -t
   ​```
   - Success → Go to Step 4
   - Failure → Go to Resolution C (Database issue)

4. Check for network issues:
   ​```bash
   mtr -rn -c 20 upstream-carrier-gateway.example.com
   ​```
   - Packet loss > 5% → Escalate to Network Engineering
   - No loss → Escalate to SIP Engineering

5. Carrier-specific investigation:
   Which carrier is affected?
   ​```sql
   -- Run on ClickHouse
   SELECT carrier, count() AS total,
          countIf(status='answered')/count()*100 AS asr
   FROM cdrs
   WHERE timestamp > now() - INTERVAL 30 MINUTE
   GROUP BY carrier ORDER BY total DESC
   ​```
   - Single carrier ASR drop → Contact carrier operations team
   - Multiple carriers in same region → Regional network issue
```

## Copy-Paste Commands: Make Them Perfect

Every command in a runbook should be immediately executable. Test them. Verify they work.

Common mistakes:
- **Placeholder values not marked**: Use `<CUSTOMER_ID>` with angle brackets to make placeholders obvious
- **Missing context**: Add comments explaining what the output should look like
- **Wrong user/permissions**: Specify if `sudo` is needed
- **Environment-specific paths**: Use variables or note the correct path per environment

```markdown
## Check customer's SIP registration status

Replace `<CUSTOMER_IP>` with the customer's source IP:

​```bash
# Search Kamailio registration database
kamcmd ul.lookup location <CUSTOMER_IP>

# Expected output for active registration:
# AOR: sip:user@domain
# Contact: sip:user@<CUSTOMER_IP>:5060
# Expires: 3600
# 
# If "404 Not Found" → Customer is not registered
​```
```

## Runbook Maintenance: The Hard Part

The hardest part of runbooks isn't writing them — it's keeping them current. Outdated runbooks are worse than no runbooks because they waste time and can lead engineers to wrong conclusions.

### Freshness Indicators
Add a visible last-updated date and owner to every runbook. If a runbook hasn't been reviewed in 6 months, mark it as stale.

### Post-Incident Updates
After every incident, ask: "Does our runbook cover this scenario?" If not, update it. If the existing steps didn't work, fix them. This is the single most effective way to improve runbooks.

### Review Schedule
- **After every incident**: Update the relevant runbook
- **Monthly**: Review the 10 most-used runbooks for accuracy
- **Quarterly**: Archive runbooks for decommissioned services
- **On-call engineers**: Flag outdated steps during their shift

🔧 **NOC Tip:** Add a "Last Verified" date separate from "Last Updated." A runbook might not need content changes but should be periodically verified that the commands still work, dashboard URLs are still valid, and escalation contacts are still correct.

## Runbook Organization

A NOC might have hundreds of runbooks. Organization determines whether engineers find the right one quickly.

### By Alert Name
The most natural organization: alert fires → search for runbook by alert name.

```
runbooks/
├── alerts/
│   ├── asr-below-threshold.md
│   ├── cpu-high-sip-proxy.md
│   ├── database-replication-lag.md
│   ├── disk-usage-critical.md
│   └── sip-503-spike.md
├── procedures/
│   ├── rolling-restart-sip-proxies.md
│   ├── database-failover.md
│   └── carrier-maintenance-window.md
└── investigations/
    ├── one-way-audio.md
    ├── call-quality-degradation.md
    └── customer-cannot-register.md
```

### Cross-Referencing
Runbooks should reference each other. The "ASR Below Threshold" runbook should link to "SIP Proxy Restart" and "Database Failover" runbooks rather than duplicating those procedures.

## The Automation Progression

Runbooks naturally evolve toward automation:

1. **Fully manual**: Document with copy-paste commands
2. **Semi-automated**: Script handles diagnosis; human decides the action
3. **Supervised automated**: Script handles everything; human approves
4. **Fully automated**: Script detects, diagnoses, acts, and verifies autonomously

Not every runbook should reach level 4. Start with frequently triggered, well-understood, low-risk procedures (as we'll explore in Lesson 162).

---

**Key Takeaways:**
1. Runbooks encode team experience into repeatable procedures — they're the difference between 5-minute and 45-minute resolutions
2. Write for the 3 AM reader: exact commands, clear decision logic, copy-pasteable
3. Decision trees guide engineers through diagnosis when multiple root causes are possible
4. Post-incident runbook updates are the most effective improvement mechanism
5. Maintain freshness with "Last Verified" dates and regular review schedules
6. Organize by alert name for fastest discovery during incidents

**Next: Lesson 162 — Automating Runbooks — From Manual to Scripted**
