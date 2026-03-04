# Lesson 144: Maintenance Windows — Safe Deployment Practices
**Module 4 | Section 4.7 — Maintenance**
**⏱ ~7 min read | Prerequisites: Lesson 98, 100, 124**

---

## The Art of Changing Production Without Breaking It

Maintenance is inevitable. Servers need OS updates, applications need new versions, databases need schema changes, and certificates need renewal. The question isn't whether to perform maintenance, but how to do it safely.

Every maintenance operation carries risk. The goal is to minimize that risk through planning, gradual execution, and constant validation. NOC engineers are the safety net during maintenance — monitoring for problems and ready to halt or rollback if something goes wrong.

## Pre-Maintenance Planning

### Impact Assessment
Before any maintenance, answer these questions:

1. **What could go wrong?** List the failure modes. A server restart might cause active calls to drop. A database migration might lock a table. A network change might partition the cluster.

2. **What's the blast radius?** How many customers are affected if it fails? One customer's dedicated trunk? All customers in a region? Globally?

3. **What's the rollback plan?** How do you undo the change? Is rollback even possible? (Database column drops can't be rolled back.)

4. **How long will it take?** Estimate total maintenance time including validation. Add 50% buffer for unexpected issues.

5. **When is the safest time?** Use traffic pattern knowledge from Lesson 126. Low-traffic windows (2-5 AM local time for the affected region) minimize customer impact.

### The Maintenance Checklist

Before starting:
- [ ] Maintenance announcement sent to affected teams
- [ ] Status page updated (if customer-facing impact expected)
- [ ] Monitoring dashboards open and baseline noted
- [ ] Alerting thresholds reviewed (suppress expected alerts, keep unexpected ones)
- [ ] Rollback procedure documented with exact commands
- [ ] Communication channel established (Slack/Teams incident channel)
- [ ] On-call engineer aware and available for escalation

🔧 **NOC Tip:** Never start maintenance without confirming your monitoring is working. Run a quick check: can you see current metrics in Grafana? Are alerts flowing to OpsGenie? If monitoring is broken, you're flying blind during the most risky operation of the day.

## Graceful Drain: The Foundation of Safe Maintenance

The most important technique for safe maintenance is **graceful draining** — removing a server from service before touching it, allowing existing work to complete.

### Step 1: Remove from Load Balancer
Remove the server from the load balancer pool (HAProxy backend) or disable it in Consul so no new requests arrive.

```bash
# Consul maintenance mode — marks all services on the node as critical
consul maint -enable -reason "Planned maintenance - OS update"

# HAProxy — set server to drain state via stats socket
echo "set server backend/server01 state drain" | socat stdio /var/run/haproxy/admin.sock
```

### Step 2: Wait for In-Flight Requests to Complete
Active SIP calls don't end when you remove a server from rotation — they continue until the caller hangs up. Wait for active calls to drain:

```bash
# Monitor active calls on the server
watch -n 5 'curl -s localhost:8080/metrics | grep active_calls'

# Wait until active calls reach 0 (or an acceptable low number)
```

For SIP, this might take 5-30 minutes depending on call duration. For HTTP APIs, it's usually seconds.

### Step 3: Perform Maintenance
Now that no traffic is flowing, perform the actual work — restart, update, reconfigure.

### Step 4: Validate Health
After maintenance, verify the service is healthy before adding it back:

```bash
# Check service health
curl -f localhost:8080/health

# Check logs for errors
journalctl -u sip-proxy --since "5 minutes ago" | grep -i error

# Verify connectivity to dependencies
consul members | grep $(hostname)
```

### Step 5: Re-Enable Traffic
Return the server to the load balancer pool:

```bash
# Disable Consul maintenance mode
consul maint -disable

# Or re-enable in HAProxy
echo "set server backend/server01 state ready" | socat stdio /var/run/haproxy/admin.sock
```

### Step 6: Monitor
Watch the server for 5-10 minutes after re-enabling traffic. Verify it's handling requests successfully and metrics look normal.

🔧 **NOC Tip:** Don't drain and maintain all servers simultaneously. The "one at a time" rule ensures the remaining servers can handle the full traffic load. If you have 4 servers, maintain one while 3 handle traffic. Only proceed to the next after the first is fully validated.

## Progressive Rollout

For multi-server maintenance, progress one server at a time:

```
Server 1: Drain → Maintain → Validate → Re-enable → Monitor 10 min
Server 2: Drain → Maintain → Validate → Re-enable → Monitor 10 min
Server 3: Drain → Maintain → Validate → Re-enable → Monitor 10 min
Server 4: Drain → Maintain → Validate → Re-enable → Monitor 10 min
```

If Server 2 shows problems after maintenance, **STOP**. Don't continue to Server 3. Investigate the issue, fix it, and only proceed when Server 2 is confirmed healthy.

## Alert Suppression During Maintenance

Expected maintenance generates expected alerts. Server going into Consul maintenance mode triggers "service critical" alerts. Pod restarts trigger "pod not ready" alerts.

Suppress these expected alerts to avoid:
1. Alert fatigue (NOC ignores all alerts during maintenance)
2. Masking real problems (a genuine issue hidden among expected alerts)

```bash
# Alertmanager silence for specific server
amtool silence add \
  alertname="ServiceDown" \
  instance="server01" \
  --comment="Planned maintenance" \
  --duration="2h"
```

**But**: Only suppress alerts for the specific server being maintained. Keep alerts active for all other servers. If an unrelated issue occurs during maintenance, you need to know.

🔧 **NOC Tip:** Set alert silences with explicit end times. If maintenance runs long and you forget to clear the silence, alerts remain suppressed after maintenance completes — potentially hiding real issues. Always set silences to expire automatically.

## Database Maintenance Specifics

Database maintenance is the highest-risk maintenance type because it can't always be rolled back:

- **Schema migrations**: Use backward-compatible changes. Add columns before the code that uses them. Never drop columns until the old code is fully decommissioned.
- **Index creation**: Use `CREATE INDEX CONCURRENTLY` to avoid table locks (Lesson 122).
- **Table locks**: Any operation that acquires an exclusive table lock will block all queries. Schedule during absolute minimum traffic.
- **Replication impact**: Schema changes must be compatible with replicas. Test on replicas first.

## Post-Maintenance Validation

After completing all maintenance:

1. **Full service check**: All servers running, all health checks passing
2. **Traffic distribution**: Load is balanced evenly across all servers
3. **Error rate comparison**: Current error rate matches pre-maintenance baseline
4. **Latency comparison**: Response times match pre-maintenance baseline
5. **Functional test**: Place a test call, send a test message, hit the API
6. **Remove silences**: Clear all alert suppressions
7. **Update status page**: Mark maintenance as completed

---

**Key Takeaways:**
1. Every maintenance operation needs an impact assessment, rollback plan, and defined maintenance window
2. Graceful draining — removing from rotation, waiting for in-flight work to complete — is the foundation of safe maintenance
3. Progress one server at a time, validating each before proceeding to the next
4. Suppress only expected alerts on the specific server being maintained — keep all other alerting active
5. Database maintenance is highest-risk because it's often irreversible — use backward-compatible changes
6. Post-maintenance validation should compare error rates and latency to pre-maintenance baselines

**Next: Lesson 129 — Post-Mortem Writing: Learning from Incidents**
