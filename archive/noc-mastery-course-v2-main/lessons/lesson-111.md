# Lesson 111: GitOps — Declarative Infrastructure from Git

**Module 3 | Section 3.3 — ArgoCD/GitOps**
**⏱ ~7 min read | Prerequisites: Lesson 89**

---

Imagine trying to answer "what changed?" during a 3 AM incident with no audit trail. Someone SSH'd into production and ran `kubectl apply` manually. No record of what was changed, when, or why. Now imagine a world where every infrastructure change is a Git commit — reviewed, approved, and reversible. That's GitOps.

## The Problem GitOps Solves

Traditional deployment workflows are imperative: an engineer runs commands that mutate production state directly. This creates several problems:

1. **No audit trail**: Who changed what? When? Why?
2. **Configuration drift**: Production drifts from what was intended
3. **Inconsistency**: Staging and production diverge because manual steps were applied differently
4. **Risky rollbacks**: Rolling back means remembering (or guessing) the previous state
5. **Access sprawl**: Everyone who deploys needs cluster credentials

For a telecom platform handling millions of calls, these problems aren't theoretical — they cause incidents.

## The GitOps Principles

GitOps is built on four principles:

### 1. Declarative Configuration
Everything is described as desired state, not imperative commands. Instead of "scale sip-proxy to 10 replicas," the configuration *declares* `replicas: 10`. Kubernetes controllers reconcile reality to match.

This is native to Kubernetes. YAML manifests, Helm charts, and Kustomize overlays are all declarative — they describe what you want, not the steps to get there.

### 2. Git as the Single Source of Truth
All configuration lives in a Git repository. The repository is *the* authority on what should be running. If it's not in Git, it shouldn't be in the cluster.

```
infra-gitops/
├── voice-services/
│   ├── sip-proxy/
│   │   ├── deployment.yaml
│   │   ├── service.yaml
│   │   └── configmap.yaml
│   └── media-server/
│       ├── deployment.yaml
│       └── service.yaml
├── messaging/
│   ├── sms-gateway/
│   └── mms-processor/
└── monitoring/
    ├── prometheus/
    └── grafana/
```

### 3. Automated Reconciliation
A GitOps operator (like ArgoCD) continuously watches the Git repository and the cluster. When they diverge — because someone committed a change to Git, or because someone manually modified the cluster — the operator reconciles.

This is the key insight: Git *pulls* changes into the cluster, rather than engineers *pushing* changes. The operator is the only thing with write access to the cluster.

### 4. Drift Detection and Correction
If someone manually modifies a resource in the cluster (bypassing Git), the GitOps operator detects the drift and can either alert or automatically revert the change.

This prevents the "someone tweaked production and forgot to update the config" problem that plagues traditional operations.

## Why NOC Engineers Should Care

As a NOC engineer, GitOps gives you superpowers:

**"What changed?"** — Check the Git log. Every change has a commit message, author, timestamp, and diff. During an incident, you can see exactly what was deployed in the last hour.

```bash
git log --oneline --since="2 hours ago" -- voice-services/sip-proxy/
# a3b4c5d  Increase sip-proxy replicas to 12 for traffic spike
# f6e7d8c  Update sip-proxy image to v2.3.2 (fix memory leak)
```

**"Can we roll back?"** — Revert the Git commit. The GitOps operator applies the previous version automatically. No scrambling to remember the old image tag or configuration.

```bash
git revert a3b4c5d
git push
# ArgoCD detects the change and rolls back the deployment
```

**"Is production matching what we expect?"** — The GitOps operator's sync status tells you instantly whether the cluster matches Git or has drifted.

**"Who approved this change?"** — Pull request history shows the review and approval chain.

## The GitOps Deployment Workflow

Here's how a deployment actually flows in a GitOps environment:

1. **Developer** creates a pull request changing the image tag in `deployment.yaml`
2. **CI pipeline** runs tests, builds the image, pushes to registry
3. **Reviewer** approves the pull request after checking changes
4. **Merge** to main branch triggers the GitOps operator
5. **Operator** (ArgoCD) detects the change and applies it to the cluster
6. **Kubernetes** performs a rolling update (Lesson 89)
7. **Monitoring** verifies the new version is healthy

At no point does anyone run `kubectl apply` manually. The Git merge IS the deployment.

🔧 **NOC Tip:** During incidents, the Git commit history is your first stop for answering "what changed?" Check the timestamps of recent merges against when the incident started. If a deployment happened 5 minutes before errors spiked, it's likely the cause — and you can revert by reverting the Git commit.

## Environments and Promotion

GitOps handles multiple environments through directory structure or branch strategy:

```
infra-gitops/
├── staging/
│   └── voice-services/
│       └── sip-proxy/
│           └── deployment.yaml  # image: v2.3.2
└── production/
    └── voice-services/
        └── sip-proxy/
            └── deployment.yaml  # image: v2.3.1 (not promoted yet)
```

Promoting to production means copying the change from staging to production directories — another Git commit, another review.

## Real-World Troubleshooting Scenario

**Situation:** Call quality degraded 20 minutes ago. SIP proxy error rates spiked from 0.1% to 5%.

**Investigation:**
```bash
# Check recent deployments via Git
git log --oneline --since="30 minutes ago" -- production/voice-services/
# e9f8a7b  (25 min ago)  Update sip-proxy config: reduce max_connections to 500

# That commit reduced connection limits right before the problem started
# Check who approved it
git log -1 --format="%H %an: %s" e9f8a7b
# e9f8a7b John Smith: Update sip-proxy config: reduce max_connections to 500

# The reduced limit is causing connections to be rejected under load
# Revert immediately
git revert e9f8a7b
git push
# ArgoCD applies the revert within 3 minutes
```

**Total investigation and mitigation time: under 5 minutes.** Without GitOps, this would involve guessing what changed, checking multiple sources, and manually applying the fix.

## Limitations and Realities

GitOps isn't magic. Some considerations:

- **Secrets management**: Storing secrets in Git (even encrypted) requires careful handling. Tools like Sealed Secrets or External Secrets Operator help.
- **Emergency changes**: Sometimes you need to bypass the Git workflow for immediate mitigation. Document these and reconcile Git afterward.
- **Sync delays**: There's a lag between Git merge and cluster application (typically 1-3 minutes). During fast-moving incidents, this may feel slow.
- **Learning curve**: Teams accustomed to `kubectl apply` need to adapt to the PR workflow.

🔧 **NOC Tip:** If you must make an emergency change directly in the cluster (bypassing Git), ALWAYS file a follow-up ticket to reconcile Git with the actual state. Otherwise, the GitOps operator will eventually revert your emergency fix.

---

**Key Takeaways:**

1. GitOps uses Git as the single source of truth for all infrastructure configuration
2. Changes flow through Git commits and pull requests — providing audit trail, review, and easy rollback
3. A GitOps operator (ArgoCD) continuously reconciles cluster state with Git
4. Drift detection catches manual changes that bypass the Git workflow
5. During incidents, Git history is the fastest way to answer "what changed?"
6. Emergency changes bypassing Git must be reconciled afterward to prevent the operator from reverting them

**Next: Lesson 96 — ArgoCD — Application Deployment and Sync**
