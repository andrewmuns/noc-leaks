# Lesson 178: Automating Runbooks — From Manual to Scripted
**Module 5 | Section 5.4 — Automation**
**⏱ ~7 min read | Prerequisites: Lesson 158, 161**

---

Every NOC engineer has been there: it's 3 AM, an alert fires, and you're bleary-eyed executing the same 15-step runbook you've done a dozen times before. Step 8 says "restart the SIP proxy on the affected node" — but you accidentally restart the wrong one because you misread the hostname. The incident that should have taken 5 minutes now takes 45, with a side order of self-inflicted outage.

This is why runbook automation exists. Not to replace NOC engineers, but to eliminate the class of errors that humans reliably make when tired, stressed, or rushing.

## When to Automate (and When Not To)

Not every runbook should be automated. The sweet spot is procedures that are:

- **Frequent**: executed more than a few times per month
- **Well-understood**: the steps are stable and rarely change
- **Low-risk**: mistakes are recoverable, or the automation can be made safe
- **Deterministic**: given the same inputs, the same actions should occur

A runbook that says "assess the situation and use your judgment" is a poor automation candidate. A runbook that says "check if the SIP registration count on node X is below threshold Y, and if so, restart the registrar service" is a perfect one.

🔧 **NOC Tip:** Start by automating the *assessment* phase of runbooks, not the action phase. A script that collects all the diagnostic information and presents it to the engineer saves time without taking any risky actions.

## The Three-Phase Structure

Well-designed automated runbooks follow a three-phase structure:

### Phase 1: Assessment

Before taking any action, the script gathers context and validates that automation is appropriate:

```bash
# Assessment phase
current_registrations=$(curl -s http://sip-proxy:9090/metrics | grep registration_count)
service_status=$(systemctl is-active kamailio)
recent_restarts=$(journalctl -u kamailio --since "1 hour ago" | grep "Started" | wc -l)

# Pre-condition check: don't restart if already restarted recently
if [ "$recent_restarts" -gt 2 ]; then
    echo "ABORT: Service restarted $recent_restarts times in the last hour. Manual investigation needed."
    exit 1
fi
```

This is where safety lives. Pre-condition checks prevent the automation from making things worse. If the service has already been restarted three times in the last hour, blindly restarting again won't help — something deeper is wrong.

### Phase 2: Action

The actual remediation steps, executed with logging at every step:

```bash
# Action phase
log "Draining connections from $target_node"
consul maint -enable -service=sip-proxy -reason="automated-restart-$(date +%s)"
sleep 30  # Allow existing calls to complete

log "Restarting kamailio on $target_node"
systemctl restart kamailio

log "Waiting for service to become healthy"
wait_for_health "http://$target_node:8080/health" 60
```

Every action is logged with timestamps. The drain step ensures existing calls complete before the restart — something a rushed human might skip.

### Phase 3: Verification

After acting, verify the fix worked:

```bash
# Verification phase
new_registrations=$(curl -s http://sip-proxy:9090/metrics | grep registration_count)
if [ "$new_registrations" -gt "$threshold" ]; then
    log "SUCCESS: Registration count recovered to $new_registrations"
else
    log "FAILURE: Registration count still low at $new_registrations. Escalating."
    send_alert "Automated restart failed on $target_node. Manual investigation required."
    exit 1
fi
```

If verification fails, the automation escalates rather than retrying blindly. This is critical — automated retry loops without human oversight are how small problems become outages.

## Dry-Run Mode

Every automated runbook should support a `--dry-run` flag that shows exactly what *would* happen without making changes:

```
$ ./restart-sip-proxy.sh --dry-run --target sip-proxy-03

[DRY RUN] Would check pre-conditions on sip-proxy-03
[DRY RUN] Current registration count: 1,247 (threshold: 500)
[DRY RUN] Service status: active
[DRY RUN] Recent restarts: 0
[DRY RUN] Would enable maintenance mode in Consul
[DRY RUN] Would wait 30 seconds for connection drain
[DRY RUN] Would restart kamailio service
[DRY RUN] Would verify health within 60 seconds
```

Dry-run mode serves two purposes: it lets engineers verify the script will do the right thing before executing, and it's invaluable for training — new engineers can see what the automation does without risk.

🔧 **NOC Tip:** Make dry-run the *default* mode. Require an explicit `--execute` flag for real actions. This prevents accidental execution from command history or copy-paste errors.

## Logging and Audit Trails

Automated runbooks must log comprehensively. Every execution should record:

- **Who** triggered it (human or automated alert)
- **When** it ran (timestamps for every step)
- **What** it did (exact commands, parameters, targets)
- **What** it found (pre-condition check results, metrics before and after)
- **Outcome** (success, failure, partial success)

These logs feed into your incident timeline. When reviewing a 3 AM incident, you want to see exactly what the automation did and didn't do. At Telnyx, automated actions should integrate with your existing logging infrastructure — ship runbook execution logs to Graylog or Loki alongside application logs so everything is correlated.

## Safety Guards and Rollback

The most important safety guard is the **blast radius limit**. An automated runbook should never be able to affect more than a safe percentage of capacity at once:

```bash
# Never restart more than 1 node at a time
# Never restart if fewer than N healthy nodes remain
healthy_nodes=$(consul members -status=alive | grep sip-proxy | wc -l)
if [ "$healthy_nodes" -le 3 ]; then
    log "ABORT: Only $healthy_nodes healthy nodes. Cannot safely restart."
    exit 1
fi
```

Rollback capability depends on the action. For configuration changes, rollback means reverting to the previous config. For service restarts, there's no "undo" — but the verification phase catches failures quickly.

## Real-World Scenario: The 3 AM Registration Storm

A monitoring alert fires at 3:12 AM: SIP registration count on `sip-proxy-07` has dropped 60% in 5 minutes. The automated runbook activates:

1. **Assessment**: Checks pre-conditions — service is running but registration count is 412 (threshold: 1,000). No recent restarts. Memory usage is at 94%. The script identifies memory exhaustion as the likely cause.
2. **Action**: Enables maintenance mode in Consul (new registrations route elsewhere), waits 30 seconds for drain, restarts Kamailio.
3. **Verification**: After restart, registration count climbs to 890 within 2 minutes. Memory at 45%. Success.

Total time: 3 minutes. A human doing this manually at 3 AM would take 15-20 minutes minimum — if they didn't make mistakes.

## From Scripts to Platforms

As your automation matures, individual scripts evolve into platforms. Tools like Rundeck, StackStorm, or custom internal platforms provide:

- Web UI for triggering runbooks
- Role-based access control
- Execution history and audit logs
- Integration with alerting systems for auto-remediation
- Scheduling for maintenance tasks

The progression is: manual runbook → shell script → parameterized script with dry-run → integrated automation platform.

🔧 **NOC Tip:** Version control your automated runbooks in Git. Treat them like production code — review changes, test before deploying, and tag releases. A broken automation script at 3 AM is worse than no automation at all.

---

**Key Takeaways:**
1. Automate frequent, well-understood, low-risk procedures first — assessment before action
2. Structure automated runbooks in three phases: assessment, action, verification
3. Always implement dry-run mode, ideally as the default behavior
4. Log everything — who, when, what, and outcome — for audit trails and incident review
5. Safety guards (blast radius limits, pre-condition checks, escalation on failure) prevent automation from making things worse
6. Version control and test your automation scripts like production code

**Next: Lesson 163 — ChatOps — Operating Infrastructure Through Chat**
