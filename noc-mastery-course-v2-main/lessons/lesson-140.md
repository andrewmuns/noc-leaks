# Lesson 140: Common Failure Pattern — Deployment-Related Failures
**Module 4 | Section 4.5 — Failure Patterns**
**⏱ ~7 min read | Prerequisites: Lesson 89, 96**

---

## Deployments: The Number One Cause of Incidents

Ask any seasoned SRE team what causes most of their incidents, and you'll hear the same answer: deployments. Across the industry, roughly 70% of outages correlate with a recent change — a code deployment, a configuration update, a database migration, or an infrastructure change.

This isn't surprising. Production systems in a steady state tend to stay stable. It's the introduction of change that creates risk. For NOC engineers, the first question when any incident begins should always be: **"What changed recently?"**

## Types of Deployment Failures

### Code Bugs
A new release introduces a bug that wasn't caught in testing. Perhaps a null pointer exception on an edge case, a race condition under high concurrency, or a logic error that only manifests with production data patterns.

In telecom: a new codec negotiation path that generates malformed SDP, a routing rule change that sends calls to the wrong carrier, or a billing calculation error that causes API 500s.

### Configuration Errors
A configuration change — environment variable, feature flag, routing table update — introduces incorrect values. These are particularly insidious because they often pass CI/CD checks (the YAML is valid) but the values are wrong.

Example: Changing a connection timeout from 5000 (milliseconds) to 5 (because someone assumed seconds), causing every downstream call to time out.

### Missing Dependencies
A new version requires a database migration, a new Kubernetes secret, or a new service that hasn't been deployed yet. The deployment succeeds (pods start) but the application fails at runtime when it can't find what it needs.

### Resource Changes
A new version consumes more CPU or memory than the previous one — perhaps due to a new feature or a dependency upgrade. Pods start getting OOMKilled or CPU-throttled, causing degraded performance that wasn't present before the deployment.

🔧 **NOC Tip:** When correlating deployments with incidents, don't just check the service that's failing. Check ALL recent deployments — the problem might be in a dependency. A new version of the billing service might break the call processing service even though the call processing service wasn't deployed.

## Correlating Deployments with Incidents

### Grafana Annotations
The most powerful correlation tool is deployment annotations in Grafana. Every deployment should create an annotation on relevant dashboards showing:
- What service was deployed
- What version (git SHA or tag)
- Who triggered the deployment
- Which environment/cluster

When an error spike appears on a Grafana panel and there's a deployment annotation right before it — that's your signal.

### ArgoCD Timeline
ArgoCD (Lesson 96) maintains a history of every sync operation. Use `argocd app history <app-name>` to see recent deployments with timestamps. Compare these timestamps with when errors began in Grafana.

### kubectl Rollout History
```bash
# Check deployment history
kubectl rollout history deployment/sip-proxy -n voice

# See details of a specific revision
kubectl rollout history deployment/sip-proxy -n voice --revision=42

# Check when pods were created (newer pods = recent deployment)
kubectl get pods -n voice -l app=sip-proxy --sort-by=.metadata.creationTimestamp
```

## The Rollback Decision

Once you've identified that a deployment caused an incident, the critical question is: **should you roll back?**

### Roll Back When:
- The issue is clearly caused by the deployment
- Customer impact is ongoing and growing
- The fix isn't immediately obvious
- The deployment changed many things (hard to isolate the problem)

### Don't Roll Back When:
- The deployment includes a database migration that can't be reversed
- The issue is minor and a forward fix is almost ready
- Rolling back would cause its own problems (breaking API changes, state incompatibilities)

### How to Roll Back

**Via kubectl:**
```bash
kubectl rollout undo deployment/sip-proxy -n voice
# Or to a specific revision:
kubectl rollout undo deployment/sip-proxy -n voice --to-revision=41
```

**Via ArgoCD:**
Revert the Git commit and sync, or manually sync to a previous revision. ArgoCD rollback through Git is preferred because it maintains the GitOps principle.

🔧 **NOC Tip:** Rollback isn't always instant. If the deployment created new database columns or changed data formats, rollback might cause data compatibility issues. Always check with the development team if you're unsure whether a rollback is safe.

## Canary and Progressive Deployments

The best defense against deployment failures is catching them early:

### Canary Deployment
Deploy the new version to a small percentage of traffic (e.g., 5%) and monitor for errors. If the canary shows problems, abort before the full rollout affects all users.

Metrics to watch during canary:
- Error rate comparison: canary vs. stable
- Latency comparison: canary vs. stable
- SIP response code distribution: canary vs. stable
- Memory/CPU usage: canary vs. stable

### Progressive Rollout
Instead of deploying to all pods simultaneously, deploy to one pod at a time with a pause between each. If any pod shows issues, halt the rollout.

Kubernetes supports this with `maxSurge` and `maxUnavailable` in the deployment strategy:
```yaml
strategy:
  rollingUpdate:
    maxSurge: 1         # Only one new pod at a time
    maxUnavailable: 0   # No reduction in healthy pods
```

## Post-Deployment Monitoring

Every deployment should be followed by active monitoring for at least 15-30 minutes:

1. **Error rates**: Any increase in 5xx responses?
2. **Latency**: Any increase in p99 response times?
3. **Pod health**: Any CrashLoopBackOff or OOMKilled?
4. **Business metrics**: Call completion rate, message delivery rate
5. **Resource usage**: Memory or CPU trending upward?

🔧 **NOC Tip:** Create a "deployment watchboard" in Grafana that shows all critical metrics on a single screen with deployment annotations. After every deployment, pull up this board and watch for 15 minutes. Most deployment-related issues manifest within the first 10 minutes.

## Real-World Scenario: The Silent Configuration Change

A platform engineer updates a Consul KV key that controls the SIP proxy's maximum concurrent calls per trunk. They change it from 1000 to 100 — intending to set it on a test trunk but accidentally targeting production.

There's no deployment (no pod restart, no ArgoCD sync), but the effect is immediate: customers start hitting trunk capacity limits. The SIP proxy returns 503 responses. The NOC sees a spike in 503s but finds no recent deployments.

**Lesson**: Configuration changes ARE deployments. They should be tracked, reviewed, and annotated the same way code deployments are. Check Consul KV change logs, feature flag changes, and routing table updates — not just ArgoCD.

## Prevention: The Deployment Checklist

Before every deployment:
- [ ] Change has been reviewed and approved
- [ ] Rollback procedure is documented and tested
- [ ] Database migrations are backward-compatible
- [ ] Monitoring dashboards are open and being watched
- [ ] The team knows a deployment is happening
- [ ] It's not Friday afternoon (seriously)

---

**Key Takeaways:**
1. Approximately 70% of incidents correlate with recent changes — always ask "what changed?" first
2. Grafana deployment annotations are the fastest way to correlate deployments with error onset
3. Roll back when customer impact is ongoing and the fix isn't immediately obvious
4. Canary deployments catch problems before they affect all traffic — use them for critical services
5. Configuration changes are deployments too — track them with the same rigor
6. Monitor actively for 15-30 minutes after every deployment with a dedicated watchboard

**Next: Lesson 125 — Common Failure Pattern: Network Partition and Split Brain**
