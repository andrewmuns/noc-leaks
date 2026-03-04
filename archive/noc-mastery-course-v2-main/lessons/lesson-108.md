# Lesson 108: Namespaces, Resource Limits, and Multi-Tenancy

**Module 3 | Section 3.2 — Kubernetes**
**⏱ ~6 min read | Prerequisites: Lesson 88**

---

In a telecom platform like Telnyx, dozens of services run on the same Kubernetes cluster: SIP proxies, media servers, billing engines, API gateways, messaging pipelines, and more. Without boundaries, a runaway billing service could starve the SIP proxy of memory, causing call failures. Namespaces and resource limits prevent this by creating isolation within a shared cluster.

## Namespaces: Logical Cluster Partitioning

A namespace is a virtual cluster within a physical cluster. Resources in one namespace are isolated from (and mostly invisible to) resources in another.

```bash
kubectl get namespaces
# NAME              STATUS   AGE
# default           Active   180d
# kube-system       Active   180d
# voice-services    Active   90d
# messaging         Active   90d
# billing           Active   90d
# monitoring        Active   90d
```

Each team or product gets its own namespace. The voice team deploys SIP proxies and media servers in `voice-services`. The messaging team deploys SMS pipeline components in `messaging`. This creates clear ownership and prevents naming collisions — both teams can have a service called `gateway` without conflict.

Namespaces are an organizational tool, not a security boundary by default. Without Network Policies (covered in Lesson 90), pods in different namespaces can still communicate freely.

🔧 **NOC Tip:** When investigating issues, always specify the namespace. `kubectl get pods` only shows the `default` namespace. Use `kubectl get pods -n voice-services` or `kubectl get pods --all-namespaces` (abbreviated `-A`) to see everything. Most Telnyx services are NOT in the default namespace.

## Resource Requests and Limits: The Guarantee and the Cap

Every container in Kubernetes can declare two resource values for CPU and memory:

- **Request**: The *minimum guarantee*. The scheduler won't place the pod on a node unless this much is available.
- **Limit**: The *maximum allowed*. The container cannot use more than this.

```yaml
resources:
  requests:
    cpu: "500m"      # 500 millicores = 0.5 CPU core
    memory: "512Mi"  # 512 MiB guaranteed
  limits:
    cpu: "2000m"     # Can burst up to 2 cores
    memory: "1Gi"    # Hard cap at 1 GiB
```

The gap between request and limit is the *burstable range*. A container requesting 500m CPU but limited to 2000m can burst to 2 cores when the node has spare capacity, but is only guaranteed 500m during contention.

### Why This Matters for Telecom

SIP proxies need predictable latency. If a billing batch job consumes all CPU on a node, SIP processing stalls and calls fail. Proper resource requests ensure the SIP proxy always gets its guaranteed CPU, regardless of what other pods are doing.

## OOMKilled: The Most Common Resource Failure

When a container exceeds its memory limit, the Linux kernel's OOM (Out of Memory) killer terminates it immediately. Kubernetes reports this as `OOMKilled`:

```bash
kubectl describe pod sip-proxy-7d4f8c-x9k2n
# ...
# Last State:     Terminated
#   Reason:       OOMKilled
#   Exit Code:    137
# ...
```

Exit code 137 = 128 + 9 (SIGKILL). The container was forcibly killed — no graceful shutdown, no cleanup. For a SIP proxy, this means all active calls on that instance are dropped immediately.

**Why does it happen?**
- Memory leak in the application (gradual increase over hours/days)
- Traffic spike causing more concurrent connections than expected
- Limit set too low for the actual workload
- JVM heap misconfigured (Java services are notorious for this)

🔧 **NOC Tip:** When you see repeated OOMKilled events for a service, check Grafana for the container's memory usage over the last 24-48 hours. If memory climbs steadily until hitting the limit, it's likely a memory leak — escalate to the development team. If memory spikes suddenly during traffic peaks, the limit may need increasing.

## CPU Throttling: Death by a Thousand Cuts

Unlike memory (hard kill), CPU limits are enforced by *throttling*. When a container tries to exceed its CPU limit, the kernel delays its execution:

```bash
# In Grafana or /sys/fs/cgroup:
container_cpu_cfs_throttled_periods_total  # How often throttling occurred
container_cpu_cfs_throttled_seconds_total  # Total time spent throttled
```

CPU throttling doesn't crash the container — it silently degrades performance. A SIP proxy that's being throttled processes INVITE messages slower, causing increased call setup latency and eventually timeouts (SIP Timer B = 32 seconds).

This is insidious because the pod appears "Running" and "Healthy" but is actually underperforming. Customers experience slow call setup or intermittent timeouts, and standard health checks pass because the container is technically responsive — just slow.

🔧 **NOC Tip:** If you see increased SIP response latency without clear network issues, check CPU throttling for the SIP proxy pods: `kubectl top pods -n voice-services`. Compare actual CPU usage to the limit. If pods are consistently hitting their CPU limit, they need either higher limits or more replicas to distribute load.

## LimitRanges: Default and Maximum Limits per Namespace

A LimitRange sets defaults and maximums for a namespace, catching pods that don't declare resources:

```yaml
apiVersion: v1
kind: LimitRange
metadata:
  name: default-limits
  namespace: voice-services
spec:
  limits:
    - default:
        cpu: "1000m"
        memory: "512Mi"
      defaultRequest:
        cpu: "250m"
        memory: "256Mi"
      max:
        cpu: "4000m"
        memory: "4Gi"
      type: Container
```

Any container in `voice-services` without explicit resources gets the default values. No container can request more than the `max`. This prevents a misconfigured deployment from requesting 64 CPUs and blocking scheduling for everything else.

## ResourceQuotas: Namespace-Level Budgets

While LimitRanges control individual containers, ResourceQuotas control the *total* resources a namespace can consume:

```yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: voice-quota
  namespace: voice-services
spec:
  hard:
    requests.cpu: "100"
    requests.memory: "200Gi"
    limits.cpu: "200"
    limits.memory: "400Gi"
    pods: "500"
```

The entire `voice-services` namespace cannot exceed 100 CPU cores of requests or 500 pods. This prevents one team from accidentally consuming the entire cluster during a horizontal scaling event.

## Real-World Troubleshooting Scenario

**Situation:** The messaging team deployed a new version of their SMS gateway. Pods are stuck in `Pending` state and messages are queuing up.

**Investigation:**
```bash
kubectl describe pod sms-gateway-abc123 -n messaging
# Events:
#   Warning  FailedScheduling  0/20 nodes are available:
#   20 Insufficient memory.
```

```bash
kubectl describe resourcequota -n messaging
# Used:    requests.memory = 195Gi
# Hard:    requests.memory = 200Gi
```

The namespace is nearly at its memory quota. The new deployment increased memory requests per pod, and there isn't enough quota headroom for all replicas.

**Resolution:** Either increase the ResourceQuota (if cluster capacity allows) or reduce memory requests per pod. In the immediate term, scale down the old deployment to free quota for the new one.

## Quality of Service (QoS) Classes

Kubernetes assigns pods QoS classes based on their resource configuration:

- **Guaranteed**: Requests = Limits for all containers. Highest priority. Never evicted unless exceeding limits.
- **Burstable**: Requests < Limits. Medium priority. Evicted after BestEffort pods.
- **BestEffort**: No requests or limits set. First to be evicted under pressure.

For critical telecom workloads (SIP proxies, media servers), always use **Guaranteed** QoS — set requests equal to limits. This ensures the pod gets exactly what it needs and is the last to be evicted during node pressure.

---

**Key Takeaways:**

1. Namespaces logically partition a cluster — always use `-n <namespace>` or `-A` with kubectl
2. Resource requests guarantee minimum resources; limits cap maximum usage
3. OOMKilled (exit code 137) means a container exceeded its memory limit and was forcibly terminated
4. CPU throttling silently degrades performance without crashing pods — check throttling metrics when latency increases
5. LimitRanges set per-container defaults; ResourceQuotas set per-namespace totals
6. Critical telecom services should use Guaranteed QoS (requests = limits) to avoid eviction

**Next: Lesson 93 — Kubernetes Troubleshooting — Essential kubectl Commands**
