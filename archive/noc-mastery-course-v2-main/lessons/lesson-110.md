# Lesson 110: Kubernetes Events and Debugging Scheduling Failures

**Module 3 | Section 3.2 — Kubernetes**
**⏱ ~6 min read | Prerequisites: Lesson 93**

---

Kubernetes Events are the cluster's activity log — a chronological record of what happened, to what resource, and why. When pods won't schedule, containers won't start, or services degrade, Events tell you what Kubernetes tried and where it failed.

## Understanding Kubernetes Events

Events are short-lived objects (default retention: 1 hour) that record state changes and errors. Every time the scheduler places a pod, a kubelet pulls an image, or a health check fails, an event is created.

```bash
# All events in a namespace, sorted chronologically
kubectl get events -n voice-services --sort-by='.metadata.creationTimestamp'

# Events cluster-wide
kubectl get events -A --sort-by='.lastTimestamp'

# Only warnings (skip normal events)
kubectl get events -n voice-services --field-selector type=Warning
```

Event output:
```
LAST SEEN   TYPE      REASON              OBJECT                       MESSAGE
2m          Warning   FailedScheduling    pod/sip-proxy-abc123         0/20 nodes are available: 10 Insufficient cpu, 10 Insufficient memory
5m          Normal    Pulling             pod/media-server-def456      Pulling image "registry/media:v3.1"
5m          Warning   Failed              pod/media-server-def456      Error: ImagePullBackOff
8m          Warning   Unhealthy           pod/billing-ghi789           Readiness probe failed: connection refused
```

Each event has: **Type** (Normal/Warning), **Reason** (machine-readable), **Object** (what it's about), and **Message** (human-readable detail).

🔧 **NOC Tip:** Events expire after 1 hour by default. If you're investigating something that happened 2 hours ago, events may be gone. Always check events early in an investigation. For longer retention, events should be shipped to your logging system (Loki/Graylog).

## Pod Status States and What They Mean

When you run `kubectl get pods`, the STATUS column is your first diagnostic signal:

### Pending
The pod is accepted but not yet running. Two sub-cases:

**Scheduling Pending** — The scheduler can't find a suitable node:
```
Events:
  Warning  FailedScheduling  0/20 nodes are available:
    10 Insufficient cpu, 5 Insufficient memory,
    5 node(s) had taint {dedicated: gpu} that the pod didn't tolerate
```

**Image Pending** — Scheduled to a node but waiting for image pull:
```
Events:
  Normal   Pulling  Pulling image "registry/sip-proxy:v2.3.1"
```

### CrashLoopBackOff
The container starts, crashes, and Kubernetes restarts it with exponential backoff (10s, 20s, 40s... up to 5 minutes).

**Common causes:**
- Application error on startup (missing config, bad database connection)
- OOMKilled immediately (memory limit too low for startup)
- Entrypoint/command misconfiguration
- Missing environment variables or secrets

```bash
# Check why it's crashing
kubectl logs <pod> -n <ns> --previous
kubectl describe pod <pod> -n <ns>  # Look at "Last State → Reason"
```

### ImagePullBackOff
Kubernetes can't pull the container image:
- Image tag doesn't exist (typo in deployment)
- Registry authentication failed (expired credentials)
- Registry is unreachable (network/DNS issue)

```bash
kubectl describe pod <pod> -n <ns>
# Events: Failed to pull image "registry/app:v99.99":
#   rpc error: code = NotFound desc = manifest unknown
```

### OOMKilled
Covered in Lesson 92 — the container exceeded its memory limit. Exit code 137.

### Evicted
The node ran out of resources (disk, memory) and Kubernetes evicted the pod to protect the node:

```
Status:    Failed
Reason:    Evicted
Message:   The node was low on resource: memory.
```

## Debugging Scheduling Failures

Scheduling failures are among the most common Kubernetes issues in production. The scheduler must find a node satisfying ALL of:

1. **Sufficient resources**: CPU and memory requests fit
2. **Node selectors/affinity**: Pod matches the required node labels
3. **Taints and tolerations**: Pod tolerates the node's taints
4. **Anti-affinity**: Pod doesn't conflict with pods already on the node
5. **PersistentVolume availability**: Required storage is accessible

### Insufficient Resources

```
0/20 nodes are available: 20 Insufficient memory
```

The cluster is full. All 20 nodes have less free memory than the pod requests.

**Investigate:**
```bash
kubectl top nodes
kubectl describe nodes | grep -A 5 "Allocated resources"
```

Look at the gap between "Requests" and "Allocatable" per node. If requests are near allocatable, the cluster needs more nodes or pods need reduced requests.

### Taints and Tolerations

Taints repel pods from nodes. Only pods with matching tolerations can schedule there.

```bash
kubectl describe node gpu-worker-01 | grep Taints
# Taints: dedicated=gpu:NoSchedule
```

If your pod doesn't have a matching toleration, it can't land on tainted nodes. This is intentional — GPU nodes are reserved for GPU workloads. But if ALL nodes are tainted (perhaps after maintenance), nothing schedules.

### Node Affinity

Pods can require specific node labels:
```yaml
affinity:
  nodeAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      nodeSelectorTerms:
        - matchExpressions:
            - key: topology.kubernetes.io/zone
              operator: In
              values: ["us-east-1a"]
```

If no nodes in `us-east-1a` exist or have capacity, the pod stays Pending.

### Pod Anti-Affinity

Critical services often use anti-affinity to spread across nodes:
```yaml
affinity:
  podAntiAffinity:
    requiredDuringSchedulingIgnoredDuringExecution:
      - labelSelector:
          matchLabels:
            app: sip-proxy
        topologyKey: kubernetes.io/hostname
```

This says "don't put two sip-proxy pods on the same node." If you have 10 nodes and want 12 replicas, 2 pods will stay Pending.

## Node Conditions

Nodes themselves can become unhealthy:

```bash
kubectl describe node worker-03 | grep -A 10 Conditions
```

| Condition | Meaning |
|-----------|---------|
| Ready=True | Node is healthy |
| Ready=False | Kubelet not responding |
| MemoryPressure=True | Node low on memory, evictions starting |
| DiskPressure=True | Node low on disk |
| PIDPressure=True | Too many processes |
| NetworkUnavailable=True | Network not configured |

When `Ready=False`, the node's pods are eventually evicted and rescheduled. When `MemoryPressure=True`, BestEffort pods are evicted first (remember QoS classes from Lesson 92).

## Real-World Scenario

**Alert:** `SIPProxyReplicasMismatch` — desired replicas: 10, available: 7.

```bash
# Find the missing pods
kubectl get pods -n voice-services -l app=sip-proxy
# 3 pods in Pending state

# Check why
kubectl describe pod sip-proxy-pending-abc -n voice-services
# FailedScheduling: 0/20 nodes available:
#   15 Insufficient cpu
#   5 had taint {maintenance: true} that pod didn't tolerate

# 5 nodes are in maintenance, reducing available capacity
# Remaining 15 nodes are nearly full

# Check node status
kubectl get nodes
# 5 nodes show SchedulingDisabled (cordoned for maintenance)

# Immediate action: if maintenance is complete, uncordon nodes
kubectl uncordon worker-node-16
kubectl uncordon worker-node-17
# ... etc

# Or: scale down less critical workloads temporarily
```

🔧 **NOC Tip:** Always check how many nodes are available before and during maintenance windows. If cordoning 5 nodes for maintenance drops available capacity below what's needed for current workloads, pods will go Pending. Plan maintenance during low-traffic windows and cordon one node at a time, waiting for its pods to reschedule before cordoning the next.

---

**Key Takeaways:**

1. Events are the cluster's activity log — check them early in any investigation (they expire in ~1 hour)
2. Pod statuses map to specific problems: Pending=scheduling, CrashLoopBackOff=app crash, ImagePullBackOff=registry issue, OOMKilled=memory
3. Scheduling failures come from insufficient resources, taints, affinity rules, or too few available nodes
4. `kubectl describe node` reveals capacity, allocated resources, and conditions
5. Node conditions (MemoryPressure, DiskPressure) trigger pod evictions starting with lowest QoS class
6. During maintenance, monitor available capacity to prevent scheduling failures

**Next: Lesson 95 — GitOps — Declarative Infrastructure from Git**
