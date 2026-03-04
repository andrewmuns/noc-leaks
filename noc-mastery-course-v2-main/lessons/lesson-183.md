# Lesson 183: CI/CD Pipelines — Understanding the Deployment Pipeline
**Module 5 | Section 5.4 — Automation**
**⏱ ~7 min read | Prerequisites: Lesson 97-100, 165**

---

A significant percentage of NOC incidents begin with the same trigger: "We deployed something." Understanding CI/CD pipelines isn't optional for NOC engineers — it's essential for fast incident response. When a deployment causes problems, knowing how to find what changed, when it deployed, and how to roll back is the difference between a 5-minute recovery and an hour-long investigation.

## What CI/CD Actually Means

**Continuous Integration (CI)** is the practice of frequently merging code changes into a shared repository, where automated builds and tests validate each change. When a developer pushes code, the CI system automatically:

1. Pulls the code
2. Compiles/builds it
3. Runs automated tests
4. Reports pass/fail

**Continuous Delivery (CD)** extends this by automatically deploying validated builds to staging environments, with a manual approval gate before production. **Continuous Deployment** goes further — automatically deploying to production without human approval.

Most telecom platforms like Telnyx use Continuous Delivery with manual approval for production deployments, because the blast radius of a bad deployment on voice infrastructure is too high for full automation.

## The Pipeline Stages

A typical CI/CD pipeline flows through these stages:

```
Code Push → Build → Unit Tests → Integration Tests → Artifact → Staging Deploy → Staging Tests → Approval → Production Deploy → Smoke Tests → Monitoring
```

### Build Stage
Source code is compiled into a deployable artifact — a Docker image, a binary package, or a deployment bundle. Each build produces a unique, versioned artifact.

### Test Stages
Automated tests validate the build:
- **Unit tests**: Test individual functions in isolation
- **Integration tests**: Test service interactions (e.g., does the SIP proxy correctly handle INVITE?)
- **End-to-end tests**: Test complete call flows through the system

### Artifact Storage
Built artifacts are stored in a registry (Docker registry, package repository) with version tags. This is crucial — you need to deploy the *exact same artifact* that was tested, not rebuild from source.

### Staging Deployment
The artifact deploys to a staging environment that mirrors production. Staging may carry a percentage of real traffic (shadow mode) or run synthetic tests.

### Production Deployment
After approval, the same artifact deploys to production using one of several strategies.

🔧 **NOC Tip:** When an incident correlates with a deployment, the first thing to find is the **artifact version**. Every running service should expose its version (via `/version` endpoint, environment variable, or container image tag). `kubectl describe pod` or `docker inspect` reveals the image tag.

## Deployment Strategies

How code reaches production matters enormously for risk and rollback speed:

### Rolling Deployment
Nodes are updated one at a time (or in small batches). At any point, some nodes run the old version and some run the new version. This is what we did with Ansible in Lesson 166.

**Pros**: Simple, gradual, partial rollback possible
**Cons**: Mixed versions running simultaneously can cause issues if the versions aren't compatible

### Blue-Green Deployment
Two identical environments exist: "blue" (current production) and "green" (new version). Traffic switches from blue to green atomically.

**Pros**: Instant switch, clean rollback (switch back to blue)
**Cons**: Requires double the infrastructure, database migrations complicate things

### Canary Deployment
The new version deploys to a small subset (1-5%) of production. Metrics are compared between canary and baseline. If the canary is healthy, traffic gradually shifts.

**Pros**: Minimal blast radius, data-driven promotion
**Cons**: Requires sophisticated traffic splitting and metric comparison

At Telnyx, canary deployments are particularly valuable for SIP infrastructure. A new SIP proxy version handling 2% of calls lets you compare ASR, ACD, and MOS between the canary and the fleet before rolling out fully.

```
Canary (2% traffic):  ASR 94.2%, MOS 4.1, p99 latency 45ms
Baseline (98%):       ASR 94.0%, MOS 4.1, p99 latency 43ms
→ Canary healthy, promoting to 25%...
```

## What NOC Engineers Need to Know

You don't need to build pipelines, but you need to:

### 1. Find What Was Deployed
```bash
# What version is running?
kubectl get pods -n voice -o jsonpath='{.items[*].spec.containers[*].image}'
# → registry.telnyx.com/sip-proxy:v2.4.7

# When was it deployed?
kubectl rollout history deployment/sip-proxy -n voice
# REVISION  CHANGE-CAUSE
# 14        Deploy v2.4.6 - 2024-03-14T18:30:00Z
# 15        Deploy v2.4.7 - 2024-03-15T02:00:00Z

# What changed in v2.4.7?
# → Check the CI/CD system (Jenkins, GitLab CI, GitHub Actions) for the build log
# → Or check Git: git log v2.4.6..v2.4.7 --oneline
```

### 2. Correlate Deployments with Incidents
When metrics degrade, overlay deployment events on your Grafana dashboards. Most monitoring setups annotate deployments automatically. The pattern is unmistakable — a metric cliff that coincides with a deployment marker.

### 3. Trigger a Rollback
```bash
# Kubernetes rollback
kubectl rollout undo deployment/sip-proxy -n voice
# → Rolls back to the previous revision

# Or to a specific version
kubectl rollout undo deployment/sip-proxy -n voice --to-revision=14

# Monitor the rollback
kubectl rollout status deployment/sip-proxy -n voice
```

🔧 **NOC Tip:** Document the rollback command for every service in your runbooks. During an incident is not the time to figure out *how* to roll back. Pre-written commands with placeholders (`REVISION_NUMBER`) save critical minutes.

## Pipeline Visibility for NOC

NOC teams should have visibility into the deployment pipeline:

- **Deployment notifications**: Every production deploy posts to a NOC channel with service name, version, deployer, and change summary
- **Deployment dashboard**: A Grafana dashboard showing recent deployments across all services with timing and status
- **Change feed**: An aggregated view of all changes (deployments, config updates, infrastructure changes) — the `!changes` command from Lesson 164

The deployment notification should look like:
```
🚀 Deployment: sip-proxy v2.4.7 → production
   Deployer: @alice
   Changes: 3 commits
   - Fix registration cache memory leak (#4821)
   - Add metric for SDP parsing time (#4819)  
   - Update OpenSSL to 3.1.5 (#4815)
   Canary: 2% → running for 15min, metrics nominal
   Rollback: kubectl rollout undo deployment/sip-proxy -n voice
```

This gives NOC engineers everything they need: what changed, who to contact, and how to roll back.

## Real-World Scenario: The Silent Deployment

Tuesday night, 11 PM. ASR starts dropping gradually — from 94% to 91% to 87% over 90 minutes. No alerts initially because the drop is slow enough to stay within alert thresholds. An observant NOC engineer notices the trend.

First check: `!changes --last 4h`

```
[20:30] sip-proxy v2.4.7 deployed to production (canary 2% for 30min, then full rollout)
[21:15] billing-service v3.1.2 deployed to production
```

The SIP proxy deployment finished at approximately 20:45 (after canary promotion). ASR started declining around 21:00. Correlation isn't causation, but it's a strong signal.

The engineer checks: the canary metrics looked good during the 30-minute canary window. But the issue is a memory leak that only manifests under sustained load after 60+ minutes — the canary window was too short to catch it.

Decision: roll back.

```
!rollback sip-proxy v2.4.6
```

ASR recovers within 10 minutes. The post-mortem recommendation: extend canary windows for SIP proxy deployments to 2 hours, and add memory growth rate as a canary comparison metric.

## The NOC-Development Feedback Loop

NOC teams are uniquely positioned to improve the deployment pipeline. Every deployment-caused incident should feed back:

- **Canary criteria**: What metrics should canary analysis check?
- **Canary duration**: How long should canaries run?
- **Rollback automation**: Should this type of degradation trigger automatic rollback?
- **Test gaps**: What test would have caught this before production?

This feedback loop makes each deployment safer than the last.

---

**Key Takeaways:**
1. Most incidents correlate with changes — knowing how to find what deployed and when is critical
2. Understand deployment strategies (rolling, blue-green, canary) and their risk profiles
3. Every NOC engineer should know how to trigger a rollback for every service they support
4. Deployment notifications and dashboards give NOC visibility into the change pipeline
5. Canary deployments limit blast radius but only catch issues that manifest within the canary window
6. Feed incident learnings back to improve canary criteria, duration, and automated rollback triggers

**Next: Lesson 168 — Terraform Basics — Infrastructure Provisioning**
