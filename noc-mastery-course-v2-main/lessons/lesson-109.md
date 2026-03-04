# Lesson 109: Kubernetes Troubleshooting — Essential kubectl Commands

**Module 3 | Section 3.2 — Kubernetes**
**⏱ ~8 min read | Prerequisites: Lessons 87-92**

---

When an incident page fires at 2 AM, your ability to rapidly investigate Kubernetes resources determines how quickly you restore service. This lesson covers the essential kubectl commands every NOC engineer needs, organized by investigation workflow rather than alphabetical reference.

## The Investigation Workflow

Kubernetes troubleshooting follows a consistent pattern:

1. **What's broken?** — List resources, find unhealthy ones
2. **Why is it broken?** — Describe the resource, read events
3. **What does the application say?** — Read container logs
4. **What's happening inside?** — Exec into the container
5. **Is it a resource problem?** — Check CPU/memory usage

Let's walk through each step with real commands.

## Step 1: What's Broken? — kubectl get

`kubectl get` lists resources. The key is knowing which flags make the output useful:

```bash
# Basic pod listing — shows status at a glance
kubectl get pods -n voice-services

# Wide output — shows node placement and IP
kubectl get pods -n voice-services -o wide

# All namespaces — when you don't know which namespace
kubectl get pods -A

# Watch mode — live updates as status changes
kubectl get pods -n voice-services -w

# YAML output — full resource definition
kubectl get pod sip-proxy-7d4f8c-x9k2n -n voice-services -o yaml

# Filter by label
kubectl get pods -n voice-services -l app=sip-proxy

# Custom columns — show exactly what you need
kubectl get pods -A -o custom-columns=\
  NAMESPACE:.metadata.namespace,\
  NAME:.metadata.name,\
  STATUS:.status.phase,\
  RESTARTS:.status.containerStatuses[0].restartCount,\
  NODE:.spec.nodeName
```

**Quick status scan patterns:**

```bash
# Find all non-Running pods cluster-wide
kubectl get pods -A --field-selector status.phase!=Running

# Find pods with high restart counts (potential CrashLoopBackOff)
kubectl get pods -A --sort-by='.status.containerStatuses[0].restartCount'
```

🔧 **NOC Tip:** Start every investigation with `kubectl get pods -A | grep -v Running` to find all unhealthy pods across the cluster. This takes 2 seconds and immediately shows you CrashLoopBackOff, Pending, Error, and OOMKilled states.

## Step 2: Why Is It Broken? — kubectl describe

`kubectl describe` gives you the resource's full story: configuration, status, conditions, and — critically — **events**:

```bash
kubectl describe pod sip-proxy-7d4f8c-x9k2n -n voice-services
```

The output is long. Focus on these sections:

**Status/State section:**
```
State:          Waiting
  Reason:       CrashLoopBackOff
Last State:     Terminated
  Reason:       OOMKilled
  Exit Code:    137
  Started:      Sun, 22 Feb 2026 12:00:00 +0000
  Finished:     Sun, 22 Feb 2026 12:05:23 +0000
```

This tells you the container was OOMKilled and is now in CrashLoopBackOff — it keeps crashing and Kubernetes is backing off restart attempts.

**Conditions section:**
```
Conditions:
  Type              Status
  Initialized       True
  Ready             False
  ContainersReady   False
  PodScheduled      True
```

`Ready: False` means the pod won't receive traffic from Services. The readiness probe is failing.

**Events section (scroll to the bottom):**
```
Events:
  Warning  BackOff  2m    kubelet  Back-off restarting failed container
  Warning  OOMKilling  5m  kubelet  Memory cgroup out of memory: Killed process 12345
  Normal   Pulled    6m   kubelet  Container image "registry/sip-proxy:v2.3.1" already present
```

Events are chronological. Read them bottom-to-top for the narrative: image pulled → started → OOM killed → restarting → back-off.

**Describe works on any resource:**
```bash
kubectl describe deployment sip-proxy -n voice-services
kubectl describe service sip-proxy-svc -n voice-services
kubectl describe node worker-node-03
kubectl describe ingress api-ingress -n api
```

Describing a **node** shows capacity, allocated resources, and conditions — essential for diagnosing scheduling failures.

## Step 3: What Does the Application Say? — kubectl logs

Container logs are your window into application behavior:

```bash
# Current container logs
kubectl logs sip-proxy-7d4f8c-x9k2n -n voice-services

# Previous container logs (crashed container)
kubectl logs sip-proxy-7d4f8c-x9k2n -n voice-services --previous

# Follow logs in real-time (like tail -f)
kubectl logs -f sip-proxy-7d4f8c-x9k2n -n voice-services

# Last 100 lines only
kubectl logs --tail=100 sip-proxy-7d4f8c-x9k2n -n voice-services

# Logs since a specific time
kubectl logs --since=5m sip-proxy-7d4f8c-x9k2n -n voice-services

# Specific container in multi-container pod
kubectl logs sip-proxy-7d4f8c-x9k2n -n voice-services -c consul-sidecar

# All pods matching a label
kubectl logs -l app=sip-proxy -n voice-services --all-containers=true
```

🔧 **NOC Tip:** `--previous` is your best friend for crashed containers. When a pod is in CrashLoopBackOff, the current container has no useful logs (it just started and is about to crash again). `--previous` shows logs from the *last* crashed instance, which contain the actual error.

## Step 4: What's Happening Inside? — kubectl exec

When logs aren't enough, get a shell inside the container:

```bash
# Interactive shell
kubectl exec -it sip-proxy-7d4f8c-x9k2n -n voice-services -- /bin/bash

# If bash isn't available (minimal images)
kubectl exec -it sip-proxy-7d4f8c-x9k2n -n voice-services -- /bin/sh

# Run a single command
kubectl exec sip-proxy-7d4f8c-x9k2n -n voice-services -- cat /etc/config/sip.conf

# Test network connectivity from inside the pod
kubectl exec sip-proxy-7d4f8c-x9k2n -n voice-services -- \
  curl -s http://billing-service.billing.svc.cluster.local:8080/health

# Check DNS resolution inside the pod
kubectl exec sip-proxy-7d4f8c-x9k2n -n voice-services -- \
  nslookup consul.service.consul
```

This is invaluable for verifying:
- Configuration files are correct (mounted ConfigMaps/Secrets)
- The container can reach dependent services (network connectivity)
- DNS resolution works from the pod's perspective
- Environment variables are set correctly

**Warning:** Many production containers use minimal base images (distroless, alpine) with no debugging tools. If you can't run `curl` or `nslookup`, deploy an ephemeral debug container or use `kubectl debug`.

## Step 5: Is It a Resource Problem? — kubectl top

```bash
# Pod-level CPU and memory usage
kubectl top pods -n voice-services

# Sort by CPU
kubectl top pods -n voice-services --sort-by=cpu

# Node-level usage
kubectl top nodes
```

Example output:
```
NAME                    CPU(cores)   MEMORY(bytes)
sip-proxy-7d4f8c-x9k2n 1850m        920Mi
sip-proxy-7d4f8c-a3b4c 450m         380Mi
sip-proxy-7d4f8c-k8m2p 1920m        980Mi
```

If the memory limit is 1Gi and pods are using 980Mi, they're about to be OOMKilled. If CPU usage matches the CPU limit, pods are being throttled.

## Putting It All Together: Real Investigation

**Alert:** `SIPProxyHighErrorRate` firing for voice-services namespace.

```bash
# 1. Find unhealthy pods
kubectl get pods -n voice-services -l app=sip-proxy
# Two pods show RESTARTS: 5 in the last hour

# 2. Describe the restarting pod
kubectl describe pod sip-proxy-7d4f8c-k8m2p -n voice-services
# Events show OOMKilled, exit code 137

# 3. Check logs from the crashed instance
kubectl logs sip-proxy-7d4f8c-k8m2p -n voice-services --previous
# "java.lang.OutOfMemoryError: Java heap space"
# The JVM heap is misconfigured for the container's memory limit

# 4. Check resource usage across all sip-proxy pods
kubectl top pods -n voice-services -l app=sip-proxy
# Surviving pods are at 90% memory — they'll crash soon too

# 5. Immediate mitigation: scale up to distribute load
kubectl scale deployment sip-proxy -n voice-services --replicas=8
```

This entire investigation takes under 3 minutes with practiced hands.

## Useful Aliases

Experienced NOC engineers create shell aliases for common commands:

```bash
alias k='kubectl'
alias kgp='kubectl get pods'
alias kgpa='kubectl get pods -A'
alias kdp='kubectl describe pod'
alias kl='kubectl logs'
alias klp='kubectl logs --previous'
alias kt='kubectl top pods'
```

---

**Key Takeaways:**

1. Start investigations with `kubectl get pods -A | grep -v Running` to find unhealthy pods instantly
2. `kubectl describe` reveals events and conditions — always read the Events section
3. `kubectl logs --previous` shows logs from crashed containers — essential for CrashLoopBackOff
4. `kubectl exec` lets you verify configuration, connectivity, and DNS from inside the pod
5. `kubectl top` reveals CPU/memory usage — compare to limits to detect OOMKill and throttling risks
6. Build muscle memory with these commands; speed matters during incidents

**Next: Lesson 94 — Kubernetes Events and Debugging Scheduling Failures**
