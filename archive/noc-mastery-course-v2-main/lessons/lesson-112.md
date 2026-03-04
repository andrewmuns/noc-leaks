# Lesson 112: ArgoCD — Application Deployment and Sync

**Module 3 | Section 3.3 — ArgoCD/GitOps**
**⏱ ~7 min read | Prerequisites: Lesson 95**

---

ArgoCD is the GitOps operator that Telnyx uses to deploy and manage applications across Kubernetes clusters. It watches Git repositories and ensures cluster state matches what's declared in code. For NOC engineers, ArgoCD is how you understand what's deployed, when it changed, and how to roll back.

## ArgoCD Core Concepts

### Applications

An ArgoCD Application is the fundamental unit — it maps a **Git repository path** to a **Kubernetes namespace and cluster**:

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: sip-proxy
  namespace: argocd
spec:
  source:
    repoURL: https://git.telnyx.com/infra/gitops.git
    path: production/voice-services/sip-proxy
    targetRevision: main
  destination:
    server: https://kubernetes.default.svc
    namespace: voice-services
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
```

This says: "Keep the `voice-services` namespace in sync with the `production/voice-services/sip-proxy` directory in the `main` branch."

### Sync Status

Every Application has a **sync status** — the relationship between Git and the cluster:

| Status | Meaning | NOC Action |
|--------|---------|------------|
| **Synced** | Cluster matches Git | All good |
| **OutOfSync** | Cluster differs from Git | Change pending or drift detected |
| **Unknown** | ArgoCD can't determine status | ArgoCD or Git connectivity issue |

### Health Status

Independently, every Application has a **health status** — whether the deployed resources are working:

| Status | Meaning | NOC Action |
|--------|---------|------------|
| **Healthy** | All resources running normally | All good |
| **Progressing** | Deployment in progress (rolling update) | Wait and monitor |
| **Degraded** | Some resources unhealthy | Investigate pods/services |
| **Suspended** | Deployment paused (e.g., manual gate) | Check if intentional |
| **Missing** | Expected resources don't exist | Check sync status |

The combination tells the full story: `Synced + Healthy` = everything's fine. `Synced + Degraded` = deployed correctly but application is failing. `OutOfSync + Healthy` = a change is pending but current version works.

🔧 **NOC Tip:** During incidents, check ArgoCD health status first. If an application shows `Degraded`, click into it to see which specific resources are unhealthy — this is often faster than manually running kubectl commands because ArgoCD aggregates the health of all resources (Deployments, Services, ConfigMaps, etc.) in one view.

## The ArgoCD UI

The ArgoCD web UI is a powerful operational tool:

**Application List View**: Shows all applications with their sync and health status at a glance. During incidents, scan for red (Degraded) or yellow (Progressing/OutOfSync) indicators.

**Application Detail View**: Shows the resource tree — every Kubernetes object managed by this application, its status, and relationships (Deployment → ReplicaSet → Pods). You can see which pods are healthy, which are failing, and click through to logs and events.

**Diff View**: When an application is OutOfSync, the diff shows exactly what's different between Git and the cluster. This is invaluable for understanding pending changes or detecting unauthorized manual modifications.

**History View**: Shows the sync history — every deployment, who triggered it, the Git commit, and whether it succeeded.

## ArgoCD CLI for NOC Operations

For terminal-based workflows:

```bash
# List all applications and their status
argocd app list

# Get detailed status of an application
argocd app get sip-proxy

# View sync history
argocd app history sip-proxy

# Manually trigger a sync
argocd app sync sip-proxy

# Force a hard refresh (re-read Git)
argocd app get sip-proxy --hard-refresh

# Roll back to a previous revision
argocd app rollback sip-proxy <history-id>

# View application diff (what would change on sync)
argocd app diff sip-proxy
```

## Automated vs. Manual Sync

Applications can be configured for:

**Automatic sync**: Any change merged to the Git branch is automatically applied. This is the standard for most services. The `selfHeal` option also reverts manual cluster modifications.

**Manual sync**: Changes are staged in Git but not applied until someone triggers a sync. Used for high-risk changes where human verification is needed before deployment.

```yaml
syncPolicy:
  automated:
    prune: true       # Delete resources removed from Git
    selfHeal: true    # Revert manual cluster changes
```

`prune: true` means if you remove a ConfigMap from Git, ArgoCD deletes it from the cluster. Without prune, orphaned resources accumulate.

`selfHeal: true` means if someone runs `kubectl edit` to manually change a resource, ArgoCD detects the drift and reverts it. This enforces Git as the single source of truth.

## Deployment Rollback via ArgoCD

Rolling back in a GitOps world has two approaches:

### Git Revert (Preferred)
Revert the Git commit that caused the problem. ArgoCD syncs the reverted state automatically. This maintains the Git history and audit trail.

```bash
git revert <bad-commit>
git push origin main
# ArgoCD detects the change and applies it (~1-3 minutes)
```

### ArgoCD Rollback (Emergency)
Use ArgoCD's built-in rollback to restore a previous sync state immediately, without touching Git:

```bash
argocd app history sip-proxy
# ID  DATE                 REVISION
# 5   2026-02-22 12:00:00  a3b4c5d
# 4   2026-02-21 16:00:00  e9f8a7b  ← last known good

argocd app rollback sip-proxy 4
```

⚠️ **Warning:** After an ArgoCD rollback, the application shows `OutOfSync` because the cluster no longer matches Git (which still has the bad commit). You must still revert in Git to prevent ArgoCD from re-applying the bad change on the next sync.

## Real-World Incident Scenario

**Alert:** `APIGateway5xxRate` spiking to 15% at 02:30 AM.

**Step 1: Check ArgoCD**
```bash
argocd app list | grep api-gateway
# api-gateway  Synced  Degraded  ...
```

Synced + Degraded = deployed successfully but pods are unhealthy.

**Step 2: Check history**
```bash
argocd app history api-gateway
# ID  DATE                    REVISION
# 12  2026-02-22 02:15:00     c7d8e9f  ← 15 minutes before alert
# 11  2026-02-21 14:00:00     a1b2c3d
```

A deployment happened 15 minutes before the incident.

**Step 3: Check what changed**
Open the ArgoCD UI, navigate to api-gateway, look at the diff between revision 11 and 12. The change updated the API gateway image from v4.2.0 to v4.3.0.

**Step 4: Rollback**
```bash
argocd app rollback api-gateway 11
```

Error rate drops to normal within 2 minutes as old pods replace new ones.

**Step 5: Reconcile Git**
```bash
git revert c7d8e9f -m "Rollback: v4.3.0 caused 5xx errors, reverting to v4.2.0"
git push origin main
```

Now Git matches the cluster again.

🔧 **NOC Tip:** Bookmark the ArgoCD UI and keep it open during shifts. The application list view with sync and health status is the single fastest way to detect deployment-related problems. When an alert fires, glance at ArgoCD before diving into Grafana — if something just deployed and went Degraded, you've found your cause in seconds.

## Sync Waves and Hooks

For complex deployments, ArgoCD supports ordering with sync waves:

```yaml
metadata:
  annotations:
    argocd.argoproj.io/sync-wave: "1"  # Deploy after wave 0
```

Wave 0 resources deploy first (e.g., ConfigMaps, Secrets), then wave 1 (Deployments), then wave 2 (post-deployment tests). This ensures dependencies are ready before dependent services deploy.

---

**Key Takeaways:**

1. ArgoCD Applications map Git repository paths to Kubernetes namespaces
2. Sync status (Synced/OutOfSync) and health status (Healthy/Degraded) are independent — check both
3. `selfHeal: true` reverts unauthorized manual cluster changes, enforcing Git as source of truth
4. For rollbacks: use ArgoCD rollback for speed, then revert in Git to prevent re-sync of the bad change
5. ArgoCD sync history correlates deployment times with incidents — check it early during investigations
6. The ArgoCD UI provides the fastest overview of deployment health across all services

**Next: Lesson 97 — Consul — Service Discovery and Health Checking**
