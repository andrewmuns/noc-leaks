# Lesson 94: AI/Inference — Scaling and Auto-scaling Inference
**Module 2 | Section 2.12 — Storage/AI**
**⏱ ~5min read | Prerequisites: Lesson 82**
---

## Introduction

A single GPU node can handle only so many inference requests per second. As Telnyx's AI products grow — speech recognition, text-to-speech, LLM assistants, number intelligence — the inference platform must scale horizontally. But GPU scaling is not like scaling web servers. GPUs are expensive, models take minutes to load, and the wrong auto-scaling strategy can either waste $100K/month in idle GPUs or leave customers waiting in a queue.

This lesson covers how Telnyx scales inference workloads, from basic replication to sophisticated auto-scaling strategies.

---

## Horizontal Scaling: Adding Replicas

The simplest form of scaling is running multiple copies (replicas) of the same model across different GPU nodes. A load balancer distributes incoming inference requests across replicas.

```yaml
# Kubernetes Deployment for an inference model
apiVersion: apps/v1
kind: Deployment
metadata:
  name: llm-7b-inference
spec:
  replicas: 4  # Four copies across four GPU nodes
  selector:
    matchLabels:
      app: llm-7b-inference
  template:
    spec:
      containers:
      - name: inference
        image: registry.telnyx.com/ai/vllm:latest
        resources:
          limits:
            nvidia.com/gpu: 1
        env:
        - name: MODEL_NAME
          value: "telnyx/llm-7b"
```

### Load Balancing Strategies

Not all inference requests are equal. A 10-token completion takes milliseconds; a 2000-token generation takes seconds. Simple round-robin can send long requests to an already-busy GPU.

- **Round-robin:** Simple but unaware of load. Works for uniform request sizes.
- **Least-connections:** Routes to the replica with fewest active requests. Better for variable workloads.
- **Queue-depth-aware:** Routes to the replica with the shallowest pending queue. Best for inference.

🔧 **NOC Tip:** At Telnyx, if you see uneven GPU utilization across replicas (one at 95%, another at 30%), the load balancing strategy may be wrong. Least-connections or queue-depth routing should be used for inference workloads. Flag this to the AI platform team.

---

## Batching Strategies

GPUs are massively parallel processors. Serving one request at a time wastes most of the GPU's compute capacity. **Batching** groups multiple requests together for parallel processing.

### Static Batching

Collect N requests, process them together, return all results. Simple but introduces latency — the batch waits until it's full or a timeout expires.

```
# Static batch config
max_batch_size: 32
batch_timeout_ms: 50  # Don't wait longer than 50ms to fill a batch
```

### Continuous (In-flight) Batching

Modern inference servers like vLLM use continuous batching. New requests join the batch as soon as a slot opens — no waiting for the full batch to complete. This dramatically improves both throughput and latency.

```
Continuous batching timeline:
  t=0   [Req A starts] [Req B starts] [Req C starts]
  t=10  [Req A done → Req D starts]   [Req B continues] [Req C continues]
  t=15  [Req D continues] [Req B done → Req E starts] [Req C continues]
```

### Impact on NOC Monitoring

Batch size directly affects the metrics you monitor:

- **Throughput (requests/sec):** Higher batch sizes = higher throughput.
- **Latency (p50, p99):** Larger static batches increase tail latency. Continuous batching keeps latency more consistent.
- **GPU memory:** Larger batches consume more VRAM. Watch for OOM.

🔧 **NOC Tip:** If inference latency suddenly spikes but GPU utilization stays moderate, check if the batch configuration changed. A misconfigured `max_batch_size` (too large) or `batch_timeout_ms` (too long) can cause unnecessary queuing.

---

## Queue Depth: The Key Scaling Signal

Queue depth measures how many inference requests are waiting to be processed. It's the most important signal for scaling decisions.

```
Request Flow:
  Client → Load Balancer → [Queue] → GPU Processing → Response
                             ↑
                     Queue depth = waiting requests
```

### Healthy vs Unhealthy Queue Depth

| Queue Depth | Meaning | Action |
|-------------|---------|--------|
| 0 | GPU is idle between requests | Possible over-provisioning |
| 1–5 | Healthy — requests flow smoothly | Normal operation |
| 10–20 | Building up — approaching saturation | Monitor closely |
| 50+ | Severely backed up | Scale up or investigate |

### Monitoring Queue Depth

```promql
# Prometheus query for inference queue depth
inference_queue_depth{model="llm-7b"}

# Alert when queue exceeds threshold for 2 minutes
inference_queue_depth{model="llm-7b"} > 20
```

🔧 **NOC Tip:** Queue depth is the metric that most directly correlates with customer experience. A customer doesn't care about your GPU utilization — they care that their API call returned in 500ms, not 10s. When queue depth climbs, latency follows.

---

## Cold Start: The Model Loading Problem

Unlike web servers that start in seconds, inference services must load the model into GPU memory before serving requests. This is the **cold start** problem.

### Typical Cold Start Times

| Model Size | Load Time | GPU Memory |
|-----------|-----------|------------|
| 1B params (FP16) | 5–10s | ~2 GB |
| 7B params (FP16) | 20–45s | ~14 GB |
| 13B params (FP16) | 45–90s | ~26 GB |
| 70B params (FP16) | 3–8min | ~140 GB (multi-GPU) |

### Cold Start Mitigation

1. **Pre-warming:** Keep minimum replicas always running — never scale to zero for production models.
2. **Model caching:** Store model weights on fast local NVMe so reloads are faster than pulling from object storage.
3. **Staggered scaling:** Don't scale up 10 replicas simultaneously — they'll all be loading and unable to serve.
4. **Health check grace period:** Configure Kubernetes readiness probes to account for model load time.

```yaml
# Readiness probe with startup grace period
readinessProbe:
  httpGet:
    path: /health
    port: 8080
  initialDelaySeconds: 120  # Give model time to load
  periodSeconds: 10
startupProbe:
  httpGet:
    path: /health
    port: 8080
  failureThreshold: 30
  periodSeconds: 10  # Up to 5 minutes to start
```

🔧 **NOC Tip:** During incidents, if you see new inference pods stuck in `Running` but not `Ready`, they're likely still loading the model. Don't panic — check the pod logs for model loading progress. For large models (70B+), this can take several minutes. The startup probe prevents traffic from hitting them too early.

---

## Auto-scaling Triggers

Auto-scaling for inference workloads uses Kubernetes HPA (Horizontal Pod Autoscaler) or custom controllers that react to GPU-specific metrics.

### Common Auto-scaling Metrics

```yaml
# HPA based on custom GPU metrics
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: llm-7b-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: llm-7b-inference
  minReplicas: 2        # Never go below 2 for redundancy
  maxReplicas: 16       # Cost ceiling
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Pods
        value: 2         # Add at most 2 pods per minute
        periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300  # Wait 5min before scaling down
      policies:
      - type: Pods
        value: 1
        periodSeconds: 120
  metrics:
  - type: Pods
    pods:
      metric:
        name: inference_queue_depth
      target:
        type: AverageValue
        averageValue: "5"  # Scale up when avg queue > 5 per replica
```

### GPU Utilization vs Request Latency

These two metrics often tell different stories:

| Scenario | GPU Utilization | Request Latency | Meaning |
|----------|----------------|-----------------|---------|
| Normal | 50–70% | Low (<500ms) | Healthy |
| Saturated | 95%+ | High (>2s) | Need more replicas |
| Inefficient batching | 30% | High (>2s) | Requests waiting, GPU underused — fix batching |
| Memory pressure | 80% | Spiky | OOM-adjacent — reduce batch size |

🔧 **NOC Tip:** **Never auto-scale on GPU utilization alone.** A GPU at 40% utilization might have terrible latency if the batching is wrong. Always include a latency or queue-depth signal in auto-scaling. At Telnyx, the standard is: scale up when `queue_depth > 5` AND `p99_latency > 1s`.

---

## Scaling Anti-patterns

### Scaling Too Aggressively

Adding 10 replicas at once means 10 simultaneous cold starts competing for network bandwidth to download model weights. Throughput actually decreases during this period.

### Scaling to Zero

For cost savings, some teams want to scale production models to zero replicas when idle. This means the next request waits 1–5 minutes. Never do this for customer-facing models.

### Ignoring Scale-down

If the HPA scales up aggressively but never scales down, you end up with dozens of idle GPU nodes burning money. Set `scaleDown.stabilizationWindowSeconds` to a reasonable value (5–15 minutes).

---

## Key Takeaways

1. **Horizontal scaling** adds model replicas across GPU nodes; use queue-depth-aware load balancing for best results.
2. **Continuous batching** (used in vLLM) is superior to static batching — it maximizes GPU throughput while minimizing latency.
3. **Queue depth** is the single most important metric for inference scaling — it directly predicts customer-facing latency.
4. **Cold starts** for large models can take minutes; always maintain minimum replicas and use startup probes.
5. **Auto-scaling should use queue depth or latency** as the primary trigger, not GPU utilization alone.
6. **Scale up gradually** (2 pods at a time) and **scale down slowly** (5-minute stabilization) to avoid thrashing.
7. **Never scale customer-facing models to zero** — the cold start penalty is unacceptable for production traffic.

---

**Next: Lesson 85 — Storage: Distributed Object Storage and Telnyx Storage**
